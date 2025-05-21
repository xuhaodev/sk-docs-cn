# 架构决策记录 （ADR）

架构决策 （AD） 是一种合理的软件设计选择，它解决了在架构上具有重要性的功能性或非功能性需求。架构决策记录 （ADR） 捕获单个 AD 及其基本原理。

有关更多信息， [请参阅](https://adr.github.io/)

## 我们如何使用 ADR 来跟踪技术决策？

1. 将 docs/decisions/adr-template.md 复制到 docs/decisions/NNNN-title-with-dashes.md，其中 NNNN 表示序列中的下一个数字。
    1. 检查现有 PR 以确保使用正确的序列号。
    2. 还有一个简短的模板 docs/decisions/adr-short-template.md
2. 编辑 NNNN-title-with-dashes.md。
    1. Status 最初必须为 `proposed`
    2. 列表 `deciders` 必须包括将签署决策的人员的 github ID。
    3. 相关的 EM 和架构师必须被列为决策者或被告知所有决策。
    4. 您应该列出在决策过程中咨询的所有合作伙伴的名称或 github ID。
    5. 保持 `deciders` 简短的列表。您还可以列出参与 `consulted` 或 `informed` 涉及该决策的人员。
3. 对于每个选项，列出每个考虑的替代方案的好、中立和坏方面。
    1. 详细的调查可以包含在 `More Information` 内联部分或作为外部文档的链接。
4. 与决策者和其他相关方分享您的 PR。
   1. 决策程序必须列为必需的审阅者。
   2. 一旦达成决定，则必须将状态更新为`accepted`，并且还必须更新日期。
   3. 使用 PR 批准来捕获对决策的批准。
5. 决定可以在以后更改并被新的 ADR 取代。在这种情况下，在原始 ADR 中记录任何负面结果是有用的。
