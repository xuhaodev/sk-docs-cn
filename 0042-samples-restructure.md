
## 上下文和问题陈述

- 目前的样本结构方式信息量不大，也不容易找到。
- Kernel Syntax Examples 中的编号失去了它的意义。
- 项目的命名并没有传达出它们到底是什么的明确信息。
- 文件夹和解决方案具有 `Examples` 不是必需的后缀，因为 中的所有内容 `samples` 都已是 `example`.

### 当前确定的样本类型

| 类型             | 描述                                                                                              |
| ---------------- | -------------------------------------------------------------------------------------------------------- |
| `GettingStarted` | 用于入门的单个分步教程                                                            |
| `Concepts`       | 按功能划分的概念特定代码片段                                                              |
| `LearnResources` | 与 Microsoft Learn、DevBlogs 等在线文档源相关的代码片段 |
| `Tutorials`      | 更深入的分步教程                                                                     |
| `Demos`          | 利用一个或多个功能的演示应用程序                               |

## 决策驱动因素和原则

- **易于搜索**：结构井然有序，便于查找不同类型的样品
- **精益命名**：文件夹、解决方案和示例名称尽可能清晰和简短
- **发出明确的信息**：避免 Semantic Kernel 特定的热度或行话
- **Cross Language**：示例结构在所有支持的 SK 语言上都相似。

## 当前现有文件夹的策略

| 当前文件夹                       | 建议                                                            |
| ------------------------------------ | ------------------------------------------------------------------- |
| KernelSyntaxExamples/Getting_Started | 搬入 `GettingStarted`                                          |
| KernelSyntaxExamples/`Examples??_*`  | 分解为 `Concepts` 多个概念子文件夹         |
| AgentSyntax示例                  | 分解为 `Concepts` 特定 `Agents` 子文件夹。          |
| 文档示例                | 移动到 `LearnResources` 子文件夹并重命名为 `MicrosoftLearn` |
| CreateChatGpt插件                  | 移动到 `Demo` 子文件夹中                                          |
| HomeAutomation                       | 移动到 `Demo` 子文件夹中                                          |
| 遥测示例                     | 移动到 `Demo` 子文件夹并重命名为 `TelemetryWithAppInsights` |
| HuggingFaceImageText示例          | 移动到 `Demo` 子文件夹并重命名为 `HuggingFaceImageToText`   |

## 考虑的根结构选项

以下选项是文件夹根结构可能考虑的选项 `samples` 。

### 选项 1 - 超窄根分类

此选项在`samples`查找样本时尽可能多地压缩不同子类别中文件夹的根目录，以使其最简。

建议的根结构

```
samples/
├── Tutorials/
│   └── Getting Started/
├── Concepts/
│   ├── Kernel Syntax**
│   └── Agents Syntax**
├── Resources/
└── Demos/
```

优点：

- 更简单、更不详细的结构（越差越好：越少越好的方法）
- 初学者将看到 （兄弟文件夹） 其他教程，这些教程可能更适合他们的需求和用例。
- 不会强制实施 Getting started。

缺点：

- 可能会增加额外的认知负荷，知道这是一个 `Getting Started` 教程

### 选项 2 - 入门根分类

此选项将 `Getting Started` 引入根文件夹， `samples` 与 中建议的结构进行比较 `Option 1`。

建议的根结构

```
samples/
├── Getting Started/
├── Tutorials/
├── Concepts/
│   ├── Kernel Syntax Decomposition**
│   └── Agents Syntax Decomposition**
├── Resources/
└── Demos/
```

优点：

- 开始使用是客户首先看到的内容
- 初学者需要额外的单击才能开始使用。

缺点：

- 如果 Getting started 示例没有客户的有效示例，则它必须返回其他文件夹以获取更多内容。

### 选项 3 - 保守 + 基于用例的根分类

此选项更为保守，并将 Syntax Examples 项目保留为根选项，并保留 Use Cases、Modalities 和 Kernel Content 的一些新文件夹。

建议的根结构

```
samples/
|── QuickStart/
|── Tutorials/
├── KernelSyntaxExamples/
├── AgentSyntaxExamples/
├── UseCases/ OR Demos/
├── KernelContent/ OR Modalities/
├── Documentation/ OR Resources/
```

优点：

- 更保守的方法是将 KernelSyntaxExamples 和 AgentSyntaxExamples 保留为根文件夹不会破坏任何现有的 Internet 链接。
- Use Cases、Modalities 和 Kernel Content 是针对不同类型样本的更具体的文件夹

缺点：

- 更详细的结构会增加查找样本的额外摩擦。
- `KernelContent` 或者 `Modalities` 是客户可能不清楚的内部术语
- `Documentation` 可能会混淆 Documents Only 文件夹，该文件夹实际上包含文档中使用的代码示例。（不明确消息）
- `Use Cases` 可能会暗示一个实际用例的想法，而实际上这些是 SK 功能的简单演示。

## KernelSyntaxExamples 分解选项

目前，Kernel Syntax Examples 包含 70 多个并排编号的示例，其中数字没有进度含义，信息量不大。

对于基于开发的 Kernel 和 Features `Concepts`的多个子文件夹的 KernelSyntaxExamples 文件夹分解，请考虑以下选项。

确定的面向组件的概念：

- 内核

  - 建筑工人
  - 功能
    - 参数
    - 方法函数
    - PromptFunctions 函数
    - 类型
    - 结果
      - 序列化
      - 元数据
      - 强类型
    - 内联函数
  - 插件
    - 描述插件
    - OpenAI 插件
    - OpenAPI 插件
      - API 清单
    - gRPC 插件
    - 可变插件
  - AI 服务（通过内核调用使用服务的示例）
    - 聊天完成
    - 文本生成
    - 服务选择器
  - 钩
  - 过滤 器
    - 函数过滤
    - 模板渲染过滤
    - 函数调用筛选（如果可用）
  - 模板

- AI 服务（直接使用服务的示例，包括单个/多个 + 流式处理和非流式处理结果）

  - 执行设置
  - 聊天完成
    - 本地模型
      - 奥拉马
      - 拥抱脸
      - LMStudio
      - 本地人工智能
    - 双子座
    - 开放人工智能
    - AzureOpenAI
    - 拥抱脸
  - 文本生成
    - 本地模型
      - 奥拉马
      - 拥抱脸
    - 开放人工智能
    - AzureOpenAI
    - 拥抱脸
  - 文本到图像
    - 开放人工智能
    - AzureOpenAI
  - 图像到文本
    - 拥抱脸
  - 文本到音频
    - 开放人工智能
  - 音频到文本
    - 开放人工智能
  - 习惯
    - 戴伊
    - 开放人工智能
      - OpenAI 文件

- 内存服务

  - 搜索

    - 语义记忆
    - 文本记忆
    - Azure AI 搜索

  - 文本嵌入
    - 开放人工智能
    - 拥抱脸

- 遥测
- 伐木
- 依赖关系注入

- Http客户端

  - 弹性
  - 用法

- 规划

  - Handlerbars

- 认证

  - Azure AD

- 函数调用

  - 自动函数调用
  - 手动函数调用

- 滤波

  - 内核钩子
  - 服务选择器

- 模板
- 达观

- 记忆

  - 语义记忆
  - 文本内存插件
  - 搜索

- 抹布

  - 内嵌
  - 函数调用

- 代理

  - 代表团
  - 图表
  - 协作
  - 创作
  - 工具
  - 聊天完成代理
    （代理语法示例：不带编号）

- 流编排器

### KernelSyntaxExamples 分解选项 1 - 按组件划分的概念

此选项分解了 Concepts Structured by Kernel Components and Features。

乍一看，这些概念是如何关联的似乎合乎逻辑且易于理解的，并且可以按照提供的结构演变为更高级的概念。

大（每个文件夹的文件较少）：

```
Concepts/
├── Kernel/
│   ├── Builder/
│   ├── Functions/
│   │   ├── Arguments/
│   │   ├── MethodFunctions/
│   │   ├── PromptFunctions/
│   │   ├── Types/
│   │   ├── Results/
│   │   │   ├── Serialization/
│   │   │   ├── Metadata/
│   │   │   └── Strongly typed/
│   │   └── InlineFunctions/
│   ├── Plugins/
│   │   ├── Describe Plugins/
│   │   ├── OpenAI Plugins/
│   │   ├── OpenAPI Plugins/
│   │   │   └── API Manifest/
│   │   ├── gRPC Plugins/
│   │   └── Mutable Plugins/
│   ├── AI Services (Examples using Services thru Kernel Invocation)/
│   │   ├── Chat Completion/
│   │   ├── Text Generation/
│   │   └── Service Selector/
│   ├── Hooks/
│   ├── Filters/
│   │   ├── Function Filtering/
│   │   ├── Template Rendering Filtering/
│   │   └── Function Call Filtering (When available)/
│   └── Templates/
├── AI Services (Examples using Services directly with Single/Multiple + Streaming and Non-Streaming results)/
│   ├── ExecutionSettings/
│   ├── Chat Completion/
│   │   ├── LocalModels/
|   │   │   ├── LMStudio/
|   │   │   ├── LocalAI/
|   │   │   ├── Ollama/
|   │   │   └── HuggingFace/
│   │   ├── Gemini/
│   │   ├── OpenAI/
│   │   ├── AzureOpenAI/
│   │   ├── LMStudio/
│   │   ├── Ollama/
│   │   └── HuggingFace/
│   ├── Text Generation/
│   │   ├── LocalModels/
|   │   │   ├── Ollama/
|   │   │   └── HuggingFace/
│   │   ├── OpenAI/
│   │   ├── AzureOpenAI/
│   │   └── HuggingFace/
│   ├── Text to Image/
│   │   ├── OpenAI/
│   │   └── AzureOpenAI/
│   ├── Image to Text/
│   │   └── HuggingFace/
│   ├── Text to Audio/
│   │   └── OpenAI/
│   ├── Audio to Text/
│   │   └── OpenAI/
│   └── Custom/
│       ├── DYI/
│       └── OpenAI/
│           └── OpenAI File/
├── Memory Services/
│   ├── Search/
│   │   ├── Semantic Memory/
│   │   ├── Text Memory/
│   │   └── Azure AI Search/
│   └── Text Embeddings/
│       ├── OpenAI/
│       └── HuggingFace/
├── Telemetry/
├── Logging/
├── Dependency Injection/
├── HttpClient/
│   ├── Resiliency/
│   └── Usage/
├── Planners/
│   └── Handlerbars/
├── Authentication/
│   └── Azure AD/
├── Function Calling/
│   ├── Auto Function Calling/
│   └── Manual Function Calling/
├── Filtering/
│   ├── Kernel Hooks/
│   └── Service Selector/
├── Templates/
├── Resilience/
├── Memory/
│   ├── Semantic Memory/
│   ├── Text Memory Plugin/
│   └── Search/
├── RAG/
│   ├── Inline/
│   └── Function Calling/
├── Agents/
│   ├── Delegation/
│   ├── Charts/
│   ├── Collaboration/
│   ├── Authoring/
│   ├── Tools/
│   └── Chat Completion Agent/
│       (Agent Syntax Examples Goes here without numbering)
└── Flow Orchestrator/
```

Compact （每个文件夹更多文件）：

```
Concepts/
├── Kernel/
│   ├── Builder/
│   ├── Functions/
│   ├── Plugins/
│   ├── AI Services (Examples using Services thru Kernel Invocation)/
│   │   ├── Chat Completion/
│   │   ├── Text Generation/
│   │   └── Service Selector/
│   ├── Hooks/
│   ├── Filters/
│   └── Templates/
├── AI Services (Examples using Services directly with Single/Multiple + Streaming and Non-Streaming results)/
│   ├── Chat Completion/
│   ├── Text Generation/
│   ├── Text to Image/
│   ├── Image to Text/
│   ├── Text to Audio/
│   ├── Audio to Text/
│   └── Custom/
├── Memory Services/
│   ├── Search/
│   └── Text Embeddings/
├── Telemetry/
├── Logging/
├── Dependency Injection/
├── HttpClient/
│   ├── Resiliency/
│   └── Usage/
├── Planners/
│   └── Handlerbars/
├── Authentication/
│   └── Azure AD/
├── Function Calling/
│   ├── Auto Function Calling/
│   └── Manual Function Calling/
├── Filtering/
│   ├── Kernel Hooks/
│   └── Service Selector/
├── Templates/
├── Resilience/
├── RAG/
├── Agents/
└── Flow Orchestrator/
```

优点：

- 易于理解组件之间的关系
- 易于演变为更高级的概念
- 清晰了解为特定功能放置或添加更多样本的位置

缺点：

- 非常深的结构，可能会让开发人员难以驾驭
- 虽然结构清晰，但可能过于冗长

### KernelSyntaxExamples 分解选项 2 - 按组件划分的概念扁平化版本

方法与选项 1 类似，但采用扁平化结构，使用单级文件夹来避免深度嵌套和复杂性，同时保持组件化概念的轻松导航。

大（每个文件夹的文件较少）：

```
Concepts/
├── KernelBuilder
├── Kernel.Functions.Arguments
├── Kernel.Functions.MethodFunctions
├── Kernel.Functions.PromptFunctions
├── Kernel.Functions.Types
├── Kernel.Functions.Results.Serialization
├── Kernel.Functions.Results.Metadata
├── Kernel.Functions.Results.StronglyTyped
├── Kernel.Functions.InlineFunctions
├── Kernel.Plugins.DescribePlugins
├── Kernel.Plugins.OpenAIPlugins
├── Kernel.Plugins.OpenAPIPlugins.APIManifest
├── Kernel.Plugins.gRPCPlugins
├── Kernel.Plugins.MutablePlugins
├── Kernel.AIServices.ChatCompletion
├── Kernel.AIServices.TextGeneration
├── Kernel.AIServices.ServiceSelector
├── Kernel.Hooks
├── Kernel.Filters.FunctionFiltering
├── Kernel.Filters.TemplateRenderingFiltering
├── Kernel.Filters.FunctionCallFiltering
├── Kernel.Templates
├── AIServices.ExecutionSettings
├── AIServices.ChatCompletion.Gemini
├── AIServices.ChatCompletion.OpenAI
├── AIServices.ChatCompletion.AzureOpenAI
├── AIServices.ChatCompletion.HuggingFace
├── AIServices.TextGeneration.OpenAI
├── AIServices.TextGeneration.AzureOpenAI
├── AIServices.TextGeneration.HuggingFace
├── AIServices.TextToImage.OpenAI
├── AIServices.TextToImage.AzureOpenAI
├── AIServices.ImageToText.HuggingFace
├── AIServices.TextToAudio.OpenAI
├── AIServices.AudioToText.OpenAI
├── AIServices.Custom.DIY
├── AIServices.Custom.OpenAI.OpenAIFile
├── MemoryServices.Search.SemanticMemory
├── MemoryServices.Search.TextMemory
├── MemoryServices.Search.AzureAISearch
├── MemoryServices.TextEmbeddings.OpenAI
├── MemoryServices.TextEmbeddings.HuggingFace
├── Telemetry
├── Logging
├── DependencyInjection
├── HttpClient.Resiliency
├── HttpClient.Usage
├── Planners.Handlerbars
├── Authentication.AzureAD
├── FunctionCalling.AutoFunctionCalling
├── FunctionCalling.ManualFunctionCalling
├── Filtering.KernelHooks
├── Filtering.ServiceSelector
├── Templates
├── Resilience
├── RAG.Inline
├── RAG.FunctionCalling
├── Agents.Delegation
├── Agents.Charts
├── Agents.Collaboration
├── Agents.Authoring
├── Agents.Tools
├── Agents.ChatCompletionAgent
└── FlowOrchestrator
```

Compact （每个文件夹更多文件）：

```
Concepts/
├── KernelBuilder
├── Kernel.Functions
├── Kernel.Plugins
├── Kernel.AIServices
├── Kernel.Hooks
├── Kernel.Filters
├── Kernel.Templates
├── AIServices.ChatCompletion
├── AIServices.TextGeneration
├── AIServices.TextToImage
├── AIServices.ImageToText
├── AIServices.TextToAudio
├── AIServices.AudioToText
├── AIServices.Custom
├── MemoryServices.Search
├── MemoryServices.TextEmbeddings
├── Telemetry
├── Logging
├── DependencyInjection
├── HttpClient
├── Planners.Handlerbars
├── Authentication.AzureAD
├── FunctionCalling
├── Filtering
├── Templates
├── Resilience
├── RAG
├── Agents
└── FlowOrchestrator
```

优点：

- 易于理解组件之间的关系
- 易于演变为更高级的概念
- 清晰了解为特定功能放置或添加更多样本的位置
- 扁平化结构避免了深度嵌套，并使其更容易在 IDE 和 GitHub UI 上导航。

缺点：

- 虽然结构易于浏览，但可能仍然过于冗长

# KernelSyntaxExamples 分解选项 3 - 按特征分组划分的概念

此选项通过将 big 和 related 功能分组在一起来分解 Kernel Syntax Examples。

```
Concepts/
├── Functions/
├── Chat Completion/
├── Text Generation/
├── Text to Image/
├── Image to Text/
├── Text to Audio/
├── Audio to Text/
├── Telemetry
├── Logging
├── Dependency Injection
├── Plugins
├── Auto Function Calling
├── Filtering
├── Memory
├── Search
├── Agents
├── Templates
├── RAG
├── Prompts
└── LocalModels/
```

优点：

- 结构更小，更易于导航
- 清晰了解为特定功能放置或添加更多样本的位置

缺点：

- 不要清楚地说明组件是如何关联的
- 由于结构更高，每个文件可能需要更多示例
- 更难演变成更高级的概念
- 更多示例将共享同一文件夹，从而更难找到特定示例（KernelSyntaxExamples 文件夹的主要痛点）

# KernelSyntaxExamples 分解选项 4 - 按难度级别划分的概念

按难度级别（从基础到专家）分解示例。整体结构与选项 3 类似，但只有子项具有该复杂度级别时会有所不同。

```
Concepts/
├── 200-Basic
|  ├── Functions
|  ├── Chat Completion
|  ├── Text Generation
|  └── ..Basic only folders/files ..
├── 300-Intermediate
|  ├── Functions
|  ├── Chat Completion
|  └── ..Intermediate only folders/files ..
├── 400-Advanced
|  ├── Manual Function Calling
|  └── ..Advanced only folders/files ..
├── 500-Expert
|  ├── Functions
|  ├── Manual Function Calling
|  └── ..Expert only folders/files ..

```

优点：

- 初学者将面向正确的难度级别，示例将更按复杂程度进行组织

缺点：

- 我们没有关于什么是基础、中级、高级和专家级别以及难度的定义。
- 每个难度级别可能需要更多示例
- 不清楚组件之间的关系
- 创建示例时，将很难知道示例的难度级别是多少，以及如何传播可能适合多个不同级别的多个示例。

## 决策结果

选择的选项：

[x] 根结构决策： **选项 2** - 入门根分类

[x] KernelSyntaxExamples 分解决策： **选项 3** - 按特征分组的概念
