
# {已解决问题和解决方案的简称}

## 上下文和问题陈述

该 `KernelFunctionMetadata.PluginName` 属性作为调用 `KernelPlugin.GetFunctionsMetadata`.
此行为的原因是允许一个 `KernelFunction` 实例与多个实例关联 `KernelPlugin` 。
此行为的缺点是该 `KernelFunctionMetadata.PluginName` 属性对回调不可用 `IFunctionFilter` 。

此 ADR 的目的是提出一项更改，允许开发人员决定何时 `KernelFunctionMetadata.PluginName` 填充。

问题：

1. [调查是否应该修复 KernelFunction 元数据中的 PluginName](https://github.com/microsoft/semantic-kernel/issues/4706)
1. [IFunctionFilter 中 FunctionInvokingContext 内的插件名称为 null](https://github.com/microsoft/semantic-kernel/issues/5452)

## 决策驱动因素

- 不要破坏现有应用程序。
- 提供使 `KernelFunctionMetadata.PluginName` 属性可用于 `IFunctionFilter` 回调的功能。

## 考虑的选项

- 将每个添加到后`KernelFunction`对其进行克隆`KernelPlugin`，并在 clone 中设置插件名称`KernelFunctionMetadata`。
- 添加新参数，以 `KernelPluginFactory.CreateFromFunctions` 启用在关联实例中设置插件名称 `KernelFunctionMetadata` 。一旦设置， `KernelFunctionMetadata.PluginName` 就无法更改。尝试这样做将导致 `InvalidOperationException` Throwing。
- 保持原样，不支持此用例，因为它可能会使 Semantic Kernel 的行为看起来不一致。

## 决策结果

所选选项：克隆每个 `KernelFunction`，因为结果是一致的行为，并且允许将同一函数添加到多个 `KernelPlugin`中。

## 选项的优缺点

### 克隆每个 `KernelFunction`

公关：https://github.com/microsoft/semantic-kernel/pull/5422

- 糟糕的是，同一个函数可以添加到多个 `KernelPlugin`中。
- 糟糕，因为行为是一致的。
- 很好，因为 API 签名没有重大更改。
- Bad，因为创建了其他 `KernelFunction` 实例。

### 将新参数添加到 `KernelPluginFactory.CreateFromFunctions`

公关：https://github.com/microsoft/semantic-kernel/pull/5171

- 很好，因为没有 `KernelFunction` 创建其他实例。
- Bad 的，因为同一个函数不能添加到多个 `KernelPlugin` 的
- 不好，因为它会让人感到困惑，即根据 的创建方式 `KernelPlugin` ，它的行为会有所不同。
- 糟糕，因为对 API 签名进行了细微的重大更改。
