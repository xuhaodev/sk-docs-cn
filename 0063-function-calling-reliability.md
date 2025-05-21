
# 函数调用可靠性

## 上下文和问题陈述
函数调用的一个关键方面决定了 SK 函数调用的可靠性，是 AI 模型能够使用公布函数的确切名称来调用函数。

AI 模型在调用函数名称时，通常会产生幻觉。在大多数情况下，
函数名称中只有一个字符是幻觉的，函数名称的其余部分是正确的。此字符是 `-` 
SK 在发布函数以唯一标识时，用作插件名称和函数名称之间的分隔符，以形成函数完全限定名称 （FQN）
函数。例如，如果插件名称为 `foo` ，函数名称为 `bar`，则函数的 FQN 为 `foo-bar`。幻觉的名字
到目前为止看到的是 `foo_bar`， `foo.bar`。

### 问题 #1：下划线分隔符幻觉 - `foo_bar`

当 AI 模型幻觉下划线分隔符时`_`，SK 检测到此错误并返回消息_“错误：未定义的函数的函数调用请求”。_
作为函数结果的一部分添加到模型中，以及原始函数调用。
某些模型可以自动从此错误中恢复并使用正确的名称调用函数，而其他模型则不能。

### 问题 #2：点分隔符幻觉 - `foo.bar`

此问题与问题 #1 类似，但在本例中，分隔符为 `.`.虽然 SK 检测到此错误并尝试在后续请求中将其返回给 AI 模型，
请求失败，并显示异常：“_Invalid messages[3][0].tool_calls.function.name： string does not match pattern.预期字符串与模式 ^[a-zA-Z0-9_-]+$ 匹配。_
失败的原因是 `.` 函数名称中不允许使用幻觉分隔符。从本质上讲，模型拒绝了它自己产生幻觉的函数名称。

### 问题 #3：自动恢复机制的可靠性  
   
当使用不同于其通告名称的名称调用函数时，找不到该函数，从而导致向 AI 模型返回错误消息，如上所述。
此错误消息为 AI 模型提供了有关问题的提示，帮助它通过使用正确的名称调用函数来自动恢复。
但是，自动恢复机制无法在不同模型之间可靠地运行。
例如，它与模型一起工作， `gpt-4o-mini(2024-07-18)` 但对 `gpt-4(0613)` and `gpt-4o(2024-08-06)` 1 失败。
当 AI 模型无法恢复时，它只会返回错误消息的变体：“ _很抱歉，但由于系统错误，我现在无法提供答案。请稍后再试。_   

## 决策驱动因素

- 尽量减少函数名称幻觉的发生。
- 增强自动恢复机制的可靠性。

## 考虑的选项
某些选项不是互斥的，可以组合使用。

### 选项 1：仅对函数 FQN 使用函数名称

此选项建议仅使用函数名称作为函数的 FQN。例如，插件中函数的 FQN `bar` `foo` 就是 `bar`。
通过仅使用函数名称，我们消除了对分隔符的需求 `-`，这通常是幻觉。

优点：
- 通过消除幻觉的来源来减少或消除函数名称幻觉（问题 #1 和 #2）。
- 减少函数 FQN 中插件名称消耗的令牌数。

缺点：
- 函数名称在所有插件中可能不唯一。例如，如果两个插件有一个同名的函数，两个插件都会提供给 AI 模型，SK 会调用遇到的第一个函数。
    - [来自 ADR 审查会议] 如果找到重复项，则可以将插件名称动态添加到重复项或所有公布的函数中。
- 缺少插件名称可能会导致函数名称的上下文不足。例如，与插件相比，该函数 `GetData` 在插件的上下文中具有不同 `Weather` 的含义`Stocks`。
    - [来自 ADR 审查会议] 插件名称/上下文可以由插件开发人员添加到函数名称或描述中，也可以由 SK 自动添加到函数描述中。
- 它无法处理幻觉函数名称。例如，如果 AI 模型产生幻觉，则函数 FQN `b0r` 而不是 `bar`。


可能的实现方式：
```csharp
// Either at the operation level
FunctionChoiceBehaviorOptions options = new new()
{
    UseFunctionNameAsFqn = true
};

var settings = new AzureOpenAIPromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(options) };

var result = await this._chatCompletionService.GetChatMessageContentAsync(chatHistory, settings, this._kernel);

// Or at the AI connector configuration level
IKernelBuilder builder = Kernel.CreateBuilder();
builder.AddOpenAIChatCompletion("<model-id>", "<api-key>", functionNamePolicy: FunctionNamePolicy.UseFunctionNameAsFqn);

// Or at the plugin level
string pluginName = string.Empty;

// If the plugin name is not an empty string, it will be used as the plugin name.   
// If it is null, then the plugin name will be inferred from the plugin type.   
// Otherwise, if the plugin name is an empty string, the plugin name will be omitted,   
// and all its functions will be advertised without a plugin name.  
kernel.ImportPluginFromType<Bar>(pluginName);
```


### 选项 2：自定义分隔符

此选项建议将分隔符或字符序列设置为可配置。开发人员可以指定一个不太可能出错的分隔符
由 AI 模型生成。例如，他们可以选择 `_` 或 `a1b` 作为分隔符。

此解决方案可能会减少函数名称幻觉的发生（问题 #1 和 #2）。

优点：
- 通过将分隔符更改为不太可能出现幻觉的角色来减少函数名称幻觉。

缺点：
- 它不适用于在插件名称中使用分隔符的情况。例如，下划线符号可以是 `my_plugin` 插件名称的一部分，也可以用作分隔符，从而生成 `my_plugin_myfunction` FQN。
    - [来自 ADR 审查会议] SK 可以在公布插件名称和函数名称之前动态删除插件名称和函数名称中出现的任何分隔符。
- 它无法处理幻觉函数名称。例如，如果 AI 模型生成函数 FQN as `MyPlugin_my_func` 而不是 `MyPlugin_my_function`。

可能的实现方式：
```csharp
// Either at the operation level
FunctionChoiceBehaviorOptions options = new new()
{
    FqnSeparator = "_"
};

var settings = new AzureOpenAIPromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(options) };

var result = await this._chatCompletionService.GetChatMessageContentAsync(chatHistory, settings, this._kernel);

// Or at the AI connector configuration level
IKernelBuilder builder = Kernel.CreateBuilder();
builder.AddOpenAIChatCompletion("<model-id>", "<api-key>", functionNamePolicy: FunctionNamePolicy.Custom("_"));
```

### 选项 3：无分隔符  
   
此选项建议在插件名称和函数名称之间不使用任何分隔符。相反，它们将直接连接。
例如，插件中函数的 FQN `bar` `foo` 将为 `foobar`.

优点：
- 通过消除幻觉的来源来减少功能名称幻觉（问题 #1 和 #2）。

缺点：
- 需要不同的函数查找启发式方法。

### 选项 4：自定义 FQN 解析器

此选项提供了一个自定义的外部 FQN 解析器，可以将函数 FQN 拆分为插件名称和函数名称。解析器将接受 AI 模型调用的函数 FQN
并返回插件名称和函数名称。为此，解析器将尝试使用各种分隔符解析 FQN：
```csharp
static (string? PluginName, string FunctionName) ParseFunctionFqn(ParseFunctionFqnContext context)
{
    static (string? PluginName, string FunctionName)? Parse(ParseFunctionFqnContext context, char separator)
    {
        string? pluginName = null;
        string functionName = context.FunctionFqn;

        int separatorPos = context.FunctionFqn.IndexOf(separator, StringComparison.Ordinal);
        if (separatorPos >= 0)
        {
            pluginName = context.FunctionFqn.AsSpan(0, separatorPos).Trim().ToString();
            functionName = context.FunctionFqn.AsSpan(separatorPos + 1).Trim().ToString();
        }

        // Check if the function registered in the kernel
        if (context.Kernel is { } kernel && kernel.Plugins.TryGetFunction(pluginName, functionName, out _))
        {
            return (pluginName, functionName);
        }

        return null;
    }

    // Try to use use hyphen, dot, and underscore sequentially as separators.
    var result = Parse(context, '-') ??
                    Parse(context, '.') ??
                    Parse(context, '_');

    if (result is not null)
    {
        return result.Value;
    }

    // If no separator is found, return the function name as is allowing AI connector to apply default behavior.
    return (null, context.FunctionFqn);
}
```

[来自 ADR 审查会议] 或者，解析器可以返回函数本身。这需要进一步调查。
此 [PR](https://github.com/microsoft/semantic-kernel/pull/10206) 可以提供有关分析程序的使用方式和位置的更多见解。

优点：
- 它将通过应用特定于 AI 模型的自定义启发式方法来解析函数 FQN，从而减轻但不会减少或完全消除函数分隔符幻觉。
- 它可以在 SK AI 连接器中轻松实现。


可能的实现方式：
```csharp
// Either at the operation level
static (string? PluginName, string FunctionName) ParseFunctionFqn(ParseFunctionFqnContext context)
{
    ...
}

FunctionChoiceBehaviorOptions options = new new()
{
    FqnParser = ParseFunctionFqn
};

var settings = new AzureOpenAIPromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(options) };

var result = await this._chatCompletionService.GetChatMessageContentAsync(chatHistory, settings, this._kernel);

// Or at the AI connector configuration level
IKernelBuilder builder = Kernel.CreateBuilder();
builder.AddOpenAIChatCompletion("<model-id>", "<api-key>", functionNamePolicy: FunctionNamePolicy.Custom("_", ParseFunctionFqn));
```

### 选项 5：改进的自动恢复机制

目前，当调用未公布的函数时，SK 会返回错误消息：“_错误：未定义的函数的函数调用请求”。_
在这三个 AI 模型中`gpt-4(0613)`， `gpt-4o-mini(2024-07-18)` `gpt-4o(2024-08-06)` 只有 `gpt-4o-mini` 和  才能自动从此错误中恢复，并使用正确的名称成功调用函数。
其他两个模型无法恢复，而是返回类似于“_对不起，但由于系统错误，我现在无法提供答案”的最终消息。_

但是，通过将函数名称添加到错误消息中 - “错误：未定义的函数的函数调用请求 **foo.bar** 。”以及
“你可以调用工具。如果工具调用失败，请自行更正。系统消息添加到聊天记录中，所有三个模型都可以从错误中自动恢复并使用正确的名称调用函数。

考虑到所有这些，我们可以在错误消息中添加函数名称，并提供添加系统消息的建议以改进自动恢复机制。

优点：
- 更多模型可以从错误中自动恢复。

缺点：
- 自动恢复机制可能不适用于所有 AI 模型。

可能的实现方式：
```csharp
// The caller code
 var chatHistory = new ChatHistory();
 chatHistory.AddSystemMessage("You can call tools. If a tool call failed, correct yourself.");
 chatHistory.AddUserMessage("<prompt>");


// In function calls processor
if (!checkIfFunctionAdvertised(functionCall))
{
    // errorMessage = "Error: Function call request for a function that wasn't defined.";
    errorMessage = $"Error: Function call request for the function that wasn't defined - {functionCall.FunctionName}.";
    return false;
}
```
 
### 选项 6：从函数名称中删除不允许的字符
   
此选项建议通过在将错误消息返回给 AI 模型时从函数 FQN 中删除不允许的字符来解决问题 2。
此更改将防止对 AI 模型的请求失败，并显示异常：“_Invalid messages[3][0].tool_calls.function.name： string does not match pattern.预期字符串与模式 `^[a-zA-Z0-9_-]+$`“_.
   
优点：
- 它将消除阻止 AI 模型从错误中自动恢复的问题 2。
   

可能的实现方式：
```csharp
// In AI connectors

var fqn = FunctionName.ToFullyQualifiedName(callRequest.FunctionName, callRequest.PluginName, OpenAIFunction.NameSeparator);

// Replace all disallowed characters with an underscore.
fqn = Regex.Replace(fqn, "[^a-zA-Z0-9_-]", "_");

toolCalls.Add(ChatToolCall.CreateFunctionToolCall(callRequest.Id, fqn, BinaryData.FromString(argument ?? string.Empty)));
```

## 决策结果
我们决定从不需要更改公共 API 表面的选项开始 - 选项 5 和 6，然后根据需要稍后继续执行其他选项。
在评估了两个应用选项的影响之后。