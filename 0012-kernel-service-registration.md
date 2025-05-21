
# 内核服务注册

## 上下文和问题陈述

插件可能具有依赖项以支持复杂场景。例如，有 `TextMemoryPlugin`，它支持 、 等函数 `retrieve` `recall` `save` `remove`。Constructor 的实现方式如下：

```csharp
public TextMemoryPlugin(ISemanticTextMemory memory)
{
    this._memory = memory;
}
```

`TextMemoryPlugin` 取决于 `ISemanticTextMemory` 接口。同样，其他插件可能有多个依赖项，应该有一种方法可以手动或自动解决所需的依赖项。

目前， `ISemanticTextMemory` 是 interface 的一个属性 `IKernel` ，它允许 `ISemanticTextMemory` `TextMemoryPlugin` 在插件初始化时注入：

```csharp
kernel.ImportFunctions(new TextMemoryPlugin(kernel.Memory));
```

应该有一种方法可以不仅支持与内存相关的接口，而且支持任何类型的服务，这些服务可以在 Plugin - `ISemanticTextMemory`， `IPromptTemplateEngine`或任何其他 `IDelegatingHandlerFactory` 服务中使用。

## 考虑的选项

### 解决方案 #1.1（默认可用）

用户负责所有插件初始化和手动解决依赖项 **** 。

```csharp
var memoryStore = new VolatileMemoryStore();
var embeddingGeneration = new OpenAITextEmbeddingGeneration(modelId, apiKey);
var semanticTextMemory = new SemanticTextMemory(memoryStore, embeddingGeneration);

var memoryPlugin = new TextMemoryPlugin(semanticTextMemory);

var kernel = Kernel.Builder.Build();

kernel.ImportFunctions(memoryPlugin);
```

注意：这是手动解决服务依赖关系的本机 .NET 方法，默认情况下，此方法应始终可用。任何其他有助于提高依赖项解析的解决方案都可以在此方法之上添加。

### 解决方案 #1.2 （默认可用）

用户负责所有插件初始化和依赖项解析，并使用 **依赖项注入** 方法。

```csharp
var serviceCollection = new ServiceCollection();

serviceCollection.AddTransient<IMemoryStore, VolatileMemoryStore>();
serviceCollection.AddTransient<ITextEmbeddingGeneration>(
    (serviceProvider) => new OpenAITextEmbeddingGeneration(modelId, apiKey));

serviceCollection.AddTransient<ISemanticTextMemory, SemanticTextMemory>();

var services = serviceCollection.BuildServiceProvider();

// In theory, TextMemoryPlugin can be also registered in DI container.
var memoryPlugin = new TextMemoryPlugin(services.GetService<ISemanticTextMemory>());

var kernel = Kernel.Builder.Build();

kernel.ImportFunctions(memoryPlugin);
```

注意：与解决方案 #1.1 类似，这种方式应该是开箱即用的。用户总是可以处理他们这边的所有依赖项，只需向 Kernel 提供所需的插件即可。

### 解决方案 #2.1

作为解决方案 #1.1 和解决方案 #1.2 的补充，在内核级别自定义服务集合和服务提供商，以简化依赖项解析过程。

Interface `IKernel` 将拥有自己的服务提供商 `KernelServiceProvider` ，其功能最少，无法获得所需的服务。

```csharp
public interface IKernelServiceProvider
{
    T? GetService<T>(string? name = null);
}

public interface IKernel
{
    IKernelServiceProvider Services { get; }
}
```

```csharp
var kernel = Kernel.Builder
    .WithLoggerFactory(ConsoleLogger.LoggerFactory)
    .WithOpenAITextEmbeddingGenerationService(modelId, apiKey)
    .WithService<IMemoryStore, VolatileMemoryStore>(),
    .WithService<ISemanticTextMemory, SemanticTextMemory>()
    .Build();

var semanticTextMemory = kernel.Services.GetService<ISemanticTextMemory>();
var memoryPlugin = new TextMemoryPlugin(semanticTextMemory);

kernel.ImportFunctions(memoryPlugin);
```

优点：

- 不依赖于特定的 DI 容器库。
- 轻量级实现。
- 可以只注册那些可以件使用的服务（与主机应用程序隔离）。
- 可以按名称多次注册同一接口****。

缺点：

- 自定义 DI 容器的实现和维护，而不是使用现有的库。
- 要导入 Plugin，仍然需要手动初始化以注入特定的服务。

### 解决方案 #2.2

此解决方案是对解决方案 #2.1 的最后一个缺点的改进，用于处理应手动初始化插件实例的情况。这将需要添加如何将 Plugin 导入 Kernel 的新方法 - 不是使用对象 **实例**，而是使用对象 **类型**。在这种情况下，Kernel 将负责 `TextMemoryPlugin` 初始化和注入自定义服务集合中所有必需的依赖项。

```csharp
// Instead of this
var semanticTextMemory = kernel.Services.GetService<ISemanticTextMemory>();
var memoryPlugin = new TextMemoryPlugin(semanticTextMemory);

kernel.ImportFunctions(memoryPlugin);

// Use this
kernel.ImportFunctions<TextMemoryPlugin>();
```

### 解决方案 #3

不要在 Kernel 中自定义服务集合和服务提供商，而是使用已经存在的 DI 库 - `Microsoft.Extensions.DependencyInjection`。

```csharp
var serviceCollection = new ServiceCollection();

serviceCollection.AddTransient<IMemoryStore, VolatileMemoryStore>();
serviceCollection.AddTransient<ITextEmbeddingGeneration>(
    (serviceProvider) => new OpenAITextEmbeddingGeneration(modelId, apiKey));

serviceCollection.AddTransient<ISemanticTextMemory, SemanticTextMemory>();

var services = serviceCollection.BuildServiceProvider();

var kernel = Kernel.Builder
    .WithLoggerFactory(ConsoleLogger.LoggerFactory)
    .WithOpenAITextEmbeddingGenerationService(modelId, apiKey)
    .WithServices(services) // Pass all registered services from host application to Kernel
    .Build();

// Plugin Import - option #1
var semanticTextMemory = kernel.Services.GetService<ISemanticTextMemory>();
var memoryPlugin = new TextMemoryPlugin(semanticTextMemory);

kernel.ImportFunctions(memoryPlugin);

// Plugin Import - option #2
kernel.ImportFunctions<TextMemoryPlugin>();
```

优点：

- 依赖项解析不需要实现 - 只需使用现有的 .NET 库。
- 可以在现有应用程序中一次性注入所有已注册的服务，并将它们用作插件依赖项。

缺点：

- 语义内核软件包的其他依赖项 - `Microsoft.Extensions.DependencyInjection`。
- 无法包含特定的服务列表（缺乏与主机应用程序的隔离）。
- 版本 `Microsoft.Extensions.DependencyInjection` 不匹配和运行时错误的可能性（例如，用户在 `Microsoft.Extensions.DependencyInjection` `--version 2.0`语义内核使用 `--version 6.0`）

## 决策结果

目前，仅支持 Solution #1.1 和 Solution #1.2，以保持 Kernel 作为单一责任单位。在将 Plugin 实例传递给 Kernel 之前，应该解决 Plugin 依赖项。
