
# Semantic Kernel 中的结构化数据插件实现

## 上下文和问题陈述

现代 AI 应用程序通常需要在利用 LLM 功能的同时与数据库中的结构化数据进行交互。由于 Semantic Kernel 的核心侧重于 AI 编排，因此我们需要一种标准化的方法将数据库作与 AI 功能集成。该 ADR 提出了一个实验性的 StructuredDataConnector 作为数据库-AI 集成的初始解决方案，专注于基本的 CRUD作和简单的查询。

## 决策驱动因素

- 需要与 SK 进行初始数据库集成模式
- 基本可组合 AI 和数据库作的要求
- 与 SK 的插件架构保持一致
- 能够通过实际使用来验证方法
- 支持强类型架构验证
- 用于 AI 交互的一致 JSON 格式

## 主要优点

1. **基于插件的架构**

   - 与 SK 的插件架构保持一致
   - 支持常见作的扩展方法
   - 利用 KernelJsonSchema 实现类型安全

2. **结构化数据作**

   - 使用架构验证的 CRUD作
   - 基于 JSON 的交互，格式正确
   - 类型安全的数据库作

3. **集成功能**

   - 内置 JSON 架构生成
   - 自动类型转换
   - 打印精美的 JSON，实现更好的 AI 交互

## 实现细节

实现包括：

1. 核心组件：

   - `StructuredDataService<TContext>`：用于数据库作的基本服务
   - `StructuredDataServiceExtensions`：CRUD作的扩展方法
   - `StructuredDataPluginFactory`：用于创建 SK 插件的工厂
   - 集成 `KernelJsonSchema` for 类型验证

2. 主要特点：

   - 从实体类型自动生成架构
   - 格式正确的 JSON 响应
   - 基于扩展的架构，可实现可维护性
   - 对 Entity Framework Core 的支持

3. 使用示例：

```csharp
var service = new StructuredDataService<ApplicationDbContext>(dbContext);
var plugin = StructuredDataPluginFactory.CreateStructuredDataPlugin<ApplicationDbContext, MyEntity>(
    service,
    operations: StructuredDataOperation.Default);
```

## 决策结果

选项： 待定：

1. 提供标准化的数据库集成
2. 利用 SK 的 schema 验证功能
3. 支持为 AI 交互提供正确的 JSON 格式
4. 通过生成的架构维护类型安全
5. 遵循既定的 SK 模式和原则

## 更多信息

这是一种实验性方法，将根据社区反馈进行改进。
