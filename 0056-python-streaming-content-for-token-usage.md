
# 令牌使用信息的流式处理内容 （Semantic Kernel Python）

## 上下文和问题陈述

目前，  Semantic Kernel 中的 `StreamingChatMessageContent` （inherits from `StreamingContentMixin`） 需要指定 choice 索引。这会产生限制，因为来自 **OpenAI 的流式聊天完成** API 的令牌使用信息将在最后一个块中返回，其中 choices 字段为空，这会导致该块的选择索引未知。有关更多信息，请参阅 [OpenAI API 文档](https://platform.openai.com/docs/api-reference/chat/create)并查找该 `stream_options` 字段。

> 最后一个区块中返回的令牌使用信息是 **** 聊天完成请求的总令牌使用量，与指定的选项数量无关。话虽如此，即使请求了多个选项，流式响应中也只有一个包含令牌使用信息的块。

我们目前的数据结构 `StreamingChatMessageContent`：

```Python
# semantic_kernel/content/streaming_chat_message_content.py
class StreamingChatMessageContent(ChatMessageContent, StreamingContentMixin):

# semantic_kernel/content/chat_message_content.py
class ChatMessageContent(KernelContent):
    content_type: Literal[ContentTypes.CHAT_MESSAGE_CONTENT] = Field(CHAT_MESSAGE_CONTENT_TAG, init=False)  # type: ignore
    tag: ClassVar[str] = CHAT_MESSAGE_CONTENT_TAG
    role: AuthorRole
    name: str | None = None
    items: list[Annotated[ITEM_TYPES, Field(..., discriminator=DISCRIMINATOR_FIELD)]] = Field(default_factory=list)
    encoding: str | None = None
    finish_reason: FinishReason | None = None

# semantic_kernel/content/streaming_content_mixin.py
class StreamingContentMixin(KernelBaseModel, ABC):
    choice_index: int

# semantic_kernel/content/kernel_content.py
class KernelContent(KernelBaseModel, ABC):
    inner_content: Any | None = None
    ai_model_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
```

## 提案 1

在非流式处理响应中，令牌使用情况作为模型响应的一部分以及可以有多个选项返回。然后，我们将选择解析为单独的 `ChatMessageContent`s，每个 s 都包含令牌使用信息，即使令牌使用是针对整个响应的，而不仅仅是单个选择。

考虑到相同的策略，当流响应中的所有选项最终由其  .`choice_index`由于我们知道请求的选择数量，因此我们可以执行以下步骤：

1. 复制请求的每个选项的最后一个块，以创建 s 列表 `StreamingChatMessageContent`，其中令牌使用信息包含在元数据中。
2. 为每个复制的块分配一个 choice 索引，从 0 开始。
3. 将列表中的复制块流式传输回客户端。

### 其他注意事项

目前，当两个 `StreamingChatMessageContent`s“添加”在一起时，元数据不会合并。我们需要确保在连接块时合并元数据。当存在冲突的元数据键时，第二个 chunk 中的元数据应覆盖第一个 chunk 中的元数据：

```Python
class StreamingChatMessageContent(ChatMessageContent, StreamingContentMixin):
    ...

    def __add__(self, other: "StreamingChatMessageContent") -> "StreamingChatMessageContent":
        ...

        return StreamingChatMessageContent(
            ...,
            metadata=self.metadata | other.metadata,
            ...
        )

    ...
```

### 风险

没有与此提案相关的重大更改和已知风险。

## 提案 2

我们允许 choice 索引在 class 中是可选的 `StreamingContentMixin` 。这将允许选择索引在 `None` 最后一个块中返回令牌使用信息时。选择索引将设置 `None` 在最后一个 chunk 中，客户端可以相应地处理 token 使用信息。

```Python
# semantic_kernel/content/streaming_content_mixin.py
class StreamingContentMixin(KernelBaseModel, ABC):
    choice_index: int | None
```

与提案 1 相比，这是一个更简单的解决方案，并且更符合 OpenAI API 返回的内容，即令牌使用与任何特定选择无关。

### 风险

这可能是一个重大更改，因为该 `choice_index` 字段当前是必需的。此方法还使流内容串联更加复杂，因为当 choice index 时需要以不同的方式处理它`None`。

## 提案 3

我们将 和 合并 `ChatMessageContent` `StreamingChatMessageContent` 为单个类 `ChatMessageContent`，并将 标记为 `StreamingChatMessageContent` 已弃用。该 `StreamingChatMessageContent` 类将在将来的发行版中删除。然后，我们将 [Proposal 1](#proposal-1) 或 [Proposal 2](#proposal-2) 应用于 `ChatMessageContent` 该类，以处理令牌使用信息。

这种方法通过消除对用于流式处理聊天消息的单独类的需求来简化代码库。该 `ChatMessageContent` 类将能够处理流式和非流式聊天消息。

```Python
# semantic_kernel/content/streaming_chat_message_content.py
@deprecated("StreamingChatMessageContent is deprecated. Use ChatMessageContent instead.")
class StreamingChatMessageContent(ChatMessageContent):
    pass

# semantic_kernel/content/chat_message_content.py
class ChatMessageContent(KernelContent):
    ...
    # Add the choice_index field to the ChatMessageContent class and make it optional
    choice_index: int | None

    # Add the __add__ method to merge the metadata when two ChatMessageContent instances are added together. This is currently an abstract method in the `StreamingContentMixin` class.
    def __add__(self, other: "ChatMessageContent") -> "ChatMessageContent":
        ...

        return ChatMessageContent(
            ...,
            choice_index=self.choice_index,
            ...
        )

    # Add the __bytes__ method to return the bytes representation of the ChatMessageContent instance. This is currently an abstract method in the `StreamingContentMixin` class.
    def __bytes__(self) -> bytes:
        ...
```

### 风险

我们正在统一流式和非流式聊天消息的返回数据结构，这可能会导致开发人员最初感到困惑，特别是如果他们不知道该类已弃用 `StreamingChatMessageContent` ，或者他们来自 SK .Net。如果开发人员从 Python 开始，但后来转向 .Net 进行生产，它也可能会产生更清晰的学习曲线。这种方法还引入了对 AI 连接器的重大更改，因为返回的数据类型会有所不同。

> 我们还需要 `StreamingTextContent` 以类似的方式更新此提案的`TextContent` and。

## 提案 4

与[提案 3 类似](#proposal-3)，我们将 和 合并 `ChatMessageContent` `StreamingChatMessageContent` 为单个类 `ChatMessageContent`，并将 标记为 `StreamingChatMessageContent` 已弃用。此外，我们还将引入另一个名为 的新 mixin `ChatMessageContentConcatenationMixin` ，用于处理两个实例的串联 `ChatMessageContent` 。然后，我们将 [Proposal 1](#proposal-1) 或 [Proposal 2](#proposal-2) 应用于 `ChatMessageContent` 该类，以处理令牌使用信息。

```Python
# semantic_kernel/content/streaming_chat_message_content.py
@deprecated("StreamingChatMessageContent is deprecated. Use ChatMessageContent instead.")
class StreamingChatMessageContent(ChatMessageContent):
    pass

# semantic_kernel/content/chat_message_content.py
class ChatMessageContent(KernelContent, ChatMessageContentConcatenationMixin):
    ...
    # Add the choice_index field to the ChatMessageContent class and make it optional
    choice_index: int | None

    # Add the __bytes__ method to return the bytes representation of the ChatMessageContent instance. This is currently an abstract method in the `StreamingContentMixin` class.
    def __bytes__(self) -> bytes:
        ...

class ChatMessageContentConcatenationMixin(KernelBaseModel, ABC):
    def __add__(self, other: "ChatMessageContent") -> "ChatMessageContent":
        ...
```

这种方法将 `ChatMessageContent` 类和串联逻辑的关注点分为两个单独的类。这有助于保持代码库的整洁和可维护性。

### 风险

与[提案 3 相同](#proposal-3)。

## 决策结果

为了最大限度地减少对客户和现有代码库的影响，我们将使用 [提案 1](#proposal-1) 来处理 OpenAI 流式响应中的代币使用信息。此提案向后兼容，并与当前非流式响应的数据结构保持一致。我们还将确保在连接两个实例时正确合并元数据 `StreamingChatMessageContent` 。此方法还确保令牌使用信息将与流响应中的所有选项相关联。

[提案 3](#proposal-3) 和 [提案 4](#proposal-4) 仍然有效，但在这个阶段可能还为时过早，因为大多数服务仍然为流式和非流式响应返回不同类型的对象。我们将在未来的重构工作中牢记它们。
