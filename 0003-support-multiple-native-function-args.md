# 添加对多种类型的多个原生函数参数的支持

## 上下文和问题陈述

使本机函数更接近正常的 C# 体验。

## 决策驱动因素

- 原生技能现在可以拥有任意数量的参数。这些参数由同名的上下文变量填充。 如果该名称不存在上下文变量，则如果通过属性或默认参数值提供默认值，则会用默认值填充它，或者如果没有，则函数将无法调用。如果第一个参数无法通过其名称或默认值获取 input，也可以从 “input” 填充第一个参数。
- 现在使用 .NET DescriptionAttribute 指定说明，使用 DefaultValueAttribute 指定 DefaultValue。 C# 编译器知道 DefaultValueAttribute，并确保所提供的值的类型与参数类型的类型相匹配。 现在，还可以使用可选参数值指定默认值。
- SKFunction 现在纯粹是一个标记属性，而不是用于敏感度。它的唯一目的是在导入技能时对哪些公共成员作为本机函数导入进行子集化。当直接从委托导入函数时，已经不需要该属性;从 MethodInfo 导入时，该要求也被取消了。
- SKFunctionContextParameterAttribute 已过时，随后将被删除。 使用 DescriptionAttribute、DefaultValueAttribute 和 SKName 属性。 在极少数情况下，方法需要访问其签名中未定义的变量，它可以在方法上使用 SKParameter 属性，该属性具有 Description 和 DefaultValue 可选属性。
- SKFunctionInputAttribute 已过时，随后将被删除。 改用 DescriptionAttribute、DefaultValueAttribute 和 SKName 属性（后者以“Input”作为名称）。但是，使用 SKName 的需求应该非常罕见。
- InvokeAsync 现在将捕获异常并将异常存储到上下文中。 这意味着本机技能应通过引发异常而不是直接与上下文交互来处理所有故障。
- 更新了名称选择启发式方法，以去除异步方法的“Async”后缀。 现在，在方法上使用的理由非常少 [SKName] 。
- 添加了对 ValueTasks 作为返回类型的支持，只是为了完整性，以便开发人员无需考虑它。它就是好用。
- 添加了在方法中接受 ILogger 或 CancellationToken 的功能;它们是从 SKContext 填充的。 这样，就几乎没有理由将 SKContext 传递到本机函数中。
- 添加了对非字符串参数的支持。支持所有 C# 基元类型和许多核心 .NET 类型，其相应的 TypeConverters 用于将字符串上下文变量分析为适当的类型。也可以使用使用 TypeConverterAttribute 属性的自定义类型，并且将根据需要使用关联的 TypeConverter。 它与 WinForms 等 UI 框架以及 ASP.NET MVC 使用的机制相同。
- 同样，添加了对非字符串返回类型的支持。

## 决策结果

[公关 1195](https://github.com/microsoft/semantic-kernel/pull/1195)

## 更多信息

**例**

_之前_：

```C#
[SKFunction("Adds value to a value")]
[SKFunctionName("Add")]
[SKFunctionInput(Description = "The value to add")]
[SKFunctionContextParameter(Name = "Amount", Description = "Amount to add")]
public Task<string> AddAsync(string initialValueText, SKContext context)
{
    if (!int.TryParse(initialValueText, NumberStyles.Any, CultureInfo.InvariantCulture, out var initialValue))
    {
        return Task.FromException<string>(new ArgumentOutOfRangeException(
            nameof(initialValueText), initialValueText, "Initial value provided is not in numeric format"));
    }

    string contextAmount = context["Amount"];
    if (!int.TryParse(contextAmount, NumberStyles.Any, CultureInfo.InvariantCulture, out var amount))
    {
        return Task.FromException<string>(new ArgumentOutOfRangeException(
            nameof(context), contextAmount, "Context amount provided is not in numeric format"));
    }

    var result = initialValue + amount;
    return Task.FromResult(result.ToString(CultureInfo.InvariantCulture));
}
```

_调整后_：

```C#
[SKFunction, Description("Adds an amount to a value")]
public int Add(
    [Description("The value to add")] int value,
    [Description("Amount to add")] int amount) =>
    value + amount;
```

**例**

_之前_：

```C#
[SKFunction("Wait a given amount of seconds")]
[SKFunctionName("Seconds")]
[SKFunctionInput(DefaultValue = "0", Description = "The number of seconds to wait")]
public async Task SecondsAsync(string secondsText)
{
    if (!decimal.TryParse(secondsText, NumberStyles.Any, CultureInfo.InvariantCulture, out var seconds))
    {
        throw new ArgumentException("Seconds provided is not in numeric format", nameof(secondsText));
    }

    var milliseconds = seconds * 1000;
    milliseconds = (milliseconds > 0) ? milliseconds : 0;

    await this._waitProvider.DelayAsync((int)milliseconds).ConfigureAwait(false);
}
```

_调整后_：

```C#
[SKFunction, Description("Wait a given amount of seconds")]
public async Task SecondsAsync([Description("The number of seconds to wait")] decimal seconds)
{
    var milliseconds = seconds * 1000;
    milliseconds = (milliseconds > 0) ? milliseconds : 0;

    await this._waitProvider.DelayAsync((int)milliseconds).ConfigureAwait(false);
}
```

**例**

_之前_：

```C#
[SKFunction("Add an event to my calendar.")]
[SKFunctionInput(Description = "Event subject")]
[SKFunctionContextParameter(Name = Parameters.Start, Description = "Event start date/time as DateTimeOffset")]
[SKFunctionContextParameter(Name = Parameters.End, Description = "Event end date/time as DateTimeOffset")]
[SKFunctionContextParameter(Name = Parameters.Location, Description = "Event location (optional)")]
[SKFunctionContextParameter(Name = Parameters.Content, Description = "Event content/body (optional)")]
[SKFunctionContextParameter(Name = Parameters.Attendees, Description = "Event attendees, separated by ',' or ';'.")]
public async Task AddEventAsync(string subject, SKContext context)
{
    ContextVariables variables = context.Variables;

    if (string.IsNullOrWhiteSpace(subject))
    {
        context.Fail("Missing variables input to use as event subject.");
        return;
    }

    if (!variables.TryGetValue(Parameters.Start, out string? start))
    {
        context.Fail($"Missing variable {Parameters.Start}.");
        return;
    }

    if (!variables.TryGetValue(Parameters.End, out string? end))
    {
        context.Fail($"Missing variable {Parameters.End}.");
        return;
    }

    CalendarEvent calendarEvent = new()
    {
        Subject = variables.Input,
        Start = DateTimeOffset.Parse(start, CultureInfo.InvariantCulture.DateTimeFormat),
        End = DateTimeOffset.Parse(end, CultureInfo.InvariantCulture.DateTimeFormat)
    };

    if (variables.TryGetValue(Parameters.Location, out string? location))
    {
        calendarEvent.Location = location;
    }

    if (variables.TryGetValue(Parameters.Content, out string? content))
    {
        calendarEvent.Content = content;
    }

    if (variables.TryGetValue(Parameters.Attendees, out string? attendees))
    {
        calendarEvent.Attendees = attendees.Split(new[] { ',', ';' }, StringSplitOptions.RemoveEmptyEntries);
    }

    this._logger.LogInformation("Adding calendar event '{0}'", calendarEvent.Subject);
    await this._connector.AddEventAsync(calendarEvent).ConfigureAwait(false);
}
```

_调整后_：

```C#
[SKFunction, Description("Add an event to my calendar.")]
public async Task AddEventAsync(
    [Description("Event subject"), SKName("input")] string subject,
    [Description("Event start date/time as DateTimeOffset")] DateTimeOffset start,
    [Description("Event end date/time as DateTimeOffset")] DateTimeOffset end,
    [Description("Event location (optional)")] string? location = null,
    [Description("Event content/body (optional)")] string? content = null,
    [Description("Event attendees, separated by ',' or ';'.")] string? attendees = null)
{
    if (string.IsNullOrWhiteSpace(subject))
    {
        throw new ArgumentException($"{nameof(subject)} variable was null or whitespace", nameof(subject));
    }

    CalendarEvent calendarEvent = new()
    {
        Subject = subject,
        Start = start,
        End = end,
        Location = location,
        Content = content,
        Attendees = attendees is not null ? attendees.Split(new[] { ',', ';' }, StringSplitOptions.RemoveEmptyEntries) : Enumerable.Empty<string>(),
    };

    this._logger.LogInformation("Adding calendar event '{0}'", calendarEvent.Subject);
    await this._connector.AddEventAsync(calendarEvent).ConfigureAwait(false);
}
```
