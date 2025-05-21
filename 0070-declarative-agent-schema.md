<!-- filepath: d:\AGI-Projects\sk-docs-cn\0070-declarative-agent-schema.md -->

# 声明性代理格式的架构

## 上下文和问题陈述

此 ADR 描述了一个架构，该架构可用于定义一个代理，该代理可以使用 Semantic Kernel Agent Framework 加载和执行。

目前，代理框架使用代码优先方法来允许定义和执行代理。
使用此 ADR 定义的架构，开发人员将能够以声明方式定义 Agent，并让 Semantic Kernel 实例化和执行 Agent。

以下是一些伪代码来说明我们需要能够做什么：

```csharp
Kernel kernel = Kernel
    .CreateBuilder()
    .AddAzureAIClientProvider(...)
    .Build();
var text =
    """
    type: azureai_agent
    name: AzureAIAgent
    description: AzureAIAgent Description
    instructions: AzureAIAgent Instructions
    model:
      id: gpt-4o-mini
    tools:
        - name: tool1
          type: code_interpreter
    """;

AzureAIAgentFactory factory = new();
var agent = await KernelAgentYaml.FromAgentYamlAsync(kernel, text, factory);
```

上面的代码代表了最简单的情况，其工作原理如下：

1. 该 `Kernel` 实例具有适当的服务，例如创建 `AzureAIClientProvider` AzureAI 代理时的实例。
2. 将 `KernelAgentYaml.FromAgentYamlAsync` 创建一个内置 Agent 实例，即 `ChatCompletionAgent`、 `OpenAIAssistantsAgent` `AzureAIAgent`中的一个。
3. 新的 Agent 实例使用自己的实例进行初始化， `Kernel` 该实例配置了所需的服务和工具，并具有默认的初始状态。

注意：考虑只创建普通 `Agent` 实例并扩展 `Agent` 抽象以包含一个允许使用用户输入调用 Agent 实例的方法。

```csharp
Kernel kernel = ...
string text = EmbeddedResource.Read("MyAgent.yaml");
AgentFactory agentFactory = new AggregatorAgentFactory(
    new ChatCompletionAgentFactory(),
    new OpenAIAssistantAgentFactory(),
    new AzureAIAgentFactory());
var agent = KernelAgentYaml.FromAgentYamlAsync(kernel, text, factory);;
```

上面的示例显示了如何支持不同的 Agent 类型。

**注意：**

1. 带有 YAML front-matter（即 Prompty 格式）的 Markdown 将是主要使用的序列化格式。
2. Agent Framework 目前不支持提供 Agent 状态。
3. 我们需要决定 Agent Framework 是否应该定义一个抽象来允许调用任何 Agent。
4. 我们还将 JSON 作为开箱即用的选项来支持。

目前，Semantic Kernel 支持三种 Agent 类型，它们具有以下属性：

1. [`ChatCompletionAgent`](https://learn.microsoft.com/en-us/dotnet/api/microsoft.semantickernel.agents.chatcompletionagent?view=semantic-kernel-dotnet):
   - `Arguments`：代理的可选参数。（继承自 ChatHistoryKernelAgent）
   - `Description`：代理的描述（可选）。（继承自 Agent）
   - `HistoryReducer`： （继承自 ChatHistoryKernelAgent）
   - `Id`：代理的标识符（可选）。（继承自 Agent）
   - `Instructions`：代理的指示（可选）。（继承自 KernelAgent）
   - `Kernel`：包含在整个代理生命周期中使用的服务、插件和过滤器的内核。（继承自 KernelAgent）
   - `Logger`：与此代理关联的 ILogger。（继承自 Agent）
   - `LoggerFactory`：此代理的 ILoggerFactory。（继承自 Agent）
   - `Name`：代理的名称（可选）。（继承自 Agent）
2. [`OpenAIAssistantAgent`](https://learn.microsoft.com/en-us/dotnet/api/microsoft.semantickernel.agents.agent.description?view=semantic-kernel-dotnet#microsoft-semantickernel-agents-agent-description):
   - `Arguments`：代理的可选参数。
   - `Definition`：辅助定义。
   - `Description`：代理的描述（可选）。（继承自 Agent）
   - `Id`：代理的标识符（可选）。（继承自 Agent）
   - `Instructions`：代理的指示（可选）。（继承自 KernelAgent）
   - `IsDeleted`：通过 DeleteAsync（CancellationToken） 删除助手时设置。通过其他方式删除的助手在调用时将导致异常。
   - `Kernel`：包含在整个代理生命周期中使用的服务、插件和过滤器的内核。（继承自 KernelAgent）
   - `Logger`：与此代理关联的 ILogger。（继承自 Agent）
   - `LoggerFactory`：此代理的 ILoggerFactory。（继承自 Agent）
   - `Name`：代理的名称（可选）。（继承自 Agent）
   - `PollingOptions`：定义轮询行为
3. [`AzureAIAgent`](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/Agents/AzureAI/AzureAIAgent.cs)
   - `Definition`：辅助定义。
   - `PollingOptions`：定义运行处理的轮询行为。
   - `Description`：代理的描述（可选）。（继承自 Agent）
   - `Id`：代理的标识符（可选）。（继承自 Agent）
   - `Instructions`：代理的指示（可选）。（继承自 KernelAgent）
   - `IsDeleted`：通过 DeleteAsync（CancellationToken） 删除助手时设置。通过其他方式删除的助手在调用时将导致异常。
   - `Kernel`：包含在整个代理生命周期中使用的服务、插件和过滤器的内核。（继承自 KernelAgent）
   - `Logger`：与此代理关联的 ILogger。（继承自 Agent）
   - `LoggerFactory`：此代理的 ILoggerFactory。（继承自 Agent）
   - `Name`：代理的名称（可选）。（继承自 Agent）

执行以声明方式定义的 Agent 时，某些属性将由运行时确定：

- `Kernel`：运行时将负责创建 `Kernel` 代理要使用的实例。此 `Kernel` 实例必须使用 Agent 所需的模型和工具进行配置。
- `Logger` 或 `LoggerFactory`：运行时将负责提供正确配置的 `Logger` 或 `LoggerFactory`。
- **函数**：运行时必须能够解析 Agent 所需的任何函数。例如，VSCode 扩展将提供一个非常基本的运行时，允许开发人员测试 Agent，并且它应该能够解析 `KernelFunctions` 当前项目中定义的。有关此示例，请参见 ADR 后面的内容。

对于定义行为的 Agent 属性，例如 `HistoryReducer` Semantic Kernel **SHOULD：**

- 提供可以声明方式配置的实现，即对于我们希望开发人员遇到的最常见场景。
- 允许从 `Kernel` 例如，作为必需的服务或可能的 `KernelFunction`'s.

## 决策驱动因素

- 架构 **必须与** 代理服务无关，即，将与面向 Azure、Open AI、Mistral AI 等的代理一起使用。
- 架构 **必须** 允许将模型设置分配给代理。
- Schema **必须** 允许将工具（例如函数、代码解释器、文件搜索等）分配给 Agent。
- 架构 **必须** 允许定义新类型的工具供代理使用。
- 架构 **必须** 允许使用语义内核提示符（包括 Prompty 格式）来定义代理指令。
- 架构 **必须是** 可扩展的，以便可以将对具有自己的设置和工具的新代理类型的支持添加到语义内核中。
- 架构 **必须** 允许第三方向语义内核提供新的 Agent 类型。
- … <!-- numbers of drivers can vary -->

本文档将介绍以下使用案例：

1. 有关代理和文件的元数据。
2. 创建一个具有功能工具和一组指导其行为的说明的 Agent。
3. 允许 Agent 指令（和其他属性）的模板化。
4. 配置模型并提供多个模型配置。
5. 配置数据源 （context/knowledge） 以供 Agent 使用。
6. 为代理配置要使用的其他工具，例如代码解释器、OpenAPI 端点、.
7. 为 Agent 启用其他模态，例如语音。
8. 错误情况，例如模型或功能工具不可用。

### 超出范围

- 此 ADR 不涵盖多代理声明格式或进程声明格式

## 考虑的选项

- 将[声明性代理架构 1.2 用于 Microsoft 365 Copilot](https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/declarative-agent-manifest-1.2)
- 扩展 Microsoft 365 Copilot 的声明性代理架构 1.2
- 扩展 [Semantic Kernel 提示架构](https://learn.microsoft.com/en-us/semantic-kernel/concepts/prompts/yaml-schema#sample-yaml-prompt)

## 选项的优缺点

### 将声明性代理架构 1.2 用于 Microsoft 365 Copilot

Semantic Kernel 已经支持此功能，请参阅 [声明式 Agent 概念示例](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Agents/DeclarativeAgents.cs)。

- 很好，这是 Microsoft 365 Copilot 采用的现有标准。
- 中性，该模式将工具拆分为两个属性，即 `capabilities` 包括代码解释器和`actions`指定 API 插件清单。
- 糟糕，因为它确实支持不同类型的 Agent。
- 不好，因为它没有提供一种方法来指定和配置 AI 模型以与 Agent 关联。
- 不好，因为它没有提供对 Agent 说明使用提示模板的方法。
- 不好，因为 `actions` property 专注于调用 REST API 并满足本机和语义功能。

### 扩展 Microsoft 365 Copilot 的声明性代理架构 1.2

一些可能的扩展包括：

1. 可以使用提示模板创建代理说明。
2. 可以指定代理模型设置，包括基于可用模型的回退。
3. 更好地定义函数，例如对 native 和 semantic 的支持。

- 很好，因为 {argument a}
- 很好，因为 {argument b}
- 中立，因为 {argument c}
- 糟糕，因为 {argument d}
- …

### 扩展语义内核提示架构

- 很好，因为 {argument a}
- 很好，因为 {argument b}
- 中立，因为 {argument c}
- 糟糕，因为 {argument d}
- …

## 决策结果

选择的选项：“{option 1} 的标题”，因为
例如，只有选项，它满足 K.O. 标准 决策驱动 | 它解决力 {force} | ... | 效果最好（见下文）}。

<!-- This is an optional element. Feel free to remove. -->

### 后果

- 好，因为 {积极的结果，例如，一个或多个所需品质的改善，...}
- 坏的，因为 {负面后果，例如，损害一个或多个期望的品质，...}
- … <!-- numbers of consequences can vary -->

<!-- This is an optional element. Feel free to remove. -->

## 验证

{描述如何验证 ADR 的实施/合规性。例如，通过审查或 ArchUnit 测试}

<!-- This is an optional element. Feel free to remove. -->

## 更多信息

### Code First 与声明式格式

以下示例显示了用于创建不同类型 Agent 的 Code First 和等效的声明性语法。

请考虑以下使用案例：

1. `ChatCompletionAgent`
2. `ChatCompletionAgent` 使用提示模板
3. `ChatCompletionAgent` 使用函数调用
4. `OpenAIAssistantAgent` 使用函数调用
5. `OpenAIAssistantAgent` 使用工具

#### `ChatCompletionAgent`

代码优先方法：

```csharp
ChatCompletionAgent agent =
    new()
    {
        Name = "Parrot",
        Instructions = "Repeat the user message in the voice of a pirate and then end with a parrot sound.",
        Kernel = kernel,
    };
```

声明性语义内核架构：

```yml
type: chat_completion_agent
name: Parrot
instructions: Repeat the user message in the voice of a pirate and then end with a parrot sound.
```

**注意**：

- `ChatCompletionAgent` 可以是默认代理类型，因此不需要显式 `type` 属性。

#### `ChatCompletionAgent` 使用提示模板

代码优先方法：

```csharp
string generateStoryYaml = EmbeddedResource.Read("GenerateStory.yaml");
PromptTemplateConfig templateConfig = KernelFunctionYaml.ToPromptTemplateConfig(generateStoryYaml);

ChatCompletionAgent agent =
    new(templateConfig, new KernelPromptTemplateFactory())
    {
        Kernel = this.CreateKernelWithChatCompletion(),
        Arguments = new KernelArguments()
        {
            { "topic", "Dog" },
            { "length", "3" },
        }
    };
```

Agent YAML 指向另一个文件，Semantic Kernel 中的 Declarative Agent 实现已经使用这种技术来加载单独的指令文件。

用于定义说明的提示模板。
```yml
Tell a story about {{$topic}} that is {{$length}} sentences long.
```

**注意**： Semantic Kernel 可以直接加载此文件。

#### `ChatCompletionAgent` 使用函数调用

代码优先方法：

```csharp
ChatCompletionAgent agent =
    new()
    {
        Instructions = "Answer questions about the menu.",
        Name = "RestaurantHost",
        Description = "This agent answers questions about the menu.",
        Kernel = kernel,
        Arguments = new KernelArguments(new OpenAIPromptExecutionSettings() { Temperature = 0.4, FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() }),
    };

KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
agent.Kernel.Plugins.Add(plugin);
```

使用 Semantic Kernel 架构的声明性：

```yml
Answer questions about the menu.
```

#### `OpenAIAssistantAgent` 使用函数调用

代码优先方法：

```csharp
OpenAIAssistantAgent agent =
    await OpenAIAssistantAgent.CreateAsync(
        clientProvider: this.GetClientProvider(),
        definition: new OpenAIAssistantDefinition("gpt_4o")
        {
            Instructions = "Answer questions about the menu.",
            Name = "RestaurantHost",
            Metadata = new Dictionary<string, string> { { AssistantSampleMetadataKey, bool.TrueString } },
        },
        kernel: new Kernel());

KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
agent.Kernel.Plugins.Add(plugin);
```

使用 Semantic Kernel 架构的声明性：

使用下面的语法，助手的定义中没有包含的函数。
这些函数必须添加到 `Kernel` 与 Agent 关联的实例中，并将在调用 Agent 时传递。

```yml
Answer questions about the menu.
``

or

```yml
Answer questions about the menu.
```

**注意**： `Kernel` 用于创建 Agent 的实例必须具有 `OpenAIClientProvider` registered as a service 的实例。

#### `OpenAIAssistantAgent` 使用工具

代码优先方法：

```csharp
OpenAIAssistantAgent agent =
    await OpenAIAssistantAgent.CreateAsync(
        clientProvider: this.GetClientProvider(),
        definition: new(this.Model)
        {
            Instructions = "You are an Agent that can write and execute code to answer questions.",
            Name = "Coder",
            EnableCodeInterpreter = true,
            EnableFileSearch = true,
            Metadata = new Dictionary<string, string> { { AssistantSampleMetadataKey, bool.TrueString } },
        },
        kernel: new Kernel());
```

使用 Semantic Kernel 进行声明性作：

```yml
You are an Agent that can write and execute code to answer questions.
```

### 声明式格式使用案例

#### 有关代理和文件的元数据

```yaml
name: RestaurantHost
type: azureai_agent
description: This agent answers questions about the menu.
version: 0.0.1
```

#### 创建一个具有功能工具和一组指导其行为的说明的代理

#### 允许 Agent 指令（和其他属性）的模板

#### 配置模型并提供多个模型配置

#### 配置供代理使用的数据源 （context/knowledge）

#### 为 Agent 配置要使用的其他工具，例如代码解释器、OpenAPI 端点

#### 为 Agent 启用其他模态，例如语音

#### 错误情况，例如模型或功能工具不可用
