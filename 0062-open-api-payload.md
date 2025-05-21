
# 为 OpenAPI 函数提供 payload

## 上下文和问题陈述
如今，SK OpenAPI 函数的有效负载可以由调用者提供，也可以由 SK 根据 OpenAPI 文档元数据和提供的参数动态构建。 

此 ADR 概述了 OpenAPI 功能当前用于处理有效负载的现有选项，并提出了一个新选项来简化复杂有效负载的动态创建。

## 在 SK 中处理有效负载的现有选项概述

### 1. 和 `payload` `content-type` 参数
此选项允许调用方创建符合 OpenAPI 架构的有效负载，并在调用时将其作为参数传递给 OpenAPI 函数。
```csharp
// Import an OpenAPI plugin with the createEvent function and disable dynamic payload construction
KernelPlugin plugin = await kernel.ImportPluginFromOpenApiAsync("<plugin-name>", new Uri("<plugin-uri>"), new OpenApiFunctionExecutionParameters 
{ 
    EnableDynamicPayload = false 
});

// Create the payload for the createEvent function
string payload = """
{
    "subject": "IT Meeting",
    "start": {
        "dateTime": "2023-10-01T10:00:00",
        "timeZone": "UTC"
    },
    "end": {
        "dateTime": "2023-10-01T11:00:00",
        "timeZone": "UTC"
    },
    "tags": [
        { "name": "IT" },
        { "name": "Meeting" }
    ]
}
""";

// Create arguments for the createEvent function
KernelArguments arguments = new ()
{
    ["payload"] = payload,
    ["content-type"] = "application/json"
};

// Invoke the createEvent function
FunctionResult functionResult = await kernel.InvokeAsync(plugin["createEvent"], arguments);
```

请注意，Semantic Kernel 不会以任何方式验证或修改有效负载。调用方有责任确保有效负载有效并符合 OpenAPI 架构。


### 2. 从 Leaf Properties 构建动态负载
此选项允许 SK 根据 OpenAPI 架构和提供的参数动态构建负载。
调用方在调用 OpenAPI 函数时不需要提供有效负载。但是，调用方必须提供参数
将用作同名 payload 属性的值。
```csharp
// Import an OpenAPI plugin with the createEvent function and disable dynamic payload construction
KernelPlugin plugin = await kernel.ImportPluginFromOpenApiAsync("<plugin-name>", new Uri("<plugin-uri>"), new OpenApiFunctionExecutionParameters 
{ 
    EnableDynamicPayload = true // It's true by default 
});

// Expected payload structure
//{
//    "subject": "...",
//    "start": {
//        "dateTime": "...",
//        "timeZone": "..."
//     },
//    "duration": "PT1H",
//    "tags":[{
//        "name": "...",
//      }
//    ],
//}

// Create arguments for the createEvent function
KernelArguments arguments = new()
{
    ["subject"] = "IT Meeting",
    ["dateTime"] = DateTimeOffset.Parse("2023-10-01T10:00:00"),
    ["timeZone"] = "UTC",
    ["duration"] = "PT1H",
    ["tags"] = new[] { new Tag("work"), new Tag("important") }
};

// Invoke the createEvent function
FunctionResult functionResult = await kernel.InvokeAsync(plugin["createEvent"], arguments);
```

此选项从根属性开始遍历有效负载架构，并在此过程中收集所有叶属性（没有任何子属性的属性）。
调用方必须为标识的叶属性提供参数，SK 将根据架构和提供的参数构建有效负载。

此选项在创建包含不同级别具有相同名称的属性的有效负载时存在限制。
考虑到导入过程会为每个 OpenAPI作创建一个内核函数，因此没有可行的方法可以创建具有多个具有相同名称的参数的内核函数。
尝试导入具有此类有效负载的插件将失败，并显示以下错误：“该函数具有两个或多个具有相同名称的参数 `<property-name>`。

此外，当两个或多个属性相互引用时，有效负载架构中可能会发生循环引用，从而创建循环。
SK 将检测此类循环引用并引发作导入失败的错误。

此选项的另一个特点是它不会遍历数组属性，而是将它们视为叶子属性。
这意味着调用方必须为数组类型的属性提供参数，但不能为数组元素或数组元素的属性提供参数。
在上面的示例中，对象数组应作为 “tags” 数组属性的参数提供。

### 3. 使用命名空间从叶属性构建动态有效负载
此选项解决了上述 dynamic payload construction 选项在不同级别处理具有相同名称的属性的限制。
它通过在子属性名称前加上其父属性名称来实现此目的，从而有效地创建唯一名称。
调用方仍需要为属性提供参数，SK 将完成其余工作。
```csharp
// Import an OpenAPI plugin with the createEvent function and disable dynamic payload construction
KernelPlugin plugin = await kernel.ImportPluginFromOpenApiAsync("<plugin-name>", new Uri("<plugin-uri>"), new OpenApiFunctionExecutionParameters 
{ 
    EnableDynamicPayload = true,
    EnablePayloadNamespacing = true
});


// Expected payload structure
//{
//    "subject": "...",
//    "start": {
//        "dateTime": "...",
//        "timeZone": "..."
//    },
//    "end": {
//        "dateTime": "...",
//        "timeZone": "..."
//    },
//    "tags":[{
//        "name": "...",
//      }
//    ],
//}

// Create arguments for the createEvent function
KernelArguments arguments = new()
{
    ["subject"] = "IT Meeting",
    ["start.dateTime"] = DateTimeOffset.Parse("2023-10-01T10:00:00"),
    ["start.timeZone"] = "UTC",
    ["end.dateTime"] = DateTimeOffset.Parse("2023-10-01T11:00:00"),
    ["end.timeZone"] = "UTC",
    ["tags"] = new[] { new Tag("work"), new Tag("important") }
};

// Invoke the createEvent function
FunctionResult functionResult = await kernel.InvokeAsync(plugin["createEvent"], arguments);
```

与上一个选项一样，此选项从根属性向下遍历有效负载架构以收集所有叶属性。遇到叶属性时，SK 会检查父属性。
如果存在父级，则叶属性名称前面会加上父级属性名称（用点分隔）以创建唯一名称。
例如，对象的`dateTime`属性 `start` 将被命名为 `start.dateTime`. 
   
此选项以与前一个相同的方式处理数组属性，将它们视为叶属性，这意味着调用者必须为它们提供参数。

此选项也容易受到有效负载架构中的循环引用的影响，如果 SK 检测到任何循环引用，它将使作导入失败。

## 在 SK 中处理有效负载的新选项

### 上下文和问题陈述
SK 不遗余力地处理动态构建有效负载的复杂性，并将这一责任从调用方那里分担出来。

但是，当有效负载包含不同级别的同名属性并且无法使用命名空间时，现有选项都不适用于复杂场景。

为了涵盖这些场景，我们提出了一个在 SK 中处理有效负载的新选项。

### 考虑的选项

- 选项 #4：从根属性中构造有效负载

### 选项 #4：从根属性构建动态负载

在某些情况下，有效负载包含具有相同名称的属性，并且由于各种原因无法使用命名空间。为了不卸载
将构建有效负载的责任交给调用者，SK 可以执行额外的步骤并从根属性中构造有效负载。由于建筑的复杂性
这些根属性的参数将位于调用方端，但如果不允许对不同级别具有相同名称的属性使用命名空间和参数，则 SK 无能为力
必须从 kernel 参数的平面列表中解析。

```csharp
// Import an OpenAPI plugin with the createEvent function and disable dynamic payload construction
KernelPlugin plugin = await kernel.ImportPluginFromOpenApiAsync("<plugin-name>", new Uri("<plugin-uri>"), new OpenApiFunctionExecutionParameters { EnableDynamicPayload = false, EnablePayloadNamespacing = true });

// Expected payload structure
//{
//    "subject": "...",
//    "start": {
//        "dateTime": "...",
//        "timeZone": "..."
//    },
//    "end": {
//        "dateTime": "...",
//        "timeZone": "..."
//    },
//    "tags":[{
//        "name": "...",
//      }
//    ],
//}

// Create arguments for the createEvent function
KernelArguments arguments = new()
{
    ["subject"] = "IT Meeting",
    ["start"] = new MeetingTime() { DateTime = DateTimeOffset.Parse("2023-10-01T10:00:00"), TimeZone = TimeZoneInfo.Utc },
    ["end"] = new MeetingTime() { DateTime = DateTimeOffset.Parse("2023-10-01T10:00:00"), TimeZone = TimeZoneInfo.Utc },
    ["tags"] = new[] { new Tag("work"), new Tag("important") }
};

// Invoke the createEvent function
FunctionResult functionResult = await kernel.InvokeAsync(plugin["createEvent"], arguments);
```

此选项自然适合现有选项 #1 之间。和 `payload` `content-type` Arguments 和选项 #2。使用叶属性构建动态负载，如下面的概述表所示。

### 选项概述
| 选择 | 访客 | SK | 局限性 |
|--------|-------|----|--------|
| 1. 和 `payload` `content-type` 参数 | 构造有效负载 | 按原样使用 | 无限制 |
| 4. 从根属性构建动态负载 | 为根属性提供参数 | 构造有效负载 | 1. 不支持 `anyOf`、 、 `allOf` `oneOf` |
| 2. 从 Leaf Properties 构建动态负载 | 为叶属性提供参数 | 构造有效负载 | 1. 不支持 `anyOf`， `allOf`， ， `oneOf`， 2.叶属性必须是唯一的，3.循环引用  |
| 3. 从叶属性 + 命名空间构建动态有效负载 | 为命名空间属性提供参数 | 构造有效负载 | 1. 不支持 `anyOf`， `allOf`， ， `oneOf`， 2.循环引用 |

### 决策结果
在讨论了这些选项之后，决定不继续实施选项 #4，因为没有强有力的证据表明它比现有的选项 #1 有任何好处。

## 样品
演示上述现有选项用法的示例可以在 [Semantic Kernel Samples 存储库中找到](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Plugins/OpenApiPlugin_PayloadHandling.cs)