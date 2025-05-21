# 添加 AI 服务元数据

## 上下文和问题陈述

开发人员需要能够了解有关 `IAIService` 将用于执行语义函数或计划的更多信息。
他们为什么需要此信息的一些示例：

1. 作为 SK 开发人员，我想编写一个 `IAIServiceSelector` 文档，允许我根据配置的模型 ID 选择要使用的 OpenAI 服务，以便我可以根据我正在执行的提示选择要使用的最佳（可能是最便宜的）模型。
2. 作为 SK 开发人员，我想编写一个调用前钩子，它将在将提示发送到 LLM 之前计算提示的令牌大小，以便确定 `IAIService` 最佳使用。我用来计算 prompt 的 token 大小的库需要 model id。

的当前实现 `IAIService` 为空。

```csharp
public interface IAIService
{
}
```

我们可以使用 `IAIService` `T IKernel.GetService<T>(string? name = null) where T : IAIService;` i.e.，即按服务类型和名称（又名服务 ID）检索实例。
的具体实例 `IAIService` 可以具有不同的属性，具体取决于服务提供商，例如，Azure OpenAI 具有部署名称，OpenAI 服务具有模型 ID。

请考虑以下代码片段：

```csharp
IKernel kernel = new KernelBuilder()
    .WithLoggerFactory(ConsoleLogger.LoggerFactory)
    .WithAzureChatCompletionService(
        deploymentName: chatDeploymentName,
        endpoint: endpoint,
        serviceId: "AzureOpenAIChat",
        apiKey: apiKey)
    .WithOpenAIChatCompletionService(
        modelId: openAIModelId,
        serviceId: "OpenAIChat",
        apiKey: openAIApiKey)
    .Build();

var service = kernel.GetService<IChatCompletion>("OpenAIChat");
```

对于 Azure OpenAI，我们使用部署名称创建服务。这是部署 AI 模型的人员指定的任意名称，例如，它可以是 `eastus-gpt-4` 或 `foo-bar`。
对于 OpenAI，我们使用模型 ID 创建服务。这必须与已部署的 OpenAI 模型之一匹配。

从使用 OpenAI 的提示创建者的角度来看，他们通常会根据模型调整提示。因此，当执行 prompt 时，我们需要能够使用模型 ID 来检索服务。如上面的代码片段所示， `IKernel` only 支持 `IAService` 按 id 检索实例。此外，它是一个 `IChatCompletion` 通用接口，因此它不包含任何提供有关特定连接器实例信息的属性。

## 决策驱动因素

* 我们需要一种机制来存储实例的通用元数据 `IAIService` 。
  * 具体实例将负责 `IAIService` 存储相关的元数据，例如 OpenAI 和 HuggingFace AI 服务的模型 ID。
* 我们需要能够迭代可用的 `IAIService` 实例。

## 考虑的选项

* 选项 #1
  * 扩展 `IAIService` 以包括以下属性：
    * `string? ModelId { get; }` ，它返回模型 ID。每个  implementation 都有责任`IAIService`使用适当的值填充 this。
    * `IReadOnlyDictionary<string, object> Attributes { get; }` ，它将属性作为 readonly 字典返回。每个实施都有责任`IAIService`使用适当的元数据填充此 URL。
  * 扩展 `INamedServiceProvider` 以包含此方法 `ICollection<T> GetServices<T>() where T : TService;`
  * 扩展 `OpenAIKernelBuilderExtensions` ，以便 `WithAzureXXX` 方法可以包含属性（ `modelId` 如果可以定位特定模型）。
* 选项 #2
  * 扩展 `IAIService` 以包括以下方法：
    * `T? GetAttributes<T>() where T : AIServiceAttributes;` ，它返回 `AIServiceAttributes`.每个 implementation 都有责任 `IAIService` 定义自己的 service attributes 类，并使用适当的值填充它。
  * 扩展 `INamedServiceProvider` 以包含此方法 `ICollection<T> GetServices<T>() where T : TService;`
  * 扩展 `OpenAIKernelBuilderExtensions` ，以便 `WithAzureXXX` 方法可以包含属性（ `modelId` 如果可以定位特定模型）。
* 选项 #3
* 选项 #2
  * 扩展 `IAIService` 以包括以下属性：
    * `public IReadOnlyDictionary<string, object> Attributes => this.InternalAttributes;` ，它返回一个只读字典。每个 implementation 都有责任 `IAIService` 定义自己的 service attributes 类，并使用适当的值填充它。
    * `ModelId`
    * `Endpoint`
    * `ApiVersion`
  * 扩展 `INamedServiceProvider` 以包含此方法 `ICollection<T> GetServices<T>() where T : TService;`
  * 扩展 `OpenAIKernelBuilderExtensions` ，以便 `WithAzureXXX` 方法可以包含属性（ `modelId` 如果可以定位特定模型）。

这些选项的使用方式如下：

作为 SK 开发人员，我想编写一个自定义 `IAIServiceSelector` 项，该自定义项将根据模型 ID 选择 AI 服务，因为我想限制使用的 LLM。
在下面的示例中，服务选择器实现查找第一个 GPT3 模型服务。

### 选项 1

``` csharp
public class Gpt3xAIServiceSelector : IAIServiceSelector
{
    public (T?, AIRequestSettings?) SelectAIService<T>(string renderedPrompt, IAIServiceProvider serviceProvider, IReadOnlyList<AIRequestSettings>? modelSettings) where T : IAIService
    {
        var services = serviceProvider.GetServices<T>();
        foreach (var service in services)
        {
            if (!string.IsNullOrEmpty(service.ModelId) && service.ModelId.StartsWith("gpt-3", StringComparison.OrdinalIgnoreCase))
            {
                Console.WriteLine($"Selected model: {service.ModelId}");
                return (service, new OpenAIRequestSettings());
            }
        }

        throw new SKException("Unable to find AI service for GPT 3.x.");
    }
}
```

## 选项 2

``` csharp
public class Gpt3xAIServiceSelector : IAIServiceSelector
{
    public (T?, AIRequestSettings?) SelectAIService<T>(string renderedPrompt, IAIServiceProvider serviceProvider, IReadOnlyList<AIRequestSettings>? modelSettings) where T : IAIService
    {
        var services = serviceProvider.GetServices<T>();
        foreach (var service in services)
        {
            var serviceModelId = service.GetAttributes<AIServiceAttributes>()?.ModelId;
            if (!string.IsNullOrEmpty(serviceModelId) && serviceModelId.StartsWith("gpt-3", StringComparison.OrdinalIgnoreCase))
            {
                Console.WriteLine($"Selected model: {serviceModelId}");
                return (service, new OpenAIRequestSettings());
            }
        }

        throw new SKException("Unable to find AI service for GPT 3.x.");
    }
}
```

## 选项 3

```csharp
public (T?, AIRequestSettings?) SelectAIService<T>(string renderedPrompt, IAIServiceProvider serviceProvider, IReadOnlyList<AIRequestSettings>? modelSettings) where T : IAIService
{
    var services = serviceProvider.GetServices<T>();
    foreach (var service in services)
    {
        var serviceModelId = service.GetModelId();
        var serviceOrganization = service.GetAttribute(OpenAIServiceAttributes.OrganizationKey);
        var serviceDeploymentName = service.GetAttribute(AzureOpenAIServiceAttributes.DeploymentNameKey);
        if (!string.IsNullOrEmpty(serviceModelId) && serviceModelId.StartsWith("gpt-3", StringComparison.OrdinalIgnoreCase))
        {
            Console.WriteLine($"Selected model: {serviceModelId}");
            return (service, new OpenAIRequestSettings());
        }
    }

    throw new SKException("Unable to find AI service for GPT 3.x.");
}
```

## 决策结果

选择的选项：选项 1，因为它是一个简单的实现，并且允许对所有可能的属性进行轻松迭代。
