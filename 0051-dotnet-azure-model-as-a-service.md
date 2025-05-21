
# 适用于 .Net Azure 模型即服务 （Azure AI Studio） 的支持连接器

## 上下文和问题陈述

客户要求使用和支持 Azure AI Studio 中部署的本机模型 [- 无服务器 API](https://learn.microsoft.com/en-us/azure/ai-studio/how-to/model-catalog-overview#model-deployment-managed-compute-and-serverless-api-pay-as-you-go)，这种使用模式以即用即付为基础，通常使用令牌进行计费。客户端可以通过 [Azure AI Model Inference API](https://learn.microsoft.com/en-us/azure/ai-studio/reference/reference-model-inference-api?tabs=azure-studio) 或客户端 SDK 访问该服务。

目前，没有对 [Azure AI Studio](https://learn.microsoft.com/en-us/azure/ai-studio/what-is-ai-studio) 的官方支持。此 ADR 的目的是检查服务的约束并探索潜在的解决方案，以便通过开发新的 AI 连接器来支持服务。

## 适用于 .NET 的 Azure 推理客户端库

Azure 团队有一个新的客户端库，即  .Net 中的 [Azure.AI.Inference](https://github.com/Azure/azure-sdk-for-net/blob/Azure.AI.Inference_1.0.0-beta.1/sdk/ai/Azure.AI.Inference/README.md)，用于与服务进行有效交互。虽然服务 API 与 OpenAI 兼容，但不允许使用 OpenAI 和 Azure OpenAI 客户端库与服务交互，因为它们在模型及其提供程序方面并不独立。这是因为 Azure AI Studio 具有除 OpenAI 模型之外的各种开源模型。

### 局限性

目前已知客户端 SDK 的第一个版本将仅支持： `Chat Completion` 和 `Text Embedding Generation` 和 `Image Embedding Generation` with `TextToImage Generation` planned。

目前没有支持模式的计划 `Text Generation` 。

## AI 连接器

### 命名空间选项

- `Microsoft.SemanticKernel.Connectors.AzureAI`
- `Microsoft.SemanticKernel.Connectors.AzureAIInference`
- `Microsoft.SemanticKernel.Connectors.AzureAIModelInference`

决定： `Microsoft.SemanticKernel.Connectors.AzureAIInference`

### 支持特定于模型的参数

模型可以拥有不属于默认 API 的补充参数。服务 API 和客户端 SDK 支持提供特定于模型的参数。用户可以通过专用参数以及其他设置（如 `temperature` 和 `top_p`等）提供特定于模型的设置。

Azure AI Inference specialized `PromptExecutionSettings`将支持这些可自定义的参数。

### 功能分支

Azure AI Inference 连接器的开发将在名为 的功能分支中完成 `feature-connectors-azureaiinference`。
