
# 内核过滤器

## 上下文和问题陈述

当前在函数执行期间拦截某些事件的方式使用 Kernel Events 和事件处理程序按预期工作。例：

```csharp
ILogger logger = loggerFactory.CreateLogger("MyLogger");

var kernel = Kernel.CreateBuilder()
    .AddOpenAIChatCompletion(
        modelId: TestConfiguration.OpenAI.ChatModelId,
        apiKey: TestConfiguration.OpenAI.ApiKey)
    .Build();

void MyInvokingHandler(object? sender, FunctionInvokingEventArgs e)
{
    logger.LogInformation("Invoking: {FunctionName}", e.Function.Name)
}

void MyInvokedHandler(object? sender, FunctionInvokedEventArgs e)
{
    if (e.Result.Metadata is not null && e.Result.Metadata.ContainsKey("Usage"))
    {
        logger.LogInformation("Token usage: {TokenUsage}", e.Result.Metadata?["Usage"]?.AsJson());
    }
}

kernel.FunctionInvoking += MyInvokingHandler;
kernel.FunctionInvoked += MyInvokedHandler;

var result = await kernel.InvokePromptAsync("How many days until Christmas? Explain your thinking.")
```

这种方法存在几个问题：

1. 事件处理程序不支持依赖项注入。很难访问在 application 中注册的特定服务，除非在特定服务可用的同一范围内定义处理程序。此方法在解决方案中可以定义处理程序的位置提供了一些限制。（例如，如果开发人员想要使用 `ILoggerFactory` 在 handler 中，应在 instance 可用时定义处理程序 `ILoggerFactory` ）。
2. 目前尚不清楚处理程序应该在应用程序运行时的哪个特定时间段附加到内核。此外，目前尚不清楚开发人员是否需要在某个时候分离它。
3. 对于以前不处理事件的 .NET 开发人员来说，可能不熟悉 .NET 中的事件机制和事件处理程序。

<!-- This is an optional element. Feel free to remove. -->

## 决策驱动因素

1. 应该支持处理程序的依赖注入，以便轻松访问应用程序中的已注册服务。
2. 在解决方案中定义处理程序时，无论是 Startup.cs 文件还是单独的文件，都不应有任何限制。
3. 应该有明确的方法来在应用程序运行时的特定点注册和删除处理程序。
4. 在 Kernel 中接收和处理事件的机制在 .NET 生态系统中应该简单且常见。
5. 新方法应支持与 Kernel Events 中可用的相同功能 - 取消函数执行、更改内核参数、在将其发送到 AI 之前更改渲染的提示等。

## 决策结果

引入 Kernel Filters - 在 Kernel 中接收事件的方法，其方式与 ASP.NET 中的作筛选器类似。

Semantic Kernel 将使用两个新的抽象，开发人员必须以满足他们需求的方式实现这些抽象。

对于与函数相关的事件： `IFunctionFilter`

```csharp
public interface IFunctionFilter
{
    void OnFunctionInvoking(FunctionInvokingContext context);

    void OnFunctionInvoked(FunctionInvokedContext context);
}
```

对于提示相关事件： `IPromptFilter`

```csharp
public interface IPromptFilter
{
    void OnPromptRendering(PromptRenderingContext context);

    void OnPromptRendered(PromptRenderedContext context);
}
```

新方法将允许开发人员在单独的类中定义过滤器，并轻松注入所需的服务以正确处理内核事件：

MyFunctionFilter.cs - 使用与上面介绍的事件处理程序相同的逻辑进行筛选：

```csharp
public sealed class MyFunctionFilter : IFunctionFilter
{
    private readonly ILogger _logger;

    public MyFunctionFilter(ILoggerFactory loggerFactory)
    {
        this._logger = loggerFactory.CreateLogger("MyLogger");
    }

    public void OnFunctionInvoking(FunctionInvokingContext context)
    {
        this._logger.LogInformation("Invoking {FunctionName}", context.Function.Name);
    }

    public void OnFunctionInvoked(FunctionInvokedContext context)
    {
        var metadata = context.Result.Metadata;

        if (metadata is not null && metadata.ContainsKey("Usage"))
        {
            this._logger.LogInformation("Token usage: {TokenUsage}", metadata["Usage"]?.AsJson());
        }
    }
}
```

一旦定义了新的过滤器，就很容易将其配置为使用依赖项注入（构建前）在内核中使用，或者在内核初始化后（构建后）添加过滤器：

```csharp
IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
kernelBuilder.AddOpenAIChatCompletion(
        modelId: TestConfiguration.OpenAI.ChatModelId,
        apiKey: TestConfiguration.OpenAI.ApiKey);

// Adding filter with DI (pre-construction)
kernelBuilder.Services.AddSingleton<IFunctionFilter, MyFunctionFilter>();

Kernel kernel = kernelBuilder.Build();

// Adding filter after Kernel initialization (post-construction)
// kernel.FunctionFilters.Add(new MyAwesomeFilter());

var result = await kernel.InvokePromptAsync("How many days until Christmas? Explain your thinking.");
```

还可以配置多个过滤器，这些过滤器将按注册顺序触发：

```csharp
kernelBuilder.Services.AddSingleton<IFunctionFilter, Filter1>();
kernelBuilder.Services.AddSingleton<IFunctionFilter, Filter2>();
kernelBuilder.Services.AddSingleton<IFunctionFilter, Filter3>();
```

如果需要，可以在运行时更改 filter 的执行顺序或删除特定的 filter：

```csharp
kernel.FunctionFilters.Insert(0, new InitialFilter());
kernel.FunctionFilters.RemoveAt(1);
```
