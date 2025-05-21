
# 向 SKFunctions 和 Planners 提供更多类型信息

## 上下文和问题陈述

目前，Semantic Kernel 只保留少量有关 SKFunctions 参数的信息，而完全没有关于 SKFunction 输出的信息。这对我们的规划器的效率有很大的负面影响，因为无法充分描述插件函数的输入和输出的模式。

规划师依赖于对可用插件的描述，我们称之为 功能手册。将此视为提供给 LLM 的用户手册，旨在向 LLM 解释其可用的功能以及如何使用它们。我们的 Sequential 计划器中的当前 Functions Manual 示例如下所示：

```
DatePluginSimpleComplex.GetDate1:
  description: Gets the date with the current date offset by the specified number of days.
  inputs:
    - numDays: The number of days to offset the date by from today. Positive for future, negative for past.

WeatherPluginSimpleComplex.GetWeatherForecast1:
  description: Gets the weather forecast for the specified date and the current location, and time.
  inputs:
    - date: The date for the forecast
```

本函数手册介绍了 LLM 可用的两个插件函数，一个用于获取当前日期（以天为单位）偏移量，另一个用于获取给定日期的天气预报。我们的客户可能希望我们的规划人员能够使用这些插件功能回答一个简单的问题是“明天的天气预报是什么？创建并执行回答此问题的计划需要调用第一个函数，然后将其结果作为参数传递给第二个函数的调用。如果用伪代码编写，则计划将如下所示：

```csharp
var dateResponse = DatePluginSimpleComplex.GetDate1(1);
var forecastResponse = WeatherPluginSimpleComplex.GetWeatherForecast1(dateResponse);
return forecastResponse;
```

这似乎是一个合理的计划，这确实与 Sequential planner 提出的计划相当。只要第一个函数的未知返回类型恰好与第二个函数的未知参数类型匹配，这也可能有效。但是，我们提供给 LLM 的函数手册并未指定了解这些类型是否匹配的必要信息。

我们提供缺失类型信息的一种方法是使用 Json Schema。这也恰好与 OpenAPI 规范为输入和输出提供类型信息的方式相同，这为本地和远程插件提供了一个有凝聚力的解决方案。如果我们使用 Json Schema，那么我们的函数手册可以看起来更像这样：

```json
[
  {
    "name": "DatePluginSimpleComplex.GetDate1",
    "description": "Gets the date with the current date offset by the specified number of days.",
    "parameters": {
      "type": "object",
      "required": ["numDays"],
      "properties": {
        "numDays": {
          "type": "integer",
          "description": "The number of days to offset the date by from today. Positive for future, negative for past."
        }
      }
    },
    "responses": {
      "200": {
        "description": "Successful response.",
        "content": {
          "application/json": {
            "schema": {
              "type": "object",
              "properties": { "date": { "type": "string" } },
              "description": "The date."
            }
          }
        }
      }
    }
  },
  {
    "name": "WeatherPluginSimpleComplex.GetWeatherForecast1",
    "description": "Gets the weather forecast for the specified date and the current location, and time.",
    "parameters": {
      "type": "object",
      "required": ["date"],
      "properties": {
        "date": { "type": "string", "description": "The date for the forecast" }
      }
    },
    "responses": {
      "200": {
        "description": "Successful response.",
        "content": {
          "application/json": {
            "schema": {
              "type": "object",
              "properties": { "degreesFahrenheit": { "type": "integer" } },
              "description": "The forecasted temperature in Fahrenheit."
            }
          }
        }
      }
    }
  }
]
```

本函数手册提供了有关 LLM 有权访问的函数的输入和输出的更多信息。它允许看到第一个函数的输出是一个复杂的对象，其中包含第二个函数所需的信息。这也伴随着使用的令牌数量的增加，但是派生类型信息的功能增加超过了这笔费用。有了这些信息，我们现在可以期待 LLM 生成一个计划，其中包括了解如何从输出中提取值并将其传递给输入。我们在测试中使用的一种有效方法是要求 LLM 将输入指定为相应输出的 Json 路径。伪代码中显示的等效计划如下所示：

```csharp
var dateResponse = DatePluginSimpleComplex.GetDate1(1);
var forecastResponse = WeatherPluginSimpleComplex.GetWeatherForecast1(dateResponse.date);
return forecastResponse.degreesFahrenheit;
```

## 建议

为了能够生成完整的函数手册（如上面基于 Json 架构的示例），SKFunctions 及其关联的函数视图需要维护有关其参数类型和返回类型的更多信息。函数视图当前具有以下定义：

```csharp
public sealed record FunctionView(
    string Name,
    string PluginName,
    string Description = "",
    IReadOnlyList<ParameterView>? Parameters = null)
{
    /// <summary>
    /// List of function parameters
    /// </summary>
    public IReadOnlyList<ParameterView> Parameters { get; init; } = Parameters ?? Array.Empty<ParameterView>();
}
```

函数参数由 `ParameterView` 包含语义描述的对象集合描述，并提供添加更多类型信息的位置。但是，没有存在放置函数输出的类型信息和语义描述的位置。为了解决这个问题，我们将添加一个名为 `ReturnParameterView` `FunctionView`：

```csharp
public sealed record FunctionView(
    string Name,
    string PluginName,
    string Description = "",
    IReadOnlyList<ParameterView>? Parameters = null,
    ReturnParameterView? ReturnParameter = null)
{
    /// <summary>
    /// List of function parameters
    /// </summary>
    public IReadOnlyList<ParameterView> Parameters { get; init; } = Parameters ?? Array.Empty<ParameterView>();

    /// <summary>
    /// Function output
    /// </summary>
    public ReturnParameterView ReturnParameter { get; init; } = ReturnParameter ?? new ReturnParameterView();
}
```

`ParameterView` 对象当前包含一个 `ParameterViewType` 属性，该属性包含有关参数类型的一些信息，但仅限于 JSON 类型 （[字符串、数字、布尔值、null、对象、数组]），并且无法描述对象的结构。要添加所需的额外类型信息，我们可以添加 native `System.Type` 属性。这适用于本地函数，因为在导入 SKFunction 时，参数 Type 始终可以访问。从 LLM 响应中激活原生类型也需要它。但是，对于远程插件，对象的本机类型将是未知的，甚至可能不存在，因此没有 `System.Type` 帮助。对于这种情况，我们需要从 OpenAPI 规范中提取类型信息，并将其存储在允许以前未知架构的属性中。此属性类型的选项包括 `JsonSchema` OSS 库（如 JsonSchema.Net 或 NJsonSchema）、 `JsonDocument` System.Text.Json 或 `string` 包含 Json 序列化架构的选项。

| 类型                      | 优点                                                         | 缺点                                                       |
| ------------------------- | ------------------------------------------------------------ | ---------------------------------------------------------- |
| JsonSchema.Net.JsonSchema | 受欢迎且更新频繁，建立在 System.Net 之上 | 依赖于 SK Core 中的 OSS                       |
| NJsonShema.JsonSchema     | 非常受欢迎，更新频繁，长期项目            | 建立在 Json.Net 之上 （Newtonsoft）                      |
| Json文档              | 原生 C# 类型，快速灵活                            | 不是 Json Schema，而是 Schema 的 Json DOM 容器 |
| 字符串                    | 本机 C# 类型                                               | 不是 Json 架构或 Json DOM，类型提示非常糟糕      |

为避免在核心抽象项目中依赖第三方库，我们将使用一个 `JsonDocument` 类型来保存加载远程插件时创建的 Json Schemas。创建或提取这些架构所需的库可以包含在需要它们的包中，即 Functions.OpenAPI、Planners.Core 和 Connectors.AI.OpenAI。该 `NativeType` 属性将在加载本机函数时填充，并在需要时用于生成 Json Schema，以及用于从 planners 和语义函数中的 LLM 响应中激活本机类型。

```csharp
public sealed record ParameterView(
    string Name,
    string? Description = null,
    string? DefaultValue = null,
    ParameterViewType? Type = null,
    bool? IsRequired = null,
    Type? NativeType = null,
    JsonDocument? Schema = null);
```
