# 将所有与 Memory 相关的逻辑移动到单独的 Plugin

## 上下文和问题陈述

与内存相关的逻辑位于不同的 C# 项目中：

- `SemanticKernel.Abstractions`
  - `IMemoryStore`
  - `ISemanticTextMemory`
  - `MemoryRecord`
  - `NullMemory`
- `SemanticKernel.Core`
  - `MemoryConfiguration`
  - `SemanticTextMemory`
  - `VolatileMemoryStore`
- `Plugins.Core`
  - `TextMemoryPlugin`

Property `ISemanticTextMemory Memory` 也是 type 的一部分 `Kernel` ，但 kernel 本身并不使用它。在 Plugins 中注入 Memory 功能需要此属性。目前， `ISemanticTextMemory` interface 是 的主要依赖项 `TextMemoryPlugin`，在某些示例中 `TextMemoryPlugin` 被初始化为 `new TextMemoryPlugin(kernel.Memory)`。

虽然这种方法适用于 Memory，但目前无法注入 `MathPlugin` 到其他 Plugin 中。遵循相同的方法并将 `Math` 属性添加到 `Kernel` 类型不是可扩展的解决方案，因为无法为每个可用的 Plugin 定义单独的属性。

## 决策驱动因素

1.  如果内核不使用 memory，则 `Kernel`memory 不应是 type 的属性。
2. 内存的处理方式应与其他插件或服务相同，这可能是特定插件可能需要的。
3. 应该有一种方法可以将内存功能注册到附加的 Vector DB 中，并将该功能注入到需要它的插件中。

## 决策结果

将所有与 Memory 相关的逻辑移动到名为 `Plugins.Memory` .这将允许简化 Kernel logic 并在需要的地方（其他插件）使用 Memory。

高级任务：

1. 将 Memory 相关代码移动到单独的项目中。
2. 实现一种在需要 Memory 的 Plugins 中注入 Memory 的方法。
3. 从 type 中删除 `Memory` property `Kernel` 。
