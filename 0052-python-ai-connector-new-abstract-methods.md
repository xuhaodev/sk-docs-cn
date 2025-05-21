
#  和 `ChatCompletionClientBase` （Semantic Kernel Python）`TextCompletionClientBase` 中的新抽象方法 

## 上下文和问题陈述

ChatCompletionClientBase 类当前包含两个抽象方法，即 `get_chat_message_contents` 和 `get_streaming_chat_message_contents`。这些方法为客户提供了标准化的接口，以便与各种模型互动。

> 我们将专注于 `ChatCompletionClientBase` 此 ADR，但 `TextCompletionClientBase` 将具有类似的结构。

随着对许多模型的函数调用的引入，Semantic Kernel 实现了一项名为 的惊人功能 `auto function invocation`。此功能减轻了开发人员手动调用模型请求的函数的负担，使开发过程更加顺畅。

自动函数调用可能会导致副作用，即对 get_chat_message_contents 或 get_streaming_chat_message_contents 的单次调用可能会导致对模型的多次调用。但是，这为我们提供了一个绝佳的机会，可以引入另一个抽象层，该抽象层仅负责对模型进行单个调用。

## 好处

- 为了简化实现，我们可以包括 `get_chat_message_contents` 和 的默认`get_streaming_chat_message_contents`实现。
- 我们可以引入用于跟踪单个模型调用的通用接口，这可以提高系统的整体监控和管理。
- 通过引入此抽象层，向系统添加新的 AI 连接器变得更加高效。

## 详

### 两种新的抽象方法

> 修订版：为了不破坏已实现自己的 AI 连接器的现有客户，这两种方法没有使用 decorator 进行修饰 `@abstractmethod` ，而是在未在内置 AI 连接器中实现时引发异常。

```python
async def _inner_get_chat_message_content(
    self,
    chat_history: ChatHistory,
    settings: PromptExecutionSettings
) -> list[ChatMessageContent]:
    raise NotImplementedError
```

```python
async def _inner_get_streaming_chat_message_content(
    self,
    chat_history: ChatHistory,
    settings: PromptExecutionSettings
) -> AsyncGenerator[list[StreamingChatMessageContent], Any]:
    raise NotImplementedError
```

### 新 `ClassVar[bool]` 变量 in `ChatCompletionClientBase` 用于指示连接器是否支持函数调用

此类变量将在派生类中被覆盖，并在 `get_chat_message_contents` 和  的默认实现中使用`get_streaming_chat_message_contents`。

```python
class ChatCompletionClientBase(AIServiceClientBase, ABC):
    """Base class for chat completion AI services."""

    SUPPORTS_FUNCTION_CALLING: ClassVar[bool] = False
    ...
```

```python
class MockChatCompletionThatSupportsFunctionCalling(ChatCompletionClientBase):

    SUPPORTS_FUNCTION_CALLING: ClassVar[bool] = True

    @override
    async def get_chat_message_contents(
        self,
        chat_history: ChatHistory,
        settings: "PromptExecutionSettings",
        **kwargs: Any,
    ) -> list[ChatMessageContent]:
        if not self.SUPPORTS_FUNCTION_CALLING:
            return ...
        ...
```
