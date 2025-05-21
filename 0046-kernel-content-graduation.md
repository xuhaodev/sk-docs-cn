
# 内核内容类型毕业

## 上下文和问题陈述

目前，我们有许多内容类型处于实验状态，此 ADR 将提供一些有关如何将它们升级到稳定状态的选项。

## 决策驱动因素

- 无中断性变更
- 方法简单，复杂性最低
- 允许扩展性
- 简洁明了

## BinaryContent 毕业

此内容应按内容专用化或直接针对不特定的类型，类似于“application/octet-stream”MIME 类型。

> **Application/Octet-Stream** 是用于任意二进制数据或字节流的 MIME，它不适合任何其他更具体的 MIME 类型。此 MIME 类型通常用作默认类型或回退类型，指示应将文件视为纯二进制数据。

#### 当前

```csharp
public class BinaryContent : KernelContent
{
    public ReadOnlyMemory<byte>? Content { get; set; }
    public async Task<Stream> GetStreamAsync()
    public async Task<ReadOnlyMemory<byte>> GetContentAsync()

    ctor(ReadOnlyMemory<byte>? content = null)
    ctor(Func<Task<Stream>> streamProvider)
}
```

#### 提出

```csharp
public class BinaryContent : KernelContent
{
    ReadOnlyMemory<byte>? Data { get; set; }
    Uri? Uri { get; set; }
    string DataUri { get; set; }

    bool CanRead { get; } // Indicates if the content can be read as bytes or data uri

    ctor(Uri? referencedUri)
    ctor(string dataUri)
    // MimeType is not optional but nullable to encourage this information to be passed always when available.
    ctor(ReadOnlyMemory<byte> data, string? mimeType)
    ctor() // Empty ctor for serialization scenarios
}
```

- No Content 属性（如果从专用类型上下文中使用，请避免冲突和/或误导信息）

  即：

  - `PdfContent.Content` （描述纯文本信息）
  - `PictureContent.Content` （公开类型 `Picture` ）

- 摆脱延迟 （延迟加载） 内容提供程序，使用更简单的 API。
- `GetContentAsync` removal （不再有 derrefed API）
- 为 `Data` 字节数组内容信息添加了 setter 和 getter 属性。

  设置此属性将覆盖 `DataUri` base64 数据部分。

- 为 `DataUri` 数据 uri 内容信息添加了 setter 和 getter 属性。

  设置此属性将使用 `Data` `MimeType` 当前有效负载详细信息覆盖 and 属性。

- 为 `Uri` 引用的内容信息添加属性。此属性不接受 not a `UriData` ，仅支持非数据方案。
- 添加 `CanRead` 属性 （指示是否可以使用 `Data` 或 `DataUri` properties 读取内容。
- 用于创建 Uri、DataUri 和 ByteArray + MimeType 的专用构造函数。

优点：

- 由于没有延迟内容，我们有了更简单的 API，并且对内容负责。
- 可以以 OR 格式写入和读取 `Data` `DataUri` 。
- 可以具有 `Uri` reference 属性，这在专用上下文中很常见。
- 完全可序列化。
- 数据 Uri 参数支持（包括序列化）。
- 数据 Uri 和 Base64 验证检查
- Data Uri 和 Data 可以动态生成
- `CanRead` 将清楚地识别内容是否可以读取为 `bytes` 或 `DataUri`。

缺点：

- 针对实验性使用者的突破性变化 `BinaryContent` 

### 数据 Uri 参数

根据 [RFC 2397，data](https://datatracker.ietf.org/doc/html/rfc2397) uri 方案支持参数

从数据URI导入的每个参数都将添加到元数据字典中，其中“data-uri-parameter-name”作为键及其重复值。

#### 提供参数化数据 URI 会将这些参数包含在 Metadata 字典中。

```csharp
var content = new BinaryContent("data:application/json;parameter1=value1;parameter2=value2;base64,SGVsbG8gV29ybGQ=");
var parameter1 = content.Metadata["data-uri-parameter1"]; // value1
var parameter2 = content.Metadata["data-uri-parameter2"]; // value2
```

#### 在获取 DataUri 属性时，内容的反序列化也将包括这些参数。

```csharp
var json = """
{
    "metadata":
    {
        "data-uri-parameter1":"value1",
        "data-uri-parameter2":"value2"
    },
    "mimeType":"application/json",
    "data":"SGVsbG8gV29ybGQ="
}
""";
var content = JsonSerializer.Deserialize<BinaryContent>(json);
content.DataUri // "data:application/json;parameter1=value1;parameter2=value2;base64,SGVsbG8gV29ybGQ="
```

### 专业化示例

#### 图像内容

```csharp
public class ImageContent : BinaryContent
{
    ctor(Uri uri) : base(uri)
    ctor(string dataUri) : base(dataUri)
    ctor(ReadOnlyMemory<byte> data, string? mimeType) : base(data, mimeType)
    ctor() // serialization scenarios
}

public class AudioContent : BinaryContent
{
    ctor(Uri uri)
}
```

优点：

- 支持数据 URI 大型内容
- 允许使用 dataUrl 方案创建二进制 ImageContent，并允许由 Url 引用。
- 支持数据 Uri 验证

## ImageContent 毕业典礼

⚠️ 目前，这不是实验性的，需要将破坏性更改升级到具有潜在好处的稳定状态。

### 问题

1. 电流 `ImageContent` 不是源自 `BinaryContent`
2. 具有不良行为，允许同一实例同时具有 distinct `DataUri` 和 `Data` at。
3. `Uri` 属性用于数据 URI 和引用的 URI 信息
4. `Uri` 不支持大型语言数据 URI 格式。
5. 不清楚 `sk developer` 内容何时可读或不可读。

#### 当前

```csharp
public class ImageContent : KernelContent
{
    Uri? Uri { get; set; }
    public ReadOnlyMemory<byte>? Data { get; set; }

    ctor(ReadOnlyMemory<byte>? data)
    ctor(Uri uri)
    ctor()
}
```

#### 提出

如 `BinaryContent` 部分示例所示，可以 `ImageContent` 毕业成为 `BinaryContent` 专业化，并继承它带来的所有好处。

```csharp
public class ImageContent : BinaryContent
{
    ctor(Uri uri) : base(uri)
    ctor(string dataUri) : base(dataUri)
    ctor(ReadOnlyMemory<byte> data, string? mimeType) : base(data, mimeType)
    ctor() // serialization scenarios
}
```

优点：

- 可以用作 `BinaryContent` 类型
- 可以以 OR 格式写入和读取 `Data` `DataUri` 。
- 可以具有 `Uri` 专用的 for referenced location。
- 完全可序列化。
- 数据 Uri 参数支持（包括序列化）。
- 数据 Uri 和 Base64 验证检查
- 可以检索
- Data Uri 和 Data 可以动态生成
- `CanRead` 将清楚地识别内容是否可以读取为 `bytes` 或 `DataUri`。

缺点：

- ⚠️ 为消费者带来突破性的变化 `ImageContent` 

### ImageContent 重大更改

- `Uri` 属性将专门用于引用的位置（非 data-uri），尝试添加 `data-uri` 格式将引发异常，建议改用该 `DataUri` 属性。
- 设置 `DataUri` 将根据提供的信息覆盖 `Data` and `MimeType` 属性。
- 尝试设置无效 `DataUri` 将引发异常。
- setting `Data` 现在将覆盖 `DataUri` 数据部分。
- 尝试在属性`ImageContent`中使用 data-uri `Uri` 序列化  将引发异常。

## AudioContent 毕业

与 `ImageContent` 提案`AudioContent`类似，可以毕业为 `BinaryContent`.

#### 当前

1. 当前 `AudioContent` 不派生支持 `Uri` 引用位置
2. `Uri` 属性用于数据 URI 和引用的 URI 信息
3. `Uri` 不支持大型语言数据 URI 格式。
4. 不清楚 `sk developer` 内容何时可读或不可读。

```csharp
public class AudioContent : KernelContent
{
    public ReadOnlyMemory<byte>? Data { get; set; }

    ctor(ReadOnlyMemory<byte>? data)
    ctor()
}
```

#### 提出

```csharp
public class AudioContent : BinaryContent
{
    ctor(Uri uri) : base(uri)
    ctor(string dataUri) : base(dataUri)
    ctor(ReadOnlyMemory<byte> data, string? mimeType) : base(data, mimeType)
    ctor() // serialization scenarios
}
```

优点：

- 可以用作 `BinaryContent` 类型
- 可以以 OR 格式写入和读取 `Data` `DataUri` 。
- 可以具有 `Uri` 专用的 for referenced location。
- 完全可序列化。
- 数据 Uri 参数支持（包括序列化）。
- 数据 Uri 和 Base64 验证检查
- 可以检索
- Data Uri 和 Data 可以动态生成
- `CanRead` 将清楚地识别内容是否可以读取为 `bytes` 或 `DataUri`。

缺点：

- 面向消费者`AudioContent`的实验性中断性变更 

## FunctionCallContent 毕业

### 当前

无需更改当前结构。

我们可能有一个基础`FunctionContent`，但同时，通过 `KernelContent` 提供明确的关注点分离来获得这两个基础是好的。

```csharp
public sealed class FunctionCallContent : KernelContent
{
    public string? Id { get; }
    public string? PluginName { get; }
    public string FunctionName { get; }
    public KernelArguments? Arguments { get; }
    public Exception? Exception { get; init; }

    ctor(string functionName, string? pluginName = null, string? id = null, KernelArguments? arguments = null)

    public async Task<FunctionResultContent> InvokeAsync(Kernel kernel, CancellationToken cancellationToken = default)
    public static IEnumerable<FunctionCallContent> GetFunctionCalls(ChatMessageContent messageContent)
}
```

## FunctionResultContent 刻度

尽管目前的结构很好，但它可能需要一些改变。

### 当前

- 从纯度的角度来看，该 `Id` 属性可能会导致混淆，因为它不是响应 ID，而是函数调用 ID。
- ctor 对于 `functionCall` `functionCallContent` 同一类型具有不同的 PARAMETER 名称。

```csharp
public sealed class FunctionResultContent : KernelContent
{
    public string? Id { get; }
    public string? PluginName { get; }
    public string? FunctionName { get; }
    public object? Result { get; }

    ctor(string? functionName = null, string? pluginName = null, string? id = null, object? result = null)
    ctor(FunctionCallContent functionCall, object? result = null)
    ctor(FunctionCallContent functionCallContent, FunctionResult result)
}
```

### 建议 - 选项 1

- 重命名 `Id` 为 `CallId` 以避免混淆。
- 调整 `ctor` 参数名称。

```csharp
public sealed class FunctionResultContent : KernelContent
{
    public string? CallId { get; }
    public string? PluginName { get; }
    public string? FunctionName { get; }
    public object? Result { get; }

    ctor(string? functionName = null, string? pluginName = null, string? callId = null, object? result = null)
    ctor(FunctionCallContent functionCallContent, object? result = null)
    ctor(FunctionCallContent functionCallContent, FunctionResult functionResult)
}
```

### 建议 - 选项 2

使用组合 a 在 `FunctionResultContent`.

优点：

- `CallContent` 具有从函数响应中再次调用函数的选项，这在某些情况下可能很方便
- 明确结果的来源以及特定于结果的数据（根类）。
- 了解调用中使用的参数。

缺点：

- 引入一个额外的跃点以从 `call` 结果中获取详细信息。

```csharp
public sealed class FunctionResultContent : KernelContent
{
    public FunctionCallContent CallContent { get; }
    public object? Result { get; }

    ctor(FunctionCallContent functionCallContent, object? result = null)
    ctor(FunctionCallContent functionCallContent, FunctionResult functionResult)
}
```

## FileReferenceContent + AnnotationContent

这两个内容是由于 `SemanticKernel.Abstractions` 序列化的方便而添加的，但非常特定于 **OpenAI Assistant API**，目前应保持为 Experimental。

作为毕业典礼，他们应该 `SemanticKernel.Agents.OpenAI` 遵循下面的建议。

```csharp
#pragma warning disable SKEXP0110
[JsonDerivedType(typeof(AnnotationContent), typeDiscriminator: nameof(AnnotationContent))]
[JsonDerivedType(typeof(FileReferenceContent), typeDiscriminator: nameof(FileReferenceContent))]
#pragma warning disable SKEXP0110
public abstract class KernelContent { ... }
```

对于其他具有 specialization 的软件包，不应鼓励这种耦合 `KernelContent` 。

### 解决方案 - JsonConverter 注释的使用 [](https://learn.microsoft.com/en-us/dotnet/standard/serialization/system-text-json/converters-how-to?pivots=dotnet-6-0#registration-sample---jsonconverter-on-a-type) 

在项目中创建专用 `JsonConverter` 帮助程序 `Agents.OpenAI` 来处理这些类型的序列化和反序列化。

使用 attribute 注释这些 Content 类型 `[JsonConverter(typeof(KernelContentConverter))]` 以指示 `JsonConverter` 要使用的 。

### Agents.OpenAI 的 JsonConverter 示例

```csharp
public class KernelContentConverter : JsonConverter<KernelContent>
{
    public override KernelContent Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        using (var jsonDoc = JsonDocument.ParseValue(ref reader))
        {
            var root = jsonDoc.RootElement;
            var typeDiscriminator = root.GetProperty("TypeDiscriminator").GetString();
            switch (typeDiscriminator)
            {
                case nameof(AnnotationContent):
                    return JsonSerializer.Deserialize<AnnotationContent>(root.GetRawText(), options);
                case nameof(FileReferenceContent):
                    return JsonSerializer.Deserialize<FileReferenceContent>(root.GetRawText(), options);
                default:
                    throw new NotSupportedException($"Type discriminator '{typeDiscriminator}' is not supported.");
            }
        }
    }

    public override void Write(Utf8JsonWriter writer, KernelContent value, JsonSerializerOptions options)
    {
        JsonSerializer.Serialize(writer, value, value.GetType(), options);
    }
}

[JsonConverter(typeof(KernelContentConverter))]
public class FileReferenceContent : KernelContent
{
    public string FileId { get; init; } = string.Empty;
    ctor()
    ctor(string fileId, ...)
}

[JsonConverter(typeof(KernelContentConverter))]
public class AnnotationContent : KernelContent
{
    public string? FileId { get; init; }
    public string? Quote { get; init; }
    public int StartIndex { get; init; }
    public int EndIndex { get; init; }
    public ctor()
    public ctor(...)
}
```

## 决策结果

- `BinaryContent`：接受。
- `ImageContent`：接受重大更改，但使用 `BinaryContent` 专业化可享受权益。没有向后兼容性，因为当前 `ImageContent` 行为是不可取的。
- `AudioContent`：使用专精的实验性重大更改 `BinaryContent` 。
- `FunctionCallContent`：按原样毕业。
- `FunctionResultContent`：从 property 到 的实验性中断性更改 `Id` `CallId` ，以避免在成为函数调用 ID 或响应 ID 时产生混淆。
- `FileReferenceContent` 和 `AnnotationContent`：无更改，继续作为实验性。
