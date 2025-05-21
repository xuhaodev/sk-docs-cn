
# 函数调用内容

## 上下文和问题陈述

如今，在 SK 中，LLM 函数调用仅由 OpenAI 连接器支持，并且函数调用模型特定于该连接器。在编写 ARD 时，正在添加两个支持函数调用的新连接器，每个连接器都有自己特定的函数调用模型。该设计中，每个新连接器都引入了自己的特定模型类用于函数调用，从连接器开发的角度来看，它不能很好地扩展，并且不允许 SK 消费者代码对连接器进行多态使用。

让 LLM/服务无关的函数调用模型类的另一种情况是使代理能够相互传递函数调用。在这种情况下，使用 OpenAI Assistant API 连接器/LLM 的代理可以将函数调用 content/request/model 传递给基于 OpenAI 聊天完成 API 构建的另一个代理以执行。

此 ADR 描述了与服务无关的函数调用模型类的高级详细信息，同时将低级详细信息留给实现阶段。此外，本 ADR 还概述了设计各个方面的已确定选项。

要求 - https://github.com/microsoft/semantic-kernel/issues/5153

## 决策驱动因素
1. 连接器应使用与服务无关的函数模型类将 LLM 函数调用传达给连接器调用方。
2. 使用者应该能够使用与服务无关的函数模型类将函数结果传回连接器。  
3. 所有现有的函数调用行为应该仍然有效。  
4. 应该可以使用与服务无关的函数模型类，而无需依赖 OpenAI 包或任何其他特定于 LLM 的包。  
5. 应该可以使用函数调用和结果类序列化聊天历史记录对象，以便将来可以解除冻结（并可能使用不同的 AI 模型运行聊天历史记录）。  
6. 应该可以在 agent 之间传递函数调用。在多代理方案中，一个代理可以为另一个代理创建函数调用来完成该调用。  
7. 应该可以模拟函数调用。开发人员应该能够将带有他们创建的函数调用的聊天消息添加到聊天历史记录对象中，然后使用任何 LLM 运行它（在 OpenAI 的情况下，这可能需要模拟函数调用 ID）。

## 1. 与服务无关的函数调用模型类
如今，SK 依赖于特定于连接器的内容类将调用函数的 LLM 意向传达给 SK 连接器调用方：
```csharp
IChatCompletionService chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

ChatHistory chatHistory = new ChatHistory();
chatHistory.AddUserMessage("Given the current time of day and weather, what is the likely color of the sky in Boston?");

// The OpenAIChatMessageContent class is specific to OpenAI connectors - OpenAIChatCompletionService, AzureOpenAIChatCompletionService.
OpenAIChatMessageContent result = (OpenAIChatMessageContent)await chatCompletionService.GetChatMessageContentAsync(chatHistory, settings, kernel);

// The ChatCompletionsFunctionToolCall belongs Azure.AI.OpenAI package that is OpenAI specific.
List<ChatCompletionsFunctionToolCall> toolCalls = result.ToolCalls.OfType<ChatCompletionsFunctionToolCall>().ToList();

chatHistory.Add(result);
foreach (ChatCompletionsFunctionToolCall toolCall in toolCalls)
{
    string content = kernel.Plugins.TryGetFunctionAndArguments(toolCall, out KernelFunction? function, out KernelArguments? arguments) ?
        JsonSerializer.Serialize((await function.InvokeAsync(kernel, arguments)).GetValue<object>()) :
        "Unable to find function. Please try again!";

    chatHistory.Add(new ChatMessageContent(
        AuthorRole.Tool,
        content,
        metadata: new Dictionary<string, object?>(1) { { OpenAIChatMessageContent.ToolIdProperty, toolCall.Id } }));
}
```

这两个 `OpenAIChatMessageContent` and `ChatCompletionsFunctionToolCall` 类都是特定于 OpenAI 的，不能由非 OpenAI 连接器使用。此外，使用 LLM 供应商特定的类会使连接器的调用方代码复杂化，并且无法多态地使用连接器 - 通过接口引用连接器 `IChatCompletionService` ，同时能够交换其实现。

为了解决这个问题，我们需要一种机制，允许将 LLM 意图以调用函数的意图传达给调用者，并以与服务无关的方式将函数调用结果返回给 LLM。此外，此机制应具有足够的可扩展性，以便在 LLM 请求函数调用并在单个响应中返回其他内容类型时支持潜在的多模式情况。

考虑到 SK 聊天补全模型类已经通过集合支持多模式场景 `ChatMessageContent.Items` ，因此此集合也可以用于函数调用场景。连接器需要将 LLM 函数调用映射到与服务无关的函数内容模型类，并将它们添加到 items 集合中。同时，连接器调用方将执行函数，并通过 items 集合将执行结果传回。

下面考虑了与服务无关的函数内容模型类的几个选项。

### 选项 1.1 - FunctionCallContent 表示函数调用 （请求） 和函数结果  
此选项假定有一个与服务无关的模型类 - `FunctionCallContent` 用于传达函数调用和函数结果：
```csharp
class FunctionCallContent : KernelContent
{
    public string? Id {get; private set;}
    public string? PluginName {get; private set;}
    public string FunctionName {get; private set;}
    public KernelArguments? Arguments {get; private set; }
    public object?/FunctionResult/string? Result {get; private set;} // The type of the property is being described below.
    
    public string GetFullyQualifiedName(string functionNameSeparator = "-") {...}

    public Task<FunctionResult> InvokeAsync(Kernel kernel, CancellationToken cancellationToken = default)
    {
        // 1. Search for the plugin/function in kernel.Plugins collection.
        // 2. Create KernelArguments by deserializing Arguments.
        // 3. Invoke the function.
    }
}
```

**优点**：
- 一个模型类，用于表示函数调用和函数结果。

**缺点**：
- 连接器需要通过分析父级在聊天历史记录中的角色来确定内容是表示函数调用还是函数结果 `ChatMessageContent` ，因为类型本身并不传达其用途。  
  * 这可能根本不是一个骗局，因为需要一个协议来定义聊天消息的特定角色 （AuthorRole.Tool？） 以将函数结果传递给连接器。本 ADR 将在下文讨论详细信息。

### 选项 1.2 - FunctionCallContent 表示函数调用，FunctionResultContent 表示函数结果
此选项建议使用两个模型类 - `FunctionCallContent` 用于将函数调用传递给连接器调用者：
```csharp
class FunctionCallContent : KernelContent
{
    public string? Id {get;}
    public string? PluginName {get;}
    public string FunctionName {get;}
    public KernelArguments? Arguments {get;}
    public Exception? Exception {get; init;}

    public Task<FunctionResultContent> InvokeAsync(Kernel kernel,CancellationToken cancellationToken = default)
    {
        // 1. Search for the plugin/function in kernel.Plugins collection.
        // 2. Create KernelArguments by deserializing Arguments.
        // 3. Invoke the function.
    }

    public static IEnumerable<FunctionCallContent> GetFunctionCalls(ChatMessageContent messageContent)
    {
        // Returns list of function calls provided via <see cref="ChatMessageContent.Items"/> collection.
    }
}
```

和 - `FunctionResultContent` 用于将函数结果传回连接器：
```csharp
class FunctionResultContent : KernelContent
{
    public string? Id {get; private set;}
    public string? PluginName {get; private set;}
    public string? FunctionName {get; private set;}

    public object?/FunctionResult/string? Result {get; set;}

    public ChatMessageContent ToChatMessage()
    {
        // Creates <see cref="ChatMessageContent"/> and adds the current instance of the class to the <see cref="ChatMessageContent.Items"/> collection.
    }
}
```

**优点**：
- 与前一个选项相比，显式模型允许调用方明确声明内容的意图，而不管父消息的角色如何 `ChatMessageContent` 。  
  * 与上述选项的缺点类似，这可能不是一个优势，因为需要定义聊天消息角色的协议，以便将函数结果传递给连接器。

**缺点**：
- 一个额外的内容类。

### 连接器调用方代码示例：
```csharp
//The GetChatMessageContentAsync method returns only one choice. However, there is a GetChatMessageContentsAsync method that can return multiple choices.
ChatMessageContent messageContent = await completionService.GetChatMessageContentAsync(chatHistory, settings, kernel);
chatHistory.Add(messageContent); // Adding original chat message content containing function call(s) to the chat history

IEnumerable<FunctionCallContent> functionCalls = FunctionCallContent.GetFunctionCalls(messageContent); // Getting list of function calls.
// Alternatively: IEnumerable<FunctionCallContent> functionCalls = messageContent.Items.OfType<FunctionCallContent>();

// Iterating over the requested function calls and invoking them.
foreach (FunctionCallContent functionCall in functionCalls)
{
    FunctionResultContent? result = null;

    try
    {
        result = await functionCall.InvokeAsync(kernel); // Resolving the function call in the `Kernel.Plugins` collection and invoking it.
    }
    catch(Exception ex)
    {
        chatHistory.Add(new FunctionResultContent(functionCall, ex).ToChatMessage());
        // or
        //string message = "Error details that LLM can reason about.";
        //chatHistory.Add(new FunctionResultContent(functionCall, message).ToChatMessageContent());
        
        continue;
    }
    
    chatHistory.Add(result.ToChatMessage());
    // or chatHistory.Add(new ChatMessageContent(AuthorRole.Tool, new ChatMessageContentItemCollection() { result }));
}

// Sending chat history containing function calls and function results to the LLM to get the final response
messageContent = await completionService.GetChatMessageContentAsync(chatHistory, settings, kernel);
```

该设计不要求调用方为每个函数结果内容创建聊天消息的实例。相反，它允许通过聊天消息的单个实例将函数结果内容的多个实例发送到连接器：
```csharp
ChatMessageContent messageContent = await completionService.GetChatMessageContentAsync(chatHistory, settings, kernel);
chatHistory.Add(messageContent); // Adding original chat message content containing function call(s) to the chat history.

IEnumerable<FunctionCallContent> functionCalls = FunctionCallContent.GetFunctionCalls(messageContent); // Getting list of function calls.

ChatMessageContentItemCollection items = new ChatMessageContentItemCollection();

// Iterating over the requested function calls and invoking them
foreach (FunctionCallContent functionCall in functionCalls)
{
    FunctionResultContent result = await functionCall.InvokeAsync(kernel);

    items.Add(result);
}

chatHistory.Add(new ChatMessageContent(AuthorRole.Tool, items);

// Sending chat history containing function calls and function results to the LLM to get the final response
messageContent = await completionService.GetChatMessageContentAsync(chatHistory, settings, kernel);
```

### 决策结果
选择选项 1.2 是因为它具有显式性质。

## 2. 聊天完成连接器的函数调用协议
不同的聊天完成连接器可能会将函数调用传达给调用方，并期望通过具有连接器特定角色的消息发回函数结果。例如， `{Azure}OpenAIChatCompletionService` 连接器使用带有角色的消息 `Assistant` 将函数调用传达给连接器调用者，并期望调用者通过带有角色的消息返回函数结果 `Tool` 。  
   
连接器返回的函数调用消息的角色对调用者来说并不重要，因为 `GetFunctionCalls` 无论响应消息的角色如何，都可以通过调用该方法轻松获取函数列表。

```csharp
ChatMessageContent messageContent = await completionService.GetChatMessageContentAsync(chatHistory, settings, kernel);

IEnumerable<FunctionCallContent> functionCalls = FunctionCallContent.GetFunctionCalls(); // Will return list of function calls regardless of the role of the messageContent if the content contains the function calls.
```

但是，对于连接器的多态使用，邮件只有一个与连接器无关的角色将函数结果发送回连接器，这一点很重要。这将允许调用方编写如下代码：

 ```csharp
 ...
IEnumerable<FunctionCallContent> functionCalls = FunctionCallContent.GetFunctionCalls();

foreach (FunctionCallContent functionCall in functionCalls)
{
    FunctionResultContent result = await functionCall.InvokeAsync(kernel);

    chatHistory.Add(result.ToChatMessage());
}
...
```

并避免使用这样的代码：

```csharp
IChatCompletionService chatCompletionService = new();
...
IEnumerable<FunctionCallContent> functionCalls = FunctionCallContent.GetFunctionCalls();

foreach (FunctionCallContent functionCall in functionCalls)
{
    FunctionResultContent result = await functionCall.InvokeAsync(kernel);

    // Using connector-specific roles instead of a single connector-agnostic one to send results back to the connector would prevent the polymorphic usage of connectors and force callers to write if/else blocks.
    if(chatCompletionService is OpenAIChatCompletionService || chatCompletionService is AzureOpenAIChatCompletionService)
    {
        chatHistory.Add(new ChatMessageContent(AuthorRole.Tool, new ChatMessageContentItemCollection() { result });
    }
    else if(chatCompletionService is AnotherCompletionService)
    {
        chatHistory.Add(new ChatMessageContent(AuthorRole.Function, new ChatMessageContentItemCollection() { result });
    }
    else if(chatCompletionService is SomeOtherCompletionService)
    {
        chatHistory.Add(new ChatMessageContent(AuthorRole.ServiceSpecificRole, new ChatMessageContentItemCollection() { result });
    }
}
...
```

### 决策结果
之所以决定使用这个 `AuthorRole.Tool` 角色，是因为它是众所周知的，从概念上讲，它可以表示功能结果以及 SK 将来需要支持的任何其他工具。

## 3. FunctionResultContent.Result 属性的类型：
有几种数据类型可用于该 `FunctionResultContent.Result` 属性。有问题的数据类型应允许以下情况：  
- 可序列化/可反序列化，以便可以序列化包含函数结果内容的聊天历史记录，并在以后需要时解除冻结。  
- 应该可以通过向 LLM 发送原始异常或描述问题的字符串来传达函数执行失败。  
   
到目前为止，已经确定了三种可能的数据类型：object、string 和 FunctionResult。

### 选项 3.1 - 对象
```csharp
class FunctionResultContent : KernelContent
{
    // Other members are omitted
    public object? Result {get; set;}
}
```

此选项可能需要使用 JSON 转换器/解析器对聊天历史记录进行 {de}序列化，其中包含由 JsonSerializer 默认不支持的类型表示的函数结果。

**优点**：
- 序列化由连接器执行，但如有必要，也可以由调用方执行。
- 如果需要，调用方可以提供其他数据以及函数结果。
- 调用者可以控制如何传达函数执行失败：通过传递 Exception 类的实例或向 LLM 提供问题的字符串描述。

**缺点**：


### 选项 3.2 - 字符串（当前实现）
```csharp
class FunctionResultContent : KernelContent
{
    // Other members are omitted
    public string? Result {get; set;}
}
```
**优点**：
- 聊天记录 {de} 序列化不需要转换器。
- 如果需要，调用方可以提供其他数据以及函数结果。
- 调用者可以控制如何传达函数执行失败：通过传递序列化异常、其消息或向 LLM 提供问题的字符串描述。

**缺点**：
- 序列化由调用方执行。对于聊天完成服务的多态使用，可能会出现问题。

### 选项 3.3 - FunctionResult
```csharp
class FunctionResultContent : KernelContent
{
    // Other members are omitted
    public FunctionResult? Result {get;set;}

    public Exception? Exception {get;set}
    or 
    public object? Error { get; set; } // Can contain either an instance of an Exception class or a string describing the problem.
}
```
**优点**：
- 使用 FunctionResult SK 域类。

**缺点**：
- 如果没有额外的 Exception/Error 属性，则无法将异常传达给连接器/LLM。  
- `FunctionResult` 今天不是 {de}可序列化的：
  * 默认情况下，该 `FunctionResult.ValueType` 属性的类型 `Type` 不能被 JsonSerializer 序列化，因为它被认为是危险的。  
  * 这同样适用于 `KernelReturnParameterMetadata.ParameterType` 和 `KernelParameterMetadata.ParameterType` 类型的属性 `Type`。  
  * 该 `FunctionResult.Function` 属性是不可反序列化的，应该用 attribute 标记 [JsonIgnore] 。  
    * 需要添加新的构造函数 ctr（object？ value = null， IReadOnlyDictionary<string, object?>？ metadata = null） 以进行反序列化。 
    * 该 `FunctionResult.Function` 属性必须是可为 null的。这可能是一个突破性的变化？对于函数过滤器 users，因为过滤器使用 `FunctionFilterContext` 通过属性公开 kernel function 实例的类 `Function` 。

### 选项 3.4 - FunctionResult： KernelContent
注意： 此选项是在对本 ADR 进行第二轮审核时建议的。
   
此选项建议将 `FunctionResult` class 设为 class 的派生 `KernelContent` ：
```csharp
public class FunctionResult : KernelContent
{
    ....
}
```
因此，该类将从类继承`FunctionResultContent`，成为内容本身，而不是使用单独的 `FunctionResult` 类来表示函数结果内容 `KernelContent` 。因此，该方法返回的函数结果 `KernelFunction.InvokeAsync` 可以直接添加到集合中 `ChatMessageContent.Items` ：
```csharp
foreach (FunctionCallContent functionCall in functionCalls)
{
    FunctionResult result = await functionCall.InvokeAsync(kernel);

    chatHistory.Add(new ChatMessageContent(AuthorRole.Tool, new ChatMessageContentItemCollection { result }));
    // instead of
    chatHistory.Add(new ChatMessageContent(AuthorRole.Tool, new ChatMessageContentItemCollection { new FunctionResultContent(functionCall, result) }));
    
    // of cause, the syntax can be simplified by having additional instance/extension methods
    chatHistory.AddFunctionResultMessage(result); // Using the new AddFunctionResultMessage extension method of ChatHistory class
}
```

问题：
- 如何将原始数据与 `FunctionCallContent` 函数结果一起传递给连接器。实际上，目前尚不清楚是否需要它。目前的基本原理是，某些模型可能希望原始函数调用的属性（例如参数）与函数结果一起传递回 LLM。如果需要，可以提出一个参数，即连接器可以在聊天历史记录中找到原始函数调用。然而，一个反驳意见是，这可能并不总是可能的，因为聊天记录可能会被截断以保存令牌、减少幻觉等。
- 如何将函数 ID 传递给 connector？
- 如何将异常传达给连接器？建议将属性添加 `Exception` `FunctionResult` 将始终由该方法分配的类 `KernelFunction.InvokeAsync` 。但是，此更改将破坏 C# 函数调用语义，如果满足合同，则应执行该函数，如果未满足合同，则应引发异常。
- 如果 `FunctionResult` 通过继承类成为非直播内容，那么以后`KernelContent`需要的时候`FunctionResult`/如果需要的话，如何表示类所代表的流媒体内容能力 `StreamingKernelContent` 呢？C# 不支持多重继承。

**优点**
- 该 `FunctionResult` 类本身就是一个内容（非流式的），并且可以传递到所有需要内容的地方。
- 不需要额外的 `FunctionResultContent` 类 。
  
**缺点**
- 和 类之间不必要的耦合 `FunctionResult` `KernelContent` 可能是一个限制因素，阻止每个类都像其他方式那样独立发展。
-  `FunctionResult.Function` 需要将属性更改为 nullable 才能序列化，或者必须应用自定义序列化来 {de}序列化函数架构，而无需函数实例本身。  
-  `Id` 应将该属性添加到 `FunctionResult` 类中，以表示 LLM 所需的函数 ID。
- 
### 决策结果
最初，决定使用选项 3.1，因为与其他两个相比，它是最灵活的选项。如果连接器需要获取函数架构，可以很容易地从 kernel 获取。Plugins 集合。函数结果元数据可以通过属性传递到连接器 `KernelContent.Metadata` 。
然而，在对该 ADR 的第二轮审查期间，建议探索选项 3.4。最后，在对选项 3.4 进行原型设计后，由于选项 3.4 的缺点，决定返回选项 3.1。

## 4. 模拟功能
在某些情况下，由于模型的训练，LLM 会忽略提示中提供的数据。但是，如果通过函数 result 将模型提供给模型，则模型可以使用相同的数据。  
   
有几种方法可以对模拟函数进行建模：

### 选项 4.1 - 模拟函数作为 SemanticFunction
```csharp
...

ChatMessageContent messageContent = await completionService.GetChatMessageContentAsync(chatHistory, settings, kernel);

// Simulated function call
FunctionCallContent simulatedFunctionCall = new FunctionCallContent(name: "weather-alert", id: "call_123");
messageContent.Items.Add(simulatedFunctionCall); // Adding a simulated function call to the connector response message

chatHistory.Add(messageContent);

// Creating SK function and invoking it
KernelFunction simulatedFunction = KernelFunctionFactory.CreateFromMethod(() => "A Tornado Watch has been issued, with potential for severe ..... Stay informed and follow safety instructions from authorities.");
FunctionResult simulatedFunctionResult = await simulatedFunction.InvokeAsync(kernel);

chatHistory.Add(new ChatMessageContent(AuthorRole.Tool, new ChatMessageContentItemCollection() { new FunctionResultContent(simulatedFunctionCall, simulatedFunctionResult) }));

messageContent = await completionService.GetChatMessageContentAsync(chatHistory, settings, kernel);

...
```
**优点**：
- 当调用方调用模拟函数时，可以触发 SK 函数过滤器/钩子。
 
**缺点**：
- 不如其他选项轻。

### 选项 4.2 - 对象作为模拟函数
```csharp
...

ChatMessageContent messageContent = await completionService.GetChatMessageContentAsync(chatHistory, settings, kernel);

// Simulated function
FunctionCallContent simulatedFunctionCall = new FunctionCallContent(name: "weather-alert", id: "call_123");
messageContent.Items.Add(simulatedFunctionCall);

chatHistory.Add(messageContent);

// Creating simulated result
string simulatedFunctionResult = "A Tornado Watch has been issued, with potential for severe ..... Stay informed and follow safety instructions from authorities."

//or

WeatherAlert simulatedFunctionResult = new WeatherAlert { Id = "34SD7RTYE4", Text = "A Tornado Watch has been issued, with potential for severe ..... Stay informed and follow safety instructions from authorities." };

chatHistory.Add(new ChatMessageContent(AuthorRole.Tool, new ChatMessageContentItemCollection() { new FunctionResultContent(simulatedFunctionCall, simulatedFunctionResult) }));

messageContent = await completionService.GetChatMessageContentAsync(chatHistory, settings, kernel);

...
```
**优点**：
- 与前一个选项相比，这是一个更轻量级的选项，因为不需要创建和执行 SK 函数。

**缺点**：
- 当调用方调用模拟函数时，无法触发 SK 函数过滤器/钩子。

### 决策结果
提供的选项不是互斥的;每个都可以根据场景使用。

## 5. 流媒体
连接器的流式处理 API 的与服务无关的函数调用模型的设计应类似于上述非流式处理模型。
  
流式处理 API 与非流式处理 API 的不同之处在于，内容以块的形式返回，而不是一次全部返回。例如，OpenAI 连接器目前以两个块的形式返回函数调用：函数 id 和 name 位于第一个块中，而函数参数则在后续块中发送。此外，LLM 可能会在同一响应中流式传输多个函数的函数调用。例如，连接器流式传输的第一个数据块可能具有第一个函数的 id 和 name，而后续数据块将具有第二个函数的 id 和 name。 

这将要求流式处理 API 的函数调用模型设计略有偏差，以便更自然地适应流式处理细节。如果出现重大偏差，将创建一个单独的 ADR 来概述详细信息。