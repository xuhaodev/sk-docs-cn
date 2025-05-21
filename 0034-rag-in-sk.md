
# 语义内核中的检索增强生成 （RAG）

## 上下文和问题陈述

### 一般信息

在 Semantic Kernel （SK） 中使用 RAG 模式有几种方法。SK 中已经存在一些方法，将来可能会添加其中一些方法以获得不同的开发体验。

本 ADR 的目的是描述 SK 中具有内存相关功能的问题位置，演示如何在当前版本的 SK 中实现 RAG，并为 RAG 提出公共 API 的新设计。

本 ADR 中提供的考虑选项不会相互矛盾，并且可以同时得到支持。支持哪个选项的决定将基于不同的因素，包括优先级、特定功能的实际要求和一般反馈。

### Vector DB 集成 - 连接器

目前实现了 12 [ 个 vector DB 连接器](https://github.com/microsoft/semantic-kernel/tree/main/dotnet/src/Connectors)（也称为 `memory connectors`），开发人员可能不清楚如何使用它们。可以直接调用连接器方法，也可以通过 `TextMemoryPlugin` [Plugins.Memory](https://www.nuget.org/packages/Microsoft.SemanticKernel.Plugins.Memory) NuGet 包（提示示例：`{{recall 'company budget by year'}} What is my budget for 2024?`）使用它

每个连接器都有独特的实现，其中一些连接器依赖于来自特定矢量数据库提供商的现有 .NET SDK，而另一些连接器则实现了使用矢量数据库提供商的 REST API 的功能。

理想情况下，每个连接器都应该始终是最新的并支持新功能。对于某些连接器，维护成本很低，因为新功能中没有包含重大更改，或者 vector DB 提供相对容易重用的 .NET SDK。对于其他连接器，维护成本较高，由于其中一些连接器仍处于 `alpha` 开发 `beta` 阶段，可能会包含重大更改或未提供 .NET SDK，这使得更新更加困难。

### IMemoryStore 接口

每个内存连接器都使用 `IMemoryStore`等 `CreateCollectionAsync` 方法实现接口 `GetNearestMatchesAsync` ，因此它可以用作 `TextMemoryPlugin`的一部分。

通过实现相同的接口，每个集成都是一致的，这使得在运行时使用不同的矢量数据库成为可能。同时，这也是缺点，因为每个向量数据库的工作方式可能不同，并且更难将所有集成适应已经存在的抽象。例如， `CreateCollectionAsync` `IMemoryStore` 当应用程序尝试将新记录添加到向量 DB 到集合时，会使用方法 from，而该集合不存在，因此在 insert作之前，它会创建新的集合。对于 [Pinecone](https://www.pinecone.io/) 矢量 DB，不支持此方案，因为 Pinecone 索引创建是一个异步过程 - API 服务将返回 201 Created HTTP 响应，并在响应正文中使用以下属性（索引尚未准备好使用）：

```json
{
    // Other properties...
    "status": {
        "ready": false,
        "state": "Initializing"
    }
}
```

在这种情况下，不可能立即将记录插入数据库，因此应实施 HTTP 轮询或类似机制来涵盖此方案。

### MemoryRecord 作为存储架构

`IMemoryStore` interface 使用 `MemoryRecord` 类作为矢量 DB 中的存储架构。这意味着 `MemoryRecord` 属性应与所有可能的连接器对齐。一旦开发人员在其数据库中使用此架构，对架构的任何更改都可能会中断应用程序，这不是一种灵活的方法。

`MemoryRecord` contains 属性 `ReadOnlyMemory<float> Embedding` 。 `MemoryRecordMetadata Metadata` `MemoryRecordMetadata` 包含如下属性：

- `string Id` - 唯一标识符。
- `string Text` - 与数据相关的文本。
- `string Description` - 描述内容的可选标题。
- `string AdditionalMetadata` - 字段，用于将自定义元数据与记录一起保存。

由于 `MemoryRecord` 和 `MemoryRecordMetadata` 不是密封类，因此应该可以根据需要扩展它们并添加更多属性。尽管如此，当前方法仍然迫使开发人员在其矢量数据库中拥有特定的基本架构，理想情况下应该避免这种情况。开发人员应该能够使用他们选择的任何架构，这些架构将涵盖他们的业务场景（类似于实体框架中的 Code First 方法）。

### TextMemory插件

TextMemoryPlugin 包含 4 个 Kernel 函数：

- `Retrieve` - 按键返回 DB 中的具体记录。
- `Recall` - 执行向量搜索并根据相关性返回多条记录。
- `Save` - 将记录保存在 Vector DB 中。
- `Remove` - 从矢量 DB 中删除记录。

所有函数都可以直接从 prompt 调用。此外，一旦这些函数在 Kernel 中注册并启用了函数调用，LLM 就可以决定调用特定函数来实现提供的目标。

`Retrieve` 和 `Recall` functions 可用于为 LLM 提供一些上下文并根据数据提出问题，但 functions `Save` 并 `Remove` 对向量 DB 中的数据执行一些作，这可能是不可预测的，有时甚至是危险的（LLM 决定删除一些记录时，不应该出现任何情况，这些记录不应该被删除）。

## 决策驱动因素

1. 对 Semantic Kernel 中数据的所有作都应该是安全的。
2. 应该有一个明确的方法如何在 Semantic Kernel 中使用 RAG 模式。
3. 抽象不应阻止开发人员使用他们选择的矢量数据库，其功能无法通过提供的接口或数据类型实现。

## 超出范围

一些与 RAG 相关的框架包含支持 RAG 模式完整周期的功能：

1. **** 从特定资源（例如 Wikipedia、OneDrive、本地 PDF 文件）读取数据。
2. **** 使用特定逻辑将数据拆分为多个块。
3. **** 从数据生成嵌入。
4. **将** 数据存储到首选向量 DB。
5. **** 根据用户查询在首选向量数据库中搜索数据。
6. **** 根据提供的数据向 LLM 提问。

目前，Semantic Kernel 有以下实验性功能：

- `TextChunker` 类将数据 **拆分** 为块。
- `ITextEmbeddingGenerationService` 抽象和实现来 **使用** OpenAI 和 HuggingFace 模型生成嵌入。
- 用于存储和****搜索**数据的**内存连接器。

由于这些功能是实验性的，如果 RAG 模式的决策不需要在 Semantic Kernel 中提供和维护列出的抽象、类和连接器，那么它们将来可能会被弃用。

目前，数据**读取**工具不在范围之内。

## 考虑的选项

### 选项 1 [支持] - 提示串联

此选项允许使用数据手动构建提示，以便 LLM 可以根据提供的上下文响应查询。可以通过使用手动字符串连接或使用提示模板和 Kernel 参数来实现。开发人员负责与他们选择的矢量数据库集成、数据搜索和提示构建以将其发送到 LLM。

这种方法在 Semantic Kernel 中不包含任何开箱即用的内存连接器，但同时它为开发人员提供了以最适合他们的方式处理数据的机会。

字符串连接：

```csharp
var kernel = Kernel.CreateBuilder()
    .AddOpenAIChatCompletion("model-id", "api-key")
    .Build();

var builder = new StringBuilder();

// User is responsible for searching the data in a way of their choice, this is an example how it could look like.
var data = await this._vectorDB.SearchAsync("Company budget by year");

builder.AppendLine(data);
builder.AppendLine("What is my budget for 2024?");

var result = await kernel.InvokePromptAsync(builder.ToString());
```

提示模板和 Kernel 参数：

```csharp
var kernel = Kernel.CreateBuilder()
    .AddOpenAIChatCompletion("model-id", "api-key")
    .Build();

// User is responsible for searching the data in a way of their choice, this is an example how it could look like.
var data = await this._vectorDB.SearchAsync("Company budget by year");

var arguments = new KernelArguments { ["budgetByYear"] = data };

var result = await kernel.InvokePromptAsync("{{budgetByYear}} What is my budget for 2024?", arguments);
```

### 选项 2 [支持] - 内存作为插件

此方法类似于选项 1，但数据搜索步骤是提示呈现过程的一部分。以下列表包含可用于数据搜索的插件：

- [ChatGPT Retrieval Plugin](https://github.com/openai/chatgpt-retrieval-plugin) - 此插件应作为单独的服务托管。它与各种[矢量数据库集成](https://github.com/openai/chatgpt-retrieval-plugin?tab=readme-ov-file#choosing-a-vector-database)。
- [SemanticKernel.Plugins.Memory.TextMemoryPlugin](https://www.nuget.org/packages/Microsoft.SemanticKernel.Plugins.Memory) - 语义内核解决方案，支持各种向量数据库。
- 自定义用户插件。

ChatGPT 检索插件：

```csharp
var kernel = Kernel.CreateBuilder()
    .AddOpenAIChatCompletion("model-id", "api-key")
    .Build();

// Import ChatGPT Retrieval Plugin using OpenAPI specification
// https://github.com/openai/chatgpt-retrieval-plugin/blob/main/.well-known/openapi.yaml
await kernel.ImportPluginFromOpenApiAsync("ChatGPTRetrievalPlugin", openApi!, executionParameters: new(authCallback: async (request, cancellationToken) =>
{
    request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", "chat-gpt-retrieval-plugin-token");
}));

const string Query = "What is my budget for 2024?";
const string Prompt = "{{ChatGPTRetrievalPlugin.query_query_post queries=$queries}} {{$query}}";

var arguments = new KernelArguments
{
    ["query"] = Query,
    ["queries"] = JsonSerializer.Serialize(new List<object> { new { query = Query, top_k = 1 } }),
};

var result = await kernel.InvokePromptAsync(Prompt, arguments);
```

TextMemory插件：

```csharp
var kernel = Kernel.CreateBuilder()
    .AddOpenAIChatCompletion("model-id", "api-key")
    .Build();

// NOTE: If the decision will be to continue support memory-related public API, then it should be revisited.
// It should be up-to-date with new Semantic Kernel patterns.
// Example: instead of `WithChromaMemoryStore`, it should be `AddChromaMemoryStore`.
var memory = new MemoryBuilder()
    .WithChromaMemoryStore("https://chroma-endpoint")
    .WithOpenAITextEmbeddingGeneration("text-embedding-ada-002", "api-key")
    .Build();

kernel.ImportPluginFromObject(new TextMemoryPlugin(memory));

var result = await kernel.InvokePromptAsync("{{recall 'Company budget by year'}} What is my budget for 2024?");
```

自定义用户插件：

```csharp
public class MyDataPlugin
{
    [KernelFunction("search")]
    public async Task<string> SearchAsync(string query)
    {
        // Make a call to vector DB and return results.
        // Here developer can use already existing .NET SDK from specific vector DB provider.
        // It's also possible to re-use Semantic Kernel memory connector directly here: 
        // new ChromaMemoryStore(...).GetNearestMatchAsync(...)
    }
}

var kernel = Kernel.CreateBuilder()
    .AddOpenAIChatCompletion("model-id", "api-key")
    .Build();

kernel.ImportPluginFromType<MyDataPlugin>();

var result = await kernel.InvokePromptAsync("{{search 'Company budget by year'}} What is my budget for 2024?");
```

自定义用户插件之所以比 IS 更灵活 `TextMemoryPlugin` ，是因为 `TextMemoryPlugin` 需要所有矢量 DB 实现 `IMemoryStore` 上述缺点的接口，而自定义用户插件可以通过开发人员选择的方式实现。对 DB 记录架构或实现特定接口的要求不会有任何限制。

### 选项 3 [部分支持] - 使用提示筛选器进行提示串联

此选项类似于选项 1，但提示串联将在 Prompt Filter 级别进行：

提示过滤器：

```csharp
public sealed class MyPromptFilter : IPromptFilter
{
    public void OnPromptRendering(PromptRenderingContext context)
    {
        // Handling of prompt rendering event...
    }

    public void OnPromptRendered(PromptRenderedContext context)
    {
        var data = "some data";
        var builder = new StringBuilder();

        builder.AppendLine(data);
        builder.AppendLine(context.RenderedPrompt);

        // Override rendered prompt before sending it to AI and include data
        context.RenderedPrompt = builder.ToString();
    }
}
```

用法：

```csharp
var kernel = Kernel.CreateBuilder()
    .AddOpenAIChatCompletion("model-id", "api-key")
    .Build();

kernel.PromptFilters.Add(new MyPromptFilter());

var result = await kernel.InvokePromptAsync("What is my budget for 2024?");
```

从使用角度来看，prompt 将仅包含用户查询，不包含其他数据。数据将在后台添加到提示中。

部分支持**此方法的原因是 ** ，对矢量 DB 的调用很可能是异步的，但当前的内核筛选器不支持异步方案。因此，为了支持异步调用，应该向 Kernel： 和 . `IAsyncFunctionFilter` `IAsyncPromptFilter`它们将与 current 相同 `IFunctionFilter` ， `IPromptFilter` 但使用 async 方法。

### 选项 4 [建议] - 内存作为 PromptExecutionSettings 的一部分

该提案是在上述现有方法之上，在 SK 中实现 RAG 模式的另一种可能方法。与 `TextMemoryPlugin`类似，这种方法需要抽象层，并且每个矢量数据库集成都需要实现特定的接口（可以是现有的 `IMemoryStore` 或全新的接口）才能与 SK 兼容。如 _Context and Problem Statement_ 部分所述，抽象层有其优点和缺点。

用户代码将如下所示：

```csharp
var kernel = Kernel.CreateBuilder()
    .AddOpenAIChatCompletion("model-id", "api-key")
    .Build();

var executionSettings = new OpenAIPromptExecutionSettings
{
    Temperature = 0.8,
    MemoryConfig = new()
    {
        // This service could be also registered using DI with specific lifetime
        Memory = new ChromaMemoryStore("https://chroma-endpoint"),
        MinRelevanceScore = 0.8,
        Limit = 3
    }
};

var function = KernelFunctionFactory.CreateFromPrompt("What is my budget for 2024?", executionSettings);

var result = await kernel.InvokePromptAsync("What is my budget for 2024?");
```

数据搜索和提示连接将在课堂的幕后进行 `KernelFunctionFromPrompt` 。

## 决策结果

临时决定提供更多示例，如何将 Semantic Kernel 中的内存作为插件使用。

最终决定将根据下一个与内存相关的要求做好准备。
