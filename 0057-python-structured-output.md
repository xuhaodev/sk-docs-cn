
# 在语义内核 Python 中支持 OpenAI 的结构化输出

## 上下文

去年，OpenAI 推出了 JSON 模式，这是旨在构建可靠的 AI 驱动应用程序的开发人员的基本功能。虽然 JSON 模式有助于提高生成有效 JSON 输出的模型可靠性，但它未能严格遵守特定架构。此限制导致开发人员采用解决方法（例如自定义开源工具、迭代提示和重试）来确保输出符合所需的格式。

为了解决这个问题，OpenAI 引入了 **结构化输出**，该功能旨在确保模型生成的输出完全符合开发人员指定的 JSON 架构。这一进步使开发人员能够通过保证 AI 输出与预定义结构匹配来构建更强大的应用程序，从而提高与下游系统的互作性。

在最近的评估中，具有结构化输出的新 GPT-4o-2024-08-06 模型在遵守复杂的 JSON 模式方面表现出 100% 的完美分数，而 GPT-4-0613 的得分不到 40%。结构化输出简化了从非结构化输入生成可靠结构化数据的过程，这是各种 AI 驱动的应用程序（如数据提取、自动化工作流和函数调用）的核心需求。

---

## 问题陈述

使用 OpenAI API 构建 AI 驱动型解决方案的开发人员在从非结构化输入中提取结构化数据时经常面临挑战。确保模型输出符合预定义的 JSON 架构对于创建可靠且可互作的系统至关重要。但是，当前模型（即使使用 JSON 模式）也不能保证架构一致性，从而导致效率低下、错误以及以重试和自定义工具的形式出现的额外开发开销。

随着结构化输出的引入，OpenAI 模型现在能够严格遵守开发人员提供的 JSON 架构。此功能消除了对繁琐解决方法的需求，并提供了一种更简化、更高效的方法来确保模型输出的一致性和可靠性。将结构化输出集成到 Semantic Kernel 编排 SDK 中，将使开发人员能够创建更强大、符合架构的应用程序，减少错误并提高整体生产力。

## 超出范围

此 ADR 将侧重于 `structured outputs` `response_format` 函数调用方面，而不是函数调用方面。将来将围绕该 ADR 创建后续 ADR。

## 使用结构化输出

### 响应格式

OpenAI 提供了一种设置 `response_format` 提示执行设置属性的新方法：

```python
from pydantic import BaseModel

from openai import OpenAI


class Step(BaseModel):
    explanation: str
    output: str


class MathResponse(BaseModel):
    steps: list[Step]
    final_answer: str


client = AsyncOpenAI()

completion = await client.beta.chat.completions.parse(
    model="gpt-4o-2024-08-06",
    messages=[
        {"role": "system", "content": "You are a helpful math tutor."},
        {"role": "user", "content": "solve 8x + 31 = 2"},
    ],
    response_format=MathResponse, # for example, a Pydantic model type is directly configured
)

message = completion.choices[0].message
if message.parsed:
    print(message.parsed.steps)
    print(message.parsed.final_answer)
else:
    print(message.refusal)
```

对于非 Pydantic 模型，SK 需要使用 `KernelParameterMetadata`'s `schema_data` 属性。这表示 SK 函数的 JSON 架构：

```json
{
  "type": "object",
  "properties": {
    "steps": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "explanation": {
            "type": "string"
          },
          "output": {
            "type": "string"
          }
        },
        "required": ["explanation", "output"],
        "additionalProperties": false
      }
    },
    "final_answer": {
      "type": "string"
    }
  },
  "required": ["steps", "final_answer"],
  "additionalProperties": false
}
```

要创建所需的 `json_schema` `response_format`：

```json
"response_format": {
    "type": "json_schema",
    "json_schema": {
        "name": "math_response",
        "strict": true,
        "schema": { // start of existing SK `schema_data` from above
            "type": "object",
            "properties": {
                "steps": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                    "explanation": {
                        "type": "string"
                    },
                    "output": {
                        "type": "string"
                    }
                    },
                    "required": ["explanation", "output"],
                    "additionalProperties": false
                }
                },
                "final_answer": {
                    "type": "string"
                }
            },
            "required": ["steps", "final_answer"],
            "additionalProperties": false
        } // end of existing SK `schema_data` from above
    }
}
```

#### 处理流式处理响应格式

新的 `structured output` 响应格式处于测试阶段，流式聊天完成代码应按如下方式处理（这与我们当前的流式聊天完成调用不同）：

```python
async with client.beta.chat.completions.stream(
    model='gpt-4o-mini',
    messages=messages,
    tools=[pydantic_function_tool(SomeClass)],
) as stream:
    async for event in stream:
        if event.type == 'content.delta':
            print(event.delta, flush=True, end='')
        elif event.type == 'content.done':
            content = event.content
        elif event.type == 'tool_calls.function.arguments.done':
            tool_calls.append({'name': event.name, 'parsed_arguments': event.parsed_arguments})

print(content)
```

管理 `OpenAIHandler` 聊天完成项的类需要处理新的结构化输出流式处理方法，类似于：

```python
async def _initiate_chat_stream(self, settings: OpenAIChatPromptExecutionSettings):
    """Initiate the chat stream request and return the stream."""
    return self.client.beta.chat.completions.stream(
        model='gpt-4o-mini',
        messages=settings.messages,
        tools=[pydantic_function_tool(SomeClass)],
    )

async def _handle_chat_stream(self, stream):
    """Handle the events from the chat stream."""
    async for event in stream:
        if event.type == 'content.delta':
            chunk_metadata = self._get_metadata_from_streaming_chat_response(event)
            yield [
                self._create_streaming_chat_message_content(event, event.delta, chunk_metadata)
            ]
        elif event.type == 'tool_calls.function.arguments.done':
            # Handle tool call results as needed
            tool_calls.append({'name': event.name, 'parsed_arguments': event.parsed_arguments})

# An example calling method could be:
async def _send_chat_stream_request(self, settings: OpenAIChatPromptExecutionSettings):
    """Send the chat stream request and handle the stream."""
    async with await self._initiate_chat_stream(settings) as stream:
        async for chunk in self._handle_chat_stream(stream):
            yield chunk
```

处理流式或非流式聊天完成的方法将基于 `response_format` 执行设置 - 无论它使用 Pydantic 模型类型还是 JSON 模式。

由于聊天 `response_format` 补全方法与目前的聊天补全方法不同，我们需要维护单独的实现来处理聊天补全，直到 OpenAI 毕业后正式将 `response_format` 该方法集成到主库中。

### 标注

-  `structured output` `response_format` 此时仅限于单个对象类型。我们将使用 Pydantic 验证器来确保用户只指定正确的对象类型/数量：

```python
@field_validator("response_format", mode="before")
    @classmethod
    def validate_response_format(cls, value):
        """Validate the response_format parameter."""
        if not isinstance(value, dict) and not (isinstance(value, type) and issubclass(value, BaseModel)):
            raise ServiceInvalidExecutionSettingsError(
                "response_format must be a dictionary or a single Pydantic model class"
            )
        return value
```

- 我们需要提供良好（且易于查找）的文档，让用户和开发人员知道哪些 OpenAI/AzureOpenAI 模型/API 版本支持 `structured outputs`。

### 所选解决方案

- 响应格式：由于这里只有一种方法，我们应该集成一个干净的实现，以使用我们现有的 and 代码来定义流式和非流式聊天完成 `OpenAIChatCompletionBase` `OpenAIHandler` 。
