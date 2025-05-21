
# 混合模型编排

## 上下文和问题陈述
考虑到不断涌现和改进的本地和基于云的模型，以及对利用在本地设备 NPU 上运行的本地 AI 模型的需求不断增长，
AI 驱动的应用程序需要能够有效、无缝地利用本地和云模型进行推理，以实现最佳的 AI 用户体验。

## 决策驱动因素

1. 模型编排层应简单且可扩展。
2. 模型编排层客户端代码不应了解或处理底层复杂性。
3. 模型编排层应允许使用不同的策略来为手头的任务选择最佳模型。

## 考虑的实施选项

以下选项考虑了实现模型编排层的几种方法。

### 选项 1：每个编排策略的 IChatClient 实现

此选项提供了一种简单明了的方法来实现模型编排层。每个策略都作为 IChatClient 接口的单独实现实现。 

例如，使用第一个配置的聊天客户端进行推理并在 AI 模型不可用时回退到下一个客户端的回退策略可以按如下方式实现：
```csharp
public sealed class FallbackChatClient : IChatClient
{
    private readonly IChatClient[] _clients;

    public FallbackChatClient(params IChatClient[] clients)
    {
        this._clients = clients;
    }

    public Task<Microsoft.Extensions.AI.ChatCompletion> CompleteAsync(IList<ChatMessage> chatMessages, ChatOptions? options = null, CancellationToken cancellationToken = default)
    {
        foreach (var client in this._clients)
        {
            try
            {
                return client.CompleteAsync(chatMessages, options, cancellationToken);
            }
            catch (HttpRequestException ex)
            {
                if (ex.StatusCode >= 500)
                {
                    // Try the next client
                    continue;
                }

                throw;
            }
        }
    }

    public IAsyncEnumerable<StreamingChatCompletionUpdate> CompleteStreamingAsync(IList<ChatMessage> chatMessages, ChatOptions? options = null, CancellationToken cancellationToken = default)
    {
        ...
    }

    public void Dispose() { /*We can't dispose clients here because they can be used up the stack*/ }

    public ChatClientMetadata Metadata => new ChatClientMetadata();

    public object? GetService(Type serviceType, object? serviceKey = null) => null;
}
```

其他编排策略（例如基于延迟或基于令牌的策略）可以采用类似的方式实现：实现 IChatClient 接口和相应聊天客户端选择策略的类。

优点：
- 不需要任何新的抽象。
- 简单明了的实施。
- 对于大多数使用案例来说已经足够了。

### 选项 2：HybridChatClient 类，每个编排策略具有聊天完成处理程序

此选项引入了一个 HybridChatClient 类，该类实现 IChatClient 接口，并将选择例程委托给由抽象 ChatCompletionHandler 类表示的提供的处理程序：
```csharp
public sealed class HybridChatClient : IChatClient
{
    private readonly IChatClient[] _chatClients;
    private readonly ChatCompletionHandler _handler;
    private readonly Kernel? _kernel;

    public HybridChatClient(IChatClient[] chatClients, ChatCompletionHandler handler, Kernel? kernel = null)
    {
        this._chatClients = chatClients;
        this._handler = handler;
        this._kernel = kernel;
    }

    public Task<Extensions.AI.ChatCompletion> CompleteAsync(IList<ChatMessage> chatMessages, ChatOptions? options = null, CancellationToken cancellationToken = default)
    {
        return this._handler.CompleteAsync(
            new ChatCompletionHandlerContext
            {
                ChatMessages = chatMessages,
                Options = options,
                ChatClients = this._chatClients.ToDictionary(c => c, c => (CompletionContext?)null),
                Kernel = this._kernel,
            }, cancellationToken);
    }

    public IAsyncEnumerable<StreamingChatCompletionUpdate> CompleteStreamingAsync(IList<ChatMessage> chatMessages, ChatOptions? options = null, CancellationToken cancellationToken = default)
    {
        ...
    }

    ...
}

public abstract class ChatCompletionHandler
{
    public abstract Task<Extensions.AI.ChatCompletion> CompleteAsync(ChatCompletionHandlerContext context, CancellationToken cancellationToken = default);

    public abstract IAsyncEnumerable<StreamingChatCompletionUpdate> CompleteStreamingAsync(ChatCompletionHandlerContext context, CancellationToken cancellationToken = default);
}
```

HybridChatClient 类通过 ChatCompletionHandlerContext 类将所有必要信息传递给处理程序，该类包含聊天客户端、聊天消息、选项和内核实例的列表。
```csharp
public class ChatCompletionHandlerContext
{
    public IDictionary<IChatClient, CompletionContext?> ChatClients { get; init; }

    public IList<ChatMessage> ChatMessages { get; init; }

    public ChatOptions? Options { get; init; }

    public Kernel? Kernel { get; init; }
}
```

上一个选项中显示的 fallback 策略可以作为以下处理程序实现：
```csharp
public class FallbackChatCompletionHandler : ChatCompletionHandler
{
    public override async Task<Extensions.AI.ChatCompletion> CompleteAsync(ChatCompletionHandlerContext context, CancellationToken cancellationToken = default)
    {
        for (int i = 0; i < context.ChatClients.Count; i++)
        {
            var chatClient = context.ChatClients.ElementAt(i).Key;

            try
            {
                return client.CompleteAsync(chatMessages, options, cancellationToken);
            }
            catch (HttpRequestException ex)
            {
                if (ex.StatusCode >= 500)
                {
                    // Try the next client
                    continue;
                }

                throw;
            }
        }

        throw new InvalidOperationException("No client provided for chat completion.");
    }

    public override async IAsyncEnumerable<StreamingChatCompletionUpdate> CompleteStreamingAsync(ChatCompletionHandlerContext context, CancellationToken cancellationToken = default)
    {
        ...
    }
}
```

调用方代码将如下所示：
```csharp
IChatClient onnxChatClient = new OnnxChatClient(...);

IChatClient openAIChatClient = new OpenAIChatClient(...);

// Tries the first client and falls back to the next one if the first one fails
FallbackChatCompletionHandler handler = new FallbackChatCompletionHandler(...);

IChatClient hybridChatClient = new HybridChatClient([onnxChatClient, openAIChatClient], handler);

...

var result = await hybridChatClient.CompleteAsync("Do I need an umbrella?", ...);
```

可以链接处理程序以创建更复杂的场景，其中处理程序执行一些预处理，然后将调用委托给另一个具有增强聊天客户端列表的处理程序。 

例如，第一个处理程序标识云模型已请求访问敏感数据，并将调用处理委托给本地模型进行处理。

```csharp
IChatClient onnxChatClient = new OnnxChatClient(...);

IChatClient llamaChatClient = new LlamaChatClient(...);

IChatClient openAIChatClient = new OpenAIChatClient(...);

// Tries the first client and falls back to the next one if the first one fails
FallbackChatCompletionHandler fallbackHandler = new FallbackChatCompletionHandler(...);
  
// Check if the request contains sensitive data, identifies the client(s) allowed to work with the sensitive data, and delegates the call handling to the next handler.
SensitiveDataHandler sensitiveDataHandler = new SensitiveDataHandler(fallbackHandler);

IChatClient hybridChatClient = new HybridChatClient(new[] { onnxChatClient, llamaChatClient, openAIChatClient }, sensitiveDataHandler);
  
var result = await hybridChatClient.CompleteAsync("Do I need an umbrella?", ...);
```

复杂编排场景的示例：

| 第一个处理程序                         | 第二个处理程序                 | 场景描述                                                      |    
|---------------------------------------|--------------------------------|---------------------------------------------------------------------------|    
| InputTokenThresholdEvaluationHandler  | FastestChatCompletionHandler   | 根据提示的输入标记大小和每个模型的最小/最大标记容量来识别模型，然后返回最快的模型的响应。 |
| InputTokenThresholdEvaluationHandler  | RelevancyChatCompletionHandler | 根据提示的输入标记大小和每个模型的最小/最大标记容量来识别模型，然后返回最相关的响应。 |
| InputTokenThresholdEvaluationHandler  | FallbackChatCompletionHandler  | 根据提示的输入标记大小和每个模型的最小/最大标记容量来识别模型，然后返回第一个可用模型的响应。 |
| SensitiveDataRoutingHandler 处理程序           | FastestChatCompletionHandler   | 根据数据敏感度识别模型，然后返回最快的模型响应。 |
| SensitiveDataRoutingHandler 处理程序           | RelevancyChatCompletionHandler | 根据数据敏感性识别模型，然后返回最相关的响应。 |
| SensitiveDataRoutingHandler 处理程序           | FallbackChatCompletionHandler  | 根据数据敏感度识别模型，然后返回第一个可用模型的响应。 |

优点：
- 允许重用相同的处理程序来创建各种复合编排策略。

缺点：
- 需要比上一个选项新的抽象和组件：用于处理下一个处理程序的上下文类和代码。

<br/>

可在此处找到演示此选项的 POC[](https://github.com/microsoft/semantic-kernel/pull/10412)。

### 选项 3：实现现有的 IAIServiceSelector 接口。

Semantic Kernel 具有允许动态选择 AI 服务的机制：

```csharp
public interface IAIServiceSelector
{
    bool TrySelectAIService<T>(
        Kernel kernel,
        KernelFunction function,
        KernelArguments arguments,
        [NotNullWhen(true)] out T? service,
        out PromptExecutionSettings? serviceSettings) where T : class, IAIService;
}
```

但是，此机制需要特定的上下文 - 内核、函数和参数，这些可能并不总是可用的。
此外，它仅适用于 IAIService 接口的实现，该接口可能与所有 AI 服务不兼容。
例如，Microsoft.Extensions.AI 中实现 IChatClient 接口的那些。

此外，此机制不能用于需要首先提示 AI 服务以确定其可用性、延迟等的编排场景。
例如，要检查 AI 服务是否可用，选择器需要向该服务发送带有选项的聊天消息。然后它应该返回
如果服务可用，则为 completion，如果服务不可用，则回退到另一个服务。鉴于 TrySelectAIService 方法不接受
聊天消息或选项，则无法使用此方法发送聊天消息。即使有可能，消费者代码也必须重新发送相同的
chat 消息发送到所选服务以获取完成，因为 selector 不会返回完成本身。此外，TrySelectAIService 方法
是同步的，因此很难在不使用同步代码的情况下发送聊天消息，这通常是不建议这样做的。

综上所述，很明显 IAIServiceSelector 接口不适合 AI 服务的混合编排，因为它是为不同的目的而设计的：
根据 SK 上下文和服务元数据同步选择 AI 服务的实例，而不考虑完成结果和流式完成方法。

优点：
- 重用现有机制进行 AI 服务选择。

缺点：
- 不适用于所有 AI 服务。
- 需要的上下文可能并非在所有情况下都可用。
- 使用者代码必须知道 IAIServiceSelector 接口，而不仅仅是使用 IChatClient 接口。
- 同步方法。

## 决策结果

选择的选项：选项 1 因为它不需要任何新的抽象;它的简单性和直接性对于大多数使用案例来说已经足够了。
如果需要更复杂的编排方案，则可以在将来考虑选项 2。