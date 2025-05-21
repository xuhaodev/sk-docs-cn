
# 实体框架作为矢量存储连接器

## 上下文和问题陈述

此 ADR 包含有关将实体框架作为矢量存储连接器添加到语义内核代码库的调查结果。 

实体框架是一种现代对象关系映射器，允许使用 .NET （C#） 跨各种数据库构建干净、可移植的高级数据访问层，包括 SQL 数据库（本地和 Azure）、SQLite、MySQL、PostgreSQL、Azure Cosmos DB 等。它支持 LINQ 查询、更改跟踪、更新和架构迁移。 

Entity Framework for Semantic Kernel 的巨大优势之一是支持多个数据库。理论上，一个 Entity Framework 连接器可以同时作为多个数据库的中心，这应该会简化与这些数据库集成的开发和维护。

但是，存在一些限制，不允许 Entity Framework 适应更新的 Vector Store 设计。

### 集合创建

在新的 Vector Store 设计中，interface `IVectorStoreRecordCollection<TKey, TRecord>` 包含对数据库集合进行作的方法：
- `CollectionExistsAsync`
- `CreateCollectionAsync`
- `CreateCollectionIfNotExistsAsync`
- `DeleteCollectionAsync`

在实体框架中，不建议在生产场景中使用编程方法创建集合（也称为架构/表）。推荐的方法是使用迁移（在代码优先方法的情况下），或使用逆向工程（也称为基架/数据库优先方法）。建议仅将编程架构创建用于测试/本地方案。此外，不同数据库的集合创建过程也不同。例如，MongoDB EF Core 提供程序不支持架构迁移或数据库优先/模型优先方法。相反，如果集合尚不存在，则在首次插入文档时会自动创建集合。这带来了 from interface 等方法的复杂性 `CreateCollectionAsync` `IVectorStoreRecordCollection<TKey, TRecord>` ，因为 EF 中没有适用于大多数数据库的集合管理抽象。对于此类情况，建议的方法是依赖自动创建或为每个数据库单独处理集合创建。例如，在 MongoDB 中，建议直接使用 MongoDB C# 驱动程序。

来源：
- https://learn.microsoft.com/en-us/ef/core/managing-schemas/
- https://learn.microsoft.com/en-us/ef/core/managing-schemas/ensure-created
- https://learn.microsoft.com/en-us/ef/core/managing-schemas/migrations/applying?tabs=dotnet-core-cli#apply-migrations-at-runtime
- https://github.com/mongodb/mongo-efcore-provider?tab=readme-ov-file#not-supported--out-of-scope-features

### 密钥管理

无法定义一组有效的键类型，因为并非所有数据库都支持所有类型作为键。在这种情况下，可以只支持键的标准类型，例如 `string`，然后应执行转换以满足特定数据库的键限制。这消除了统一连接器实施的优势，因为应该为每个数据库单独处理密钥管理。

来源：
- https://learn.microsoft.com/en-us/ef/core/modeling/keys?tabs=data-annotations

### 病媒管理

`ReadOnlyMemory<T>` 类型，目前在大多数 SK 连接器中用于保存嵌入向量，但在 Entity Framework 中不受现成支持。尝试使用此类型时，会出现以下错误：

```
The property '{Property Name}' could not be mapped because it is of type 'ReadOnlyMemory<float>?', which is not a supported primitive type or a valid entity type. Either explicitly map this property, or ignore it using the '[NotMapped]' attribute or by using 'EntityTypeBuilder.Ignore' in 'OnModelCreating'.
```

但是，可以使用 `byte[]` type 或 create explicit mapping 来支持 `ReadOnlyMemory<T>`.它已经在 package 中实现 `pgvector` ，但尚不清楚它是否适用于不同的数据库。

来源： 
- https://github.com/pgvector/pgvector-dotnet/blob/master/README.md#entity-framework-core
- https://github.com/pgvector/pgvector-dotnet/blob/master/src/Pgvector/Vector.cs
- https://github.com/pgvector/pgvector-dotnet/blob/master/src/Pgvector.EntityFrameworkCore/VectorTypeMapping.cs

### 测试

使用 SQLite 数据库创建 Entity Framework 连接器并编写测试并不意味着此集成适用于其他 EF 支持的数据库。每个数据库都实现自己的实体框架功能集，因此为了确保实体框架连接器涵盖特定数据库的主要用例，应单独使用每个数据库添加单元/集成测试。 

来源：
- https://github.com/mongodb/mongo-efcore-provider?tab=readme-ov-file#supported-features

### 兼容性

无法使用最新的 Entity Framework Core 包并针对 .NET Standard 进行开发。支持 .NET Standard 的 EF Core 的最新版本是 5.0 版（最新的 EF Core 版本是 8.0）。这意味着实体框架连接器只能面向 .NET 8.0（这与目前其他可用的 SK 连接器不同，后者同时面向 net8.0 和 netstandard2.0）。

另一种方法是使用 Entity Framework 6，它可以同时面向 net8.0 和 netstandard2.0，但此版本的 Entity Framework 不再积极开发。Entity Framework Core 提供不会在 EF6 中实现的新功能。

来源： 
- https://learn.microsoft.com/en-us/ef/core/miscellaneous/platforms
- https://learn.microsoft.com/en-us/ef/efcore-and-ef6/

### 当前 SK 连接器的存在

考虑到 Semantic Kernel 已经与数据库进行了一些集成，这些数据库也是 Entity Framework 支持的，因此有多种选择如何继续：
- 同时支持 Entity Framework 和 DB 连接器（例如 `Microsoft.SemanticKernel.Connectors.EntityFramework` 和 `Microsoft.SemanticKernel.Connectors.MongoDB`）- 在这种情况下，两个连接器应产生完全相同的结果，因此需要额外的工作（例如实施相同的单元/集成测试集）来确保此状态。此外，对 logic 的任何修改都应在两个 connector 中应用。 
- 仅支持一个实体框架连接器（例如 `Microsoft.SemanticKernel.Connectors.EntityFramework`） - 在这种情况下，应删除现有 DB 连接器，这可能是对现有客户的重大更改。还需要执行额外的工作，以确保 Entity Framework 涵盖与以前的 DB 连接器完全相同的功能集。
- 仅支持一个 DB 连接器（例如 `Microsoft.SemanticKernel.Connectors.MongoDB`） - 在这种情况下，如果此类连接器已存在 - 则不需要其他工作。如果此类连接器不存在且添加它很重要，则需要执行其他工作才能实现该 DB 连接器。


支持 Entity Framework 和 Semantic Kernel 数据库的表 （仅适用于支持向量搜索的数据库） ：

|数据库引擎|维护者 / 供应商|在 EF 中受支持|在 SK 中受支持|更新至 SK memory v2 设计
|-|-|-|-|-|
|Azure Cosmos|Microsoft|是的|是的|是的|
|Azure SQL 和 SQL Server|Microsoft|是的|是的|不|
|SQLite|Microsoft|是的|是的|不|
|PostgreSQL 数据库|Npgsql 开发团队|是的|是的|不|
|MongoDB 数据库|MongoDB 数据库|是的|是的|不|
|MySQL （MySQL的|神谕|是的|不|不|
|Oracle 数据库|神谕|是的|不|不|
|Google Cloud Spanner|Cloud Spanner 生态系统|是的|不|不|

**注意**：
一个数据库引擎可以有多个实体框架集成，这些集成可以由不同的供应商维护（例如，有 2 个 MySQL EF NuGet 包 - 一个由 Oracle 维护，另一个由 Pomelo Foundation Project 维护）。

Vector DB 连接器，它们在 Semantic Kernel 中额外支持：
- Azure AI 搜索
- 色度
- 米尔沃斯
- 松果
- Qdrant
- 雷迪斯
- 维维亚特

来源：
- https://learn.microsoft.com/en-us/ef/core/providers/?tabs=dotnet-core-cli#current-providers

## 考虑的选项

- 添加新 `Microsoft.SemanticKernel.Connectors.EntityFramework` 连接器。
- 不要添加 `Microsoft.SemanticKernel.Connectors.EntityFramework` 连接器，但需要时为单个数据库添加新的连接器。

## 决策结果

根据上述调查，决定不添加 Entity Framework 连接器，而是在需要时为单个数据库添加新连接器。做出此决定的原因是，实体框架提供程序并不统一支持集合管理作，并且需要特定于数据库的代码进行键处理和对象映射。这些因素将使使用 Entity Framework 连接器变得不可靠，并且不会抽象出基础数据库。此外，Entity Framework 支持但 Semantic Kernel 没有内存连接器的向量数据库的数量非常少。
