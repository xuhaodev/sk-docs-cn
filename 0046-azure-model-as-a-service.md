
# SK 中对 Azure 模型即服务的支持

## 上下文和问题陈述

客户要求在 SK 中实施模型即服务 （MaaS），MaaS（也称为[无服务器 API](https://learn.microsoft.com/en-us/azure/ai-studio/how-to/model-catalog-overview#model-deployment-managed-compute-and-serverless-api-pay-as-you-go)）在 [Azure AI Studio](https://learn.microsoft.com/en-us/azure/ai-studio/what-is-ai-studio) 中提供。这种消费模式采用即用即付模式，通常使用 Token 进行计费。客户端可以通过 [Azure AI Model Inference API](https://learn.microsoft.com/en-us/azure/ai-studio/reference/reference-model-inference-api?tabs=azure-studio) 或客户端 SDK 访问该服务。

目前，SK 中没有官方对 MaaS 的支持。此 ADR 的目的是检查服务的约束并探索潜在的解决方案，以便通过开发新的 AI 连接器来支持 SK 中的服务。

## 客户端 SDK

Azure 团队将提供一个新的客户端库，即 `Azure.AI.Inference` .Net 和 Python 库 `azure-ai-inference` ，用于与服务进行有效交互。虽然服务 API 与 OpenAI 兼容，但不允许使用 OpenAI 和 Azure OpenAI 客户端库与服务交互，因为它们在模型及其提供程序方面并不独立。这是因为 Azure AI Studio 具有除 OpenAI 模型之外的各种开源模型。

### 局限性

客户端 SDK 的初始版本将仅支持聊天完成和文本/图像嵌入生成，稍后将添加图像生成。

目前尚不清楚支持文本完成的计划，并且 SDK 不太可能包含对文本完成的支持。因此，新的 AI 连接器在初始版本中**将不支持**文本补全，直到我们获得更多客户信号或客户端 SDK 添加支持。

## AI 连接器

### 命名选项

- 天蓝色
- AzureAI
- AzureAIInference
- AzureAIModelInference

  决定： `AzureAIInference`

### 支持特定于模型的参数

模型可以拥有不属于默认 API 的补充参数。服务 API 和客户端 SDK 支持提供特定于模型的参数。用户可以通过专用参数以及其他设置（如 `temperature` 和 `top_p`等）提供特定于模型的设置。

在 SK 的上下文中，执行参数被归类到 `PromptExecutionSettings`，它由所有特定于连接器的设置类继承。新连接器的设置将包含一个 类型的 成员 `dictionary`，该成员将特定于模型的参数组合在一起。
