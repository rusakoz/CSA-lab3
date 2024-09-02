# Архитектура компьютера. Лабораторная работа №3

- Кожемякин Руслан Алексеевич, P3223
- alg -> asm | acc | neum | hw | instr | binary -> struct | stream | mem | pstr | prob1 | cache
- Базовый вариант

## Язык программирования

``` ebnf
<program> ::= <statement>

<statement> ::= <declaration>
              | <input_statement>
              | <print_statement>
              | <if_statement>
              | <while_statement>

<declaration>     ::= <type> <name> "=" <expression> <nl>
<input_statement> ::= "<<" <name> <nl>
<print_statement> ::= ">>" <expression> <nl>
<if_statement>    ::= "if" "(" <expression> ")" "{" <program> "}" <nl>
<while_statement> ::= "while" "(" <expression> ")" "{" <program> "}" <nl>

<expression> ::= <term> | <expression> ( <binary_op> | <comparison_op> ) <expression>
<term> ::= <name>
         | <string_literal>
         | <number>
         | <expression>

<type>           ::= "int" | "string"
<name>           ::= "[_a-zA-Z]\w*"
<string_literal> ::= "[^"]*"
<number>         ::= "[+-]?[0-9]\d*|0"
<nl>             ::= "\n"

<binary_op>     ::= "+" | "-" | "*" | "/" | "%"
<comparison_op> ::= "==" | "!=" | ">" | "<" | ">=" | "<="

comment         ::= "//" <any symbols except "\n">
```
Код выполняется последовательно. Операции:
- `+` сложение
- `-` вычитание
- `*` умножение
- `/` целочисленное деление
- `%` остаток от деления
- `>` сравнение(больше)
- `>=` сравнение(больше, либо равно)
- `<` сравнение(меньше)
- `<=` сравнение(меньше, либо равно)
- `==` сравнение(равенство)
- `!=` сравнение(неравенство)

В языке реализованны следующие возможности:
- Память выделяется статически, при запуске модели. Видимость данных -- глобальная. Поддержка литералов -- строковая, числовая.
- Тип данных указывается явно, статическая типизация данных.
- Условие `if` и цикл `while`.
- Основные математические выражения, логические выражения, условные выражения.
- Ввод/вывод данных.
- Каждая строчка кода заканчивает с "\n"

## Организация памяти
Архитектура Фон Неймана
- Память инструкций и данных общая.
- Размер памяти 2^32 бит.
- Инструкции хранятся с ячейки 00, далее данные, последние 2 ячейки выделены для ввода/вывода
- 
```
         Memory
+---------------------+
|  00  :     jmp      |
|  01  :  instruction |
|  02  :  instruction |
|  ...       ...      |
|  b   :   variable   |
|  b+1 :   variable   |
|  ...       ...      |
|  i-1 :    input     |
|  i   :    output    |
+---------------------+
```

## Система команд
Особенности процессора:
- Машинное слово инструкций от 1 байта до 5 байт.
- Машинное слово данных 4 байта, знаковое
- Регистры:
  - A -- хранит результаты вычислений, определяет флаги N и Z.
  - PC -- счетчик команд, также используется при переходах.
  - RA -- хранит адрес ячейки памяти, с которой происходит взаимодействие.
- Ввод/вывод - stream, занимает последние 2 ячейки памяти.

### Набор инструкций
| Инструкция | Такты          | Описание                                    |
|------------|--------------|---------------------------------------------|
| HLT        |   | Останов                 |
| CLA        |   | Очистить A                 |
| LD M       |      | Загрузка M в A                            |
| ST M       |             | Сохранение значения из A в M              |
| ADD M      |             | Сложить значение M с A                    |
| SUB M      |            | Вычесть                                     |
| MUL M      |             | Умножить                                    |
| DIV M      |             | Разделить                                   |
| MOD M      |             | Взять остаток от деления A на M           |
| CMP M      |             | Установить флаги от операции A - M        |
| JMP M      |     | Перейти на инструкцию M                     |
| BEQ M       |             | Переход, если флаг Z = 1                    |
| BNE M      |             | Переход, если флаг Z = 0                    |
| BGE M       |             | Переход, если флаг N = 1                    |
| BG M       |             | Переход, если флаг N = 0 и Z = 0            |

- `A` - аккумуляторный регистр.
- Флаг `Z` - результат операции равен 0.
- Флаг `N` - результат операции отрицательный.
- Все **адресные команды** поддерживают прямую и непосредственную адресацию.  
  Команды LD и ST дополнительно поддерживают косвенную адресацию.
- `M` - адрес в памяти.

### Кодирование инструкций
Бинарное кодирование инструкций
```
|  opcode | mode |              arg                        |
------------------------------------------------------------
| 0000 00 |  00  | 0000 0000 0000 0000 0000 0000 0000 0000 | - 5 байт
| 0000 00 |  00  | 0000 0000 0000 0000 0000 0000           |
| 0000 00 |  00  | 0000 0000 0000 0000                     |
| 0000 00 |  00  | 0000 0000                               |
| 0000 00 |  00  |                                         |
```

## Транслятор
Принимает на вход 2 файла.
Файл №1 с кодом на нашем ЯП, разбирает его на части и превращает в машинный код, параллельно валидируя основные моменты.
Затем транслятор упаковывает бинарный машинный код в файл №2.

### Правила генерации машинного кода
Построчный проход по коду с анализом строк при помощи regexp, при обнаружении ошибок выбрасываются ошибки.

## Модель процессора

``` text
                                                                                             +--------+
                                                                                             | input  |
                                                                                             |--------|
 +-----------------------------------------+                                                 | output |
 |                                         |                                                 |--------|
 |                                         |                                                 |        |
 |                DataPath                 |                                                 |        |
 |                                         |                                                 |        | 
 |                                         | <------------------(output)-------------------- |        | <--- oe
 +-----------------------------------------+ -------------------(input)--------------------> |  data  |
             ^              ^                                                                | memory | <--- wr
      signal |              | arg                                                            |        | 
             |              |                                                                |        |
 +-----------------------------------------+                                                 |        |
 |                                         |                                                 |        |     
 |                                         |                                                 |        |
 |               ControlUnit               |                                                 |--------|    
 |                                         |                                                 |        |     
 |                                         | <----------------(instructions)---------------- | instr  |
 +-----------------------------------------+ ----------------------(PC)--------------------> | memory |
                                                                                             +--------+     
```

### ControlUnit
``` text

   latch_program_counter
              | 
              v
    +----+---------+--------+          +--------+
    |    | program |        |          | MEMORY |
    |    | counter | -------+--------> +--------+
    |    +---------+                       |  
    |    ^                       (current_instruction)
    |    |                                 |          +---------+
  (+1)   |     +---------(instr_arg)-------+          |  tick   |
    |    |     |                           |     +----| counter |
    |    |     v                           |     |    +---------+
    |    +-----+                           v     v         ^
    |    |     |                       +--------------+    |
    +--> | MUX | <----(sel_next)------ | instructions |----+
         |     |                       |   decoder    |
         +-----+                       |              |<-----+
                                       +--------------+      |
                                        |          |         |
                                 signal |      arg |         |
                                        v          v         |
                                        +----------+  flags  |
                                        |          |---------+
                                        | DataPath |
                         input -------->|          |----------> output
                                        +----------+
```

### DataPath
``` text
                                                                     
                                       +------------+            +----------+ <-- latch_addr
                +-------(output)------ |   MEMORY   | <--(addr)--| addr_reg |
                |                      +------------+            +----------+ <--+                 
                |                                                                |
                |                        | flags |--->     sel -> +-------+ -----+
                v    alu_op --> +--------+-------+--------+ ----> |  MUX  |
                +-------+       |                         |       +-------+ <----- instr_arg
                |  MUX  | ----> |           ALU           | ----------+   
instr_arg ----> +-------+       |                         |           |   
                ^               +-------------------------+           v
                |                            ^                    +-------+ <----- input
               sel                           |                    |  MUX  |
                                             |                    +-------+ <----- sel
                                       +-----------+                  |
                           output <--- |    ACC    | <----------------+
                                       +-----------+
                                             ^
                                             |
                                         latch_acc
```


## Тестирование
Тестирование выполняется при помощи golden test-ов. Тесты и конфигурации в формате yaml.


Пример использования и журнал работы процессора на примере `cat`:
``` shell

```

Пример проверки исходного кода:
``` shell

```

## Статистика
| ФИО                         | алг             | LoC | code байт | code инстр. | инстр. | такт. |
|-----------------------------|-----------------|-----|-----------|-------------|--------|-------|
| Кожемякин Руслан Алексеевич | hello           |    |        |          |     |    |
| Кожемякин Руслан Алексеевич | cat             |    |        |          |    |   |
| Кожемякин Руслан Алексеевич | prob1           |    |        |           |   |  |
