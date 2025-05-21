
# 使用 Markdown Any Decision Records 跟踪 Semantic Kernel 架构决策

## 上下文和问题陈述

我们正在积极开发多种不同语言版本的语义内核，即 C#、Python、Java 和 Typescript。
我们需要一种方法来使实现与关键架构决策保持一致，例如，我们正在审查对用于存储的格式的更改
semantic function configuration （config.json） 的 intent 函数配置，当此更改达成一致时，它必须反映在所有 Semantic Kernel 实现中。

MADR 是一个精益模板，用于以结构化的方式捕获任何决策。该模板起源于捕获架构决策，并发展为允许捕获所做出的任何决策的模板。
有关更多信息， [请参阅](https://adr.github.io/)

<!-- This is an optional element. Feel free to remove. -->

## 决策驱动因素

- 架构更改和相关的决策过程应该对社区透明。
- 决策记录存储在存储库中，涉及各种语言端口的团队可以轻松发现。

## 考虑的选项

- 使用 MADR 格式并将决策文档存储在存储库中。

## 决策结果

已选择选项：

## 选项的优缺点

### 使用 MADR 格式并将决策文档存储在存储库中

我们将如何使用 ADR 来跟踪技术决策？

1. 将 docs/decisions/adr-template.md 复制到 docs/decisions/NNNN-title-with-dashes.md，其中 NNNN 表示序列中的下一个数字。
   1. 检查现有 PR 以确保使用正确的序列号。
   2. 还有一个简短的模板 docs/decisions/adr-short-template.md
2. 编辑 NNNN-title-with-dashes.md。
   1. Status 最初必须为 `proposed`
   2. 列表 `deciders` 必须包括将签署决定的人员的别名。
   3. 相关的 EM 必须 `dluc` 被列为决策者或被告知所有决定。
   4. 您应该列出在决策过程中咨询的所有合作伙伴的别名。
3. 对于每个选项，列出每个考虑的替代方案的好、中立和坏方面。
   1. 详细的调查可以包含在 `More Information` 内联部分或作为外部文档的链接。
4. 与决策者和其他相关方分享您的 PR。
   1. 决策程序必须列为必需的审阅者。
   2. 一旦达成决定，则必须将状态更新为`accepted`，并且还必须更新日期。
   3. 使用 PR 批准来捕获对决策的批准。
5. 决定可以在以后更改并被新的 ADR 取代。在这种情况下，在原始 ADR 中记录任何负面结果是有用的。

- 很好，因为轻量级格式易于编辑
- 很好，因为这使用标准的 Git 审核流程进行注释和审批
- 很好，因为决策和审核流程对社区是透明的
