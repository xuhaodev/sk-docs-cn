
# 语义函数的多模型支持

## 上下文和问题陈述

开发人员需要能够同时使用多个模型，例如，将 GPT4 用于某些提示，将 GPT3.5 用于其他提示以降低成本。

## 使用案例

Semantic Kernel V1.0 的范围内提供了选择 AI 服务和模型请求设置的功能：

1. 按服务 ID 显示。
   - 服务 ID 唯一标识已注册的 AI 服务，通常在应用程序范围内定义。
1. 由开发人员定义的策略。
   -  _开发人员定义的策略_ 是一种代码优先的方法，其中开发人员提供逻辑。
1. 按模型 ID 显示。
   - 模型 ID 唯一标识大型语言模型。多个 AI 服务提供商可以支持同一个 LLM。
1. 按任意 AI 服务属性
   - 例如，AI 服务可以定义唯一标识 AI 提供商的提供商 ID，例如“Azure OpenAI”、“OpenAI”、“Hugging Face”

**此ADR侧重于上述列表中的第1项和第2项。为了实现 3 和 4，我们需要提供存储元数据的能力 `AIService` 。**

## 决策结果

支持此ADR中列出的用例1和2，并创建单独的ADR以增加对AI服务元数据的支持。

## 使用案例描述

**注意：所有代码都是伪代码，并不能准确反映最终实现的外观。**

### 按 Service ID 选择 Model Request Settings

_作为使用 Semantic Kernel 的开发人员，我可以为语义函数配置多个请求设置，并将每个设置与一个服务 ID 相关联，以便在使用不同的服务执行我的语义函数时使用正确的请求设置。_

语义函数模板配置允许配置多个模型请求设置。在这种情况下，开发人员根据用于执行语义函数的服务 ID 配置不同的设置。
在下面的示例中，语义函数是使用 “AzureText” 执行的， `max_tokens=60` 因为 “AzureText” 是为提示配置的模型列表中的第一个服务 ID。

```csharp
// Configure a Kernel with multiple LLM's
IKernel kernel = new KernelBuilder()
    .WithLoggerFactory(ConsoleLogger.LoggerFactory)
    .WithAzureTextCompletionService(deploymentName: aoai.DeploymentName,
        endpoint: aoai.Endpoint, serviceId: "AzureText", apiKey: aoai.ApiKey)
    .WithAzureChatCompletionService(deploymentName: aoai.ChatDeploymentName,
        endpoint: aoai.Endpoint, serviceId: "AzureChat", apiKey: aoai.ApiKey)
    .WithOpenAITextCompletionService(modelId: oai.ModelId,
        serviceId: "OpenAIText", apiKey: oai.ApiKey, setAsDefault: true)
    .WithOpenAIChatCompletionService(modelId: oai.ChatModelId,
        serviceId: "OpenAIChat", apiKey: oai.ApiKey, setAsDefault: true)
    .Build();

// Configure semantic function with multiple LLM request settings
var modelSettings = new List<AIRequestSettings>
{
    new OpenAIRequestSettings() { ServiceId = "AzureText", MaxTokens = 60 },
    new OpenAIRequestSettings() { ServiceId = "AzureChat", MaxTokens = 120 },
    new OpenAIRequestSettings() { ServiceId = "OpenAIText", MaxTokens = 180 },
    new OpenAIRequestSettings() { ServiceId = "OpenAIChat", MaxTokens = 240 }
};
var prompt = "Hello AI, what can you do for me?";
var promptTemplateConfig = new PromptTemplateConfig() { ModelSettings = modelSettings };
var func = kernel.CreateSemanticFunction(prompt, config: promptTemplateConfig, "HelloAI");

// Semantic function is executed with AzureText using max_tokens=60
result = await kernel.RunAsync(func);
```

其工作原理是使用 `IAIServiceSelector` 接口作为策略，在调用语义函数时向用户选择 AI 服务和请求设置。
接口定义如下：

```csharp
public interface IAIServiceSelector
{
    (T?, AIRequestSettings?) SelectAIService<T>(
                            string renderedPrompt,
                            IAIServiceProvider serviceProvider,
                            IReadOnlyList<AIRequestSettings>? modelSettings) where T : IAIService;
}
```

提供了一个默认 `OrderedIAIServiceSelector` 实现，该实现根据为语义函数定义的模型请求设置的顺序选择 AI 服务。

- 该实现会检查服务是否存在、相应的服务 ID，如果存在，并且将使用关联的模型请求设置。
- 如果未定义模型请求设置，则使用默认文本完成服务。
- 可以通过将服务 ID 保留为未定义或为空来指定一组默认请求设置，将使用第一个此类默认值。
- 如果没有 default（如果指定了），并且没有任何指定的服务可用，则作将失败。

### 按 Developer Defined Strategy 选择 AI 服务和模型请求设置

_作为使用 Semantic Kernel 的开发人员，我可以提供一个实现，用于选择用于执行我的函数的 AI 服务和请求设置，以便我可以动态控制用于执行我的语义函数的 AI 服务和设置。_

在这种情况下，开发人员根据服务 ID 配置不同的设置，并提供一个 AI 服务选择器，用于确定在执行语义函数时将使用哪个 AI 服务。
在下面的示例中，语义函数使用 AI 服务和 AI 请求设置返回的任何结果执行，`MyAIServiceSelector`例如，可以创建一个 AI 服务选择器，该选择器计算呈现的提示的令牌计数，并使用它来确定要使用的服务。

```csharp
// Configure a Kernel with multiple LLM's
IKernel kernel = new KernelBuilder()
    .WithLoggerFactory(ConsoleLogger.LoggerFactory)
    .WithAzureTextCompletionService(deploymentName: aoai.DeploymentName,
        endpoint: aoai.Endpoint, serviceId: "AzureText", apiKey: aoai.ApiKey)
    .WithAzureChatCompletionService(deploymentName: aoai.ChatDeploymentName,
        endpoint: aoai.Endpoint, serviceId: "AzureChat", apiKey: aoai.ApiKey)
    .WithOpenAITextCompletionService(modelId: oai.ModelId,
        serviceId: "OpenAIText", apiKey: oai.ApiKey, setAsDefault: true)
    .WithOpenAIChatCompletionService(modelId: oai.ChatModelId,
        serviceId: "OpenAIChat", apiKey: oai.ApiKey, setAsDefault: true)
    .WithAIServiceSelector(new MyAIServiceSelector())
    .Build();

// Configure semantic function with multiple LLM request settings
var modelSettings = new List<AIRequestSettings>
{
    new OpenAIRequestSettings() { ServiceId = "AzureText", MaxTokens = 60 },
    new OpenAIRequestSettings() { ServiceId = "AzureChat", MaxTokens = 120 },
    new OpenAIRequestSettings() { ServiceId = "OpenAIText", MaxTokens = 180 },
    new OpenAIRequestSettings() { ServiceId = "OpenAIChat", MaxTokens = 240 }
};
var prompt = "Hello AI, what can you do for me?";
var promptTemplateConfig = new PromptTemplateConfig() { ModelSettings = modelSettings };
var func = kernel.CreateSemanticFunction(prompt, config: promptTemplateConfig, "HelloAI");

// Semantic function is executed with AI Service and AI request Settings dynamically determined
result = await kernel.RunAsync(func, funcVariables);
```

## 更多信息

### 按 Service ID 选择 AI 服务

支持以下使用案例。开发人员可以创建具有多个命名 AI 服务的“内核”实例。调用语义函数时，可以指定服务 ID（以及要使用的可选请求设置）。命名的 AI 服务将用于执行提示。

```csharp
var aoai = TestConfiguration.AzureOpenAI;
var oai = TestConfiguration.OpenAI;

// Configure a Kernel with multiple LLM's
IKernel kernel = Kernel.Builder
    .WithLoggerFactory(ConsoleLogger.LoggerFactory)
    .WithAzureTextCompletionService(deploymentName: aoai.DeploymentName,
        endpoint: aoai.Endpoint, serviceId: "AzureText", apiKey: aoai.ApiKey)
    .WithAzureChatCompletionService(deploymentName: aoai.ChatDeploymentName,
        endpoint: aoai.Endpoint, serviceId: "AzureChat", apiKey: aoai.ApiKey)
    .WithOpenAITextCompletionService(modelId: oai.ModelId,
        serviceId: "OpenAIText", apiKey: oai.ApiKey)
    .WithOpenAIChatCompletionService(modelId: oai.ChatModelId,
        serviceId: "OpenAIChat", apiKey: oai.ApiKey)
    .Build();

// Invoke the semantic function and service and request settings to use
result = await kernel.InvokeSemanticFunctionAsync(prompt,
    requestSettings: new OpenAIRequestSettings()
        { ServiceId = "AzureText", MaxTokens = 60 });

result = await kernel.InvokeSemanticFunctionAsync(prompt,
    requestSettings: new OpenAIRequestSettings()
        { ServiceId = "AzureChat", MaxTokens = 120 });

result = await kernel.InvokeSemanticFunctionAsync(prompt,
    requestSettings: new OpenAIRequestSettings()
        { ServiceId = "OpenAIText", MaxTokens = 180 });

result = await kernel.InvokeSemanticFunctionAsync(prompt,
    requestSettings: new OpenAIRequestSettings()
        { ServiceId = "OpenAIChat", MaxTokens = 240 });
```
