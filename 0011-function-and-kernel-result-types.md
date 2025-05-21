# 将 SKContext 替换为 FunctionResult 和 KernelResult 模型的函数/内核结果类型

## 上下文和问题陈述

方法 `function.InvokeAsync` 并 `kernel.RunAsync` 返回 `SKContext` 为结果类型。这有几个问题：

1. `SKContext` contains 属性 `Result`，即 `string`。基于此，无法在 Kernel 中返回复杂类型或实现流式处理功能。
2. `SKContext` contains property `ModelResults`，它与特定于 LLM 的逻辑耦合，因此它仅适用于特定情况下的语义函数。
3. `SKContext` 作为 pipeline 中函数之间传递信息的机制应该是内部实现。Kernel 的调用者应该提供 input/request 并接收一些结果，但不能。 `SKContext`
4. `SKContext` 包含与上次执行的函数相关的信息，但无法访问有关 pipeline 中特定函数的信息。

## 决策驱动因素

1. 内核应该能够返回复杂类型并支持流式处理功能。
2. 当 kernel 未与 AI logic耦合时，它应该能够以某种方式返回与函数执行相关的数据（例如使用的 token 数量）。
3. `SKContext` 应该作为在函数之间传递信息的内部机制。
4. 应该有一种方法可以区分函数结果和内核结果，因为这些实体本质上是不同的，将来可能包含不同的属性集。
5. 在管道中间访问特定功能结果的可能性将为用户提供更多关于其功能如何执行的见解。

## 考虑的选项

1. 用作 `dynamic` 返回类型 - 此选项提供了一些灵活性，但另一方面删除了强类型，这是 .NET 环境中的首选选项。此外，无法区分函数结果和内核结果。
2. 定义新类型 - `FunctionResult` 和 `KernelResult` - 所选方法。

## 决策结果

new `FunctionResult` 和 `KernelResult` return 类型应涵盖从函数返回复杂类型、支持流式处理以及单独访问每个函数结果的可能性等场景。

### 复杂类型和流式处理

对于复杂类型和流式处理，将在 中 `object Value` 定义`FunctionResult`属性来存储单个函数结果，并在 中`KernelResult`定义属性来存储执行管道中最后一个函数的结果。为了更好的可用性，泛型方法 `GetValue<T>` 将允许强制转换为 `object Value` 特定类型。

例子：

```csharp
// string
var text = (await kernel.RunAsync(function)).GetValue<string>();

// complex type
var myComplexType = (await kernel.RunAsync(function)).GetValue<MyComplexType>();

// streaming
var results = (await kernel.RunAsync(function)).GetValue<IAsyncEnumerable<int>>();

await foreach (var result in results)
{
    Console.WriteLine(result);
}
```

何时 `FunctionResult`/`KernelResult` 将存储 `TypeA` ，调用者将尝试将其转换为 `TypeB` - 在这种情况下 `InvalidCastException` ，将抛出有关类型的详细信息。这将为调用方提供一些信息，应该使用哪种类型进行强制转换。

### 元数据

要返回与函数执行相关的其他信息 - 属性 `Dictionary<string, object> Metadata` 将添加到 `FunctionResult`。这将允许将任何类型的信息传递给调用者，这应该会提供一些关于函数如何执行的见解（例如，使用的令牌数量、AI 模型响应等）。

例子：

```csharp
var functionResult = await function.InvokeAsync(context);
Console.WriteLine(functionResult.Metadata["MyInfo"]);
```

### 多个函数结果

`KernelResult` 将包含函数结果 - 的集合 `IReadOnlyCollection<FunctionResult> FunctionResults`。这将允许从 中获取特定的函数结果 `KernelResult`。Properties `FunctionName` 和 `PluginName` in `FunctionResult` 将有助于从 collection 中获取特定函数。

例：

```csharp
var kernelResult = await kernel.RunAsync(function1, function2, function3);

var functionResult2 = kernelResult.FunctionResults.First(l => l.FunctionName == "Function2" && l.PluginName == "MyPlugin");

Assert.Equal("Result2", functionResult2.GetValue<string>());
```
