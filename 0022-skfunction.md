
# 语义内核函数是使用 Interface 或 Abstract Base Class 定义的

## 上下文和问题陈述

语义内核必须定义一个抽象来表示一个函数，即一个可以作为 AI 编排的一部分调用的方法。
目前，这个抽象是 `ISKFunction` interface。
ADR 的目标是确定这是否是用于满足 Semantic Kernel 长期目标的最佳抽象。

## 决策驱动因素

- 抽象 **必须** 可扩展，以便以后可以添加新功能。
- 对抽象的更改 **不得** 导致使用者的中断性变更。
- 目前尚不清楚我们是否需要允许消费者提供他们自己的 `SKFunction` implementation。如果我们这样做，这可能会导致问题，因为我们向 Semantic Kernel 添加新功能，例如，如果我们定义一个新的钩子类型怎么办？

## 考虑的选项

- `ISKFunction` 接口
- `SKFunction` 基类

### `ISKFunction` 接口

- 很好，因为实现可以扩展任何任意类
- 不好，因为我们只能更改 implementations 的默认行为，而 customer implementations 可能会变得不兼容。
- 糟糕，因为我们无法阻止客户实施此接口。
- 糟糕，因为对界面的更改对使用者来说是破坏性的更改。

### `SKFunction` 案例类

- 很好，因为对界面的更改不会 **** 对使用者造成重大影响。
- 很好，因为可以创建类构造函数 `internal` ，这样我们就可以阻止扩展，直到我们知道有有效的用例。
- 很好，因为我们将来可以很容易地更改默认实现。
- 不好，因为 implementations 只能扩展 `SKFunction`.

## 决策结果

选择的选项： “`SKFunction` base class”，因为我们可以提供一些默认实现，并且可以限制新 SKFunction 的创建，直到我们更好地理解这些用例。
