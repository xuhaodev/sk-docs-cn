
# 考虑将 JsonSerializerOptions 集成到 SK 中的方法

## 上下文和问题陈述
如今，SK 依靠 JSON 序列化和架构生成功能为函数参数和返回类型生成架构，在封送过程中将它们从 JSON 反序列化为目标类型，将 AI 模型序列化到 SK 并返回，等等。   
  
目前，序列化代码要么不使用 JsonSerializerOptions （JSO），要么使用硬编码的预定义代码来实现特定目的，而无法提供自定义代码。这对于 JSON 序列化默认使用反射的非 AOT 场景非常有效。但是，在不支持所有必需的反射 API 的原生 AOT 应用程序中，基于反射的序列化将不起作用，并且会崩溃。  
   
若要为 Native-AOT 方案启用序列化，所有序列化代码都应使用由基类表示的源生成的上下文协定 `JsonSerializerContext` 。有关更多详细信息，请参阅[如何在 System.Text.Json 中使用源生成](https://learn.microsoft.com/en-us/dotnet/standard/serialization/system-text-json/source-generation?pivots=dotnet-8-0#specify-source-generation-mode)一文。此外，应该有一种方法可以通过 SK 公共 API 表面向 JSON 序列化功能提供这些源生成的类。 
   
此 ADR 概述了将具有已配置源生成合约的 JSO 传递到启用 Native-AOT 的 SK 组件的 JSON 序列化代码的潜在选项。

## 决策驱动因素

- 可以提供外部源生成的上下文协定，直至 SK JSON 序列化功能。
- 直观、清晰、轻松地向 SK 组件提供源生成的上下文契约。
- 与 Microsoft.Extensions.AI 集成很容易

## 考虑的选项

- 选项 #1：所有 SK 组件都有一个全局 SSO
- 选项 #2：每个 SK 组件的 JSO
- 选项 #3：每个 SK 组件作的 JSO

## 选项 #1：所有 SK 组件都有一个全局 SSO
此选项假定将 `JsonSerializerOptions` type `JsonSerializerOptions` 的新属性`Kernel`添加到  class 中。所有外部源生成的上下文契约都将在那里注册，所有需要 JSO 的 SK 组件都将从那里解析它们：

```csharp
public sealed class MyPlugin { public Order CreateOrder() => new(); }

public sealed class Order { public string? Number { get; set; } }

[JsonSerializable(typeof(Order))]
internal sealed partial class OrderJsonSerializerContext : JsonSerializerContext
{
}

public async Task TestAsync()
{
    JsonSerializerOptions options = new JsonSerializerOptions();
    options.TypeInfoResolverChain.Add(OrderJsonSerializerContext.Default);

    Kernel kernel = new Kernel();
    kernel.JsonSerializerOptions = options;

    // All the following Kernel extension methods use JSOs configured on the `Kernel.JsonSerializerOptions` property
    kernel.CreateFunctionFromMethod(() => new Order());
    kernel.CreateFunctionFromPrompt("<prompt>");
    kernel.CreatePluginFromFunctions("<plugin>", [kernel.CreateFunctionFromMethod(() => new Order())]);
    kernel.CreatePluginFromType<MyPlugin>("<plugin>");
    kernel.CreatePluginFromPromptDirectory("<directory>", "<plugin>");
    kernel.CreatePluginFromObject(new MyPlugin(), "<plugin>");

    // AI connectors can use the `Kernel.JsonSerializerOptions` property as well
    var onnxService = new OnnxRuntimeGenAIChatCompletionService("<modelId>", "<modelPath>");
    var res = await onnxService.GetChatMessageContentsAsync(new ChatHistory(), new PromptExecutionSettings(), kernel);

    // The APIs below can't use the `Kernel.JsonSerializerOptions` property because they don't have access to the `Kernel` instance
    KernelFunctionFactory.CreateFromMethod(() => new Order(), options);
    KernelFunctionFactory.CreateFromPrompt("<prompt>", options);

    KernelPluginFactory.CreateFromObject(new MyPlugin(), options, "<plugin>");
    KernelPluginFactory.CreateFromType<MyPlugin>(options, "<plugin>");
    KernelPluginFactory.CreateFromFunctions("<plugin>", [kernel.CreateFunctionFromMethod(() => new Order())]);
}
```

优点：  
- 所有 SK 组件都使用在一个位置配置的 JSO。如果需要，可以提供具有不同选项的内核克隆。  
   
缺点：  
- 可能需要将 SK 组件更改为依赖于内核（如果尚未更改）。  
- 根据 JSO 的初始化方式，此选项在 AOT 应用程序中使用不兼容的 API 时可能不像其他选项那样明确，从而导致根据运行时错误注册源生成的协定。  
- 与上述类似，可能不清楚哪个组件/API 需要 JSO，从而将发现推迟到运行时。  
- 将添加另一种在 SK 中提供 JSO 的方式。低级 KernelFunctionFactory 和 KernelPluginFactory 通过方法参数接受 JSO。  
- SK AI 连接器 **** 在其作中接受内核的可选实例，该实例会发送混合信号。一方面，它是可选的，这意味着 AI 连接器可以在没有它的情况下工作;另一方面，如果未提供内核，则 AOT 应用程序中的作将失败。
- 在需要多个内核实例的方案中，每个实例可能具有唯一的 JSO，则创建函数时使用的内核的 JSO 将在函数的生命周期内使用。将不会应用可能用于调用该函数的任何其他内核的 JSO，而将使用创建该函数时使用的内核中的 JSO 的 JSO。

### 向内核提供 JSON 序列化程序选项 （JSO） 的方法：
1. 通过 `Kernel` constructor.
    ```csharp
    private readonly JsonSerializerOptions? _serializerOptions = null;

    // Existing AOT incompatible constructor
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of JSON serialization in SK, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of JSON serialization in SK, making it incompatible with AOT scenarios.")]
    public Kernel(IServiceProvider? services = null,KernelPluginCollection? plugins = null) {}

    // New AOT compatible constructor
    public Kernel(JsonSerializerOptions jsonSerializerOptions, IServiceProvider? services = null,KernelPluginCollection? plugins = null) 
    { 
        this._serializerOptions = jsonSerializerOptions;
        this._serializerOptions.MakeReadOnly(); // Prevent mutations that may not be picked up by SK components created with initial JSOs.
    }

    public JsonSerializerOptions JsonSerializerOptions => this._serializerOptions ??= JsonSerializerOptions.Default;
    ```
    优点：
    - 在编译时使用不兼容 AOT 的构造函数时，将显示与 AOT 相关的警告。

2. 通过 `Kernel.JsonSerializerOptions` 属性 setter
    ```csharp
    private readonly JsonSerializerOptions? _serializerOptions = null;

    public JsonSerializerOptions JsonSerializerOptions
    {
        get
        {
            return this._serializerOptions ??= ??? // JsonSerializerOptions.Default will work for non-AOT scenarios and will fail in AOT ones.
        }
        set
        {
            this._serializerOptions = value;
        }
    }
    ```
    缺点：
    - 在 AOT 应用程序中进行内核初始化期间，不会生成 AOT 警告，从而导致运行时失败。
    - 在 SK 组件（KernelFunction 通过构造函数接受 JSO）创建后分配的 JSO 不会被组件选取。

3. 地
    待定。

## 选项 #2：每个 SK 组件的 JSO
此选项假定在组件的实例化站点或构造函数中提供 JSO：
```csharp
    public sealed class Order { public string? Number { get; set; } }

    [JsonSerializable(typeof(Order))]
    internal sealed partial class OrderJsonSerializerContext : JsonSerializerContext
    {
    }

    JsonSerializerOptions options = new JsonSerializerOptions();
    options.TypeInfoResolverChain.Add(OrderJsonSerializerContext.Default);

    // All the following kernel extension methods accept JSOs explicitly supplied as an argument for the corresponding parameter:
    kernel.CreateFunctionFromMethod(() => new Order(), options);
    kernel.CreateFunctionFromPrompt("<prompt>", options);
    kernel.CreatePluginFromFunctions("<plugin>", [kernel.CreateFunctionFromMethod(() => new Order(), options)]);
    kernel.CreatePluginFromType<MyPlugin>("<plugin>", options);
    kernel.CreatePluginFromPromptDirectory("<directory>", "<plugin>", options);
    kernel.CreatePluginFromObject(new MyPlugin(), "<plugin>", options);

    // The AI connectors accept JSOs at the instantiation site rather than at the invocation site.
    var onnxService = new OnnxRuntimeGenAIChatCompletionService("<modelId>", "<modelPath>", options);
    var res = await onnxService.GetChatMessageContentsAsync(new ChatHistory(), new PromptExecutionSettings());

    // The APIs below already accept JSOs at the instantiation site.
    KernelFunctionFactory.CreateFromMethod(() => new Order(), options);
    KernelFunctionFactory.CreateFromPrompt("<prompt>", options);

    KernelPluginFactory.CreateFromObject(new MyPlugin(), options, "<plugin>");
    KernelPluginFactory.CreateFromType<MyPlugin>(options, "<plugin>");
    KernelPluginFactory.CreateFromFunctions("<plugin>", [kernel.CreateFunctionFromMethod(() => new Order())]);
```
优点：
- AOT 警告将在编译时在每个组件实例化站点生成。
- 在所有 SK 组件中使用 JSO 的方式相同。
- 不需要 SK 组件依赖 Kernel。

缺点：
- 没有一个中心位置来注册源生成的上下文。如果应用程序有大量的引导代码驻留在许多不同的类中，这些类之间可能具有继承关系，则这可能是一个优势。

AI 连接器可以接受 JSO 作为构造函数中的参数或可选属性。当一个或几个连接器被重构为与 AOT 兼容时，将做出该决定。

## 选项 #3：每个 SK 组件作的 JSO
此选项假定在组件作调用站点而不是实例化站点提供 JSO。

优点：
- AOT 警告将在编译时在每个组件作调用站点生成。

缺点：
- 必须为所有需要外部源生成合约的 SK 组件添加新的接受 JSO 的作/方法重载。
- 将添加另一种在 SK 中提供 JSO 的方式。低级 KernelFunctionFactory 和 KernelPluginFactory 通过方法参数接受 JSO。  
- 不适用于所有 SK 组件。KernelFunction 在被调用以生成架构之前需要 JSO。 
- 鼓励无效使用 JSO，其中每个方法调用可能会创建 JSO，这可能会在内存方面造成昂贵。

## 决策结果
“选项 #2 每个 SK 组件的 JSO”比其他选项更受欢迎，因为它提供了一种在组件的实例化/创建站点提供 JSO 的明确、统一、清晰、简单和有效的方法。