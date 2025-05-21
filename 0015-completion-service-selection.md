
# 完井服务类型选择策略

## 上下文和问题陈述

如今，SK 使用文本完成服务运行所有文本提示。随着新的聊天完成提示和可能的其他提示类型（如图像）的添加，我们需要一种方法来选择完成服务类型来运行这些提示。

<!-- This is an optional element. Feel free to remove. -->

## 决策驱动因素

- Semantic Function 应该能够识别在处理文本、聊天或图像提示时要使用的完成服务类型。

## 考虑的选项

**1. 由 “prompt_type” 属性标识的完成服务类型。** 此选项假定将 'prompt_type' 属性添加到提示模板配置模型类 'PromptTemplateConfig' 中。该属性将由提示开发人员指定一次，并将由 'SemanticFunction' 类用于决定在解析该特定完成服务类型的实例时要使用的完成服务类型（而不是实例）。

**提示模板**

```json
{
    "schema": "1",
    "description": "Hello AI, what can you do for me?",
    "prompt_type": "<text|chat|image>",
    "models": [...]
}
```

**语义函数伪代码**

```csharp
if(string.IsNullOrEmpty(promptTemplateConfig.PromptType) || promptTemplateConfig.PromptType == "text")
{
    var service = this._serviceSelector.SelectAIService<ITextCompletion>(context.ServiceProvider, this._modelSettings);
    //render the prompt, call the service, process and return result
}
else (promptTemplateConfig.PromptType == "chat")
{
    var service = this._serviceSelector.SelectAIService<IChatCompletion>(context.ServiceProvider, this._modelSettings);
    //render the prompt, call the service, process and return result
},
else (promptTemplateConfig.PromptType == "image")
{
    var service = this._serviceSelector.SelectAIService<IImageGeneration>(context.ServiceProvider, this._modelSettings);
    //render the prompt, call the service, process and return result
}
```

**例**

```json
name: ComicStrip.Create
prompt: "Generate ideas for a comic strip based on {{$input}}. Design characters, develop the plot, ..."
config: {
	"schema": 1,
	"prompt_type": "text",
	...
}

name: ComicStrip.Draw
prompt: "Draw the comic strip - {{$comicStrip.Create $input}}"
config: {
	"schema": 1,
	"prompt_type": "image",
	...
}
```

优点：

- 确定性地指定要使用的完成服务 **类型** ，因此文本完成服务不会呈现图像提示，反之亦然。

缺点：

- 由提示开发人员指定的另一个属性。

**2. 由提示内容标识的完成服务类型。** 此选项背后的想法是通过使用正则表达式来检查是否存在与提示类型关联的特定标记来分析呈现的提示。例如， `<message role="*"></message>` 呈现的提示中存在标记可能表示该提示是聊天提示，应由聊天完成服务处理。当我们有两种完成服务类型 - 文本和聊天 - 时，这种方法可能会可靠地工作，因为逻辑很简单：如果在渲染的提示中找到消息标签，则使用聊天完成服务处理它;否则，请使用 Text Completion 服务。但是，当我们开始添加新的提示类型时，此逻辑变得不可靠，并且这些提示缺少特定于其提示类型的标记。例如，如果我们添加图像提示，我们将无法区分文本提示和图像提示，除非图像提示具有唯一标识文本提示和图像提示。

```csharp
if (Regex.IsMatch(renderedPrompt, @"<message>.*?</message>"))
{
    var service = this._serviceSelector.SelectAIService<IChatCompletion>(context.ServiceProvider, this._modelSettings);
    //render the prompt, call the service, process and return result
},
else
{
    var service = this._serviceSelector.SelectAIService<ITextCompletion>(context.ServiceProvider, this._modelSettings);
    //render the prompt, call the service, process and return result
}
```

**例**

```json
name: ComicStrip.Create
prompt: "Generate ideas for a comic strip based on {{$input}}. Design characters, develop the plot, ..."
config: {
	"schema": 1,
	...
}

name: ComicStrip.Draw
prompt: "Draw the comic strip - {{$comicStrip.Create $input}}"
config: {
	"schema": 1,
	...
}
```

优点：

- 无需新属性来标识提示类型。

缺点：

- 除非提示包含专门标识提示类型的唯一标记，否则不可靠。

## 决策结果

我们决定选择 '2.由提示内容选项标识的完成服务类型，当我们遇到此选项不支持的其他完成服务类型时，或者当我们对使用不同的机制来选择完成服务类型有一组可靠的要求时，将重新考虑它。
