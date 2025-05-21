
# Planner 遥测增强功能

## 上下文和问题陈述

对于使用 Semantic Kernel 规划功能的应用程序来说，能够持续监控规划器和计划的性能并对其进行调试将是非常有益的。

## 场景

Contoso 是一家使用 SK 开发 AI 应用程序的公司。

1. Contoso 需要持续监控特定规划者的令牌使用情况，包括提示令牌、完成令牌和总令牌。
2. Contoso 需要持续监视特定规划者创建计划所需的时间。
3. Contoso 需要持续监视特定规划者创建有效计划的成功率。
4. Contoso 需要持续监视成功执行的特定计划类型的成功率。
5. Contoso 希望能够查看特定 Planner 运行的令牌使用情况。
6. Contoso 希望能够查看创建特定计划程序运行计划所花费的时间。
7. Contoso 希望能够查看计划中的步骤。
8. Contoso 希望能够查看每个计划步骤的输入和输出。
9. Contoso 想要更改一些可能影响规划器性能的设置。他们想知道在提交更改之前性能将受到什么影响。
10. Contoso 希望更新到更便宜、更快速的新模型。他们想知道新模型在规划任务中的执行情况。

## 超出范围

1. 我们提供了一个有关如何将遥测数据发送到 Application Insights 的示例。尽管技术上支持其他遥测服务选项，但我们不会介绍在此 ADR 中设置这些选项的可能方法。
2. 本 ADR 并不寻求修改 SK 中的当前仪表设计。
3. 我们不考虑不返回令牌使用情况的服务。

## 决策驱动因素

- 框架应与 Telemetry Service 无关。
- SK 应发出以下指标：
  - 输入提示 （Prompt） 的令牌使用情况
    - 说明：提示是使用令牌 （） 的最小单位`KernelFunctionFromPrompt`。
    - 维度：ComponentType、ComponentName、Service ID、Model ID
    - 类型： 直方图
    - 例：
      | 组件类型 | 组件名称 | 服务 ID | 型号 ID | 价值 |
      |---|---|---|---|---|
      | 功能 | 写诗 | | GPT-3.5-涡轮增压 | 40
      | 功能 | TellJoke 公司 | | GPT-4 的 | 50
      | 功能 | WriteAndTellJoke （写入和讲述笑话） | | GPT-3.5-涡轮增压 | 30
      | 计划 | CreateHandlebarsPlan | | GPT-3.5-涡轮增压 | 100
  - 提示 （Completion） 的输出令牌使用情况
    - 说明：提示是使用令牌 （） 的最小单位`KernelFunctionFromPrompt`。
    - 维度：ComponentType、ComponentName、Service ID、Model ID
    - 类型： 直方图
    - 例：
      | 组件类型 | 组件名称 | 服务 ID | 型号 ID | 价值 |
      |---|---|---|---|---|
      | 功能 | 写诗 | | GPT-3.5-涡轮增压 | 40
      | 功能 | TellJoke 公司 | | GPT-4 的 | 50
      | 功能 | WriteAndTellJoke （写入和讲述笑话） | | GPT-3.5-涡轮增压 | 30
      | 计划 | CreateHandlebarsPlan | | GPT-3.5-涡轮增压 | 100
  - 函数的聚合执行时间
    - 描述：一个函数可以由零个或多个提示组成。函数的执行时间是函数调用从开始到结束的持续时间 `invoke` 。
    - 维度：ComponentType、ComponentName、Service ID、Model ID
    - 类型： 直方图
    - 例：
      | 组件类型 | 组件名称 | 价值 |
      |---|---|---|
      | 功能 | 写诗 | 1 分钟
      | 功能 | TellJoke 公司 | 1 分钟
      | 功能 | WriteAndTellJoke （写入和讲述笑话） | 1.5 米
      | 计划 | CreateHandlebarsPlan | 2 分钟
  - 规划器的成功/失败计数
    - 描述：当 Planner 生成有效计划时，它被视为成功。当模型响应成功解析为所需格式的计划并且它包含一个或多个步骤时，计划有效。
    - 维度：ComponentType、ComponentName、Service ID、Model ID
    - 类型： 计数器
    - 例：
      | 组件类型 | 组件名称 | 失败 | 成功
      |---|---|---|---|
      | 计划 | CreateHandlebarsPlan | 5 | 95
      | 计划 | 创建 HSequentialPlan | 20 | 80
  - 计划的成功/失败计数
    - 描述：当计划中的所有步骤都成功执行时，计划执行被视为成功。
    - 维度：ComponentType、ComponentName、Service ID、Model ID
    - 类型： 计数器
    - 例：
      | 组件类型 | 组件名称 | 失败 | 成功
      |---|---|---|---|
      | 计划 | 车把平面图 | 5 | 95
      | 计划 | SequentialPlan 计划 | 20 | 80

## 考虑的选项

- 函数钩子
  - 将 logic 注入到将在调用函数之前或之后执行的函数。
- 仪表
  - 伐木
  - 指标
  - 痕迹

## 其他注意事项

SK 目前跟踪连接器中的令牌使用指标;但是，这些指标未分类。因此，开发人员无法确定不同作的 Token 使用情况。为了解决这个问题，我们提出了以下两种方法：

- 自下而上：将令牌使用信息从连接器传播回函数。
- 自上而下：将函数信息向下传播到连接器，使它们能够使用函数信息标记指标项。

我们决定实施自下而上的方法，原因如下：

1. SK 已配置为通过 `ContentBase`.我们只需要扩展需要传播的项目列表，例如模型信息。
2. 目前，SK 没有将函数信息向下传递到连接器级别的方法。尽管我们考虑使用 [行李](https://opentelemetry.io/docs/concepts/signals/baggage/#:~:text=In%20OpenTelemetry%2C%20Baggage%20is%20contextual%20information%20that%E2%80%99s%20passed,available%20to%20any%20span%20created%20within%20that%20trace.) 作为向下传播信息的一种方式，但出于安全考虑，OpenTelemetry 团队的专家建议不要使用这种方法。

使用自下而上的方法，我们需要从元数据中检索令牌使用信息：

```csharp
// Note that not all services support usage details.
/// <summary>
/// Captures usage details, including token information.
/// </summary>
private void CaptureUsageDetails(string? modelId, IDictionary<string, object?>? metadata, ILogger logger)
{
  if (string.IsNullOrWhiteSpace(modelId))
  {
    logger.LogWarning("No model ID provided to capture usage details.");
    return;
  }

  if (metadata is null)
  {
    logger.LogWarning("No metadata provided to capture usage details.");
    return;
  }

  if (!metadata.TryGetValue("Usage", out object? usageObject) || usageObject is null)
  {
    logger.LogWarning("No usage details provided to capture usage details.");
    return;
  }

  var promptTokens = 0;
  var completionTokens = 0;
  try
  {
    var jsonObject = JsonSerializer.Deserialize<JsonElement>(JsonSerializer.Serialize(usageObject));
    promptTokens = jsonObject.GetProperty("PromptTokens").GetInt32();
    completionTokens = jsonObject.GetProperty("CompletionTokens").GetInt32();
  }
  catch (Exception ex) when (ex is KeyNotFoundException)
  {
    logger.LogInformation("Usage details not found in model result.");
  }
  catch (Exception ex)
  {
    logger.LogError(ex, "Error while parsing usage details from model result.");
    throw;
  }

  logger.LogInformation(
    "Prompt tokens: {PromptTokens}. Completion tokens: {CompletionTokens}.",
    promptTokens, completionTokens);

  TagList tags = new() {
    { "semantic_kernel.function.name", this.Name },
    { "semantic_kernel.function.model_id", modelId }
  };

  s_invocationTokenUsagePrompt.Record(promptTokens, in tags);
  s_invocationTokenUsageCompletion.Record(completionTokens, in tags);
}
```

> 请注意，我们不考虑不返回令牌使用情况的服务。目前只有OpenAI和Azure OpenAI服务返回令牌使用信息。

## 决策结果

1. 新指标名称：
   | 米 | 指标 |
   |---|---|
   |Microsoft.SemanticKernel.Planning| <ul><li>semantic_kernel.planning.invoke_plan.duration</li></ul> |
   |Microsoft.SemanticKernel 内核| <ul><li>semantic_kernel.function.invocation.token_usage.prompt</li><li>semantic_kernel.function.invocation.token_usage.completion</li></ul> |
   > 注意：我们还会将所有现有量度的“sk”前缀替换为“semantic_kernel”，以避免歧义。
2. 仪表

## 验证

可以添加测试以确保所有预期的遥测项都已就位且格式正确。

## 描述 选项

### 函数钩子

函数钩子允许开发人员将逻辑注入内核，这些逻辑将在调用函数之前或之后执行。示例使用案例包括在调用函数之前记录函数输入，以及在函数返回后记录结果。
有关更多信息，请参阅以下 ADR：

1. [内核钩子阶段 1](./0005-kernel-hooks-phase1.md)
2. [内核钩子阶段 2](./0018-kernel-hooks-phase2.md)

我们可以在函数注册期间注入默认回调来记录所有函数的关键信息。

优点：

1. 为开发人员提供最大的曝光率和灵活性。即，应用程序开发人员可以通过添加更多回调来非常轻松地记录单个函数的附加信息。

缺点：

1. 不创建量度，需要额外的工作来聚合结果。
2. 仅依赖日志不会提供跟踪详细信息。
3. 日志的修改频率更高，这可能会导致实施不稳定，并且需要额外的维护。
4. 钩子只能访问有限的函数数据。

> 注意：由于 SK 中已经实现了分布式跟踪，开发人员可以在 hook 中创建自定义遥测数据，只要 hook 中的信息可用，这些遥测数据将在配置后发送到遥测服务。但是，在 hook 内创建的遥测项不会作为父子关系与函数相关联，因为它们不在函数的范围内。

### 分布式跟踪

分布式跟踪是一种诊断技术，可以定位分布式应用程序中的故障和性能瓶颈。.Net 具有对在库中添加分布式跟踪的本机支持，并且 .Net 库还经过检测以自动生成分布式跟踪信息。

有关更多信息，请参阅此文档： [.Net 分布式跟踪](https://learn.microsoft.com/en-us/dotnet/core/diagnostics/)

总体优点：

1. 本机 .Net 支持。
2. 分布式跟踪已在 SK 中实现。我们只需要添加更多的遥测数据。
3. 遥测服务与 [OpenTelemetry 无关](https://opentelemetry.io/docs/what-is-opentelemetry/)。

总体缺点：

1. 使用 SK 作为库的应用程序开发人员添加自定义跟踪和指标的灵活性较低。

#### 伐木

日志将用于在代码运行时记录有趣的事件。

```csharp
// Use LoggerMessage attribute for optimal performance
this._logger.LogPlanCreationStarted();
this._logger.LogPlanCreated();
```

#### [指标](https://learn.microsoft.com/en-us/dotnet/core/diagnostics/metrics)

指标将用于记录加班的测量值。

```csharp
/// <summary><see cref="Meter"/> for function-related metrics.</summary>
private static readonly Meter s_meter = new("Microsoft.SemanticKernel");

/// <summary><see cref="Histogram{T}"/> to record plan execution duration.</summary>
private static readonly Histogram<double> s_planExecutionDuration =
  s_meter.CreateHistogram<double>(
    name: "semantic_kernel.planning.invoke_plan.duration",
    unit: "s",
    description: "Duration time of plan execution.");

TagList tags = new() { { "semantic_kernel.plan.name", planName } };

try
{
  ...
}
catch (Exception ex)
{
  // If a measurement is tagged with "error.type", then it's a failure.
  tags.Add("error.type", ex.GetType().FullName);
}

s_planExecutionDuration.Record(duration.TotalSeconds, in tags);
```

#### [痕迹](https://learn.microsoft.com/en-us/dotnet/core/diagnostics/distributed-tracing)

活动用于通过应用程序跟踪依赖关系，将其他组件完成的工作关联起来，并形成一个称为跟踪的活动树。

```csharp
ActivitySource s_activitySource = new("Microsoft.SemanticKernel");

// Create and start an activity
using var activity = s_activitySource.StartActivity(this.Name);

// Use LoggerMessage attribute for optimal performance
logger.LoggerGoal(goal);
logger.LoggerPlan(plan);
```

> 注意：跟踪日志将包含敏感数据，应在生产环境中关闭：https://learn.microsoft.com/en-us/dotnet/core/extensions/logging?tabs=command-line#log-level

## 应用程序如何将遥测数据发送到 Application Insights 的示例

```csharp
using var traceProvider = Sdk.CreateTracerProviderBuilder()
  .AddSource("Microsoft.SemanticKernel*")
  .AddAzureMonitorTraceExporter(options => options.ConnectionString = connectionString)
  .Build();

using var meterProvider = Sdk.CreateMeterProviderBuilder()
  .AddMeter("Microsoft.SemanticKernel*")
  .AddAzureMonitorMetricExporter(options => options.ConnectionString = connectionString)
  .Build();

using var loggerFactory = LoggerFactory.Create(builder =>
{
  // Add OpenTelemetry as a logging provider
  builder.AddOpenTelemetry(options =>
  {
    options.AddAzureMonitorLogExporter(options => options.ConnectionString = connectionString);
    // Format log messages. This is default to false.
    options.IncludeFormattedMessage = true;
  });
  builder.SetMinimumLevel(MinLogLevel);
});
```

## 更多信息

需要完成的其他工作：

1. 更新 [遥测文档](../../dotnet/docs/TELEMETRY.md)
