
# 用于 Kernel 和 Functions 的流式处理功能 - 第 1 阶段

## 上下文和问题陈述

在 co-pilot 实现中，从 LLM（大型语言模型）M 简化消息输出是很常见的，目前在使用 ISKFunctions.InvokeAsync 或 Kernel.RunAsync 方法时无法做到这一点，这迫使用户绕过内核和函数，以直接使用 `ITextCompletion` 和服务 `IChatCompletion` 作为当前支持流式处理的唯一接口。

目前，并非所有提供商都支持流式处理功能，作为我们设计的一部分，我们尝试确保服务具有适当的抽象，不仅支持文本流式处理，而且对其他类型的数据（如图像、音频、视频等）开放。

当 sk 开发人员尝试获取流数据时，需要清楚这一点。

## 决策驱动因素

1. sk 开发人员应该能够使用 Kernel.RunAsync 或 ISKFunctions.InvokeAsync 方法从内核和函数获取流数据

2. sk 开发人员应该能够以通用方式获取数据，因此 Kernel 和 Functions 能够流式传输任何类型的数据，而不限于文本。

3. sk 开发人员在从不支持流式处理的模型中使用流式处理时，仍应能够使用它，并且只有一个流式处理更新表示整个数据。

## 超出范围

- 在此阶段，将不支持使用计划进行流式传输。尝试这样做将引发异常。
- 内核流式处理将不支持多个函数 （pipeline）。
- 此阶段将不支持输入流式处理。
- 不支持流式传输功能的 Post Hook Skipping、Repeat 和 Cancelling。

## 考虑的选项

### 选项 1 - 专用流式处理接口

使用专用的流接口，允许 sk 开发人员以通用方式获取流数据，包括字符串、字节数组，并允许 Kernel 和 Functions 实现能够流式传输任何类型的数据，而不限于文本。

这种方法还公开了内核和函数中的专用接口以使用流式处理，使 sk 开发人员清楚地知道以 IAsyncEnumerable 格式返回的数据类型是什么。

`ITextCompletion` 并且 `IChatCompletion` 将具有新的 API 来直接获取 `byte[]` 和 `string` 流式传输数据以及专用 `StreamingContent` 返回。

sk 开发人员将能够为 指定泛型类型， `Kernel.RunStreamingAsync<T>()` 并 `ISKFunction.InvokeStreamingAsync<T>` 获取流数据。如果未指定类型，则 Kernel 和 Functions 会将数据作为 StreamingContent 返回。

如果未指定类型或无法强制转换字符串表示形式，则会引发异常。

如果指定的类型是 `StreamingContent` 连接器支持的其他 any 类型，则不会引发错误。

## 用户体验目标

```csharp
//(providing the type at as generic parameter)

// Getting a Raw Streaming data from Kernel
await foreach(string update in kernel.RunStreamingAsync<byte[]>(function, variables))

// Getting a String as Streaming data from Kernel
await foreach(string update in kernel.RunStreamingAsync<string>(function, variables))

// Getting a StreamingContent as Streaming data from Kernel
await foreach(StreamingContent update in kernel.RunStreamingAsync<StreamingContent>(variables, function))
// OR
await foreach(StreamingContent update in kernel.RunStreamingAsync(function, variables)) // defaults to Generic above)
{
    Console.WriteLine(update);
}
```

抽象类，连接器将负责提供其专用类型，`StreamingContent`该类型将包含数据以及与流结果相关的任何元数据。

```csharp

public abstract class StreamingContent
{
    public abstract int ChoiceIndex { get; }

    /// Returns a string representation of the chunk content
    public abstract override string ToString();

    /// Abstract byte[] representation of the chunk content in a way it could be composed/appended with previous chunk contents.
    /// Depending on the nature of the underlying type, this method may be more efficient than <see cref="ToString"/>.
    public abstract byte[] ToByteArray();

    /// Internal chunk content object reference. (Breaking glass).
    /// Each connector will have its own internal object representing the content chunk content.
    /// The usage of this property is considered "unsafe". Use it only if strictly necessary.
    public object? InnerContent { get; }

    /// The metadata associated with the content.
    public Dictionary<string, object>? Metadata { get; set; }

    /// The current context associated the function call.
    internal SKContext? Context { get; set; }

    /// <param name="innerContent">Inner content object reference</param>
    protected StreamingContent(object? innerContent)
    {
        this.InnerContent = innerContent;
    }
}
```

StreamingChatContent 的专用化示例

```csharp
//
public class StreamingChatContent : StreamingContent
{
    public override int ChoiceIndex { get; }
    public FunctionCall? FunctionCall { get; }
    public string? Content { get; }
    public AuthorRole? Role { get; }
    public string? Name { get; }

    public StreamingChatContent(AzureOpenAIChatMessage chatMessage, int resultIndex) : base(chatMessage)
    {
        this.ChoiceIndex = resultIndex;
        this.FunctionCall = chatMessage.InnerChatMessage?.FunctionCall;
        this.Content = chatMessage.Content;
        this.Role = new AuthorRole(chatMessage.Role.ToString());
        this.Name = chatMessage.InnerChatMessage?.Name;
    }

    public override byte[] ToByteArray() => Encoding.UTF8.GetBytes(this.ToString());
    public override string ToString() => this.Content ?? string.Empty;
}
```

`IChatCompletion` 接口 `ITextCompletion` 将具有新的 API 来获取通用的流式处理内容数据。

```csharp
interface ITextCompletion + IChatCompletion
{
    IAsyncEnumerable<T> GetStreamingContentAsync<T>(...);

    // Throw exception if T is not supported
}

interface IKernel
{
    // Get streaming function content of T
    IAsyncEnumerable<T> RunStreamingAsync<T>(ContextVariables variables, ISKFunction function);
}

interface ISKFunction
{
    // Get streaming function content of T
    IAsyncEnumerable<T> InvokeStreamingAsync<T>(SKContext context);
}
```

## 提示/语义函数行为

当使用流式处理 API 调用提示函数时，它们将尝试使用 Connectors 流式处理实现。
连接器将负责提供专用类型的 `StreamingContent` ，即使底层后端 API 不支持流式处理，输出也将是一个包含整个数据的 streamingcontent。

## 方法/本机函数行为

方法函数将自动支持 `StreamingContent` `StreamingMethodContent` 在迭代器中返回的对象作为包装。

```csharp
public sealed class StreamingMethodContent : StreamingContent
{
    public override int ChoiceIndex => 0;

    /// Method object value that represents the content chunk
    public object Value { get; }

    /// Default implementation
    public override byte[] ToByteArray()
    {
        if (this.Value is byte[])
        {
            // If the method value is byte[] we return it directly
            return (byte[])this.Value;
        }

        // By default if a native value is not byte[] we output the UTF8 string representation of the value
        return Encoding.UTF8.GetBytes(this.Value?.ToString());
    }

    /// <inheritdoc/>
    public override string ToString()
    {
        return this.Value.ToString();
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="StreamingMethodContent"/> class.
    /// </summary>
    /// <param name="innerContent">Underlying object that represents the chunk</param>
    public StreamingMethodContent(object innerContent) : base(innerContent)
    {
        this.Value = innerContent;
    }
}
```

如果 MethodFunction 返回 `IAsyncEnumerable` each，则可枚举结果将自动包装， `StreamingMethodContent` 以保持流行为和整体抽象的一致性。

当 MethodFunction 不是 时 `IAsyncEnumerable`，完整结果将包装在 a `StreamingMethodContent` 中，并将作为单个项目返回。

## 优点

1. 所有 User Experience Goal 部分选项都将可用。
2. Kernel 和 Functions 实现将能够流式传输任何类型的数据，不仅限于文本
3. sk 开发人员将能够从该方法中提供它期望的流式处理内容类型 `GetStreamingContentAsync<T>` 。
4. Sk 开发人员将能够从具有相同结果类型的 Kernel、Functions 和 Connectors 获取流。

## 缺点

1. 如果 sk 开发人员想要使用专用类型的 ， `StreamingContent` 他将需要知道正在使用什么连接器，以使用正确的 **StreamingContent 扩展方法** 或直接提供键入 `<T>`.
2. 连接器将承担更大的责任来支持正确的特殊类型的 `StreamingContent`.

### 选项 2 - 专用流式处理接口（返回类）

与选项 1 相比的所有更改，但略有不同：

- Kernel 和 SKFunction 流式处理 API 接口将返回 `StreamingFunctionResult<T>` ，该接口还实现了 `IAsyncEnumerable<T>`
- 连接器流式处理 API 接口将返回 `StreamingConnectorContent<T>` ，该接口也实现 `IAsyncEnumerable<T>`

 `StreamingConnectorContent` 连接器需要该类，作为传递与请求相关的任何信息的一种方式，而不是函数可用于填充 `StreamingFunctionResult` 元数据的块。

## 用户体验目标

选项 2 最大好处：

```csharp
// When the caller needs to know more about the streaming he can get the result reference before starting the streaming.
var streamingResult = await kernel.RunStreamingAsync(function);
// Do something with streamingResult properties

// Consuming the streamingResult requires an extra await:
await foreach(StreamingContent chunk content in await streamingResult)
```

使用其他作将非常相似（只需要额外的 `await` 作来获取迭代器）

```csharp
// Getting a Raw Streaming data from Kernel
await foreach(string update in await kernel.RunStreamingAsync<byte[]>(function, variables))

// Getting a String as Streaming data from Kernel
await foreach(string update in await kernel.RunStreamingAsync<string>(function, variables))

// Getting a StreamingContent as Streaming data from Kernel
await foreach(StreamingContent update in await kernel.RunStreamingAsync<StreamingContent>(variables, function))
// OR
await foreach(StreamingContent update in await kernel.RunStreamingAsync(function, variables)) // defaults to Generic above)
{
    Console.WriteLine(update);
}

```

StreamingConnectorResult 是一个类，它可以存储有关使用流之前的结果的信息，以及流在连接器级别使用的任何基础对象（碎玻璃）。

```csharp

public sealed class StreamingConnectorResult<T> : IAsyncEnumerable<T>
{
    private readonly IAsyncEnumerable<T> _StreamingContentource;

    public object? InnerResult { get; private set; } = null;

    public StreamingConnectorResult(Func<IAsyncEnumerable<T>> streamingReference, object? innerConnectorResult)
    {
        this._StreamingContentource = streamingReference.Invoke();
        this.InnerResult = innerConnectorResult;
    }
}

interface ITextCompletion + IChatCompletion
{
    Task<StreamingConnectorResult<T>> GetStreamingContentAsync<T>();
    // Throw exception if T is not supported
    // Initially connectors
}
```

StreamingFunctionResult 是一个类，它可以存储有关使用流之前的结果的信息，以及流从 Kernel 和 SKFunctions 使用的任何基础对象 （碎玻璃） 的信息。

```csharp
public sealed class StreamingFunctionResult<T> : IAsyncEnumerable<T>
{
    internal Dictionary<string, object>? _metadata;
    private readonly IAsyncEnumerable<T> _streamingResult;

    public string FunctionName { get; internal set; }
    public Dictionary<string, object> Metadata { get; internal set; }

    /// <summary>
    /// Internal object reference. (Breaking glass).
    /// Each connector will have its own internal object representing the result.
    /// </summary>
    public object? InnerResult { get; private set; } = null;

    /// <summary>
    /// Instance of <see cref="SKContext"/> used by the function.
    /// </summary>
    internal SKContext Context { get; private set; }

    public StreamingFunctionResult(string functionName, SKContext context, Func<IAsyncEnumerable<T>> streamingResult, object? innerFunctionResult)
    {
        this.FunctionName = functionName;
        this.Context = context;
        this._streamingResult = streamingResult.Invoke();
        this.InnerResult = innerFunctionResult;
    }
}

interface ISKFunction
{
    // Extension generic method to get from type <T>
    Task<StreamingFunctionResult<T>> InvokeStreamingAsync<T>(...);
}

static class KernelExtensions
{
    public static async Task<StreamingFunctionResult<T>> RunStreamingAsync<T>(this Kernel kernel, ISKFunction skFunction, ContextVariables? variables, CancellationToken cancellationToken)
    {
        ...
    }
}
```

## 优点

1. 选项 1 的所有优势 +
2. 使用 StreamingFunctionResults 可以让 sk 开发人员在使用流之前了解有关结果的更多详细信息，例如：
   - 底层 API 提供的任何元数据，
   - SKContext
   - 函数名称和详细信息
3. 使用 Streaming 的体验与选项 1 非常相似（需要额外的 await 才能获得结果）
4. API 的行为类似于非流式处理 API（返回结果表示以获取值）

## 缺点

1. 选项 1 的所有缺点 +
2. 增加了复杂性，因为 IAsyncEnumerable 不能直接在方法结果中传递，这要求在实现 IAsyncEnumerator 的 Results 内部调整委托方法。
3. 增加了复杂性，其中需要在 Results 中实现 IDisposable 以释放响应对象，并且调用方需要处理结果的处置。
4. 一旦调用方获得一个`StreamingFunctionResult`网络连接，该网络连接将保持打开状态，直到调用方实现使用它（枚举 `IAsyncEnumerable`）。

## 决策结果

选项 1 被选为最佳选项，因为选项 2 的小好处并不能证明缺点中描述的复杂性是合理的。

还决定可以将与连接器后端响应相关的元数据添加到 `StreamingContent.Metadata` 属性中。这将允许 sk 开发人员获取元数据，即使没有 `StreamingConnectorResult` 或 `StreamingFunctionResult`。
