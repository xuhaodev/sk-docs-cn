
# 文件服务

## 上下文和问题陈述
OpenAI 提供了文件服务，用于上传文件用于*辅助检索*或*模型微调*： `https://api.openai.com/v1/files`

其他提供商也可能提供某种类型的文件服务，例如 Gemini。

> 注意： *Azure Open AI* 目前不支持 OpenAI 文件服务 API。

## 考虑的选项

1. 添加 OpenAI 文件服务支持 `Microsoft.SemanticKernel.Experimental.Agents`
2. 添加文件服务抽象并实现对 OpenAI 的支持
3. 添加 OpenAI 文件服务支持，无需抽象

## 决策结果

> 选项 3. **添加 OpenAI 文件服务支持，无需抽象**
> 使用 label 将代码标记为实验代码： `SKEXP0010`

定义通用文件服务接口为除 OpenAI 之外的其他供应商提供了一个扩展点**。

## 选项的优缺点

### 选项 1.添加 OpenAI 文件服务支持 `Microsoft.SemanticKernel.Experimental.Agents`
**优点：**
1. 对现有 AI 连接器没有影响。

**缺点：**
1. 不能通过 AI 连接器重复使用。
1. 没有常见的抽象。
1. 用于 OpenAI 助手以外的用途的非自然依赖项绑定。

### 选项 2.添加文件服务抽象并实现对 OpenAI 的支持
**优点：**
1. 定义文件服务交互的通用接口。
1. 允许对供应商特定的服务进行专业化。

**缺点：**
1. 其他系统可能与现有假设不同。


### 选项 3.添加 OpenAI 文件服务支持，无需抽象
**优点：**
1. 提供对 OpenAI file-service 的支持。

**缺点：**
1. 来自其他供应商的文件服务产品按具体情况提供支持，没有通用性。


## 更多信息

### BinaryContent 的签名

> 注意： `BinaryContent` object 能够提供任一 `BinaryData` 或 `Stream` 任何调用的构造函数。

#### `Microsoft.SemanticKernel.Abstractions`

```csharp
namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents binary content.
/// </summary>
public sealed class BinaryContent : KernelContent
{
    public BinaryContent(
        BinaryData content,
        string? modelId = null,
        object? innerContent = null,
        IReadOnlyDictionary<string, object?>? metadata = null);

    public BinaryContent(
        Func<Stream> streamProvider,
        string? modelId = null,
        object? innerContent = null,
        IReadOnlyDictionary<string, object?>? metadata = null);

    public Task<BinaryData> GetContentAsync();

    public Task<Stream> GetStreamAsync();
}
```
### 选项 3 的签名：

#### `Microsoft.SemanticKernel.Connectors.OpenAI`
```csharp
namespace Microsoft.SemanticKernel.Connectors.OpenAI;

public sealed class OpenAIFileService
{
    public async Task<OpenAIFileReference> GetFileAsync(
        string id,
        CancellationToken cancellationToken = default);

    public async Task<IEnumerable<OpenAIFileReference>> GetFilesAsync(CancellationToken cancellationToken = default);

    public async Task<BinaryContent> GetFileContentAsync(
        string id,
        CancellationToken cancellationToken = default);

    public async Task DeleteFileAsync(
        string id,
        CancellationToken cancellationToken = default);

    public async Task<OpenAIFileReference> UploadContentAsync(
        BinaryContent content,
        OpenAIFileUploadExecutionSettings settings,
        CancellationToken cancellationToken = default);
}

public sealed class OpenAIFileUploadExecutionSettings
{
    public string FileName { get; }
 
    public OpenAIFilePurpose Purpose { get; }
}

public sealed class OpenAIFileReference
{
    public string Id { get; set; }

    public DateTime CreatedTimestamp { get; set; }

    public string FileName { get; set; }
    
    public OpenAIFilePurpose Purpose { get; set; }

    public int SizeInBytes { get; set; }
}

public enum OpenAIFilePurpose
{
    Assistants,
    Finetuning,
}
```
