## 建议

### IChatCompletion

以前：

```csharp
public interface IChatCompletion : IAIService
{
    ChatHistory CreateNewChat(string? instructions = null);

    Task<IReadOnlyList<IChatResult>> GetChatCompletionsAsync(ChatHistory chat, ...);

    Task<IReadOnlyList<IChatResult>> GetChatCompletionsAsync(string prompt, ...);

    IAsyncEnumerable<T> GetStreamingContentAsync<T>(ChatHistory chatHistory, ...);
}

public static class ChatCompletionExtensions
{
    public static async Task<string> GenerateMessageAsync(ChatHistory chat, ...);
}
```

后：

```csharp
public interface IChatCompletion : IAIService
{
    Task<IReadOnlyList<ChatContent>> GetChatContentsAsync(ChatHistory chat, ..> tags)

    IAsyncEnumerable<StreamingChatContent> GetStreamingChatContentsAsync(ChatHistory chatHistory, ...);
}

public static class ChatCompletionExtensions
{
    //                       v Single          vv Standardized Prompt (Parse <message> tags)
    public static async Task<ChatContent> GetChatContentAsync(string prompt, ...);

    //                       v Single
    public static async Task<ChatContent> GetChatContentAsync(ChatHistory chatHistory, ...);

    public static IAsyncEnumerable<StreamingChatContent> GetStreamingChatContentsAsync(string prompt, ...);
}
```

### ITextCompletion

以前：

```csharp
public interface ITextCompletion : IAIService
{
    Task<IReadOnlyList<ITextResult>> GetCompletionsAsync(string prompt, ...);

    IAsyncEnumerable<T> GetStreamingContentAsync<T>(string prompt, ...);
}

public static class TextCompletionExtensions
{
    public static async Task<string> CompleteAsync(string text, ...);

    public static IAsyncEnumerable<StreamingContent> GetStreamingContentAsync(string input, ...);
}
```

后：

```csharp
public interface ITextCompletion : IAIService
{
    Task<IReadOnlyList<TextContent>> GetTextContentsAsync(string prompt, ...);

    IAsyncEnumerable<StreamingTextContent> GetStreamingTextContentsAsync(string prompt, ...);
}

public static class TextCompletionExtensions
{
    public static async Task<TextContent> GetTextContentAsync(string prompt, ...);
}
```

## 内容抽象

### 型号比较

#### 当前的流式抽象

| 流式 （Current）                         | Specialized\* 流媒体 （current）                               |
| ------------------------------------------- | --------------------------------------------------------------- |
| `StreamingChatContent` ： `StreamingContent` | `OpenAIStreamingChatContent`                                    |
| `StreamingTextContent` ： `StreamingContent` | `OpenAIStreamingTextContent`、 `HuggingFaceStreamingTextContent` |

#### 非流式抽象 （Before 和 After）

| Non-Streaming （Before） （非流式处理 （之前））        | 非流式处理 （之后）          | Specialized\* 非流式处理 （After）           |
| ----------------------------- | ------------------------------ | --------------------------------------------- |
| `IChatResult` ： `IResultBase` | `ChatContent` ： `ModelContent` | `OpenAIChatContent`                           |
| `ITextResult` ： `IResultBase` | `TextContent` ： `ModelContent` | `OpenAITextContent`、 `HuggingFaceTextContent` |
| `ChatMessage`                 | `ChatContent` ： `ModelContent` | `OpenAIChatContent`                           |

_\*Specialized：特定于单个 AI 服务的连接器实现。_

### 新的非流式抽象：

`ModelContent` 被选中来表示 `non-streaming content` 最顶层的抽象，该抽象可以是专用的，并包含 AI 服务返回的所有信息。（元数据、原始内容等）

```csharp
/// <summary>
/// Base class for all AI non-streaming results
/// </summary>
public abstract class ModelContent
{
    /// <summary>
    /// Raw content object reference. (Breaking glass).
    /// </summary>
    public object? InnerContent { get; }

    /// <summary>
    /// The metadata associated with the content.
    /// ⚠️ (Token Usage + More Backend API Metadata) info will be in this dictionary. Old IResult.ModelResult) ⚠️
    /// </summary>
    public Dictionary<string, object?>? Metadata { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="CompleteContent"/> class.
    /// </summary>
    /// <param name="rawContent">Raw content object reference</param>
    /// <param name="metadata">Metadata associated with the content</param>
    protected CompleteContent(object rawContent, Dictionary<string, object>? metadata = null)
    {
        this.InnerContent = rawContent;
        this.Metadata = metadata;
    }
}
```

```csharp
/// <summary>
/// Chat content abstraction
/// </summary>
public class ChatContent : ModelContent
{
    /// <summary>
    /// Role of the author of the message
    /// </summary>
    public AuthorRole Role { get; set; }

    /// <summary>
    /// Content of the message
    /// </summary>
    public string Content { get; protected set; }

    /// <summary>
    /// Creates a new instance of the <see cref="ChatContent"/> class
    /// </summary>
    /// <param name="chatMessage"></param>
    /// <param name="metadata">Dictionary for any additional metadata</param>
    public ChatContent(ChatMessage chatMessage, Dictionary<string, object>? metadata = null) : base(chatMessage, metadata)
    {
        this.Role = chatMessage.Role;
        this.Content = chatMessage.Content;
    }
}
```

```csharp
/// <summary>
/// Represents a text content result.
/// </summary>
public class TextContent : ModelContent
{
    /// <summary>
    /// The text content.
    /// </summary>
    public string Text { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="TextContent"/> class.
    /// </summary>
    /// <param name="text">Text content</param>
    /// <param name="metadata">Additional metadata</param>
    public TextContent(string text, Dictionary<string, object>? metadata = null) : base(text, metadata)
    {
        this.Text = text;
    }
}
```

### 最终用户体验

- 使用  或  时`Function.InvokeAsync`，最终用户体验不会发生变化 `Kernel.InvokeAsync`
- 仅在直接使用连接器 API 时进行更改

#### 示例 16 - 自定义 LLMS

以前

```csharp
await foreach (var message in textCompletion.GetStreamingContentAsync(prompt, executionSettings))
{
    Console.Write(message);
}
```

后

```csharp
await foreach (var message in textCompletion.GetStreamingTextContentAsync(prompt, executionSettings))
{
    Console.Write(message);
}
```

#### 示例 17 - ChatGPT

以前

```csharp
string reply = await chatGPT.GenerateMessageAsync(chatHistory);
chatHistory.AddAssistantMessage(reply);
```

后

```csharp
var reply = await chatGPT.GetChatContentAsync(chatHistory);
chatHistory.AddMessage(reply);

// OR
chatHistory.AddAssistantMessage(reply.Content);
```

### 清理

所有旧的接口和类都将被删除，以支持新的接口和类。
