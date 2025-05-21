
# 在 VectorStore 抽象中支持混合搜索

## 上下文和问题陈述

除了简单的向量搜索外，许多数据库还支持混合搜索。
混合搜索通常会产生更高质量的搜索结果，因此能够通过 VectorStore 抽象进行混合搜索
是一个需要添加的重要功能。

支持混合搜索的方式因数据库而异。支持混合搜索的两种最常见方法是：

1. 并行使用密集向量搜索和关键字/全文搜索，然后合并结果。
1. 并行使用密集向量搜索和稀疏向量搜索，然后组合结果。

稀疏向量与密集向量的不同之处在于，它们通常具有更多的维度，但许多维度为零。
稀疏向量与文本搜索一起使用时，词汇表中的每个单词/标记都有一个维度，该值表示单词的重要性
在源文本中。
单词在特定文本块中越常见，单词在语料库中越不常见，稀疏向量中的值就越高。

生成稀疏向量的机制多种多样，例如

- [TF-IDF](https://en.wikipedia.org/wiki/Tf%E2%80%93idf)
- [斯普拉德](https://www.pinecone.io/learn/splade/)
- [BGE-m3 稀疏嵌入模型](https://huggingface.co/BAAI/bge-m3)。
- [松果稀疏英语 v0](https://docs.pinecone.io/models/pinecone-sparse-english-v0)

虽然这些在 Python 中得到了很好的支持，但目前在 .net 中并没有得到很好的支持。
添加对生成稀疏向量的支持超出了此 ADR 的范围。

更多背景信息：

- [Qdrant 关于使用稀疏向量进行混合搜索的背景文章](https://qdrant.tech/articles/sparse-vectors)
- [适合初学者的 TF-IDF 解说器](https://medium.com/@coldstart_coder/understanding-and-implementing-tf-idf-in-python-a325d1301484)

ML.Net 包含 TF-IDF 的实现，可用于在 .net 中生成稀疏向量。有关示例，请参阅 [此处](https://github.com/dotnet/machinelearning/blob/886e2ff125c0060f5a251056c7eb2a7d28738984/docs/samples/Microsoft.ML.Samples/Dynamic/Transforms/Text/ProduceWordBags.cs#L55-L105) 。

### 不同数据库中的混合搜索支持

|特征|Azure AI 搜索|维维亚特|雷迪斯|色度|松果|PostgreSQL 的|Qdrant|米尔沃斯|Elasticsearch|CosmosDB NoSql|MongoDB 数据库|
|-|-|-|-|-|-|-|-|-|-|-|-|
|支持混合搜索|Y|Y|N （不使用 fusion 并行执行）|N|Y|Y|Y|Y|Y|Y|Y|
|混合搜索定义|矢量 + 全文|[向量 + 关键词 （BM25F）](https://weaviate.io/developers/weaviate/search/hybrid)|||[关键字的向量 + 稀疏向量](https://docs.pinecone.io/guides/get-started/key-features#hybrid-search)|[向量 + 关键字](https://jkatz05.com/post/postgres/hybrid-search-postgres-pgvector/)|[向量 + 稀疏向量 / 关键字](https://qdrant.tech/documentation/concepts/hybrid-queries/)|[向量 + 稀疏向量](https://milvus.io/docs/multi-vector-search.md)|矢量 + 全文|[矢量 + 全文 （BM25）](https://learn.microsoft.com/en-us/azure/cosmos-db/gen-ai/hybrid-search)|[矢量 + 全文](https://www.mongodb.com/docs/atlas/atlas-search/tutorial/hybrid-search)|
|熔融方法可配置|N|Y|||?|Y|Y|Y|Y，但只有一个选项|Y，但只有一个选项|N|
|融合方法|[RRF](https://learn.microsoft.com/en-us/azure/search/hybrid-search-ranking)|排名/RelativeScore|||?|[构建您自己的](https://jkatz05.com/post/postgres/hybrid-search-postgres-pgvector/)|RRF / DBSF|[RRF / 加权](https://milvus.io/docs/multi-vector-search.md)|[RRF](https://www.elastic.co/search-labs/tutorials/search-tutorial/vector-search/hybrid-search)|[RRF](https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/query/rrf)|[RRF](https://www.mongodb.com/docs/atlas/atlas-search/tutorial/hybrid-search)|
|混合搜索输入参数|向量 + 字符串|[向量 + 字符串](https://weaviate.io/developers/weaviate/api/graphql/search-operators#hybrid)|||向量 + 稀疏向量|向量 + 字符串|[向量 + 稀疏向量](https://qdrant.tech/documentation/concepts/hybrid-queries/)|[向量 + 稀疏向量](https://milvus.io/docs/multi-vector-search.md)|向量 + 字符串|向量 + 字符串数组|向量 + 字符串|
|稀疏距离函数|不适用|不适用|||[dotproduct 仅适用于密集和稀疏，1 个设置用于两者](https://docs.pinecone.io/guides/data/understanding-hybrid-search#sparse-dense-workflow)|不适用|点产品|内积|不适用|不适用|不适用|
|稀疏索引选项|不适用|不适用|||没有单独的 CONFIG 到 DENSE|不适用|ondisk / inmemory + IDF|[SPARSE_INVERTED_INDEX / SPARSE_WAND](https://milvus.io/docs/index.md?tab=sparse)|不适用|不适用|不适用|
|稀疏数据模型|不适用|不适用|||[indices & values 数组](https://docs.pinecone.io/guides/data/upsert-sparse-dense-vectors)|不适用|indices & values 数组|[稀疏矩阵 / 字典列表 / 元组列表](https://milvus.io/docs/sparse_vector.md#Use-sparse-vectors-in-Milvus)|不适用|不适用|不适用|
|关键字匹配行为|[以 searchMode=any 分隔的空格执行 OR，searchmode=all 执行 AND](https://learn.microsoft.com/en-us/azure/search/search-lucene-query-architecture)|[按空格分割的分词会影响排名](https://weaviate.io/developers/weaviate/search/bm25)|||不适用|[分词化](https://www.postgresql.org/docs/current/textsearch-controls.html)|[<p>无 FTS 索引：子字符串完全匹配</p><p>存在 FTS 索引：必须存在所有单词</p>](https://qdrant.tech/documentation/concepts/filtering/#full-text-match)|不适用|[And/Or 功能](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-match-bool-prefix-query.html)|-|[允许使用 OR 的多个多词短语](https://www.mongodb.com/docs/atlas/atlas-search/phrase/)和一个[多词 prhase，其中单词可以是 OR 或 AND](https://www.mongodb.com/docs/atlas/atlas-search/text/)|

词汇表：

- RRF = 倒数秩融合
- DBSF = 基于分布的分数融合
- IDF = 逆向文档频率

### Cosmos DB NoSQL 全文搜索配置所需的语言

Cosmos DB NoSQL 需要为全文搜索指定语言，并且需要为混合搜索启用全文搜索索引。
因此，我们需要支持一种在创建索引时指定语言的方法。

Cosmos DB NoSQL 是示例中唯一具有此类型的必需设置的数据库。

|特征|Azure AI 搜索|维维亚特|雷迪斯|色度|松果|PostgreSQL 的|Qdrant|米尔沃斯|Elasticsearch|CosmosDB NoSql|MongoDB 数据库|
|-|-|-|-|-|-|-|-|-|-|-|-|
|需要 FullTextSearch 索引进行混合搜索|Y|Y|不适用|不适用|不适用|Y|N [可选](https://qdrant.tech/documentation/concepts/filtering/#full-text-match)|不适用|Y|Y|[Y](https://www.mongodb.com/docs/atlas/atlas-search/tutorial/hybrid-search/?msockid=04b550d92f2f619c271a45a42e066050#create-the-atlas-vector-search-and-fts-indexes)|
|必需的 FullTextSearch 索引选项|不需要， [很多可选](https://learn.microsoft.com/en-us/rest/api/searchservice/indexes/create?view=rest-searchservice-2024-07-01&tabs=HTTP)|无需任何选项，[也无需任何可选内容](https://weaviate.io/developers/weaviate/concepts/indexing#collections-without-indexes)||||[所需语言](https://jkatz05.com/post/postgres/hybrid-search-postgres-pgvector/)|不需要， [一些可选](https://qdrant.tech/documentation/concepts/indexing/#full-text-index)||不需要， [很多可选](https://elastic.github.io/elasticsearch-net/8.16.3/api/Elastic.Clients.Elasticsearch.Mapping.TextProperty.html)|所需语言|不需要， [很多可选](https://www.mongodb.com/docs/atlas/atlas-search/field-types/string-type/#configure-fts-field-type-field-properties)|

### 关键字搜索界面选项

每个数据库都有不同的关键字搜索功能。有些在列出混合搜索的关键词时只支持非常基本的界面。下表列出了每个数据库与我们可能希望支持的特定关键字 public interface 的兼容性。

|特征|Azure AI 搜索|维维亚特|PostgreSQL 的|Qdrant|Elasticsearch|CosmosDB NoSql|MongoDB 数据库|
|-|-|-|-|-|-|-|-|
|<p>string[] keyword</p><p>每个元素一个单词</p><p>任何匹配的单词都会提升排名。</p>|Y|Y（必须用空格连接）|[Y（必须用空格连接）](https://www.postgresql.org/docs/current/textsearch-controls.html)|Y（通过具有多个 OR 匹配的筛选器）|Y|Y|[Y（必须用空格连接）](https://pymongo.readthedocs.io/en/stable/api/pymongo/collection.html#pymongo.collection.Collection.find_one)|
|<p>string[] 关键字</p><p>每个元素一个或多个单词</p><p>必须存在单个元素中的所有单词才能提高排名。</p>|Y|N|Y|Y（通过具有多个 OR 匹配和 FTS 指数的过滤器）|-|N|N|
|<p>string[] 关键字</p><p>每个元素一个或多个单词</p><p>单个元素中的多个单词是必须完全匹配才能提高排名的短语。</p>|Y|N|Y|仅通过具有多个 OR 匹配且无索引的过滤器|-|N|Y|
|<p>string 关键字</p><p>空格分隔的单词</p><p>任何匹配的单词都会提升排名。</p>|Y|Y|Y|N（需要拆分单词）|-|N（需要拆分单词）|Y|

### 命名选项

|接口名称|方法名称|参数|选项类名称|关键字属性选择器|密集向量属性选择器|
|-|-|-|-|-|-|
|关键字VectorizedHybridSearch|关键字VectorizedHybridSearch|字符串[] + 密集向量|KeywordVectorizedHybridSearchOptions|FullTextPropertyName （完整文本属性名称）|VectorPropertyName （向量属性名称）|
|SparseVectorizedHybridSearch|SparseVectorizedHybridSearch|稀疏向量 + 密集向量|SparseVectorizedHybridSearchOptions|SparseVectorPropertyName （稀疏向量属性名称）|VectorPropertyName （向量属性名称）|
|关键字矢量化文本混合搜索|关键字矢量化文本混合搜索|字符串[] + 字符串|KeywordVectorizableTextHybridSearchOptions|FullTextPropertyName （完整文本属性名称）|VectorPropertyName （向量属性名称）|
|SparseVectorizableTextHybridSearch|SparseVectorizableTextHybridSearch|字符串[] + 字符串|SparseVectorizableTextHybridSearchOptions|SparseVectorPropertyName （稀疏向量属性名称）|VectorPropertyName （向量属性名称）|

|接口名称|方法名称|参数|选项类名称|关键字属性选择器|密集向量属性选择器|
|-|-|-|-|-|-|
|关键字VectorizedHybridSearch|混合搜索|字符串[] + 密集向量|KeywordVectorizedHybridSearchOptions|FullTextPropertyName （完整文本属性名称）|VectorPropertyName （向量属性名称）|
|SparseVectorizedHybridSearch|混合搜索|稀疏向量 + 密集向量|SparseVectorizedHybridSearchOptions|SparseVectorPropertyName （稀疏向量属性名称）|VectorPropertyName （向量属性名称）|
|关键字矢量化文本混合搜索|混合搜索|字符串[] + 字符串|KeywordVectorizableTextHybridSearchOptions|FullTextPropertyName （完整文本属性名称）|VectorPropertyName （向量属性名称）|
|SparseVectorizableTextHybridSearch|混合搜索|字符串[] + 字符串|SparseVectorizableTextHybridSearchOptions|SparseVectorPropertyName （稀疏向量属性名称）|VectorPropertyName （向量属性名称）|

|接口名称|方法名称|参数|选项类名称|关键字属性选择器|密集向量属性选择器|
|-|-|-|-|-|-|
|HybridSearchWithKeywords|混合搜索|字符串[] + 密集向量|HybridSearchOptions|FullTextPropertyName （完整文本属性名称）|VectorPropertyName （向量属性名称）|
|HybridSearchWithSparseVector|HybridSearchWithSparseVector|稀疏向量 + 密集向量|HybridSearchWithSparseVectorOptions|SparseVectorPropertyName （稀疏向量属性名称）|VectorPropertyName （向量属性名称）|
|HybridSearchWithKeywordsAndVectorizableText|混合搜索|字符串[] + 字符串|HybridSearchOptions|FullTextPropertyName （完整文本属性名称）|VectorPropertyName （向量属性名称）|
|HybridSearchWithVectorizableKeywordsAndText|HybridSearchWithSparseVector|字符串[] + 字符串|HybridSearchWithSparseVectorOptions|SparseVectorPropertyName （稀疏向量属性名称）|VectorPropertyName （向量属性名称）|

|面积|搜索类型|参数|方法名称|
|-|-|-|-|
|**非矢量搜索**||||
|非矢量搜索|规则，无矢量||搜索|
|**使用命名方法进行向量搜索**||||
|向量搜索|使用 Vector|`ReadonlyMemory<float> vector`|矢量搜索|
|向量搜索|使用可矢量化文本|`string text`|VectorSearchWithText （向量搜索文本）|
|向量搜索|使用可矢量化图像|`string/byte[]/other image`|矢量搜索与图像|
|向量搜索|使用可矢量化的图像 + 文本|`string/byte[]/other image, string text`|VectorSearchWithImageAndText （矢量搜索带图像和文本）|
|**使用命名参数进行向量搜索**||||
|向量搜索|使用 Vector|`new Vector(ReadonlyMemory<float>)`|矢量搜索|
|向量搜索|使用可矢量化文本|`new VectorizableText(string text)`|矢量搜索|
|向量搜索|使用可矢量化图像|`new VectorizableImage(string/byte[]/other image)`|矢量搜索|
|向量搜索|使用可矢量化的图像 + 文本|`VectorizableMultimodal(string/byte[]/other image, string text)`|矢量搜索|
|**混合搜索**||||
|混合搜索|使用 DenseVector 和字符串[] 关键字|`ReadonlyMemory<float> vector, string[] keywords`|混合搜索|
|混合搜索|使用可矢量化字符串和字符串[] 关键字|`string vectorizableText, string[] keywords`|混合搜索|
|混合搜索|使用 DenseVector 和 SparseVector|`ReadonlyMemory<float> vector, ? sparseVector`|HybridSearchWithSparseVector|
|混合搜索|使用可矢量化字符串和稀疏矢量化字符串[] 关键字|`string vectorizableText, string[] vectorizableKeywords`|HybridSearchWithSparseVector|

```csharp
var collection;

// ----------------------- Method names vary -----------------------
// We'll need to add a new interface with a new method name for each data type that we want to search for.

public Task VectorSearch(ReadonlyMemory<float> vector, VectorSearchOptions options = null, CancellationToken cancellationToken);
public Task VectorSearchWithText(string text, VectorSearchOptions options = null, CancellationToken cancellationToken = null);
public Task VectorSearchWithImage(VectorizableData image, VectorSearchOptions options = null, CancellationToken cancellationToken = null);
collection.VectorSearchWithImageAndText(VectorizableData image, string text, VectorSearchOptions options = null, CancellationToken cancellationToken = null);

collection.VectorSearch(new ReadonlyMemory<float>([...]));
collection.VectorSearchWithText("Apples and oranges are tasty.");
collection.VectorSearchWithImage("fdslkjfskdlfjdslkjfdskljfdslkjfsd");
collection.VectorSearchWithImageAndText("fdslkjfskdlfjdslkjfdskljfdslkjfsd", "Apples and oranges are tasty.");

// ----------------------- Param types vary -----------------------
// We'll need to add a new interface for each data type that we want to search for.

// Vector Search
public Task VectorSearch<TRecord>(Embedding embedding, VectorSearchOptions<TRecord> options = null, CancellationToken cancellationToken);
public Task VectorSearch<TRecord>(VectorizableImage vectorizableImage, VectorSearchOptions<TRecord> options = null, CancellationToken cancellationToken = null);
public Task VectorSearch<TRecord>(VectorizableMultimodal vectorizableMultiModal, VectorSearchOptions<TRecord> options = null, CancellationToken cancellationToken = null);

collection.VectorSearch(new Embedding(new ReadonlyMemory<float>([...])));
collection.VectorSearch(new VectorizableText("Apples and oranges are tasty."));
collection.VectorSearch(new VectorizableImage("fdslkjfskdlfjdslkjfdskljfdslkjfsd"));
collection.VectorSearch(new VectorizableMultimodal("fdslkjfskdlfjdslkjfdskljfdslkjfsd", "Apples and oranges are tasty."));

// Hybrid search
// Same as next option, since hybrid is currently explicitly dense vectors plus keywords.

// ----------------------- Array of params inheriting from a common base type -----------------------
// We can potentially add extension methods, to make it easier to use.
// We just need to add new embedding or vectorizable data types for new data types that we want to search for.

// Vector Search
public Task VectorSearch<TRecord>(Embedding embedding, VectorSearchOptions<TRecord> options = null, CancellationToken cancellationToken = null);
public Task VectorSearch<TRecord>(VectorizableData vectorizableData, VectorSearchOptions<TRecord> options = null, CancellationToken cancellationToken = null);
public Task VectorSearch<TRecord>(VectorizableData[] vectorizableData, VectorSearchOptions<TRecord> options = null, CancellationToken cancellationToken = null);
public Task VectorSearch<TRecord, TVectorType>(TVectorType embedding, VectorSearchOptions<TRecord> options = null, CancellationToken cancellationToken);

// Convenience extension methods
public Task VectorSearch<TRecord>(Embedding embedding, VectorSearchOptions<TRecord> options = null, CancellationToken cancellationToken);
public Task VectorSearch<TRecord>(string text, VectorSearchOptions<TRecord> options = null, CancellationToken cancellationToken = null);

public Task Search<TRecord>(NonVectorSearchOptions<TRecord> options = null, CancellationToken cancellationToken);

collection.VectorSearch(new Embedding(new ReadonlyMemory<float>([...])));
collection.VectorSearch("Apples and oranges are tasty."); // Via extension?
collection.VectorSearch(new VectorizableData("Apples and oranges are tasty.", "text/plain"));

collection.VectorSearch(["Apples and oranges are tasty."]); // Via extension?
collection.VectorSearch([new VectorizableData("Apples and oranges are tasty.", "text/plain")]);
collection.VectorSearch([new VectorizableData("fdslkjfskdlfjdslkjfdskljfdslkjfsd", "image/jpeg")]);
collection.VectorSearch([new VectorizableData("fdslkjfskdlfjdslkjfdskljfdslkjfsd", "image/jpeg"), new VectorizableText("Apples and oranges are tasty.")]);

// Hybrid search
public Task HybridSearch<TRecord, TVectorType>(TVector vector, VectorizableData vectorizableData, HybridSearchOptions<TRecord> options = null, CancellationToken cancellationToken = null);

public Task HybridSearch<TRecord>(Embedding denseVector, Embedding sparseVector, HybridSearchOptions<TRecord> options = null, CancellationToken cancellationToken = null);
public Task HybridSearch<TRecord>(Embedding Densevector, VectorizableData sparseVectorizableData, HybridSearchOptions<TRecord> options = null, CancellationToken cancellationToken = null);
public Task HybridSearch<TRecord>(VectorizableData denseVectorizableData, VectorizableData sparseVectorizableData, HybridSearchOptions<TRecord> options = null, CancellationToken cancellationToken = null);
public Task HybridSearch<TRecord>(VectorizableData denseVectorizableData, Embedding sparseVector, HybridSearchOptions<TRecord> options = null, CancellationToken cancellationToken = null);

collection.HybridSearch(new Embedding(new ReadonlyMemory<float>([...])), ["Apples", "Oranges"], new() { VectorPropertyName = "DescriptionEmbedding", FullTextPropertyName = "Keywords" })
collection.HybridSearch(new VectorizableText("Apples and oranges are tasty."), ["Apples", "Oranges"], new() { VectorPropertyName = "DescriptionEmbedding", FullTextPropertyName = "Keywords" });
collection.HybridSearchWithSparseVector(new Embedding(new ReadonlyMemory<float>([...])), new SparseEmbedding(), new() { VectorPropertyName = "DescriptionEmbedding", SparseVectorPropertyName = "KeywordsEmbedding" });
collection.HybridSearchWithSparseVector(new VectorizableText("Apples and oranges are tasty."), new SparseEmbedding(), new() { VectorPropertyName = "DescriptionEmbedding", SparseVectorPropertyName = "KeywordsEmbedding" });
collection.HybridSearchWithSparseVector(new VectorizableText("Apples and oranges are tasty."), new SparseVectorizableText("Apples", "Oranges"), new() { VectorPropertyName = "DescriptionEmbedding", SparseVectorPropertyName = "KeywordsEmbedding" });

// ----------------------- One name, regular params, common options, with target property type determining search type -----------------------

// With generic vector (short term)
public Task HybridSearch<TRecord, TVectorType>(TVector vector, string[] keywords, HybridSearchOptions<TRecord> options = null, CancellationToken cancellationToken);

// With embedding (long term)
public Task HybridSearch<TRecord>(Embedding vector, string[] keywords, HybridSearchOptions<TRecord> options = null, CancellationToken cancellationToken);
public Task HybridSearch<TRecord>(Embedding vector, SparseEmbedding sparseVector, HybridSearchOptions<TRecord> options = null, CancellationToken cancellationToken);
public Task HybridSearch<TRecord>(string vectorizableText, SparseEmbedding sparseVector, HybridSearchOptions<TRecord> options = null, CancellationToken cancellationToken);
public Task HybridSearch<TRecord>(string vectorizableText, string[] sparseVectorizableText, HybridSearchOptions<TRecord> options = null, CancellationToken cancellationToken);
public Task HybridSearch<TRecord>(Embedding vector, string[] sparseVectorizableText, HybridSearchOptions<TRecord> options = null, CancellationToken cancellationToken);

// Is there a good name for the fulltextsearchproperty/sparsevectorproperty.
HybridSearchPropertyName
AdditionalSearchPropertyName
AdditionalPropertyName
SecondaryPropertyName
HybridSearchSecondaryPropertyName
KeywordsPropertyName
KeywordsSearchPropertyName

// ----------------------- Pass Embedding/VectorizableContent via common base class with target property name -----------------------

class SearchTarget<TRecord>();
class VectorSearchTarget<TRecord, TVectorType>(ReadonlyMemory<TVectorType> vector, Expression<Func<TRecord, object>> targetProperty) : SearchTarget<TRecord>();
class KeywordsSearchTarget<TRecord>(string[] keywords, Expression<Func<TRecord, object>> targetProperty) : SearchTarget<TRecord>();
class SparseSearchTarget<TRecord>(SparseVector vector, Expression<Func<TRecord, object>> targetProperty) : SearchTarget<TRecord>();

public Task HybridSearch(
    SearchTarget<TRecord>[] searchParams,
    HybridSearchOptions options = null,
    CancellationToken cancellationToken);
// Extension Methods:
public Task HybridSearch(
    ReadonlyMemory<float> vector vector,
    string targetVectorPropertyName,
    string[] keywords,
    string targetHybridSearchPropertyName,
    HybridSearchOptions options = null,
    CancellationToken cancellationToken);
public Task HybridSearch(
    ReadonlyMemory<float> vector vector,
    string targetVectorFieldName,
    SparseVector sparseVector,
    string targetHybridSearchPropertyName,
    HybridSearchOptions options = null,
    CancellationToken cancellationToken);
```

### 基于关键字的混合搜索

```csharp
interface IKeywordVectorizedHybridSearch<TRecord>
{
    Task<VectorSearchResults<TRecord>> KeywordVectorizedHybridSearch<TVector>(
        TVector vector,
        ICollection<string> keywords,
        KeywordVectorizedHybridSearchOptions options,
        CancellationToken cancellationToken);
}

class KeywordVectorizedHybridSearchOptions
{
    // The name of the property to target the vector search against.
    public string? VectorPropertyName { get; init; }

    // The name of the property to target the text search against.
    public string? FullTextPropertyName { get; init; }

    public VectorSearchFilter? Filter { get; init; }
    public int Top { get; init; } = 3;
    public int Skip { get; init; } = 0;
    public bool IncludeVectors { get; init; } = false;
    public bool IncludeTotalCount { get; init; } = false;
}
```

### 基于稀疏向量的混合搜索

```csharp
interface ISparseVectorizedHybridSearch<TRecord>
{
    Task<VectorSearchResults<TRecord>> SparseVectorizedHybridSearch<TVector, TSparseVector>(
        TVector vector,
        TSparseVector sparsevector,
        SparseVectorizedHybridSearchOptions options,
        CancellationToken cancellationToken);
}

class SparseVectorizedHybridSearchOptions
{
    // The name of the property to target the dense vector search against.
    public string? VectorPropertyName { get; init; }
    // The name of the property to target the sparse vector search against.
    public string? SparseVectorPropertyName { get; init; }

    public VectorSearchFilter? Filter { get; init; }
    public int Top { get; init; } = 3;
    public int Skip { get; init; } = 0;
    public bool IncludeVectors { get; init; } = false;
    public bool IncludeTotalCount { get; init; } = false;
}
```

### 基于关键字的可矢量化文本混合搜索

```csharp
interface IKeywordVectorizableHybridSearch<TRecord>
{
    Task<VectorSearchResults<TRecord>> KeywordVectorizableHybridSearch(
        string searchText,
        ICollection<string> keywords,
        KeywordVectorizableHybridSearchOptions options = default,
        CancellationToken cancellationToken = default);
}

class KeywordVectorizableHybridSearchOptions
{
    // The name of the property to target the dense vector search against.
    public string? VectorPropertyName { get; init; }
    // The name of the property to target the text search against.
    public string? FullTextPropertyName { get; init; }

    public VectorSearchFilter? Filter { get; init; }
    public int Top { get; init; } = 3;
    public int Skip { get; init; } = 0;
    public bool IncludeVectors { get; init; } = false;
    public bool IncludeTotalCount { get; init; } = false;
}
```

### 基于稀疏向量的可矢量化文本混合搜索

```csharp
interface ISparseVectorizableTextHybridSearch<TRecord>
{
    Task<VectorSearchResults<TRecord>> SparseVectorizableTextHybridSearch(
        string searchText,
        ICollection<string> keywords,
        SparseVectorizableTextHybridSearchOptions options = default,
        CancellationToken cancellationToken = default);
}

class SparseVectorizableTextHybridSearchOptions
{
    // The name of the property to target the dense vector search against.
    public string? VectorPropertyName { get; init; }
    // The name of the property to target the sparse vector search against.
    public string? SparseVectorPropertyName { get; init; }

    public VectorSearchFilter? Filter { get; init; }
    public int Top { get; init; } = 3;
    public int Skip { get; init; } = 0;
    public bool IncludeVectors { get; init; } = false;
    public bool IncludeTotalCount { get; init; } = false;
}
```

## 决策驱动因素

- 需要支持生成稀疏向量，才能使基于稀疏向量的混合搜索可行。
- 需要支持每个记录多个向量场景。
- 在我们的评估集中，没有一个数据库被确定为支持在 upsert 上将文本转换为数据库中的稀疏向量，并将这些稀疏向量存储在可检索的字段中。当然，其中一些 DB 可能会在内部使用稀疏向量来实现关键字搜索，而无需将它们暴露给调用者。

## 确定考虑的选项的范围

### 1. 仅限关键字混合搜索

目前只实施KeywordVectorizedHybridSearch & KeywordVectorizableTextHybridSearch，直到
我们可以添加对生成稀疏向量的支持。

### 2. 关键字和稀疏矢量化混合搜索

实现KeywordVectorizedHybridSearch和KeywordVectorizableTextHybridSearch，但只实现
KeywordVectorizableTextHybridSearch，因为我们的评估集中没有数据库支持在数据库中生成稀疏向量。
这将要求我们生成可以从文本生成稀疏向量的代码。

### 3. 上述所有混合搜索

创建所有四个接口并实现 SparseVectorizableTextHybridSearch 的实现，该
在客户端代码中生成稀疏向量。
这将要求我们生成可以从文本生成稀疏向量的代码。

### 4. 广义混合搜索

某些数据库支持更通用的混合搜索版本，您可以在其中进行两个（有时是多个）任何类型的搜索，并使用您选择的融合方法组合这些搜索的结果。
您可以使用这种更通用的搜索来实现 Vector + Keyword 搜索。
但是，对于仅支持 Vector + Keyword 混合搜索的数据库，不可能在这些数据库之上实现通用混合搜索。

## PropertyName 命名考虑的选项

### 1. 显式密集命名

DenseVectorPropertyName （密度向量属性名称）
SparseVectorPropertyName （稀疏向量属性名称）

DenseVectorPropertyName （密度向量属性名称）
FullTextPropertyName （完整文本属性名称）

- 优点：考虑到还涉及稀疏向量，这更明确。
- 缺点：它与非混合向量搜索中的命名不一致。

### 2. 隐式密集命名

VectorPropertyName （向量属性名称）
SparseVectorPropertyName （稀疏向量属性名称）

VectorPropertyName （向量属性名称）
FullTextPropertyName （完整文本属性名称）

- 优点：这与非混合向量搜索中的命名一致。
- 缺点：它在内部不一致，即我们有 sparse vector，但对于 dense，它只是 vector。

## 关键字拆分考虑的选项

### 1. 接受 在界面中拆分关键字

接受 string 的 ICollection，其中每个值都是一个单独的关键字。
采用单个关键字并调用该版本的版本 `ICollection<string>` 也可以作为扩展方法提供。

```csharp
    Task<VectorSearchResults<TRecord>> KeywordVectorizedHybridSearch(
        TVector vector,
        ICollection<string> keywords,
        KeywordVectorizedHybridSearchOptions options,
        CancellationToken cancellationToken);
```

- 优点：如果底层数据库需要拆分关键字，则更容易在连接器中使用
- 优点： 仅广泛支持解决方案，请参阅上面的比较表。

### 2. 在界面中接受单个字符串

接受包含所有关键字的单个字符串。

```csharp
    Task<VectorSearchResults<TRecord>> KeywordVectorizedHybridSearch(
        TVector vector,
        string keywords,
        KeywordVectorizedHybridSearchOptions options,
        CancellationToken cancellationToken);
```

- 优点： 用户更容易使用，因为他们不需要进行任何关键字拆分。
- 缺点：我们没有能力正确清理字符串，例如，根据语言适当地拆分单词，并可能删除填充词。

### 3. 接受 either in 接口

接受任一选项，并根据底层数据库的需要组合或拆分连接器中的关键字。

```csharp
    Task<VectorSearchResults<TRecord>> KeywordVectorizedHybridSearch(
        TVector vector,
        ICollection<string> keywords,
        KeywordVectorizedHybridSearchOptions options,
        CancellationToken cancellationToken);
    Task<VectorSearchResults<TRecord>> KeywordVectorizedHybridSearch(
        TVector vector,
        string keywords,
        KeywordVectorizedHybridSearchOptions options,
        CancellationToken cancellationToken);
```

- 优点： 用户更容易使用，因为他们可以选择更适合自己的
- 缺点： 我们仍然必须通过组合关键字或拆分它们来与内部演示文稿进行转换。
- 缺点：我们没有能力正确清理单个字符串，例如，根据语言适当地拆分单词，并可能删除填充词。

### 4. 接受接口中的任一，但抛出不支持的

接受任一选项，但抛出基础数据库不支持的选项。

- 优点： 我们更容易实施。
- 缺点： 用户更难使用。

### 5. 每个都有单独的接口

为 Enumerable 和 single string 选项创建一个单独的接口，并且仅为每个 db 实现底层系统支持的接口。

- 优点： 我们更容易实施。
- 缺点： 用户更难使用。

## 全文搜索索引 强制配置 考虑的选项

Cosmos DB NoSQL 要求在创建全文搜索索引时指定语言。
其他 DB 具有可设置的可选值。

### 1. 通过收集选项传入选项

此选项只需将 language 选项添加到集合的 options 类中，即可完成最低限度的作。
然后，此语言将用于集合创建的所有全文搜索索引。

- 优点： 最容易实现
- 缺点： 不允许将多种语言用于一条记录中的不同字段
- 缺点： 没有添加对所有数据库的所有全文搜索选项的支持

### 2. 为 RecordDefinition 和数据模型属性添加扩展

向 VectorStoreRecordProperty 添加属性包，以允许提供特定于数据库的元数据。
添加一个可以继承的抽象基本属性，该属性允许将额外的元数据添加到数据模型中。
其中，每个数据库都有自己的属性来指定其设置，并有一个方法将内容转换为
VectorStoreRecordProperty 所需的属性包。

- 优点： 允许对一条记录中的不同字段使用多种语言
- 优点： 允许其他数据库通过自己的属性添加自己的设置
- 缺点： 需要实施更多工作

## 决策结果

### 范围

已选择选项 “1.Keyword Hybrid Search Only“，因为企业对生成稀疏向量的支持很差，并且没有端到端的故事，因此该值很低。

### PropertyName 命名

所选选项 “2.隐式密集命名“，因为它与现有的向量搜索选项命名一致。

### 关键字拆分

已选择选项 “1.Accept Split keywords in interface“，因为它是数据库中唯一一个得到广泛支持的。

### Naming Options 决策

我们一致认为，我们的北极星设计将支持 Embedding 类型和某种形式的可矢量化数据（可能是来自 MEAI 的 DataContent）作为两者的输入
常规搜索和混合搜索。

```csharp
public Task VectorSearch<TRecord>(Embedding embedding, VectorSearchOptions<TRecord> options = null, CancellationToken cancellationToken = null);
public Task VectorSearch<TRecord>(VectorizableData vectorizableData, VectorSearchOptions<TRecord> options = null, CancellationToken cancellationToken = null);
public Task VectorSearch<TRecord>(VectorizableData[] vectorizableData, VectorSearchOptions<TRecord> options = null, CancellationToken cancellationToken = null);

public Task HybridSearch<TRecord, TVectorType>(TVector vector, VectorizableData vectorizableData, HybridSearchOptions<TRecord> options = null, CancellationToken cancellationToken = null);
```

我们将有一个 HybridSearch 方法名称，将来会针对不同的输入使用不同的重载，但是将有一个选项类。
用于选择目标关键字字段的属性选择器，或者将来将调用稀疏向量字段 `AdditionalPropertyName`。

在我们努力使正确的数据类型和 Embedding 类型可用时，我们将提供以下接口。

```csharp
public Task HybridSearch<TVector>(TVector vector, ICollection<string> keywords, HybridSearchOptions<TRecord> options = null, CancellationToken cancellationToken);
```
