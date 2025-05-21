
# Handlebars Prompt 模板帮助程序

## 上下文和问题陈述

我们希望将 Handlebars 用作模板工厂，用于在 Semantic Kernel 中渲染 Prompts 和 Planner。Handlebars 提供了一种简单而富有表现力的语法，用于创建具有逻辑和数据的动态模板。但是，Handlebars 没有对与我们的用例相关的某些功能和场景的内置支持，例如：

- 将文本块标记为具有聊天完成连接器角色的消息。
- 从内核调用函数并将参数传递给它们。
- 在模板上下文中设置和获取变量。
- 执行常见作，例如串联、算术、比较和 JSON 序列化。
- 支持渲染模板的不同输出类型和格式。

因此，我们需要使用自定义帮助程序来扩展 Handlebars，这些帮助程序可以解决这些差距，并为提示和规划工程师提供一致且方便的方式来编写模板。

首先，我们将通过**_为常见作和实用程序烘焙一组定义的自定义系统帮助程序_**来实现此目的，这些作和实用程序未提供任何内置 Handlebars 帮助程序，其中包括：

- 允许我们完全控制 Handlebars 模板工厂可以执行哪些功能。
- 通过为任何内置 Handlebars 帮助程序未提供但通常由模型产生幻觉的常见作和实用程序提供帮助程序，增强了模板工厂的功能和可用性。
- 提高渲染模板的表达性和可读性，因为帮助程序可用于对模板数据/参数执行简单或复杂的逻辑或转换。
- 为用户提供灵活性和便利性，因为他们可以：

  - 选择语法，然后
  - 扩展、添加或省略某些帮助程序

  以最好地满足他们的需求和偏好。

- 允许自定义可能具有不同行为或要求的特定作或实用程序，例如处理输出类型、格式或错误。

这些帮助程序将处理参数的评估、作或实用程序的执行以及将结果写入模板。此类作的示例包括 `{{concat string1 string2 ...}}`、 `{{equal value1 value2}}` `{{json object}}` `{{set name=value}}` `{{get name}}` `{{or condition1 condition2}}`等。

其次，我们必须 **_将 Kernel 中注册的函数作为_** Handlebars 模板工厂的帮助程序公开出来。下面详细介绍了此选项。

## 决策驱动因素

- 我们希望尽可能多地利用现有的 Handlebars 帮助程序、语法和机制来加载帮助程序，而不会引入不必要的复杂性或不一致性。
- 我们希望为 prompt 和 SK 工程师提供有用且直观的 helpers。
- 我们希望确保 Helpers 有良好的文档记录、测试和维护，并且它们不会相互冲突或与内置的 Handlebars Helper 冲突。
- 我们希望为渲染的模板支持不同的输出类型和格式，例如文本、JSON 或复杂对象，并允许模板指定所需的输出类型。

## 考虑的选项

我们考虑了以下使用内核函数扩展 Handlebars 的选项作为自定义帮助程序：

**1. 使用单个 helper 从内核调用函数。** 此选项将使用通用帮助程序（如 `{{invoke pluginName-functionName param1=value1 param2=value2 ...}}`）从内核调用任何函数并向其传递参数。帮助程序将处理函数的执行、参数和结果的转换以及将结果写入模板的过程。

**2. 对内核中的每个函数使用单独的帮助程序。** 此选项将为每个函数注册一个新的帮助程序，例如 `{{pluginName-functionName param1=value1 param2=value2 ...}}`，以处理函数的执行、参数和结果的转换以及将结果写入模板。

## 优点和缺点

### 1. 使用单个泛型帮助程序从内核调用函数

优点：

- 简化了帮助程序的注册和维护，因为只需要`invoke`定义和更新一个帮助程序 。
- 为从内核调用任何函数提供一致且统一的语法，无论插件或函数名称、参数详细信息或结果如何。
- 允许对内核函数进行自定义和特殊逻辑，例如处理输出类型、执行限制或错误。
- 允许使用位置参数或命名参数以及哈希参数将参数传递给函数。

缺点：

- 降低模板的表达性和可读性，因为函数名称和参数包装在泛型帮助程序调用中。
- 为模型添加额外的语法以学习和跟踪，这可能会导致在渲染过程中出现更多错误。

### 2. 对_内核中的每个函数_使用通用帮助程序 

优点：

- 具有选项 1 的所有优点，但在很大程度上提高了模板的表达性和可读性，因为函数名称和参数直接写入模板中。
- 保持处理每个函数的易维护性，因为每个帮助程序都将遵循相同的模板化逻辑进行注册和执行。

缺点：

- 如果函数名称或参数名称与内置 Handlebars 帮助程序或内核变量匹配，可能会导致它们发生冲突或混淆。

## 决策结果

我们决定采用选项 2：提供特殊的帮助程序来调用内核中的任何函数。这些帮助程序将为每个已注册的函数遵循相同的逻辑和语法。我们相信，这种方法以及将启用特殊实用程序逻辑或行为的自定义系统帮助程序，为 Handlebars 模板工厂和我们的用户提供了简单性、表现力、灵活性和功能性之间的最佳平衡。

使用这种方法，

- 我们将允许客户使用任何内置的 [Handlebars.Net 帮助程序](https://github.com/Handlebars-Net/Handlebars.Net.Helpers)。
- 我们将提供默认注册的 Utility Helpers。
- 我们将提供默认注册的提示帮助程序（例如聊天消息）。
- 我们将注册在 `Kernel`.
- 我们将允许客户控制哪些插件注册为 helpers 以及 helpers 签名的语法。
  - 默认情况下，我们将遵循 [HandlebarsHelperOptions 中定义的所有选项](https://github.com/Handlebars-Net/Handlebars.Net.Helpers/blob/8f7c9c082e18845f6a620bbe34bf4607dcba405b/src/Handlebars.Net.Helpers/Options/HandlebarsHelpersOptions.cs#L12)。
  - 此外，我们将扩展此配置以包含一个 `RegisterCustomHelpersCallback` 选项，用户可以设置该选项来注册自定义帮助程序。
- 我们将允许通过对象轻松访问 Kernel 函数参数，即函数变量和执行设置 `KernelArguments` 。
- 我们将允许客户控制何时将插件函数注册为帮助程序。
  - 默认情况下，这是在渲染模板时完成的。
  - （可选）当通过传入 Plugin 集合来构造 Handlebars 模板工厂时，可以执行此作。
- 如果内置 helpers、变量或内核对象之间发生冲突：
  - 我们将抛出一个错误，清楚地解释问题所在，以及
  - 允许客户提供自己的实施和覆盖，包括不注册默认帮助程序的选项。这可以通过设置为 `Options.Categories` empty array  来完成`[]`。

我们还决定遵循一些准则和最佳实践来设计和实现 helpers，例如：

- 记录每个帮助程序的用途、语法、参数和行为，并为它们提供示例和测试。
- 以清晰一致的方式命名 Helper，并避免与内置的 Handlebars Helpers 或内核函数或变量发生冲突或混淆。
  - 对自定义系统帮助程序使用独立函数名称（即 json、set）
  - 对`-`注册为处理内核函数的帮助程序使用分隔符 “”，以将它们彼此区分开来，并与我们的系统或内置的 Handlebars 帮助程序区分开来。
- 支持位置参数和哈希参数，用于将参数传递给帮助程序，并验证所需类型和计数的参数。
- 处理帮助程序的输出类型、格式和错误，包括复杂类型或 JSON 架构。
- 以高效且安全的方式实现帮助程序，并避免对模板上下文或数据产生任何副作用或不必要的修改。

实际上，在 Handlebars Template Engine 中将启用四个帮助程序存储桶：

1. Handlebars 库中的默认辅助函数，包括：
   - [启用循环和条件的内置帮助程序](https://handlebarsjs.com/guide/builtin-helpers.html)（#if、#each、#with #unless）
   - [Handlebars.Net.Helpers](https://github.com/Handlebars-Net/Handlebars.Net.Helpers/wiki)
2. 内核中的函数
3. 有助于提示工程师的帮助程序（即 message 或 ）
4. 可用于对模板数据或参数（即 set、get、json、concat、equals、range、array）执行简单逻辑或转换的实用程序帮助程序

### Handlebars Prompt 模板引擎的伪代码

带有内置帮助程序的 Handlebars 提示模板工厂的原型实现可能如下所示：

```csharp
/// Options for Handlebars helpers (built-in and custom).
public sealed class HandlebarsPromptTemplateOptions : HandlebarsHelpersOptions
{
  // Categories tracking built-in system helpers
  public enum KernelHelperCategories
  {
    Prompt,
    Plugin,
    Context,
    String,
    ...
  }

  /// Default character to use for delimiting plugin name and function name in a Handlebars template.
  public string DefaultNameDelimiter { get; set; } = "-";

  /// Delegate for registering custom helpers.
  public delegate void RegisterCustomHelpersCallback(IHandlebars handlebarsInstance, KernelArguments executionContext);

  /// Callback for registering custom helpers.
  public RegisterCustomHelpersCallback? RegisterCustomHelpers { get; set; } = null;

  // Pseudocode, some combination of both KernelHelperCategories and the default HandlebarsHelpersOptions.Categories.
  public List<Enum> AllCategories = KernelHelperCategories.AddRange(Categories);
}
```

```csharp
// Handlebars Prompt Template
internal class HandlebarsPromptTemplate : IPromptTemplate
{
  public async Task<string> RenderAsync(Kernel kernel, KernelArguments arguments, CancellationToken cancellationToken = default)
  {
    arguments ??= new();
    var handlebarsInstance = HandlebarsDotNet.Handlebars.Create();

    // Add helpers for kernel functions
    KernelFunctionHelpers.Register(handlebarsInstance, kernel, arguments, this._options.PrefixSeparator, cancellationToken);

    // Add built-in system helpers
    KernelSystemHelpers.Register(handlebarsInstance, arguments, this._options);

    // Register any custom helpers
    if (this._options.RegisterCustomHelpers is not null)
    {
      this._options.RegisterCustomHelpers(handlebarsInstance, arguments);
    }
    ...

    return await Task.FromResult(prompt).ConfigureAwait(true);
  }
}

```

```csharp
/// Extension class to register Kernel functions as helpers.
public static class KernelFunctionHelpers
{
  public static void Register(
    IHandlebars handlebarsInstance,
    Kernel kernel,
    KernelArguments executionContext,
    string nameDelimiter,
    CancellationToken cancellationToken = default)
  {
      kernel.Plugins.GetFunctionsMetadata().ToList()
          .ForEach(function =>
              RegisterFunctionAsHelper(kernel, executionContext, handlebarsInstance, function, nameDelimiter, cancellationToken)
          );
  }

  private static void RegisterFunctionAsHelper(
    Kernel kernel,
    KernelArguments executionContext,
    IHandlebars handlebarsInstance,
    KernelFunctionMetadata functionMetadata,
    string nameDelimiter,
    CancellationToken cancellationToken = default)
  {
    // Register helper for each function
    handlebarsInstance.RegisterHelper(fullyResolvedFunctionName, (in HelperOptions options, in Context context, in Arguments handlebarsArguments) =>
    {
      // Get parameters from template arguments; check for required parameters + type match

      // If HashParameterDictionary
      ProcessHashArguments(functionMetadata, executionContext, handlebarsArguments[0] as IDictionary<string, object>, nameDelimiter);

      // Else
      ProcessPositionalArguments(functionMetadata, executionContext, handlebarsArguments);

      KernelFunction function = kernel.Plugins.GetFunction(functionMetadata.PluginName, functionMetadata.Name);

      InvokeSKFunction(kernel, function, GetKernelArguments(executionContext), cancellationToken);
    });
  }
  ...
}
```

```csharp
/// Extension class to register additional helpers as Kernel System helpers.
public static class KernelSystemHelpers
{
    public static void Register(IHandlebars handlebarsInstance, KernelArguments arguments, HandlebarsPromptTemplateOptions options)
    {
        RegisterHandlebarsDotNetHelpers(handlebarsInstance, options);
        RegisterSystemHelpers(handlebarsInstance, arguments, options);
    }

    // Registering all helpers provided by https://github.com/Handlebars-Net/Handlebars.Net.Helpers.
    private static void RegisterHandlebarsDotNetHelpers(IHandlebars handlebarsInstance, HandlebarsPromptTemplateOptions helperOptions)
    {
        HandlebarsHelpers.Register(handlebarsInstance, optionsCallback: options =>
        {
            ...helperOptions
        });
    }

    // Registering all helpers built by the SK team to support the kernel.
    private static void RegisterSystemHelpers(
      IHandlebars handlebarsInstance, KernelArguments arguments, HandlebarsPromptTemplateOptions helperOptions)
    {
      // Where each built-in helper will have its own defined class, following the same pattern that is used by Handlebars.Net.Helpers.
      // https://github.com/Handlebars-Net/Handlebars.Net.Helpers
      if (helperOptions.AllCategories contains helperCategory)
      ...
      KernelPromptHelpers.Register(handlebarsContext);
      KernelPluginHelpers.Register(handlebarsContext);
      KernelStringHelpers..Register(handlebarsContext);
      ...
    }
}
```

**注意：这只是一个原型实现，仅用于说明目的。**

Handlebars 支持将不同的对象类型作为 render 上的变量。这为在语义函数中直接使用对象而不仅仅是字符串提供了选项，即循环数组或访问复杂对象的属性，而无需在调用之前序列化或反序列化对象。
