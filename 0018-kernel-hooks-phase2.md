## 上下文和问题陈述

目前，内核调用和调用的处理程序不会向处理程序公开提示。

该提案是一种向处理程序公开 prompt 的方法。

- 预执行 / 调用

  - Get：调用 LLM 之前 `SemanticFunction.TemplateEngine`current 生成的提示 
  - Set：在将提示内容发送到 LLM 之前对其进行修改

- 后执行 / 调用

  - Get：生成的提示

## 决策驱动因素

- 在 Kernel.RunAsync 执行中，每个函数执行只应生成一次提示模板。
- 处理程序应该能够在 LLM 执行之前查看和修改提示。
- 处理程序应该能够在 LLM 执行后看到 prompt。
- 调用 Kernel.RunAsync（function） 或 ISKFunction.InvokeAsync（kernel） 应触发事件。

## 超出范围

- 使用 Pre-Hooks 跳过计划步骤。
- 在 Pre/Post Hooks 中获取使用过的服务（Template Engine、IAIServices 等）。
- 在 Pre/Post Hooks 中获取请求设置。

## 前/后钩子的内核当前状态

内核的当前状态：

```csharp
class Kernel : IKernel

RunAsync()
{
    var context = this.CreateNewContext(variables);
    var functionDetails = skFunction.Describe();
    var functionInvokingArgs = this.OnFunctionInvoking(functionDetails, context);

    functionResult = await skFunction.InvokeAsync(context, cancellationToken: cancellationToken);
    var functionInvokedArgs = this.OnFunctionInvoked(functionDetails, functionResult);
}
```

## 开发人员体验

以下是使用 Pre/Post Hooks 进行编码以获取或修改提示时的预期最终用户体验。

```csharp
const string FunctionPrompt = "Write a random paragraph about: {{$input}}.";

var excuseFunction = kernel.CreateSemanticFunction(...);

void MyPreHandler(object? sender, FunctionInvokingEventArgs e)
{
    Console.WriteLine($"{e.FunctionView.PluginName}.{e.FunctionView.Name} : Pre Execution Handler - Triggered");

    // Will be false for non semantic functions
    if (e.TryGetRenderedPrompt(out var prompt))
    {
        Console.WriteLine("Rendered Prompt:");
        Console.WriteLine(prompt);

        // Update the prompt if needed
        e.TryUpdateRenderedPrompt("Write a random paragraph about: Overriding a prompt");
    }
}

void MyPostHandler(object? sender, FunctionInvokedEventArgs e)
{
    Console.WriteLine($"{e.FunctionView.PluginName}.{e.FunctionView.Name} : Post Execution Handler - Triggered");
    // Will be false for non semantic functions
    if (e.TryGetRenderedPrompt(out var prompt))
    {
        Console.WriteLine("Used Prompt:");
        Console.WriteLine(prompt);
    }
}

kernel.FunctionInvoking += MyPreHandler;
kernel.FunctionInvoked += MyPostHandler;

const string Input = "I missed the F1 final race";
var result = await kernel.RunAsync(Input, excuseFunction);
Console.WriteLine($"Function Result: {result.GetValue<string>()}");
```

预期输出：

```
MyPlugin.MyFunction : Pre Execution Handler - Triggered
Rendered Prompt:
Write a random paragraph about: I missed the F1 final race.

MyPlugin.MyFunction : Post Execution Handler - Triggered
Used Prompt:
Write a random paragraph about: Overriding a prompt

FunctionResult: <LLM Completion>
```

## 考虑的选项

### 所有选项通用的改进

将 `Dictionary<string, object>` property `Metadata` 从 `FunctionInvokedEventArgs`  移动到 `SKEventArgs` abstract class。

优点：

- 这将使所有 SKEventArgs 可扩展，从而允许在不可能时将额外信息传递给 EventArgs `specialization` 。

### 选项 1：SemanticFunctions 的内核感知

```csharp
class Kernel : IKernel

RunAsync()
{

    if (skFunction is SemanticFunction semanticFunction)
    {
        var prompt = await semanticFunction.TemplateEngine.RenderAsync(semanticFunction.Template, context);
        var functionInvokingArgs = this.OnFunctionInvoking(functionDetails, context, prompt);
        // InvokeWithPromptAsync internal
        functionResult = await semanticFunction.InternalInvokeWithPromptAsync(prompt, context, cancellationToken: cancellationToken);
    }
    else
    {
        functionResult = await skFunction.InvokeAsync(context, cancellationToken: cancellationToken);
    }
}
class SemanticFunction : ISKFunction

public InvokeAsync(context, cancellationToken)
{
    var prompt = _templateEngine.RenderAsync();
    return InternalInvokeWithPromptAsync(prompt, context, cancellationToken);
}

internal InternalInvokeWithPromptAsync(string prompt)
{
    ... current logic to call LLM
}
```

### 优点和缺点

优点：

- 实施更简单、更快捷
- 少量更改主要限于 `Kernel` 和 `SemanticFunction` 类

缺点：

- `Kernel` 了解 `SemanticFunction` 实现细节
- 无法扩展以显示自定义实现的提示 `ISKFunctions` 

### 选项 2：将如何处理事件委托给 ISKFunction （Interfaces 方法）

```csharp
class Kernel : IKernel
{
    RunAsync() {
        var functionInvokingArgs = await this.TriggerEvent<FunctionInvokingEventArgs>(this.FunctionInvoking, skFunction, context);

        var functionResult = await skFunction.InvokeAsync(context, cancellationToken: cancellationToken);

        var functionInvokedArgs = await this.TriggerEvent<FunctionInvokedEventArgs>(
            this.FunctionInvoked,
            skFunction,
            context);
    }

    private TEventArgs? TriggerEvent<TEventArgs>(EventHandler<TEventArgs>? eventHandler, ISKFunction function, SKContext context) where TEventArgs : SKEventArgs
    {
        if (eventHandler is null)
        {
            return null;
        }

        if (function is ISKFunctionEventSupport<TEventArgs> supportedFunction)
        {
            var eventArgs = await supportedFunction.PrepareEventArgsAsync(context);
            eventHandler.Invoke(this, eventArgs);
            return eventArgs;
        }

        // Think about allowing to add data with the extra interface.

        // If a function don't support the specific event we can:
        return null; // Ignore or Throw.
        throw new NotSupportedException($"The provided function \"{function.Name}\" does not supports and implements ISKFunctionHandles<{typeof(TEventArgs).Name}>");
    }
}

public interface ISKFunctionEventSupport<TEventArgs> where TEventArgs : SKEventArgs
{
    Task<TEventArgs> PrepareEventArgsAsync(SKContext context, TEventArgs? eventArgs = null);
}

class SemanticFunction : ISKFunction,
    ISKFunctionEventSupport<FunctionInvokingEventArgs>,
    ISKFunctionEventSupport<FunctionInvokedEventArgs>
{

    public FunctionInvokingEventArgs PrepareEventArgsAsync(SKContext context, FunctionInvokingEventArgs? eventArgs = null)
    {
        var renderedPrompt = await this.RenderPromptTemplateAsync(context);
        context.Variables.Set(SemanticFunction.RenderedPromptKey, renderedPrompt);

        return new SemanticFunctionInvokingEventArgs(this.Describe(), context);
        // OR                                                          Metadata Dictionary<string, object>
        return new FunctionInvokingEventArgs(this.Describe(), context, new Dictionary<string, object>() { { RenderedPrompt, renderedPrompt } });
    }

    public FunctionInvokedEventArgs PrepareEventArgsAsync(SKContext context, FunctionInvokedEventArgs? eventArgs = null)
    {
        return Task.FromResult<FunctionInvokedEventArgs>(new SemanticFunctionInvokedEventArgs(this.Describe(), context));
    }
}

public sealed class SemanticFunctionInvokedEventArgs : FunctionInvokedEventArgs
{
    public SemanticFunctionInvokedEventArgs(FunctionDescription functionDescription, SKContext context)
        : base(functionDescription, context)
    {
        _context = context;
        Metadata[RenderedPromptKey] = this._context.Variables[RenderedPromptKey];
    }

    public string? RenderedPrompt => this.Metadata[RenderedPromptKey];

}

public sealed class SemanticFunctionInvokingEventArgs : FunctionInvokingEventArgs
{
    public SemanticFunctionInvokingEventArgs(FunctionDescription functionDescription, SKContext context)
        : base(functionDescription, context)
    {
        _context = context;
    }
    public string? RenderedPrompt => this._context.Variables[RenderedPromptKey];
}
```

### 优点和缺点

优点：

- `Kernel` 不知道 `SemanticFunction` 实现细节或任何其他 `ISKFunction` 实现
- 可扩展以显示每个自定义实现的专用 EventArgs `ISKFunctions` ，包括语义函数的提示
- 可扩展以支持内核上的未来事件 `ISKFunctionEventSupport<NewEvent>` 
- 函数可以有自己的 EventArgs 特化。
- interface 是可选的，因此 custom `ISKFunctions` 可以选择是否实现它

缺点：

- 如果任何自定义函数 `ISKFunctionEventSupport` 现在想要支持事件，则必须负责实现接口。
- 在另一个事件处理方法中处理事件 `ISKFunction` 需要更复杂的方法来管理上下文和提示 + 不同事件处理方法中的任何其他数据。

### 选项 3：将如何处理事件委托给 ISKFunction（InvokeAsync 委托方法）

将 Kernel 事件处理程序委托包装器添加到 `ISKFunction.InvokeAsync` 接口。
这种方法分担了处理 和 实现之间的事件 `Kernel` `ISKFunction`的责任，流控制将由 Kernel 处理，而 Kernel `ISKFunction` 将负责调用委托包装器并将数据添加到 `SKEventArgs` 将传递给处理程序的数据中。

```csharp
class Kernel : IKernel
{
    RunAsync() {
        var functionInvokingDelegateWrapper = new(this.FunctionInvoking);
        var functionInvokedDelegateWrapper = new(this.FunctionInvoked);

        var functionResult = await skFunction.InvokeAsync(context, functionInvokingDelegateWrapper, functionInvokingDelegateWrapper, functionInvokedDelegateWrapper);

        // Kernel will analyze the delegate results and make flow related decisions
        if (functionInvokingDelegateWrapper.EventArgs.CancelRequested ... ) { ... }
        if (functionInvokingDelegateWrapper.EventArgs.SkipRequested ... ) { ... }
        if (functionInvokedDelegateWrapper.EventArgs.Repeat ... ) { ... }
    }
}

class SemanticFunction : ISKFunction {
    InvokeAsync(
        SKContext context,
        FunctionInvokingDelegateWrapper functionInvokingDelegateWrapper,
        FunctionInvokedDelegateWrapper functionInvokedDelegateWrapper)
    {
        // The Semantic will have to call the delegate wrappers and share responsibility with the `Kernel`.
        if (functionInvokingDelegateWrapper.Handler is not null)
        {
            var renderedPrompt = await this.RenderPromptTemplateAsync(context);
            functionInvokingDelegateWrapper.EventArgs.RenderedPrompt = renderedPrompt;

            functionInvokingDelegateWrapper.Handler.Invoke(this, functionInvokingDelegateWrapper.EventArgs);

            if (functionInvokingDelegateWrapper.EventArgs?.CancelToken.IsCancellationRequested ?? false)
            {
                // Need to enforce an non processed result
                return new SKFunctionResult(context);

                //OR make InvokeAsync allow returning null FunctionResult?
                return null;
            }
        }
    }
}

// Wrapper for the EventHandler
class FunctionDelegateWrapper<TEventArgs> where TEventArgs : SKEventArgs
{
    FunctionInvokingDelegateWrapper(EventHandler<TEventArgs> eventHandler) {}

    // Set allows specialized eventargs to be set.
    public TEventArgs EventArgs { get; set; }
    public EventHandler<TEventArgs> Handler => _eventHandler;
}
```

### 优点和缺点

优点：

- `ISKFunction` 在 EventArgs 中处理和公开数据 （Rendered Prompt） 和状态的代码/复杂性较低。
- `Kernel` 不知道 `SemanticFunction` 实现细节或任何其他 `ISKFunction` 实现
- `Kernel` 代码/复杂性较低
- 可以扩展以显示每个自定义实现的专用 EventArgs `ISKFunctions` ，包括语义函数的提示

缺点：

- 如果需要，无法添加新事件（需要更改 ISKFunction 接口）
- 函数需要实现与依赖项 （Kernel） 事件相关的行为
- 由于 Kernel 需要与事件处理程序的结果进行交互，因此需要一个包装策略来通过内核级别的引用访问结果（流的控制）
- 将 Kernel 事件处理程序的全部责任传递给下游的函数听起来不太正确 （Single Responsibility）

### 选项 4：将如何处理事件委托给 ISKFunction （SKContext Delegates 方法）

将 Kernel 事件处理程序委托包装器添加到 `ISKFunction.InvokeAsync` 接口。
这种方法分担了处理 和 实现之间的事件 `Kernel` `ISKFunction`的责任，流控制将由 Kernel 处理，而 Kernel `ISKFunction` 将负责调用委托包装器并将数据添加到 `SKEventArgs` 将传递给处理程序的数据中。

```csharp
class Kernel : IKernel
{
    CreateNewContext() {
        var context = new SKContext(...);
        context.AddEventHandlers(this.FunctionInvoking, this.FunctionInvoked);
        return context;
    }
    RunAsync() {
        functionResult = await skFunction.InvokeAsync(context, ...);
        if (this.IsCancelRequested(functionResult.Context)))
            break;
        if (this.IsSkipRequested(functionResult.Context))
            continue;
        if (this.IsRepeatRequested(...))
            goto repeat;

        ...
    }
}

class SKContext {

    internal EventHandlerWrapper<FunctionInvokingEventArgs>? FunctionInvokingHandler { get; private set; }
    internal EventHandlerWrapper<FunctionInvokedEventArgs>? FunctionInvokedHandler { get; private set; }

    internal SKContext(
        ...
        ICollection<EventHandlerWrapper?>? eventHandlerWrappers = null
    {
        ...
        this.InitializeEventWrappers(eventHandlerWrappers);
    }

    void InitializeEventWrappers(ICollection<EventHandlerWrapper?>? eventHandlerWrappers)
    {
        if (eventHandlerWrappers is not null)
        {
            foreach (var handler in eventHandlerWrappers)
            {
                if (handler is EventHandlerWrapper<FunctionInvokingEventArgs> invokingWrapper)
                {
                    this.FunctionInvokingHandler = invokingWrapper;
                    continue;
                }

                if (handler is EventHandlerWrapper<FunctionInvokedEventArgs> invokedWrapper)
                {
                    this.FunctionInvokedHandler = invokedWrapper;
                }
            }
        }
    }
}

class SemanticFunction : ISKFunction {
    InvokeAsync(
        SKContext context
    {
        string renderedPrompt = await this._promptTemplate.RenderAsync(context, cancellationToken).ConfigureAwait(false);

        this.CallFunctionInvoking(context, renderedPrompt);
        if (this.IsInvokingCancelOrSkipRequested(context, out var stopReason))
        {
            return new StopFunctionResult(this.Name, this.PluginName, context, stopReason!.Value);
        }

        string completion = await GetCompletionsResultContentAsync(...);

        var result = new FunctionResult(this.Name, this.PluginName, context, completion);
        result.Metadata.Add(SemanticFunction.RenderedPromptMetadataKey, renderedPrompt);

        this.CallFunctionInvoked(result, context, renderedPrompt);
        if (this.IsInvokedCancelRequested(context, out stopReason))
        {
            return new StopFunctionResult(this.Name, this.PluginName, context, result.Value, stopReason!.Value);
        }

        return result;
    }
}
```

### 优点和缺点

优点：

- `ISKFunction` 在 EventArgs 中处理和公开数据 （Rendered Prompt） 和状态的代码/复杂性较低。
- `Kernel` 不知道 `SemanticFunction` 实现细节或任何其他 `ISKFunction` 实现
- `Kernel` 代码/复杂性较低
- 可以扩展以显示每个自定义实现的专用 EventArgs `ISKFunctions` ，包括语义函数的提示
- 可扩展性更强，因为 `ISKFunction` 无需更改接口即可添加新事件。
- `SKContext` 可以扩展以添加新事件，而不会引入中断性变更。

缺点：

- 函数现在需要实现逻辑来处理上下文中的事件
- 由于 Kernel 需要与事件处理程序的结果进行交互，因此需要一个包装策略来通过内核级别的引用访问结果（流的控制）
- 将 Kernel 事件处理程序的全部责任传递给下游的函数听起来不太正确 （Single Responsibility）

## 决策结果

### 选项 4：将如何处理事件委托给 ISKFunction （SKContext Delegates 方法）

这允许函数实现一些内核逻辑，但有一个很大的好处，即不会为同一 Execution Context 的不同方法拆分 logic。

最大好处：
**`ISKFunction` 在 EventArgs 中处理和公开数据和状态的代码/复杂性较低。**
**`ISKFunction` interface 不需要更改来添加新事件。**

此实现允许在 InvokeAsync 中获取 renderedPrompt，而无需使用不同的方法管理上下文和提示。

上述内容也适用于调用中可用的任何其他数据，并且可以将其添加为新的 EventArgs 属性。
