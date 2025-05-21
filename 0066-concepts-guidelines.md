
# 结构化概念

## 上下文和问题陈述

目前，概念画板项目已经有了很大的发展，许多样本并不一致地遵循结构化的模式或指南。

需要考虑重新审视我们的样本模式，以支持关键驱动因素。

本 ADR 首先建议我们可以遵循的规则，以使新概念遵循良好的模式，使它们易于理解、查找和描述。

Semantic Kernel 的受众差异很大 — 从专业开发人员、初学者到非开发人员。我们明白，确保示例和指南尽可能简单明了是我们的首要任务。

### 决策驱动因素

- 容易找到
- 易于理解
- 易于设置
- 易于执行

上述驱动因素侧重于确保我们遵循示例的良好实践、模式和结构，保证正确的文档，简化代码以便于理解，以及使用描述性类、方法和变量。

我们还了解确保我们的样品易于复制和粘贴（按“原样”工作）并尽可能顺畅的重要性。

## 溶液

将一组易于遵循的指南和良好实践应用于概念画板项目将有助于维护一个易于查找、理解、设置和执行的良好示例集合。

该指南将适用于概念画板项目的任何维护或新添加的示例。这些内容可以添加到概念画板项目中的新 CONTRIBUTING.md 文件中。

> [!注意]分析器已经确保的规则/约定未在下面的列表中提及。
> 
## 规则

### 示例类

Concepts 项目中的每个类都必须有一个 xmldoc 描述，说明所采样的内容，以及关于所采样内容的明确信息。

✅ 要有 xmldoc 描述，详细说明要采样的内容。

✅ 要为所需的包提供 xmldoc 备注。

✅ 请考虑使用 xmldoc remarks 来获取更多信息。

❌ 避免使用通用描述。

✅ DO 命名类至少包含两个单词，用下划线分隔 `First_Second_Third_Fourth`。

✅ DO name 类，并为 `First` 给定的概念或提供者名称保留单词（例如， `OpenAI_ChatCompletion`）。

当文件包含特定 的示例`<provider>`时，它应以 作为 `<provider>` 第一个单词 `<provider>` 。 此处还可以包括 runtime、platform、protocol 或 service 名称。

✅ 考虑命名 `Second` 和后面的单词，以创建最佳分组，例如， 
例如， `AzureAISearch_VectorStore_ConsumeFromMemoryStore`.

✅ 当单词超过两个时，请考虑使用从左到右的分组进行命名， 
例如， `AzureAISearch_VectorStore_ConsumeFromMemoryStore`： 对于 `AzureAISearch` Within `VectorStore` Grouping，有一个 `ConsumeFromMemoryStore` 示例。

### 示例方法

✅ 务必有一个 xmldoc 描述，详细说明当类具有多个 sample 方法时要采样的内容。

✅ DO 具有描述性方法名称，限制为 5 个单词，以下划线分隔， 
例如， `[Fact] public Task First_Second_Third_Fourth_Fifth()`.

❌ 不要对 Task 使用 `Async` suffix。

❌ 避免在方法签名中使用参数。

❌ 一个类中的样本数不能超过 3 个。需要时，将示例拆分为多个类。

### 法典

✅ 务必保持代码清晰简洁。在大多数情况下，变量名称和 API 应该是不言自明的。

✅ 考虑对大型示例方法的代码进行注释。

❌ 不要对变量、方法或类使用首字母缩略词或短名称。

❌ 避免对不属于示例文件的常见帮助程序类或方法的任何引用， 
例如，避免使用像 `BaseTest.OutputLastMessage`.

## 决策结果

待定
