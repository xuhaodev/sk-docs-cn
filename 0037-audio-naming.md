
# 音频抽象和实现命名

## 上下文和问题陈述

### 抽象化

今天我们有以下接口来处理音频：

- IAudioToTextService
- ITextToAudioService

`IAudioToTextService` 接受音频作为输入并返回文本作为输出，接受 `ITextToAudioService` 文本作为输入并返回音频作为输出。

这些抽象的命名并不表示音频转换的性质。例如， `IAudioToTextService` interface 不指示它是 audio transcription 还是 audio translation。这可能是一个问题，同时也是一个优势。

通过拥有通用的文本到音频和音频到文本接口，可以使用相同的接口涵盖不同类型的音频转换（转录、翻译、语音识别、音乐识别等），因为最终它只是文本输入/音频输出合同，反之亦然。在这种情况下，我们可以避免创建多个音频接口，这些接口可能包含完全相同的方法签名。

另一方面，如果将来需要区分用户应用程序内部或 Kernel 本身的音频转换的特定抽象，则可能会出现问题。

### 实现

另一个问题是 OpenAI 的音频实现命名：

- AzureOpenAIAudioToTextService
- OpenAIAudioToTextService
- AzureOpenAITextToAudioService
- OpenAITextToAudioService

在这种情况下，命名是不正确的，因为它没有使用 OpenAI 文档的官方命名，这可能会造成混淆。例如，音频到文本的转换称为 [Speech to text （语音到文本](https://platform.openai.com/docs/guides/speech-to-text)）。

但是，重命名 `OpenAIAudioToTextService` to `OpenAISpeechToTextService` 可能还不够，因为语音转文本 API 有 2 个不同的端点 - `transcriptions` 和 `translations`.当前的 OpenAI 音频连接器使用 `transcriptions` endpoint，但名称 `OpenAISpeechToTextService` 不会反映这一点。可能的名称可以是 `OpenAIAudioTranscriptionService`。

## 考虑的选项

### [抽象 - 选项 #1]

暂时保持命名不变 （`IAudioToTextService`， `ITextToAudioService`） 并将这些接口用于所有与音频相关的连接器，直到我们看到某些特定的音频转换不适合现有的接口签名。

此选项的主要问题是 - 是否有可能需要区分业务逻辑和/或内核本身中的音频转换类型（转录、翻译等）？

可能是的，当应用程序想要在 logic 中同时使用 `transcription` 和 `translation` 时。目前尚不清楚应该注入哪个音频接口来执行具体转换。

在这种情况下，您仍然可以保留当前接口名称，但创建子接口来指定具体的音频转码类型，例如：

```csharp
public interface IAudioTranscriptionService : IAudioToTextService {}
public interface IAudioTranslationService : IAudioToTextService {}
```

它的缺点是这些接口很可能是空的。主要目的是在同时使用它们时能够进行区分。

### [抽象 - 选项 #2]

重命名 `IAudioToTextService` 和 `ITextToAudioService` 更具体的转码类型（例如 `ITextToSpeechService`），对于任何其他类型的音频转码 - 创建一个单独的界面，除了命名之外，该界面可能完全相同。

这种方法的缺点是，即使对于相同类型的转换（例如语音到文本），也很难选择一个好名称，因为在不同的 AI 提供商中，此功能的名称不同，因此很难避免不一致。例如，在 OpenAI 中是[音频转录，](https://platform.openai.com/docs/api-reference/audio/createTranscription)而在 Hugging Face 中是[自动语音识别](https://huggingface.co/models?pipeline_tag=automatic-speech-recognition)。

当前名称 （） 的优点是`IAudioToTextService`它更通用，并且同时涵盖 Hugging Face 和 OpenAI 服务。它不是以 AI 功能命名的，而是以接口约定（音频输入/文本输出）命名的。

### [实现]

至于实现，也有两种选择 - 保持原样或根据 AI 提供者调用功能的方式重命名类，重命名很可能是这里的最佳选择，因为从用户的角度来看，会更容易理解使用了哪些具体的 OpenAI 功能（例如 `transcription` 或 `translation`）， 因此，查找相关文档会更容易，依此类推。

建议的重命名：

- AzureOpenAIAudioToTextService -> AzureOpenAIAudioTranscriptionService
- OpenAIAudioToTextService -> OpenAIAudioTranscriptionService
- AzureOpenAITextToAudioService -> AzureOpenAITextToSpeechService
- OpenAITextToAudioService -> OpenAITextToSpeechService

## 命名比较

| AI 提供商  | 音频转换    | 建议的接口         | 建议的实施             |
| ------------ | ------------------- | -------------------------- | ----------------------------------- |
| Microsoft    | 语音转文本      | IAudioTranscriptionService | MicrosoftSpeechToTextService        |
| 拥抱脸 | 语音识别  | IAudioTranscriptionService | HuggingFaceSpeechRecognitionService |
| 组装AI   | 转录       | IAudioTranscriptionService | AssemblyAIAudioTranscriptionService |
| 开放人工智能       | 音频转录 | IAudioTranscriptionService | OpenAIAudioTranscriptionService     |
| 谷歌       | 语音转文本      | IAudioTranscriptionService | GoogleSpeechToTextService           |
| 亚马逊河       | 转录       | IAudioTranscriptionService | 亚马逊音频转录服务     |
| Microsoft    | 语音翻译  | IAudioTranslationService   | MicrosoftSpeechTranslationService   |
| 开放人工智能       | 音频翻译   | IAudioTranslationService   | OpenAIAudioTranslationService       |
| 元         | 文本到音乐       | ITextToMusicService        | MetaTextToMusicService              |
| Microsoft    | 文本转语音      | ITextToSpeechService       | MicrosoftTextToSpeechService        |
| 开放人工智能       | 文本转语音      | ITextToSpeechService       | OpenAITextToSpeechService           |
| 谷歌       | 文本转语音      | ITextToSpeechService       | GoogleTextToSpeechService           |
| 亚马逊河       | 文本转语音      | ITextToSpeechService       | AmazonTextToSpeechService           |
| 拥抱脸 | 文本转语音      | ITextToSpeechService       | HuggingFaceTextToSpeechService      |
| 元         | 文本到声音       | 待定                        | 待定                                 |
| 拥抱脸 | 文本转音频       | 待定                        | 待定                                 |
| 拥抱脸 | 音频到音频      | 待定                        | 待定                                 |

## 决策结果

重命名现有的音频连接器，以遵循表中提供的命名`Naming comparison`，并对未来的音频抽象和实现使用相同的命名。
