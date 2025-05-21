
# 聊天完成角色的 SK 提示语法

## 上下文和问题陈述

如今，SK 无法将提示中的文本块标记为具有特定角色（例如助手、系统或用户）的消息。因此，SK 无法将提示分块到聊天完成连接器所需的消息列表中。

此外，可以使用各种模板引擎（如 Handlebars、Jinja 等）支持的一系列模板语法来定义提示。这些语法中的每一种都可能以不同的方式表示聊天消息或角色。因此，如果没有适当的抽象，模板引擎语法可能会泄漏到 SK 的域中，从而将 SK 与模板引擎耦合，从而无法支持新的模板引擎。

<!-- This is an optional element. Feel free to remove. -->

## 决策驱动因素

- 应该可以将提示中的文本块标记为具有角色的消息，以便可以将其转换为聊天消息列表，以供聊天完成连接器使用。
- 特定于模板引擎 message/role 的语法应映射到 SK message/role 语法，以便从特定的模板引擎语法中抽象 SK。

## 考虑的选项

**1. 消息/角色标签由提示中指定的函数生成。** 此选项依赖于许多模板引擎可以调用模板中指定的函数这一事实。因此，可以使用模板引擎注册内部函数，该函数将根据提供的参数创建 message/model 标签。提示模板引擎将执行该函数并将函数结果发送到该提示模板中，并且渲染的提示将为每个消息/角色提供一个部分，以这些标签进行装饰。以下是如何使用 SK basic 模板引擎和 Handlebars 完成此作的示例：

功能：

```csharp
internal class SystemFunctions
{
    public string Message(string role)
    {
        return $"<message role=\"{role}\">";
    }
}
```

提示：

```bash
{{message role="system"}}
You are a bank manager. Be helpful, respectful, appreciate diverse language styles.
{{message role="system"}}

{{message role="user"}}
I want to {{$input}}
{{message role="user"}}
```

呈现的提示符：

```xml
<message role="system">
You are a bank manager. Be helpful, respectful, appreciate diverse language styles.
</message>
<message role="user">
I want to buy a house.
</message>
```

**2. 消息/角色标签由特定于提示的机制生成。** 此选项利用模板引擎语法构造、帮助程序和处理程序（函数除外）将 SK 消息/角色标记注入到最终提示中。
在下面的示例中，要解析使用 handlebars 语法的提示，我们需要注册一个数据块帮助程序（当 Handlebars 引擎遇到它时调用的回调）以在结果提示中发出 SK message/role 标签。

Block 帮助程序：

```csharp
this.handlebarsEngine.RegisterHelper("system", (EncodedTextWriter output, Context context, Arguments arguments) => {
  //Emit the <message role="system"> tags
});
this.handlebarsEngine.RegisterHelper("user", (EncodedTextWriter output, Context context, Arguments arguments) => {
  //Emit the <message role="user"> tags
});
```

提示：

```bash
{{#system~}}
You are a bank manager. Be helpful, respectful, appreciate diverse language styles.
{{~/system}}
{{#user~}}
I want to {{$input}}
{{~/user}}
```

呈现的提示符：

```xml
<message role="system">
You are a bank manager. Be helpful, respectful, appreciate diverse language styles.
</message>
<message role="user">
I want to buy a house.
</message>
```

**3. 消息/角色标签应用于提示模板引擎之上**。此选项假定直接在提示符中指定 SK message/role 标记，以模板引擎不解析/处理它们并将其视为常规文本的方式表示 message/role 块。
在下面的示例中，提示 `<message role="*">` 标签标记系统和用户消息的边界，SK basic 模板引擎将其视为常规文本，而不进行处理。

提示：

```xml
<message role="system">
You are a bank manager. Be helpful, respectful, appreciate diverse language styles.
</message>
<message role="user">
I want to {{$input}}
</message>
```

呈现的提示符：

```xml
<message role="system">
You are a bank manager. Be helpful, respectful, appreciate diverse language styles.
</message>
<message role="user">
I want to buy a house.
</message>
```

## 优点和缺点

**1. 消息/角色标签由提示中指定的函数生成**

优点：

- 函数可以定义一次，并在支持函数调用的提示模板中重用。

缺点：

- 某些模板引擎可能不支持函数。
- 系统/内部功能应由 SK 预先注册，因此用户无需导入它们。
- 每个提示模板引擎都将包含如何发现和调用 system/internal 函数。

**2. 消息/角色标签由提示特定机制生成**

优点：

- 使用最佳模板引擎语法构造启用消息/角色表示，与该特定引擎的其他构造保持一致。

缺点：

- 每个提示模板引擎都必须注册回调/处理程序，以处理模板语法构造渲染以发出 SK 消息/角色标签。

**3. 消息/角色标签应用于提示模板引擎之上**

优点：

- 无需更改 prompt 模板引擎。

缺点：

- message/role 标记语法可能与该模板引擎的其他语法构造不一致。
- 消息/角色标记中的语法错误将由解析提示的组件检测，而不是由提示模板引擎检测。

## 决策结果

我们同意不将我们自己局限于一个可能的选项，因为将该选项应用于我们将来可能需要支持的新模板引擎可能不可行。相反，每次添加新的模板引擎时，都应该考虑每个选项，并且应该为该特定模板引擎首选最佳选项。

大家还同意，目前，我们将采用“3.message/role tags are applied on top of the prompt template engine“选项，以支持 SK 中的消息/角色提示语法，目前使用该 `BasicPromptTemplateEngine` 引擎。
