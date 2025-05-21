# Java 文件夹结构

## 上下文和问题陈述

该分支正在开发 Semantic Kernel 到 Java 的移植 `experimental-java` 。使用的文件夹结构与 .Net 实现不同。
此 ADR 的目的是记录 Java 端口将使用的文件夹结构，以便开发人员清楚地了解如何在 .Net 和 Java 实现之间导航。

## 决策驱动因素

* 目标是学习已经拥有出色多语言支持的 SDK，例如 [Azure SDK](https://github.com/Azure/azure-sdk/)
* Java SK 应遵循 Java 的一般设计准则和约定。对于 Java 开发人员来说，这应该感觉很自然。
* 不同的语言版本应与 .Net 实现一致。在发生冲突的情况下，与 Java 约定的一致性是最高优先级。
* SK for Java 和 .Net 应该感觉像是由单个团队开发的单个产品。
* Java 和 .Net 之间应该具有同等功能。必须在 FEATURE_MATRIX 中跟踪功能状态 [](../../FEATURE_MATRIX.md)

## 考虑的选项

以下是 .Net 和 Java 文件夹结构的比较

```bash
dotnet/src
           Connectors
           Extensions
           IntegrationTests
           InternalUtilities
           SemanticKernel.Abstractions
           SemanticKernel.MetaPackage
           SemanticKernel.UnitTests
           SemanticKernel
           Skills
```

| 文件夹                         | 描述 |
|--------------------------------|-------------|
| 连接                     | 各种 Connector 实现的父文件夹，例如 AI 或内存服务 |
| 扩展                     | SK 扩展的父文件夹，例如 planner 实现 |
| 集成测试               | 集成测试 |
| 内部实用程序              | 内部工具，即共享代码 |
| SemanticKernel.Abstractions    | SK API 定义 |
| SemanticKernel.MetaPackage     | SK common 包集合 |
| SemanticKernel.UnitTests       | 单元测试 |
| SemanticKernel 内核                 | SK 实现 |
| 技能                         | 各种技能实现的父文件夹，例如 Core、MS Graph、GRPC、OpenAI 等 |

一些观察：

* 文件夹 `src` 位于文件夹结构的最开头，这会降低灵活性
* 该术语的使用 `Skills` 是由于变化

```bash
java
     api-test
     samples
     semantickernel-api
     semantickernel-bom
     semantickernel-connectors-parent
     semantickernel-core-skills
     semantickernel-core
     semantickernel-extensions-parent
```

| 文件夹                              | 描述 |
|-------------------------------------|-------------|
| `api-test`                          | 集成测试和 API 使用示例 |
| `samples`                           | SK 样本 |
| `semantickernel-api`                | SK API 定义 |
| `semantickernel-bom`                | SK 物料清单 |
| `semantickernel-connectors-parent`  | 各种 Connector 实现的父文件夹 |
| `semantickernel-core-skills`        | SK 核心技能（在 .Net 中，这些是核心实现的一部分） |
| `semantickernel-core`               | SK core 实现 |
| `semantickernel-extensions-parent`  | SK 扩展的父文件夹，例如 planner implementation |

一些观察：

* 将小写文件夹名称与分隔符一起使用 `-` 是惯用的 Java
* 这些 `src` 文件夹的位置尽可能靠近源文件，例如， `semantickernel-api/src/main/java`这是惯用的 Java
* 单元测试与实现一起包含
* 样品位于 `java` 文件夹中，每个样品都独立运行

## 决策结果

请遵循以下准则：

* 文件夹名称将与使用的名称（或计划用于 .Net）的文件夹名称匹配，但符合惯用的 Java 文件夹命名约定
* 使用 `bom` 而不是 `MetaPackage` 后者，因为后者以 .Net 为中心
* 使用 `api` 而不是 `Abstractions` 后者，因为后者以 .Net 为中心
*  `semantickernel-core-skills` 移动到新 `plugins` 文件夹并重命名为 `plugins-core`
* 使用术语 `plugins` instead of `skills` and avoid introduce technical debt

| 文件夹                           | 描述 |
|----------------------------------|-------------|
| `connectors`                     | 包含： `semantickernel-connectors-ai-openai`， `semantickernel-connectors-ai-huggingface`， `semantickernel-connectors-memory-qadrant`， ...  |
| `extensions`                     | 包含： `semantickernel-planning-action-planner`， `semantickernel-planning-sequential-planner` |
| `integration-tests`              | 集成测试 |
| `semantickernel-api`             | SK API 定义 |
| `semantickernel-bom`             | SK common 包集合 |
| `semantickernel-core`            | SK core 实现 |
| `plugins`                        | 包含： `semantickernel-plugins-core`， `semantickernel-plugins-document`， `semantickernel-plugins-msgraph`， ... |
