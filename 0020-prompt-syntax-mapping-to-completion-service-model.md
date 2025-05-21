# 提示语法到完成服务模型的映射

## 上下文和问题陈述
如今，SK 使用文本完成服务运行所有提示，只需将呈现的提示按原样直接传递给配置的文本完成服务/连接器，无需任何修改。随着新的聊天完成提示和可能的其他提示类型（例如图像）的添加，我们需要一种方法将特定于完成的提示语法映射到相应的完成服务数据模型。

例如， [ 聊天完成提示中的](https://github.com/microsoft/semantic-kernel/blob/main/docs/decisions/0014-chat-completion-roles-in-prompt.md)聊天完成语法：
```xml
<message role="system">
    You are a creative assistant helping individuals and businesses with their innovative projects.
</message>
<message role="user">
    I want to brainstorm the idea of {{$input}}
</message>
```
应映射到 [ 具有两条聊天消息的 ](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel.Abstractions/AI/ChatCompletion/ChatHistory.cs)ChatHistory 类的实例：

```csharp
var messages = new ChatHistory();
messages.Add(new ChatMessage(new AuthorRole("system"), "You are a creative assistant helping individuals and businesses with their innovative projects."));
messages.Add(new ChatMessage(new AuthorRole("user"), "I want to brainstorm the idea of {{$input}}"));
```

此 ADR 概述了提示语法映射功能位置的潜在选项。

## 考虑的选项
**1. 完成连接器类。** 此选项建议让完成连接器类负责 `prompt syntax -> completion service data model` 映射。关于此映射功能是在连接器类本身中实现还是委托给映射器类的决定应在实现阶段做出，这超出了此 ADR 的范围。

优点：
 -  `SemanticFunction`在添加新的完成类型连接器（音频、视频等）时，无需更改 即可支持新提示语法的映射。
 
 - 提示可以由
    - Kernel.RunAsync 
    - 完成连接器

缺点：
 - 每个新的补全连接器，无论是现有类型还是新类型，都必须实现映射功能

**2. SemanticFunction 类。** 此选项建议 `SemanticFunction` class 负责 Map。与前一个选项类似，此功能的确切位置（无论是在类中 `SemanticFunction` 还是在 mapper 类中）应在实现阶段确定。

优点：
 - 新类型的新连接器或现有连接器不必实现映射功能

缺点：
 -  `SemanticFunction` 每次 SK 需要支持新的补全类型时，都必须更改该类
 - 提示只能由 Kernel.RunAsync 方法运行。

## 决策结果
同意使用选项 1 - `1. Completion connector classes` 因为它是一种更灵活的解决方案，并且允许在不修改类的情况下添加新的连接器 `SemanticFunction` 。