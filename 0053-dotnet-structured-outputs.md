
# Semantic Kernel 的 .NET 版本中的结构化输出实现

## 上下文和问题陈述

[结构化输出](https://platform.openai.com/docs/guides/structured-outputs) 是 OpenAI API 中的一项功能，可确保模型始终根据提供的 JSON 架构生成响应。这提供了对模型响应的更多控制，允许避免模型幻觉并编写更简单的提示，而无需具体说明响应格式。此 ADR 介绍了如何在 .NET 版本的 Semantic Kernel 中启用此功能的几个选项。

以下是如何在 .NET 和 Python OpenAI SDK 中实现的几个示例：

.NET OpenAI 开发工具包：
```csharp
ChatCompletionOptions options = new()
{
    ResponseFormat = ChatResponseFormat.CreateJsonSchemaFormat(
        name: "math_reasoning",
        jsonSchema: BinaryData.FromString("""
            {
                "type": "object",
                "properties": {
                "steps": {
                    "type": "array",
                    "items": {
                    "type": "object",
                    "properties": {
                        "explanation": { "type": "string" },
                        "output": { "type": "string" }
                    },
                    "required": ["explanation", "output"],
                    "additionalProperties": false
                    }
                },
                "final_answer": { "type": "string" }
                },
                "required": ["steps", "final_answer"],
                "additionalProperties": false
            }
            """),
    strictSchemaEnabled: true)
};

ChatCompletion chatCompletion = await client.CompleteChatAsync(
    ["How can I solve 8x + 7 = -23?"],
    options);

using JsonDocument structuredJson = JsonDocument.Parse(chatCompletion.ToString());

Console.WriteLine($"Final answer: {structuredJson.RootElement.GetProperty("final_answer").GetString()}");
Console.WriteLine("Reasoning steps:");
```

Python OpenAI 开发工具包：

```python
class CalendarEvent(BaseModel):
    name: str
    date: str
    participants: list[str]

completion = client.beta.chat.completions.parse(
    model="gpt-4o-2024-08-06",
    messages=[
        {"role": "system", "content": "Extract the event information."},
        {"role": "user", "content": "Alice and Bob are going to a science fair on Friday."},
    ],
    response_format=CalendarEvent,
)

event = completion.choices[0].message.parsed
```

## 考虑的选项

**注意**：本 ADR 中提供的所有选项并不互斥 - 它们可以同时实施和支持。

### 选项 #1：将 OpenAI.Chat.Chat.ChatResponseFormat 对象用于 ResponseFormat 属性（类似于 .NET OpenAI SDK）

这种方法意味着 `OpenAI.Chat.ChatResponseFormat` 具有 JSON Schema 的对象将由用户构建并提供给 `OpenAIPromptExecutionSettings.ResponseFormat` 属性，语义内核会将其按原样传递给 .NET OpenAI SDK。 

使用示例：

```csharp
// Initialize Kernel
Kernel kernel = Kernel.CreateBuilder()
    .AddOpenAIChatCompletion(
        modelId: "gpt-4o-2024-08-06",
        apiKey: TestConfiguration.OpenAI.ApiKey)
    .Build();

// Create JSON Schema with desired response type from string.
ChatResponseFormat chatResponseFormat = ChatResponseFormat.CreateJsonSchemaFormat(
    name: "math_reasoning",
    jsonSchema: BinaryData.FromString("""
        {
            "type": "object",
            "properties": {
                "Steps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "Explanation": { "type": "string" },
                            "Output": { "type": "string" }
                        },
                    "required": ["Explanation", "Output"],
                    "additionalProperties": false
                    }
                },
                "FinalAnswer": { "type": "string" }
            },
            "required": ["Steps", "FinalAnswer"],
            "additionalProperties": false
        }
        """),
    strictSchemaEnabled: true);

// Pass ChatResponseFormat in OpenAIPromptExecutionSettings.ResponseFormat property.
var executionSettings = new OpenAIPromptExecutionSettings
{
    ResponseFormat = chatResponseFormat
};

// Get string result.
var result = await kernel.InvokePromptAsync("How can I solve 8x + 7 = -23?", new(executionSettings));

Console.WriteLine(result.ToString());

// Output:

// {
//    "Steps":[
//       {
//          "Explanation":"Start with the equation: (8x + 7 = -23). The goal is to isolate (x) on one side of the equation. To begin, we need to remove the constant term from the left side of the equation.",
//          "Output":"8x + 7 = -23"
//       },
//       {
//          "Explanation":"Subtract 7 from both sides of the equation to eliminate the constant from the left side.",
//          "Output":"8x + 7 - 7 = -23 - 7"
//       },
//       {
//          "Explanation":"Simplify both sides: The +7 and -7 on the left will cancel out, while on the right side, -23 - 7 equals -30.",
//          "Output":"8x = -30"
//       },
//       {
//          "Explanation":"Now, solve for (x) by dividing both sides of the equation by 8. This will isolate (x).",
//          "Output":"8x / 8 = -30 / 8"
//       },
//       {
//          "Explanation":"Simplify the right side of the equation by performing the division: -30 divided by 8 equals -3.75.",
//          "Output":"x = -3.75"
//       }
//    ],
//    "FinalAnswer":"x = -3.75"
// }
```

优点：
- Semantic Kernel 已经支持这种方法，无需任何其他更改，因为有一个逻辑可以将 `ChatResponseFormat` 对象按原样传递给 .NET OpenAI SDK。 
- 与 .NET OpenAI SDK 一致。

缺点：
- 没有类型安全。有关响应类型的信息应由用户手动构建以执行请求。要访问每个响应属性，也应手动处理响应。可以定义 C# 类型并使用 JSON 反序列化进行响应，但请求的 JSON 架构仍将单独定义，这意味着有关类型的信息将存储在 2 个位置，对类型的任何修改都应在 2 个位置处理。
- 与 Python 版本不一致，其中响应类型在类中定义，并通过 `response_format` 简单赋值传递给属性。 

### 选项 #2：对 ResponseFormat 属性使用 C# 类型（类似于 Python OpenAI SDK）

这种方法意味着 `OpenAI.Chat.ChatResponseFormat` 带有 JSON Schema 的对象将由 Semantic Kernel 构建，用户只需要定义 C# 类型并将其分配给 `OpenAIPromptExecutionSettings.ResponseFormat` 属性。

使用示例：

```csharp
// Define desired response models
private sealed class MathReasoning
{
    public List<MathReasoningStep> Steps { get; set; }

    public string FinalAnswer { get; set; }
}

private sealed class MathReasoningStep
{
    public string Explanation { get; set; }

    public string Output { get; set; }
}

// Initialize Kernel
Kernel kernel = Kernel.CreateBuilder()
    .AddOpenAIChatCompletion(
        modelId: "gpt-4o-2024-08-06",
        apiKey: TestConfiguration.OpenAI.ApiKey)
    .Build();

// Pass desired response type in OpenAIPromptExecutionSettings.ResponseFormat property.
var executionSettings = new OpenAIPromptExecutionSettings
{
    ResponseFormat = typeof(MathReasoning)
};

// Get string result.
var result = await kernel.InvokePromptAsync("How can I solve 8x + 7 = -23?", new(executionSettings));

// Deserialize string to desired response type.
var mathReasoning = JsonSerializer.Deserialize<MathReasoning>(result.ToString())!;

OutputResult(mathReasoning);

// Output:

// Step #1
// Explanation: Start with the given equation.
// Output: 8x + 7 = -23

// Step #2
// Explanation: To isolate the term containing x, subtract 7 from both sides of the equation.
// Output: 8x + 7 - 7 = -23 - 7

// Step #3
// Explanation: To solve for x, divide both sides of the equation by 8, which is the coefficient of x.
// Output: (8x)/8 = (-30)/8

// Step #4
// Explanation: This simplifies to x = -3.75, as dividing -30 by 8 gives -3.75.
// Output: x = -3.75

// Final answer: x = -3.75
```

优点：
- 类型安全。用户不需要手动定义 JSON 架构，因为它将由 Semantic Kernel 处理，因此用户可以只专注于定义 C# 类型。可以添加或删除 C# 类型的属性，以更改所需响应的格式。 `Description` 属性以提供有关特定属性的更多详细信息。
- 与 Python OpenAI SDK 一致。
- 由于语义内核代码库已经具有从 C# 类型构建 JSON 架构的逻辑，因此只需进行最少的代码更改。

缺点：
- 所需的类型应通过 or assignment 提供 `ResponseFormat = typeof(MathReasoning)` `ResponseFormat = object.GetType()` ，这可以通过使用 C# 泛型进行改进。
- 来自 Kernel 的响应仍然是 `string`，因此应由用户手动将其反序列化为所需的类型。

### 选项 #3：使用 C# 泛型

此方法类似于选项 #2，但可以使用 `ResponseFormat = typeof(MathReasoning)` C# 泛型`ResponseFormat = object.GetType()`，而不是通过  or  赋值提供类型信息。

使用示例：

```csharp
// Define desired response models
private sealed class MathReasoning
{
    public List<MathReasoningStep> Steps { get; set; }

    public string FinalAnswer { get; set; }
}

private sealed class MathReasoningStep
{
    public string Explanation { get; set; }

    public string Output { get; set; }
}

// Initialize Kernel
Kernel kernel = Kernel.CreateBuilder()
    .AddOpenAIChatCompletion(
        modelId: "gpt-4o-2024-08-06",
        apiKey: TestConfiguration.OpenAI.ApiKey)
    .Build();

// Get MathReasoning result.
var result = await kernel.InvokePromptAsync<MathReasoning>("How can I solve 8x + 7 = -23?");

OutputResult(mathReasoning);
```

优点：
- 使用简单，无需稍后定义 `PromptExecutionSettings` 和反序列化字符串响应。

缺点：
- 与选项 #1 和选项 #2 相比，实现复杂性：
    1. 聊天完成服务返回一个字符串，因此应在某处添加反序列化逻辑以返回类型而不是字符串。可能的位置： `FunctionResult`，因为它已经包含 `GetValue<T>` 泛型方法，但它不包含反序列化逻辑，因此应该添加和测试它。 
    2. `IChatCompletionService` 并且其方法不是通用的，但有关响应类型的信息仍应传递给 OpenAI 连接器。一种方法是添加 的通用版本 `IChatCompletionService`，这可能会引入许多额外的代码更改。另一种方法是通过 object 传递类型信息 `PromptExecutionSettings` 。考虑到 `IChatCompletionService` uses `PromptExecutionSettings` 而不是 `OpenAIPromptExecutionSettings`， `ResponseFormat` 属性应该移动到基执行设置类，这样就可以传递有关响应格式的信息，而无需耦合到特定的连接器。另一方面，目前尚不清楚 parameter 是否 `ResponseFormat` 对其他 AI 连接器有用。
    3. 不支持流式处理方案，因为对于反序列化，应首先聚合所有响应内容。如果 Semantic Kernel 将执行聚合，则流式处理功能将丢失。

## 超出范围

函数调用功能超出了此 ADR 的范围，因为结构化输出功能已部分用于当前函数调用实现，方法是向 JSON 架构提供有关函数及其参数的信息。要添加到此过程的唯一剩余参数是 `strict` property，应将其设置为 `true` 在函数调用中启用 Structured Outputs。此参数可以通过 type 公开 `PromptExecutionSettings` 。 

通过将 `strict` property 设置为 `true` for function calling process，模型不应创建其他不存在的参数或函数，这可能会解决幻觉问题。另一方面，为函数调用启用结构化输出将在第一个请求期间引入额外的延迟，因为架构首先被处理，因此它可能会影响性能，这意味着此属性应有据可查。

有关更多信息，请参阅： [使用结构化输出进行函数调用](https://platform.openai.com/docs/guides/function-calling/function-calling-with-structured-outputs)。

## 决策结果

1. 支持 Option #1 和 Option #2，为 Option #3 创建一个任务以单独处理它。 
2. 在 Function Calling 中为 Structured Outputs 创建一个任务并单独处理它。
