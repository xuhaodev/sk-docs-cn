
# 内核/函数处理程序 - 第 1 阶段

## 上下文和问题陈述

Kernel 函数调用者需要能够在尝试之前和之后处理/拦截 Kernel 中的任何函数执行。允许它修改提示、中止执行或修改输出和许多其他方案，如下所示：

- 预执行 / 函数调用

  - 获取： SKContext
  - Set：修改发送到函数的输入参数
  - Set：Abort/Cancel 管道执行
  - Set：跳过函数执行

- 后执行 / 调用的函数

  - Get：LLM 模型结果（令牌使用、停止序列等）
  - 获取： SKContext
  - Get：输出参数
  - Set：修改输出参数内容（返回输出前）
  - Set：取消管道执行
  - Set：重复函数执行

## 超出范围（将处于第 2 阶段）

- 预执行 / 函数调用

  - Get：呈现的提示
  - Get：当前使用的设置
  - Set：修改渲染的提示

- 后执行 / 调用的函数
  - Get：呈现的提示
  - Get：当前使用的设置

## 决策驱动因素

- 架构更改和相关的决策过程应该对社区透明。
- 决策记录存储在存储库中，涉及各种语言端口的团队可以轻松发现。
- 简单、可扩展且易于理解。

## 考虑的选项

1. 回调注册 + 递归
2. 单次回调
3. 基于事件的注册
4. 中间件
5. ISKFunction 事件支持接口

## 选项的优缺点

### 1. 回调注册递归委托 （kernel， plan， function）

- 在 plan 和 function 级别指定为 configuration 时，能够指定将触发的回调 Handlers 是什么。

优点：

- 用于观察和将作为参数公开的数据更改为 （Get/Set） 方案的委托签名的常见模式
- 注册回调会返回可用于在将来取消函数执行的注册对象。
- 递归方法，允许为同一事件注册多个回调，还允许在预先存在的回调之上注册回调。

缺点：

- 注册可能会使用更多内存，并且可能不会在递归方法中进行垃圾回收，只有在释放函数或计划时才会进行。

### 2. 单个回调委托 （Kernel， Plan， Function）

- 在内核级别指定为 configuration ，能够指定将触发的回调 Handlers 是什么。
  - 在函数创建时指定：作为函数构造函数的一部分，能够指定将触发的回调处理程序是什么。
  - 在函数调用时指定：作为函数调用的一部分，能够指定什么是回调处理程序作为将触发的参数。

优点：

- 用于观察和将作为参数公开的数据更改为 （Get/Set） 方案的委托签名的常见模式

缺点：

- 仅限于一种观察特定事件的方法（Pre Post 和 InExecution）。- 函数 用作参数时，需要三个新参数作为函数的一部分。（在函数调用时指定）- 额外 Cons on

### 3. 事件基础注册（仅限 Kernel）

在 IKernel 和 ISKFunction 上公开调用可以观察交互的事件。

优点：

- 多个侦听器可以为同一事件注册
- 监听器可以随意注册和注销
- 用于观察和将作为参数公开的数据更改为 （Get/Set） 方案的事件签名的常见模式 （EventArgs）

缺点：

- 事件处理程序是 void 的，这使得 EventArgs by reference 成为修改数据的唯一方法。
- 不清楚这种方法对异步模式/多线程的支持程度
- 不支持 `ISKFunction.InvokeAsync`

### 4. 中间件（仅限内核）

在内核级别指定，并且只能通过 IKernel.RunAsync作使用，此模式类似于 asp.net 核心中间件，使用上下文和 requestdelegate next 运行管道以控制（Pre/Post 条件）

优点：

- 处理 Pre/Post Setting/Filtering 数据的通用模式

缺点：

- 函数可以在自己的实例上运行，中间件意味着更多的复杂性，并且存在外部容器/管理器（内核）来拦截/观察函数调用。

### 5. ISKFunction 事件支持接口

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
- `Kernel` 将不得不检查该函数是否实现了该接口，如果没有，则必须抛出异常或忽略该事件。
- 曾经仅限于 InvokeAsync 的函数实现现在需要分散在多个位置，并处理与需要在调用开始或结束时获取的内容相关的执行状态。

## 主要问题

- 问：执行后处理程序应该在 LLM 结果之后还是在函数执行本身结束之前立即执行？
  A：目前 post execution Handler 是在函数执行后执行的。

- 问：前/后处理程序是否应该很多 （pub/sub） 允许注册/注销？
  答：通过使用标准 .NET 事件实现，这已经支持由调用方管理的多个注册和注销。

- 问：应该允许在预先存在的 Handlers 之上设置 Handlers，否则会引发错误？
  答：通过使用标准 .NET 事件实现，标准行为不会引发错误，并且会执行所有已注册的处理程序。

- 问：在计划上设置 Handlers 应该自动为所有内部步骤 + 覆盖流程中的现有步骤级联此 Handlers？
  答：处理程序将在执行每个步骤之前和之后触发，其方式与 Kernel RunAsync 管道的工作方式相同。

- 问：当函数执行前处理程序打算取消执行时，是否应该调用链中的其他处理程序？
  答：目前，标准的 .net 行为是调用所有已注册的处理程序。这样，函数执行将完全取决于调用所有处理程序后 Cancellation Request 的最终状态。

## 决策结果

已选选项： **3.事件基础注册（仅限内核）**

此方法是最简单的方法，并且利用了标准 .NET 事件实现的优势。

将实施进一步的更改，以完全支持第 2 阶段中的所有场景。
