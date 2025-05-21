
# 筛选器中的异常处理

## 上下文和问题陈述

在 .NET 版本的语义内核中，当内核函数引发异常时，它将通过执行堆栈传播，直到某些代码捕获它。要处理 的异常 `kernel.InvokeAsync(function)`，此代码应包装在 block 中 `try/catch` ，这是处理异常的直观方法。

不幸的是， `try/catch` block 对于自动函数调用场景没有用，当一个函数是基于某个提示被调用时。在这种情况下，当 function 抛出异常时，消息 `Error: Exception while invoking function.` 将被添加到具有`tool`作者角色的聊天历史记录中，这应该为 LLM 提供一些出错的上下文。

需要能够覆盖函数 result - 而不是抛出异常并向 AI 发送错误消息，应该可以设置一些自定义结果，这应该允许控制 LLM 行为。

## 考虑的选项

### [选项 1] 向现有接口添加新方法 `IFunctionFilter` 

抽象化：

```csharp
public interface IFunctionFilter
{
    void OnFunctionInvoking(FunctionInvokingContext context);

    void OnFunctionInvoked(FunctionInvokedContext context);

    // New method
    void OnFunctionException(FunctionExceptionContext context);
}
```

弊：

- 向现有接口添加新方法将是一项重大更改，因为它将强制当前过滤器用户实现新方法。
- 使用函数过滤器时，即使不需要异常处理，也始终需要实现此方法。另一方面，此方法不会返回任何内容，因此它可能始终为空，或者使用 .NET 多目标，应该可以为 C# 8 及更高版本定义默认实现。

### [选项 2] 引入新 `IExceptionFilter` 界面

新接口将允许接收异常对象、取消异常或重新引发新类型的异常。此选项也可以稍后添加为更高级别的过滤器，以进行全局异常处理。

抽象化：

```csharp
public interface IExceptionFilter
{
    // ExceptionContext class will contain information about actual exception, kernel function etc.
    void OnException(ExceptionContext context);
}
```

用法：

```csharp
public class MyFilter : IFunctionFilter, IExceptionFilter
{
    public void OnFunctionInvoking(FunctionInvokingContext context) { }

    public void OnFunctionInvoked(FunctionInvokedContext context) { }

    public void OnException(ExceptionContext context) {}
}
```

优势：

- 这不是一个重大更改，所有异常处理逻辑都应该添加到现有筛选机制之上。
- 类似于 `IExceptionFilter` ASP.NET 中的 API。

弊：

- 对于异常处理，应该实现单独的接口，这可能不直观且难以记住。

### [选项 3] 在现有接口中扩展 Context 模型 `IFunctionFilter` 

在 method 中 `IFunctionFilter.OnFunctionInvoked` ，可以通过添加 property 来扩展 `FunctionInvokedContext` model `Exception` 。在这种情况下，`OnFunctionInvoked`一旦触发，就可以观察函数执行期间是否有异常。

如果出现异常，用户什么都不能做，异常会照常抛出，这意味着为了处理它，函数调用应该用 block 包装 `try/catch` 。但是也可以取消该异常并覆盖函数结果，这应该可以更好地控制函数执行和传递给 LLM 的内容。

抽象化：

```csharp
public sealed class FunctionInvokedContext : FunctionFilterContext
{
    // other properties...

    public Exception? Exception { get; private set; }
}
```

用法：

```csharp
public class MyFilter : IFunctionFilter
{
    public void OnFunctionInvoking(FunctionInvokingContext context) { }

    public void OnFunctionInvoked(FunctionInvokedContext context)
    {
        // This means that exception occurred during function execution.
        // If we ignore it, the exception will be thrown as usual.
        if (context.Exception is not null)
        {
            // Possible options to handle it:

            // 1. Do not throw an exception that occurred during function execution
            context.Exception = null;

            // 2. Override the result with some value, that is meaningful to LLM
            context.Result = new FunctionResult(context.Function, "Friendly message instead of exception");

            // 3. Rethrow another type of exception if needed - Option 1.
            context.Exception = new Exception("New exception");

            // 3. Rethrow another type of exception if needed - Option 2.
            throw new Exception("New exception");
        }
    }
}
```

优势：

- 需要对现有实现进行最少的更改，并且不会破坏现有的过滤器用户。
- 类似于 `IActionFilter` ASP.NET 中的 API。
- 可扩展，因为可以在需要时为其他类型的过滤器（提示或函数调用过滤器）扩展类似的 Context 模型。

弊：

- 不。使用 或 的 NET 友好型异常处理方式 `context.Exception = null` `context.Exception = new AnotherException()`，而不是使用本机 `try/catch` 方法。

### [选项 4] 通过添加 `IFunctionFilter` 委托 `next` 来更改签名。

这种方法改变了过滤器目前的工作方式。`Invoking`在使用 delegate 执行函数期间，将只有一个方法将被调用，而不是在 filter 中`Invoked`有两个  and `next` 方法，该方法将负责调用管道中下一个注册的过滤器或函数本身，以防没有剩余的过滤器。

抽象化：

```csharp
public interface IFunctionFilter
{
    Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next);
}
```

用法：

```csharp
public class MyFilter : IFunctionFilter
{
    public async Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next)
    {
        // Perform some actions before function invocation
        await next(context);
        // Perform some actions after function invocation
    }
}
```

使用本机方法进行异常处理 `try/catch` ：

```csharp
public async Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next)
{
    try
    {
        await next(context);
    }
    catch (Exception exception)
    {
        this._logger.LogError(exception, "Something went wrong during function invocation");

        // Example: override function result value
        context.Result = new FunctionResult(context.Function, "Friendly message instead of exception");

        // Example: Rethrow another type of exception if needed
        throw new InvalidOperationException("New exception");
    }
}
```

优势：

- 本机方式如何处理和重新引发异常。
- 类似于 `IAsyncActionFilter` ASP.NET 中的`IEndpointFilter` API。
- 要实现一个 filter 方法而不是两个 （）`Invoking/Invoked` - 这允许将调用上下文信息保存在一个方法中，而不是将其存储在类级别。例如，要测量函数执行时间， `Stopwatch` 可以在调用之前创建和启动 `await next(context)` ，并在调用后使用，而在方法中 `Invoking/Invoked` ，数据应该以其他方式在过滤器作之间传递，例如在类级别设置它，这更难维护。
- 不需要取消逻辑（例如 `context.Cancel = true`）。要取消作，只需不调用 `await next(context)`.

弊：

- 请记住在所有 `await next(context)` 过滤器中手动调用。如果未调用，则不会调用 pipeline 和/或 function 本身中的 next filter。

## 决策结果

继续执行选项 4 并将此方法应用于函数、提示符和函数调用筛选器。
