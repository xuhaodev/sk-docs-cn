
# 重构以支持通用 LLM 请求设置

## 上下文和问题陈述

Semantic Kernel abstractions 包包括许多类（`CompleteRequestSettings`、 `ChatRequestSettings` `PromptTemplateConfig.CompletionConfig`、），用于支持：

1. 在调用 AI 服务时传递 LLM 请求设置
2. 加载与语义函数关联的 `config.json`LLM 请求设置的反序列化 

这些类的问题在于它们仅包含 OpenAI 特定的属性。开发人员只能传递 OpenAI 特定的请求设置，这意味着：

1. 可以传递无效的设置，例如，传递给 `MaxTokens` Huggingface
2. 无法发送与 OpenAI 属性不重叠的设置，例如，Oobabooga 支持其他参数，例如、`do_sample`、`typical_p`、...

链接到 Oobabooga AI 服务的实现者提出的问题： <https://github.com/microsoft/semantic-kernel/issues/2735>

## 决策驱动因素

- 语义内核抽象必须与 AI 服务无关，即删除 OpenAI 特定属性。
- 解决方案必须继续支持从 加载语义函数配置（包括 AI 请求设置）。 `config.json`
- 为开发人员提供良好的体验，例如，必须能够使用 type safety、intellisense 等进行编程。
- 为 AI 服务的实现者提供良好的体验，即，应该清楚如何为他们支持的服务定义适当的 AI 请求设置抽象。
- 语义内核实现和示例代码应避免在旨在与多个 AI 服务一起使用的代码中指定特定于 OpenAI 的请求设置。
- 如果实现是特定于 OpenAI 的，则必须明确语义内核实现和示例代码。

## 考虑的选项

- 用于 `dynamic` 传递请求设置
- 用于 `object` 传递请求设置
- 为 AI 请求设置定义一个基类，所有实现都必须扩展该基类

注意：在 Dmytro 进行的早期调查中，使用泛型被打了折扣。

## 决策结果

**建议：** 为 AI 请求设置定义一个基类，所有实现都必须扩展该基类。

## 选项的优缺点

### 用于 `dynamic` 传递请求设置

 `IChatCompletion` 界面将如下所示：

```csharp
public interface IChatCompletion : IAIService
{
    ChatHistory CreateNewChat(string? instructions = null);

    Task<IReadOnlyList<IChatResult>> GetChatCompletionsAsync(
        ChatHistory chat,
        dynamic? requestSettings = null,
        CancellationToken cancellationToken = default);

    IAsyncEnumerable<IChatStreamingResult> GetStreamingChatCompletionsAsync(
        ChatHistory chat,
        dynamic? requestSettings = null,
        CancellationToken cancellationToken = default);
}
```

开发人员可以使用以下选项来指定语义函数的请求设置：

```csharp
// Option 1: Use an anonymous type
await kernel.InvokeSemanticFunctionAsync("Hello AI, what can you do for me?", requestSettings: new { MaxTokens = 256, Temperature = 0.7 });

// Option 2: Use an OpenAI specific class
await kernel.InvokeSemanticFunctionAsync(prompt, requestSettings: new OpenAIRequestSettings() { MaxTokens = 256, Temperature = 0.7 });

// Option 3: Load prompt template configuration from a JSON payload
string configPayload = @"{
    ""schema"": 1,
    ""description"": ""Say hello to an AI"",
    ""type"": ""completion"",
    ""completion"": {
        ""max_tokens"": 60,
        ""temperature"": 0.5,
        ""top_p"": 0.0,
        ""presence_penalty"": 0.0,
        ""frequency_penalty"": 0.0
    }
}";
var templateConfig = JsonSerializer.Deserialize<PromptTemplateConfig>(configPayload);
var func = kernel.CreateSemanticFunction(prompt, config: templateConfig!, "HelloAI");
await kernel.RunAsync(func);
```

公关： <https://github.com/microsoft/semantic-kernel/pull/2807>

- 很好，SK 抽象不包含对 OpenAI 特定请求设置的引用
- 中性，因为可以使用匿名类型，这允许开发人员传入多个 AI 服务可能支持的属性，例如， `temperature` 或组合不同 AI 服务的属性，例如 `max_tokens` （OpenAI） 和 `max_new_tokens` （Oobabooga）。
- 不好，因为开发人员不清楚在创建语义函数时应该传递什么
- 不好，因为聊天/文本完成服务的实现者不清楚他们应该接受什么或如何添加特定于服务的属性。
- 糟糕的是，对于尚未解析 dynamic 参数的代码路径，没有编译器类型检查，这会影响代码质量。类型问题显示为 `RuntimeBinderException`，可能难以排除故障。需要特别小心返回类型，例如，可能需要指定显式类型，而不是再次指定，`var`以避免错误，例如 `Microsoft.CSharp.RuntimeBinder.RuntimeBinderException : Cannot apply indexing with [] to an expression of type 'object'`

### 用于 `object` 传递请求设置

 `IChatCompletion` 界面将如下所示：

```csharp
public interface IChatCompletion : IAIService
{
    ChatHistory CreateNewChat(string? instructions = null);

    Task<IReadOnlyList<IChatResult>> GetChatCompletionsAsync(
        ChatHistory chat,
        object? requestSettings = null,
        CancellationToken cancellationToken = default);

    IAsyncEnumerable<IChatStreamingResult> GetStreamingChatCompletionsAsync(
        ChatHistory chat,
        object? requestSettings = null,
        CancellationToken cancellationToken = default);
}
```

调用模式与情况相同 `dynamic` ，即使用匿名类型、特定于 AI 服务的类（例如） `OpenAIRequestSettings` 或从 JSON 加载。

公关： <https://github.com/microsoft/semantic-kernel/pull/2819>

- 很好，SK 抽象不包含对 OpenAI 特定请求设置的引用
- 中性，因为可以使用匿名类型，这允许开发人员传入多个 AI 服务可能支持的属性，例如， `temperature` 或组合不同 AI 服务的属性，例如 `max_tokens` （OpenAI） 和 `max_new_tokens` （Oobabooga）。
- 不好，因为开发人员不清楚在创建语义函数时应该传递什么
- 不好，因为聊天/文本完成服务的实现者不清楚他们应该接受什么或如何添加特定于服务的属性。
- 糟糕的是，需要代码来执行类型检查和显式强制转换。情况比实际情况略好 `dynamic` 。

### 为 AI 请求设置定义一个基类，所有实现都必须扩展该基类

 `IChatCompletion` 界面将如下所示：

```csharp
public interface IChatCompletion : IAIService
{
    ChatHistory CreateNewChat(string? instructions = null);

    Task<IReadOnlyList<IChatResult>> GetChatCompletionsAsync(
        ChatHistory chat,
        AIRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default);

    IAsyncEnumerable<IChatStreamingResult> GetStreamingChatCompletionsAsync(
        ChatHistory chat,
        AIRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default);
}
```

`AIRequestSettings` 定义如下：

```csharp
public class AIRequestSettings
{
    /// <summary>
    /// Service identifier.
    /// </summary>
    [JsonPropertyName("service_id")]
    [JsonPropertyOrder(1)]
    public string? ServiceId { get; set; } = null;

    /// <summary>
    /// Extra properties
    /// </summary>
    [JsonExtensionData]
    public Dictionary<string, object>? ExtensionData { get; set; }
}
```

开发人员可以使用以下选项来指定语义函数的请求设置：

```csharp
// Option 1: Invoke the semantic function and pass an OpenAI specific instance
var result = await kernel.InvokeSemanticFunctionAsync(prompt, requestSettings: new OpenAIRequestSettings() { MaxTokens = 256, Temperature = 0.7 });
Console.WriteLine(result.Result);

// Option 2: Load prompt template configuration from a JSON payload
string configPayload = @"{
    ""schema"": 1,
    ""description"": ""Say hello to an AI"",
    ""type"": ""completion"",
    ""completion"": {
        ""max_tokens"": 60,
        ""temperature"": 0.5,
        ""top_p"": 0.0,
        ""presence_penalty"": 0.0,
        ""frequency_penalty"": 0.0
        }
}";
var templateConfig = JsonSerializer.Deserialize<PromptTemplateConfig>(configPayload);
var func = kernel.CreateSemanticFunction(prompt, config: templateConfig!, "HelloAI");

await kernel.RunAsync(func);
```

也可以使用以下模式：

```csharp
this._summarizeConversationFunction = kernel.CreateSemanticFunction(
    SemanticFunctionConstants.SummarizeConversationDefinition,
    skillName: nameof(ConversationSummarySkill),
    description: "Given a section of a conversation, summarize conversation.",
    requestSettings: new AIRequestSettings()
    {
        ExtensionData = new Dictionary<string, object>()
        {
            { "Temperature", 0.1 },
            { "TopP", 0.5 },
            { "MaxTokens", MaxTokens }
        }
    });

```

此模式的警告是，假设更具体的实现 `AIRequestSettings` 使用 JSON 序列化/反序列化从 base hydrate 实例 `AIRequestSettings`，这仅在默认 JsonConverter 支持所有属性时才有效，例如，

- 如果我们有 `MyAIRequestSettings` which includes a `Uri` property.的实现 `MyAIRequestSettings` 将确保加载 URI 转换器，以便它可以正确序列化/反序列化设置。
- 如果 的设置 `MyAIRequestSettings` 被发送到依赖于默认 JsonConverter 的 AI 服务，那么 `NotSupportedException` 将引发异常。

公关： <https://github.com/microsoft/semantic-kernel/pull/2829>

- 很好，SK 抽象不包含对 OpenAI 特定请求设置的引用
- 很好，因为开发人员在创建语义函数时很清楚他们应该传递什么，并且很容易发现存在哪些特定于服务的请求设置实现。
- 很好，因为聊天 / 文本完成服务的实现者很清楚他们应该接受什么，以及如何扩展基本抽象以添加特定于服务的属性。
- 中性，因为 `ExtensionData` 可以使用它允许开发人员传入多个 AI 服务可能支持的属性，例如， `temperature` 或组合不同 AI 服务的属性，例如 `max_tokens` （OpenAI） 和 `max_new_tokens` （Oobabooga）。
