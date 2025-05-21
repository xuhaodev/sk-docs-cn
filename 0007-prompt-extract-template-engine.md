# 从 Semantic Kernel 核心中提取 Prompt Template Engine

## 上下文和问题陈述

Semantic Kernel 包括一个默认的提示模板引擎，用于渲染 Semantic Kernel 提示，即 `skprompt.txt` 文件。提示模板在发送到 AI 之前进行渲染，以允许动态生成提示，例如，包括输入参数或本机或语义函数执行的结果。
为了降低 Semantic Kernel 的复杂性和 API 表面，将提取提示模板引擎并将其添加到它自己的包中。

长期目标是实现以下方案：

1. 实现自定义模板引擎，例如，使用 Handlebars 模板。现在支持此功能，但我们希望简化要实现的 API。
2. 支持使用零个或多个模板引擎。

## 决策驱动因素

* 减少 API 表面和语义内核核心的复杂性。
* 简化 `IPromptTemplateEngine` 界面，以便更轻松地实现自定义模板引擎。
* 在不破坏现有客户端的情况下进行更改。

## 决策结果

* 创建名为 的新程序包 `Microsoft.SemanticKernel.TemplateEngine`。
* 维护所有提示模板引擎代码的现有命名空间。
* 简化 `IPromptTemplateEngine` 接口，仅要求实现 `RenderAsync`.
* 动态加载现有组件（`PromptTemplateEngine`如果 `Microsoft.SemanticKernel.TemplateEngine` 程序集可用）。
