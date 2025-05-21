
# 在模板函数调用中添加对多个命名参数的支持

## 上下文和问题陈述

本机函数现在支持多个参数，这些参数从具有相同名称的上下文值填充。语义函数目前仅支持调用不超过 1 个参数的原生函数。这些更改的目的是添加对在具有多个命名参数的语义函数中调用本机函数的支持。

## 决策驱动因素

- 与指导对等
- 可读性
- 与 SK 开发人员熟悉的语言相似
- YAML 兼容性

## 考虑的选项

### 语法思路 1：使用逗号

```handlebars
{{Skill.MyFunction street: "123 Main St", zip: "98123", city:"Seattle", age: 25}}
```

优点：

- 逗号可以使较长的函数调用更易于阅读，尤其是在 arg 分隔符（在本例中为冒号）前后允许使用空格时。

缺点：

- 指南不使用逗号
- 空格已在其他地方用作分隔符，因此无需增加支持逗号的复杂性

### 语法构想 2：JavaScript/C# 样式分隔符（冒号）

```handlebars

{{MyFunction street:"123 Main St" zip:"98123" city:"Seattle" age: "25"}}

```

优点：

- 类似于 JavaScript 对象语法和 C# 命名参数语法

缺点：

- 与使用等号作为 arg 部分分隔符的 Guidance 语法不一致
- 如果我们将来支持 YAML 提示符，则与 YAML 键/值对太相似了。可能可以支持冒号作为分隔符，但最好有一个不同于普通 YAML 语法的分隔符。

### 语法思路 3：Python/Guidance-Style 分隔符

```handlebars
{{MyFunction street="123 Main St" zip="98123" city="Seattle"}}
```

优点：

- 类似于 Python 的关键字参数语法
- 类似于 Guidance 的命名参数语法
- 如果我们将来支持 YAML 提示，则与 YAML 键/值对不太相似。

缺点：

- 与 C# 语法不一致

### 语法思路 4：允许 arg 名称/值分隔符之间有空格

```handlebars
{{MyFunction street="123 Main St" zip="98123" city="Seattle"}}
```

优点：

- 遵循许多具有空格灵活性的编程语言所遵循的约定，其中代码中的空格、制表符和换行符不会影响程序的功能

缺点：

- 提升除非可以使用逗号否则更难阅读的代码（请参见 [使用逗号](#syntax-idea-1-using-commas)）
- 支持的复杂性更高
- 与不支持 = 符号前后空格的 Guidance 不一致。

## 决策结果

选择的选项：“语法理念 3：Python/Guidance-Style 关键字参数”，因为它与指导方针的语法非常一致，并且与 YAML 最兼容，以及“语法理念 4：允许在参数名称/值分隔符之间使用空格”，以获得更灵活的开发人员体验。

其他决定：

- 继续支持最多 1 个位置参数以实现向后兼容性。目前，传递给函数的参数被假定为 `$input` 上下文变量。

例

```handlebars
{{MyFunction "inputVal" street="123 Main St" zip="98123" city="Seattle"}}
```

- 仅允许将 arg 值定义为字符串或变量，例如

```handlebars
{{MyFunction street=$street zip="98123" city="Seattle"}}
```

如果 function 需要 argument 的 value 不是 string，SDK 将使用相应的 TypeConverter 来解析 Evaluating 表达式时提供的字符串。
