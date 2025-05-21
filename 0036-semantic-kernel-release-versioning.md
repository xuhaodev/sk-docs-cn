
# 语义内核版本版本控制

## 上下文和问题陈述

此 ADR 总结了在发布新版本的 Semantic Kernel 时用于更改包版本号的方法。

ADR 与语义内核的 .Net、Java 和 Python 版本相关（一旦包达到 v1.0）。

1. [NuGet 上的语义内核](https://www.nuget.org/packages/Microsoft.SemanticKernel/)
1. [Semantic Kernel on Python 包索引](https://pypi.org/project/semantic-kernel/)
1. [Maven Central 上的语义内核](https://central.sonatype.com/search?q=com.microsoft.semantic-kernel)

## 决策驱动因素

### 语义版本控制和文档

- 我们不会遵守严格的[语义版本控制](https://semver.org/)，因为 NuGet 包并不严格遵循这一点。
- 我们将在发行说明中记录微不足道的不兼容 API 更改
- 我们预计 Semantic Kernel 的大多数定期更新都将包含新功能，并且会向后兼容
 
### 包版本控制

- 在创建新发行版时，我们将在所有软件包上使用相同的版本号
- 所有软件包都包含在每个发行版中，并且即使未更改特定软件包，版本号也会递增
- 我们将测试每个版本以确保所有软件包都兼容
- 我们建议客户使用相同版本的软件包，这是我们将支持的配置

### 主要版本

- 我们不会为影响较小的不兼容 API 更改增加 MAJOR 版本 <sup>1</sup>
- 我们不会因对实验性功能或 Alpha 包的 API 更改而增加 MAJOR 版本
  
<sup>1</sup> 低影响不兼容的 API 更改通常只影响 Semantic Kernel 内部实现或单元测试。我们预计不会对 Semantic Kernel 的 API 表面进行任何重大更改。
  
### 次要版本

- 当我们以向后兼容的方式添加功能时，我们将递增 MINOR 版本
  
### 补丁版本

- 当发布时我们只进行了向后兼容的错误修复，我们将增加 PATCH 版本。

### 版本后缀

使用以下版本后缀：

- `preview` 或 `beta` - 此后缀用于接近发行版的软件包，例如，version `1.x.x-preview` 将用于接近其版本 1.x 发行版的软件包。软件包将功能完整，接口将非常接近发行版。后缀 `preview` 用于 .Net 版本，也 `beta` 用于 Python 版本。
- `alpha` - 此后缀用于功能不完整且公共接口仍在开发中且预期会更改的软件包。
