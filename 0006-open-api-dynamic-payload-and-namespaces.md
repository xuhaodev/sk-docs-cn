
# 用于 PUT 和 POST RestAPI作和参数命名空间的动态有效负载构建

## 上下文和问题陈述

目前，SK OpenAPI 不允许为 PUT 和 POST RestAPI作动态创建有效负载/正文，即使所有必需的元数据都可用。该功能最初未完全开发并最终被删除的原因之一是 PUT 和 POST RestAPI作的 JSON 有效负载/正文内容可能包含在不同级别具有相同名称的属性。目前尚不清楚如何从上下文变量的平面列表中明确解析它们的值。该功能尚未添加的另一个原因是，“payload”上下文变量以及 RestAPI作数据契约模式（OpenAPI、JSON 模式、Typings？）应该足以让 LLM 提供完全充实的 JSON payload/body 内容，而无需动态构建它。

<!-- This is an optional element. Feel free to remove. -->

## 决策驱动因素

- 创建一种机制，以便为 PUT 和 POST RestAPI作动态构建有效负载/正文。
- 开发一种机制（命名空间），允许在不同级别区分 PUT 和 POST RestAPI作具有相同名称的有效负载属性。
- 旨在最大限度地减少中断性变更并尽可能保持代码的向后兼容性。

## 考虑的选项

- 默认情况下，启用动态创建有效负载和/或命名空间。
- 启用基于配置的动态创建有效负载和/或命名空间。

## 决策结果

所选选项：“Enable the dynamic creation of payload and based on configuration”。此选项使内容保持兼容，因此更改不会影响任何 SK 使用者代码。此外，它还允许 SK Consumer 代码轻松控制这两种机制，并根据场景打开或关闭它们。

## 其他详细信息

### 启用有效负载的动态创建

为了能够为 PUT 和 POST RestAPI作动态创建 payloads/body，请将 `EnableDynamicPayload` `OpenApiSkillExecutionParameters` 执行参数的属性设置为 `true` 在导入 AI 插件时：

```csharp
var plugin = await kernel.ImportPluginFunctionsAsync("<skill name>", new Uri("<chatGPT-plugin>"), new OpenApiSkillExecutionParameters(httpClient) { EnableDynamicPayload = true });
```

要为需要有效负载的 RestAPI作动态构造有效负载，如下所示：

```json
{
  "value": "secret-value",
  "attributes": {
    "enabled": true
  }
}
```

请在 context variables collection 中注册以下参数：

```csharp
var contextVariables = new ContextVariables();
contextVariables.Set("value", "secret-value");
contextVariables.Set("enabled", true);
```

### 启用命名空间

要启用命名空间，请在 `EnablePayloadNamespacing` 导入 AI 插件时`OpenApiSkillExecutionParameters`将执行参数 `true` 的属性设置为 to：

```csharp
var plugin = await kernel.ImportPluginFunctionsAsync("<skill name>", new Uri("<chatGPT-plugin>"), new OpenApiSkillExecutionParameters(httpClient) { EnablePayloadNamespacing = true });
```

请记住，命名空间机制依赖于使用父参数名称作为参数名称的前缀，以点分隔。因此，在将 'namespaced' 参数名称添加到上下文变量时，请使用 'namespaced' 参数名称。让我们考虑一下这个 JSON：

```json
{
  "upn": "<sender upn>",
  "receiver": {
    "upn": "<receiver upn>"
  },
  "cc": {
    "upn": "<cc upn>"
  }
}
```

它包含 `upn` 不同级别的属性。参数 （属性值） 的参数注册将如下所示：

```csharp
var contextVariables = new ContextVariables();
contextVariables.Set("upn", "<sender-upn-value>");
contextVariables.Set("receiver.upn", "<receiver-upn-value>");
contextVariables.Set("cc.upn", "<cc-upn-value>");
```
