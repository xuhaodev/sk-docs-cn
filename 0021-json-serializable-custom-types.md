
# JSON 可序列化自定义类型

## 上下文和问题陈述

此 ADR 旨在通过允许开发人员使用任何可使用 `System.Text.Json` .

为了允许在规划器的函数手册中使用 JSON Schema 来描述函数，对 JSON 可序列化类型进行标准化是必要的。使用 JSON Schema 来描述函数的输入和输出类型将允许规划者验证该函数是否被正确使用。

如今，在 Semantic Kernel 中使用自定义类型要求开发人员实现自定义 `TypeConverter` ，以便与类型的字符串表示形式相互转换。如下所示 [功能/MethodFunctions_Advanced] ：

```csharp
    [TypeConverter(typeof(MyCustomTypeConverter))]
    private sealed class MyCustomType
    {
        public int Number { get; set; }

        public string? Text { get; set; }
    }

    private sealed class MyCustomTypeConverter : TypeConverter
    {
        public override bool CanConvertFrom(ITypeDescriptorContext? context, Type sourceType) => true;

        public override object? ConvertFrom(ITypeDescriptorContext? context, CultureInfo? culture, object value)
        {
            return JsonSerializer.Deserialize<MyCustomType>((string)value);
        }

        public override object? ConvertTo(ITypeDescriptorContext? context, CultureInfo? culture, object? value, Type destinationType)
        {
            return JsonSerializer.Serialize(value);
        }
    }
```

现在，仅当无法使用自定义类型进行序列化时，才需要上述方法 `System.Text.Json`。

## 考虑的选项

**1. 使用 `System.Text.Json` if a `TypeConverter` 对给定类型不可用时回退到序列化**

- 原始类型将使用它们的原生 `TypeConverter`s 来处理
  - 我们保留`TypeConverter`对原始类型的本机使用，以防止任何有损转换。
- 复杂类型将由其注册的 `TypeConverter`（如果提供）处理。
- 如果 `TypeConverter` 为复杂类型注册了 no，则我们自己的 `JsonSerializationTypeConverter` 将用于尝试使用 JSON 进行 JSON 序列化/反序列化 `System.Text.Json`。
  - 如果类型无法序列化/反序列化，则会引发详细的错误消息。

这会将 `GetTypeConverter()` 方法`NativeFunction.cs`更改为如下所示，如果未 `null` 找到该类型，`TypeConverter`则返回  before：

```csharp
private static TypeConverter GetTypeConverter(Type targetType)
    {
        if (targetType == typeof(byte)) { return new ByteConverter(); }
        if (targetType == typeof(sbyte)) { return new SByteConverter(); }
        if (targetType == typeof(bool)) { return new BooleanConverter(); }
        if (targetType == typeof(ushort)) { return new UInt16Converter(); }
        if (targetType == typeof(short)) { return new Int16Converter(); }
        if (targetType == typeof(char)) { return new CharConverter(); }
        if (targetType == typeof(uint)) { return new UInt32Converter(); }
        if (targetType == typeof(int)) { return new Int32Converter(); }
        if (targetType == typeof(ulong)) { return new UInt64Converter(); }
        if (targetType == typeof(long)) { return new Int64Converter(); }
        if (targetType == typeof(float)) { return new SingleConverter(); }
        if (targetType == typeof(double)) { return new DoubleConverter(); }
        if (targetType == typeof(decimal)) { return new DecimalConverter(); }
        if (targetType == typeof(TimeSpan)) { return new TimeSpanConverter(); }
        if (targetType == typeof(DateTime)) { return new DateTimeConverter(); }
        if (targetType == typeof(DateTimeOffset)) { return new DateTimeOffsetConverter(); }
        if (targetType == typeof(Uri)) { return new UriTypeConverter(); }
        if (targetType == typeof(Guid)) { return new GuidConverter(); }

        if (targetType.GetCustomAttribute<TypeConverterAttribute>() is TypeConverterAttribute tca &&
            Type.GetType(tca.ConverterTypeName, throwOnError: false) is Type converterType &&
            Activator.CreateInstance(converterType) is TypeConverter converter)
        {
            return converter;
        }

        // now returns a JSON-serializing TypeConverter by default, instead of returning null
        return new JsonSerializationTypeConverter();
    }

    private sealed class JsonSerializationTypeConverter : TypeConverter
    {
        public override bool CanConvertFrom(ITypeDescriptorContext? context, Type sourceType) => true;

        public override object? ConvertFrom(ITypeDescriptorContext? context, CultureInfo? culture, object value)
        {
            return JsonSerializer.Deserialize<object>((string)value);
        }

        public override object? ConvertTo(ITypeDescriptorContext? context, CultureInfo? culture, object? value, Type destinationType)
        {
            return JsonSerializer.Serialize(value);
        }
    }

```

_什么时候需要序列化/反序列化？_

必填

- **Native to Semantic：** 将变量从 Native 传递到 Semantic **需要** 将 Native Function 的输出从复杂类型序列化为字符串，以便将其传递给 LLM。
- **语义到本机：** 将变量从语义传递到本机 **将** 需要在字符串之间将语义函数的输出反序列化为本机函数所需的复杂类型格式。

不需要

- **Native 到 Native：** 将变量从 Native 传递到 Native **不需要** 任何序列化或反序列化，因为复杂类型可以按原样传递。
- **语义到语义：** 将变量从 Semantic 传递到 Semantic **不需要** 任何序列化或反序列化，因为复杂类型将使用其字符串表示形式进行传递。

**2. 仅使用原生序列化方法**
最初考虑了此选项，这将有效地消除 `TypeConverter`s 的使用，转而使用 simple `JsonConverter`，但指出这可能会导致原始类型之间的有损转换。例如，当从 a 转换为 `float` an `int` 时，基元可能会以某种方式被本机序列化方法截断，而该方法无法提供准确的结果。

## 决策结果
