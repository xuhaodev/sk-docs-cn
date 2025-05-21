
# 更新的向量搜索设计

## 要求

1. 支持按 Vector 搜索。
1. 支持具有不同类型元素的 Vector，并允许扩展性以支持将来的新型 Vector（例如稀疏）。
1. 支持按文本搜索。这是支持服务执行嵌入生成的方案或在管道中完成嵌入生成的方案所必需的。
1. 允许按其他模式（例如 image）进行搜索的可扩展性。
1. 允许扩展性执行混合搜索。
1. 允许基本筛选，并有可能在将来扩展。
1. 提供扩展方法，简化搜索体验。

## 接口

vector search interface 接受一个 `VectorSearchQuery` 对象。此对象是具有各种子类的抽象基类
表示不同类型的搜索。

```csharp
interface IVectorSearch<TRecord>
{
    IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync(
        VectorSearchQuery vectorQuery,
        CancellationToken cancellationToken = default);
}
```

每个 `VectorSearchQuery` 子类代表一种特定的搜索类型。
可能的变体受到以下事实的限制 `VectorSearchQuery` ：并且所有 subclasses 都有内部构造函数。
因此，开发人员无法创建自定义搜索查询类型并期望它由 . `IVectorSearch.SearchAsync`
但是，以这种方式拥有子类允许每个查询具有不同的参数和选项。

```csharp
// Base class for all vector search queries.
abstract class VectorSearchQuery(
    string queryType,
    object? searchOptions)
{
    public static VectorizedSearchQuery<TVector> CreateQuery<TVector>(TVector vector, VectorSearchOptions? options = default) => new(vector, options);
    public static VectorizableTextSearchQuery CreateQuery(string text, VectorSearchOptions? options = default) => new(text, options);

    // Showing future extensibility possibilities.
    public static HybridTextVectorizedSearchQuery<TVector> CreateHybridQuery<TVector>(TVector vector, string text, HybridVectorSearchOptions? options = default) => new(vector, text, options);
    public static HybridVectorizableTextSearchQuery CreateHybridQuery(string text, HybridVectorSearchOptions? options = default) => new(text, options);
}

// Vector search using vector.
class VectorizedSearchQuery<TVector>(
    TVector vector,
    VectorSearchOptions? searchOptions) : VectorSearchQuery;

// Vector search using query text that will be vectorized downstream.
class VectorizableTextSearchQuery(
    string queryText,
    VectorSearchOptions? searchOptions) : VectorSearchQuery;

// Hybrid search using a vector and a text portion that will be used for a keyword search.
class HybridTextVectorizedSearchQuery<TVector>(
    TVector vector,
    string queryText,
    HybridVectorSearchOptions? searchOptions) : VectorSearchQuery;

// Hybrid search using text that will be vectorized downstream and also used for a keyword search.
class HybridVectorizableTextSearchQuery(
    string queryText,
    HybridVectorSearchOptions? searchOptions) : VectorSearchQuery

// Options for basic vector search.
public class VectorSearchOptions
{
    public static VectorSearchOptions Default { get; } = new VectorSearchOptions();
    public VectorSearchFilter? Filter { get; init; } = new VectorSearchFilter();
    public string? VectorFieldName { get; init; }
    public int Limit { get; init; } = 3;
    public int Offset { get; init; } = 0;
    public bool IncludeVectors { get; init; } = false;
}

// Options for hybrid vector search.
public sealed class HybridVectorSearchOptions
{
    public static HybridVectorSearchOptions Default { get; } = new HybridVectorSearchOptions();
    public VectorSearchFilter? Filter { get; init; } = new VectorSearchFilter();
    public string? VectorFieldName { get; init; }
    public int Limit { get; init; } = 3;
    public int Offset { get; init; } = 0;
    public bool IncludeVectors { get; init; } = false;

    public string? HybridFieldName { get; init; }
}
```

为了简化调用搜索，无需调用 CreateQuery，我们可以使用扩展方法。
例如，您可以 `SearchAsync(VectorSearchQuery.CreateQuery(vector))` 调用 `SearchAsync(vector)`

```csharp
public static class VectorSearchExtensions
{
    public static IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync<TRecord, TVector>(
        this IVectorSearch<TRecord> search,
        TVector vector,
        VectorSearchOptions? options = default,
        CancellationToken cancellationToken = default)
        where TRecord : class
    {
        return search.SearchAsync(new VectorizedSearchQuery<TVector>(vector, options), cancellationToken);
    }

    public static IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync<TRecord>(
        this IVectorSearch<TRecord> search,
        string searchText,
        VectorSearchOptions? options = default,
        CancellationToken cancellationToken = default)
        where TRecord : class
    {
        return search.SearchAsync(new VectorizableTextSearchQuery(searchText, options), cancellationToken);
    }

    // etc...
}
```

## 使用示例

```csharp
public sealed class Glossary
{
    [VectorStoreRecordKey]
    public ulong Key { get; set; }
    [VectorStoreRecordData]
    public string Category { get; set; }
    [VectorStoreRecordData]
    public string Term { get; set; }
    [VectorStoreRecordData]
    public string Definition { get; set; }
    [VectorStoreRecordVector(1536)]
    public ReadOnlyMemory<float> DefinitionEmbedding { get; set; }
}

public async Task VectorSearchAsync(IVectorSearch<Glossary> vectorSearch)
{
    var searchEmbedding = new ReadOnlyMemory<float>(new float[1536]);

    // Vector search.
    var searchResults = vectorSearch.SearchAsync(VectorSearchQuery.CreateQuery(searchEmbedding));
    searchResults = vectorSearch.SearchAsync(searchEmbedding); // Extension method.

    // Vector search with specific vector field.
    searchResults = vectorSearch.SearchAsync(VectorSearchQuery.CreateQuery(searchEmbedding, new() { VectorFieldName = nameof(Glossary.DefinitionEmbedding) }));
    searchResults = vectorSearch.SearchAsync(searchEmbedding, new() { VectorFieldName = nameof(Glossary.DefinitionEmbedding) }); // Extension method.

    // Text vector search.
    searchResults = vectorSearch.SearchAsync(VectorSearchQuery.CreateQuery("What does Semantic Kernel mean?"));
    searchResults = vectorSearch.SearchAsync("What does Semantic Kernel mean?"); // Extension method.

    // Text vector search with specific vector field.
    searchResults = vectorSearch.SearchAsync(VectorSearchQuery.CreateQuery("What does Semantic Kernel mean?", new() { VectorFieldName = nameof(Glossary.DefinitionEmbedding) }));
    searchResults = vectorSearch.SearchAsync("What does Semantic Kernel mean?", new() { VectorFieldName = nameof(Glossary.DefinitionEmbedding) }); // Extension method.

    // Hybrid vector search.
    searchResults = vectorSearch.SearchAsync(VectorSearchQuery.CreateHybridQuery(searchEmbedding, "What does Semantic Kernel mean?", new() { HybridFieldName = nameof(Glossary.Definition) }));
    searchResults = vectorSearch.HybridVectorizedTextSearchAsync(searchEmbedding, "What does Semantic Kernel mean?", new() { HybridFieldName = nameof(Glossary.Definition) }); // Extension method.

    // Hybrid text vector search with field names specified for both vector and keyword search.
    searchResults = vectorSearch.SearchAsync(VectorSearchQuery.CreateHybridQuery("What does Semantic Kernel mean?", new() { VectorFieldName = nameof(Glossary.DefinitionEmbedding), HybridFieldName = nameof(Glossary.Definition) }));
    searchResults = vectorSearch.HybridVectorizableTextSearchAsync("What does Semantic Kernel mean?", new() { VectorFieldName = nameof(Glossary.DefinitionEmbedding), HybridFieldName = nameof(Glossary.Definition) }); // Extension method.

    // In future we can also support images or other modalities, e.g.
    IVectorSearch<Images> imageVectorSearch = ...
    searchResults = imageVectorSearch.SearchAsync(VectorSearchQuery.CreateBase64EncodedImageQuery(base64EncodedImageString, new() { VectorFieldName = nameof(Images.ImageEmbedding) }));

    // Vector search with filtering.
    var filter = new BasicVectorSearchFilter().EqualTo(nameof(Glossary.Category), "Core Definitions");
    searchResults = vectorSearch.SearchAsync(
        VectorSearchQuery.CreateQuery(
            searchEmbedding,
            new()
            {
                Filter = filter,
                VectorFieldName = nameof(Glossary.DefinitionEmbedding)
            }));
}
```

## 考虑的选项

### 选项 1：搜索对象

有关此选项的描述[，请参阅上面的 ](#interface)Interface 部分。

优点：

- 它可以支持多种查询类型，每种类型都有不同的选项。
- 将来很容易添加更多查询类型，而不会成为重大更改。

缺点：

- 连接器实现不支持的任何查询类型都将导致引发异常。

### 选项 2：仅矢量

抽象将仅支持最基本的功能，而所有其他功能都支持具体实现。
例如，某些矢量数据库不支持在服务中生成嵌入，因此连接器不支持 `VectorizableTextSearchQuery` 选项 1。

优点：

- 用户不需要知道哪些 vector store 连接器类型支持哪些查询类型。

缺点：

- 仅允许按抽象中的向量进行搜索，这是一个非常低的公分母。

```csharp
interface IVectorSearch<TRecord>
{
    IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync<TVector>(
        TVector vector,
        VectorSearchOptions? searchOptions
        CancellationToken cancellationToken = default);
}

class AzureAISearchVectorStoreRecordCollection<TRecord> : IVectorSearch<TRecord>
{
    public IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync<TVector>(
        TVector vector,
        VectorSearchOptions? searchOptions
        CancellationToken cancellationToken = default);

    public IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync(
        string queryText,
        VectorSearchOptions? searchOptions
        CancellationToken cancellationToken = default);
}
```

### 选项 3：抽象基类

主要要求之一是允许将来使用其他查询类型进行扩展。
实现此目的的一种方法是使用可以自动实现新方法的抽象基类
与 NotSupported 一起引发，除非被每个实现覆盖。此行为将
与选项 1 类似。但是，对于选项 1，相同的行为是通过扩展方法实现的。
方法集最终与选项 1 和选项 3 相同，只是选项 1 也具有
一个 Search 方法 `VectorSearchQuery` 作为输入。

`IVectorSearch` 是 的单独接口 `IVectorStoreRecordCollection`，但目的是
for `IVectorStoreRecordCollection` 继承自 `IVectorSearch`。

这意味着 的一些 （大多数） implementation `IVectorSearch` 将成为 `IVectorStoreRecordCollection` implementations 的一部分。
我们预计`IVectorSearch`在商店支持搜索的情况下，我们需要支持独立实现
但不一定是可写的。

因此，需要抽象基类的层次结构。

我们还考虑了默认接口方法，但 .net Framework 不支持此方法，SK 必须支持 .net Framework。

优点：

- 它可以支持多种查询类型，每种类型都有不同的选项。
- 将来很容易添加更多查询类型，而不会成为重大更改。
- 允许每种搜索类型使用不同的返回类型。

缺点：

- 连接器实现不支持的任何查询类型都将导致引发异常。
- 不支持多重继承，因此在需要支持多个键类型的情况下，这不起作用。
- 不支持多重继承，因此任何需要添加到 的附加功能都`VectorStoreRecordCollection`无法使用类似的机制添加。

```csharp
abstract class BaseVectorSearch<TRecord>
    where TRecord : class
{
    public virtual IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync<TVector>(
        this IVectorSearch<TRecord> search,
        TVector vector,
        VectorSearchOptions? options = default,
        CancellationToken cancellationToken = default)
    {
        throw new NotSupportedException($"Vectorized search is not supported by the {this._connectorName} connector");
    }

    public virtual IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync(
        this IVectorSearch<TRecord> search,
        string searchText,
        VectorSearchOptions? options = default,
        CancellationToken cancellationToken = default)
    {
        throw new NotSupportedException($"Vectorizable text search is not supported by the {this._connectorName} connector");
    }
}

abstract class BaseVectorStoreRecordCollection<TKey, TRecord> : BaseVectorSearch<TRecord>
{
    public virtual async Task CreateCollectionIfNotExistsAsync(CancellationToken cancellationToken = default)
    {
        if (!await this.CollectionExistsAsync(cancellationToken).ConfigureAwait(false))
        {
            await this.CreateCollectionAsync(cancellationToken).ConfigureAwait(false);
        }
    }
}

// We support multiple types of keys here, but we cannot inherit from multiple base classes.
class QdrantVectorStoreRecordCollection<TRecord> : BaseVectorStoreRecordCollection<ulong, TRecord> : BaseVectorStoreRecordCollection<Guid, TRecord>
{
}
```

### 选项 4：每种搜索类型的界面

主要要求之一是允许将来使用其他查询类型进行扩展。
实现此目的的一种方法是添加其他接口，因为 implementations 支持其他功能。

优点：

- 允许不同的实现支持不同的搜索类型，而无需为不支持的功能引发异常。
- 允许每种搜索类型使用不同的返回类型。

缺点：

- 用户仍然需要知道每个实现实现了哪些接口，以便根据需要转换为这些接口。
- 随着时间的推移，我们将无法添加更多的搜索功能 `IVectorStoreRecordCollection` ，因为这将是一个重大更改。因此，具有 `IVectorStoreRecordCollection`实例 的用户，但想要例如执行混合搜索，则需要先强制转换为 `IHybridTextVectorizedSearch` first，然后才能进行搜索。

```csharp

// Vector search using vector.
interface IVectorizedSearch<TRecord>
{
    IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync<TVector>(
        TVector vector,
        VectorSearchOptions? searchOptions);
}

// Vector search using query text that will be vectorized downstream.
interface IVectorizableTextSearch<TRecord>
{
    IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync<TVector>(
        string queryText,
        VectorSearchOptions? searchOptions);
}

// Hybrid search using a vector and a text portion that will be used for a keyword search.
interface IHybridTextVectorizedSearch<TRecord>
{
    IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync<TVector>(
        TVector vector,
        string queryText,
        HybridVectorSearchOptions? searchOptions);
}

// Hybrid search using text that will be vectorized downstream and also used for a keyword search.
interface IHybridVectorizableTextSearch<TRecord>
{
    IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync<TVector>(
    string queryText,
    HybridVectorSearchOptions? searchOptions);
}

class AzureAISearchVectorStoreRecordCollection<TRecord>: IVectorStoreRecordCollection<string, TRecord>, IVectorizedSearch<TRecord>, IVectorizableTextSearch<TRecord>
{
}

```

## 决策结果

选项： 4

共识是选项 4 对用户来说更容易理解，默认情况下只公开适用于所有 vector store 的功能。
