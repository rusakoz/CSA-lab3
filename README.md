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
<if_statement>    ::= "if" "(" <expression> ")" "{" <nl> <program> "}" <nl>
<while_statement> ::= "while" "(" <expression> ")" "{" <nl> <program> "}" <nl>

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
<comparison_op> ::= "==" | "!=" | ">" | "<" | "||"

comment         ::= "//" <any symbols except "\n">
```
Код выполняется последовательно. Операции:
- `+` сложение.
- `-` вычитание.
- `*` умножение.
- `/` целочисленное деление.
- `%` остаток от деления.
- `>` сравнение(больше).
- `<` сравнение(меньше).
- `==` сравнение(равенство).
- `!=` сравнение(неравенство).
- `||` логическое ИЛИ.

В языке реализованны следующие возможности:
- Память выделяется статически, при запуске модели. Видимость данных -- глобальная. Поддержка литералов -- строковая, числовая.
- Тип данных указывается явно, статическая типизация данных.
- Условие `if` с подержкой 1 выражения вида: `(a < b || a < c)`.
- Цикл `while` с подержкой 1 выражения вида: `(a < b)`.
- Основные математические выражения, логические выражения, условные выражения.
- Ввод/вывод данных.
- Каждая строчка кода заканчивает "\n".

## Организация памяти
Архитектура Фон Неймана
- Память инструкций и данных общая.
- Размер памяти до 2^32 бит.
- Инструкции хранятся с ячейки 00, далее данные, последние 2 ячейки выделены для ввода/вывода.
- У инструкций есть 3 вида адресации:
  - Прямая(DIRECT) -- Адрес операнда в памяти определяется заданным в команде 32-разрядным значением.
  - Косвенная(~INDIRECT) -- Адрес ячейки памяти, в которой содержится адрес операнда.
  - Непосредственная(#IMMEDIATE) -- Операнд содержится прямо в команде.
```
         Memory
+---------------------+
|  00  :  instruction |
|  01  :  instruction |
|  ...       ...      |
|  b   :   variable   |
|  b+1 :   variable   |
|  ...       ...      |
|  i-1 :    input     |
|  i   :    output    |
+---------------------+
```

## Система команд
Реализовано в [isa](./main/isa.py)
Особенности процессора:
- Машинное слово 1 или 5 байт.
- Регистры:
  - ACC -- хранит результаты вычислений, определяет флаги N и Z.
  - PC -- счетчик команд, также используется при переходах.
  - AR -- хранит адрес ячейки памяти, с которой происходит взаимодействие.
- Адресация: `DIRECT`, `INDIRECT`, `IMMEDIATE`.
- Ввод/вывод - stream, занимает последние 2 ячейки памяти.

### Набор инструкций
| Инструкция |     Такты    |                  Описание                   |
|------------|--------------|---------------------------------------------|
| LD M       |              | Загрузка   M в ACC                          |
| ST M       |              | Сохранение значения из ACC в M              |
| ADD M      |              | Сложить    значение M с ACC                 |
| SUB M      |              | Вычесть    значение M с ACC                 |
| DIV M      |              | Разделить  значение ACC на M                |
| MUL M      |              | Умножить   значение ACC на M                |
| MOD M      |              | Остаток от деления ACC на M                 |
| CMP M      |              | Установить флаги от операции ACC - M        |
| JMP M      |              | Перейти на инструкцию M                     |
| BEQ M      |              | Переход, если флаг Z = 1                    |
| BNE M      |              | Переход, если флаг Z = 0                    |
| BGE M      |              | Переход, если флаг N = 1                    |
| BG M       |              | Переход, если флаг N = 0                    |
| HLT        |              | Останов                                     |

- `ACC` - аккумуляторный регистр.
- `M` - адрес.
- Флаг `Z` - zero.
- Флаг `N` - negative.
- Адресные команды поддерживают `DIRECT` и `IMMEDIATE` адресацию.  
- Команды `LD` и `ST` `DIRECT`, `IMMEDIATE` и `INDIRECT`.

### Кодирование инструкций
Бинарное кодирование инструкций, либо 1 байт, либо 5 байт
```
| opcode  | mode |                   arg                   |
------------------------------------------------------------
| 0000 00 |  00  | 0000 0000 0000 0000 0000 0000 0000 0000 | - 5 байт
| 0000 00 |  00  |                                         | - 1 байт
```

## Транслятор
Реализовано в [translator](./main/translator/translator.py)
Принимает на вход 2 файла.
Файл №1 с кодом на нашем ЯП, разбирает его на части и превращает в машинный код, параллельно валидируя основные моменты.
Затем транслятор упаковывает бинарный машинный код в файл №2.

- На вход подается:
  - <input_file> -- файл с исходным кодом на придуманном языке.
  - <binary_file> -- файл для записи бинарных инструкций.
  - <debug_file> -- файл для вывода инстукций вида: <address> - <HEXCODE> - <mnemonic>.

## Модель процессора
Реализовано [machine](./main/machine/machine.py)

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
Реализовано в классе ControlUnit

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
    |    |     |                      +--------------+     |
    +--> | MUX | <----(sel_next)----- | instructions |-----+
         |     |                      |   decoder    |
         +-----+                      |              |<------+
                                      +--------------+       |
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
Реализовано в классе DataPath

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
Реализация [golden](./tests/golden_test.py)
Тестирование выполняется при помощи `pytest` golden test-ов.
Линтеры `ruff`.
Тесты:
  - [cat](./tests/golden/cat.yml)
  - [hello_user](./tests/golden/hello_user.yml)
  - [prob1](./tests/golden/prob1.yml)

Запустить тесты: `poetry run pytest . -v`

Обновить конфигурацию golden tests: `poetry run pytest . -v --update-goldens`

CI при помощи Github Action:

``` yaml
name: Python-CI

on:
  push:
    branches:
      - master

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.12

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install poetry
          poetry install

      - name: Run tests and collect coverage
        run: |
          poetry run coverage run -m pytest .
          poetry run coverage report -m
        env:
          CI: true

  lint:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.12

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install poetry
          poetry install

      - name: Check code formatting with Ruff
        run: poetry run ruff format --check .

      - name: Run Ruff linters
        run: poetry run ruff check .
```

где:

- `poetry` -- управления зависимостями для языка программирования Python.
- `coverage` -- формирование отчёта об уровне покрытия исходного кода.
- `pytest` -- утилита для запуска тестов.
- `ruff` -- утилита для форматирования и проверки стиля кодирования.


Пример использования и журнал работы процессора на примере `cat`:
На вход подается файл со строкой `foo`

Код программы:
``` text
str string = ""
  while (1 < 2) {
      << string
      >> string
  }
```

Странслированный код:
``` text
  =============INSTRUCTIONS============
  <address>       <HEXCODE>    <mnemonic>
     0          0200000001       LD #1
     1          0400000076       ST 118
     2          0200000002       LD #2
     3          0400000077       ST 119
     4          0000000076       LD 118
     5          1c00000077       CMP 119
     6          300000005c       BG 92
     7          0200000000       LD #0
     8          040000005d       ST 93
     9          0200000000       LD #0
     10         040000005e       ST 94
     11         0200000000       LD #0
     12         040000005f       ST 95
     13         0200000000       LD #0
     14         0400000060       ST 96
     15         0200000000       LD #0
     16         0400000061       ST 97
     17         0200000000       LD #0
     18         0400000062       ST 98
     19         0200000000       LD #0
     20         0400000063       ST 99
     21         0200000000       LD #0
     22         0400000064       ST 100
     23         0200000000       LD #0
     24         0400000065       ST 101
     25         0200000000       LD #0
     26         0400000066       ST 102
     27         0200000000       LD #0
     28         0400000067       ST 103
     29         0200000000       LD #0
     30         0400000068       ST 104
     31         0200000000       LD #0
     32         0400000069       ST 105
     33         0200000000       LD #0
     34         040000006a       ST 106
     35         0200000000       LD #0
     36         040000006b       ST 107
     37         0200000000       LD #0
     38         040000006c       ST 108
     39         0200000000       LD #0
     40         040000006d       ST 109
     41         0200000000       LD #0
     42         040000006e       ST 110
     43         0200000000       LD #0
     44         040000006f       ST 111
     45         0200000000       LD #0
     46         0400000070       ST 112
     47         0200000000       LD #0
     48         0400000071       ST 113
     49         0200000000       LD #0
     50         0400000072       ST 114
     51         0200000000       LD #0
     52         0400000073       ST 115
     53         0200000000       LD #0
     54         0400000074       ST 116
     55         0200000000       LD #0
     56         0400000078       ST 120
     57         020000005d       LD #93
     58         0400000079       ST 121
     59         00000007fe       LD 2046
     60         1e00000000       CMP #0
     61         2400000049       BEQ 73
     62         0500000079       ST ~121
     63         0000000078       LD 120
     64         0a00000001       ADD #1
     65         0400000078       ST 120
     66         0000000079       LD 121
     67         0a00000001       ADD #1
     68         0400000079       ST 121
     69         0000000078       LD 120
     70         1e00000018       CMP #24
     71         2400000049       BEQ 73
     72         200000003b       JMP 59
     73         0200000000       LD #0
     74         040000007a       ST 122
     75         020000005d       LD #93
     76         040000007b       ST 123
     77         010000007b       LD ~123
     78         1e00000000       CMP #0
     79         240000005b       BEQ 91
     80         04000007ff       ST 2047
     81         000000007a       LD 122
     82         0a00000001       ADD #1
     83         040000007a       ST 122
     84         000000007b       LD 123
     85         0a00000001       ADD #1
     86         040000007b       ST 123
     87         000000007a       LD 122
     88         1e00000018       CMP #24
     89         240000005b       BEQ 91
     90         200000004d       JMP 77
     91         2000000002       JMP 2
     92         34               HLT
```

Дебаг вывод:
``` text
  DEBUG   machine:simulation    TICK: 0     PC: 0    ADDR: 0    MEM_OUT: 0    ALU: 0    ACC: 0    LD #1
  DEBUG   machine:simulation    TICK: 1     PC: 1    ADDR: 0    MEM_OUT: 0    ALU: 1    ACC: 1    ST 118
  DEBUG   machine:simulation    TICK: 3     PC: 2    ADDR: 118    MEM_OUT: 0    ALU: 1    ACC: 1    LD #2
  DEBUG   machine:simulation    TICK: 4     PC: 3    ADDR: 118    MEM_OUT: 0    ALU: 2    ACC: 2    ST 119
  DEBUG   machine:simulation    TICK: 6     PC: 4    ADDR: 119    MEM_OUT: 0    ALU: 2    ACC: 2    LD 118
  DEBUG   machine:simulation    TICK: 8     PC: 5    ADDR: 118    MEM_OUT: 1    ALU: 1    ACC: 1    CMP 119
  DEBUG   machine:simulation    TICK: 10     PC: 6    ADDR: 119    MEM_OUT: 2    ALU: -1    ACC: 1    BG 92
  DEBUG   machine:simulation    TICK: 11     PC: 7    ADDR: 119    MEM_OUT: 2    ALU: -1    ACC: 1    LD #0
  DEBUG   machine:simulation    TICK: 12     PC: 8    ADDR: 119    MEM_OUT: 2    ALU: 0    ACC: 0    ST 93
  DEBUG   machine:simulation    TICK: 14     PC: 9    ADDR: 93    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 15     PC: 10    ADDR: 93    MEM_OUT: 2    ALU: 0    ACC: 0    ST 94
  DEBUG   machine:simulation    TICK: 17     PC: 11    ADDR: 94    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 18     PC: 12    ADDR: 94    MEM_OUT: 2    ALU: 0    ACC: 0    ST 95
  DEBUG   machine:simulation    TICK: 20     PC: 13    ADDR: 95    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 21     PC: 14    ADDR: 95    MEM_OUT: 2    ALU: 0    ACC: 0    ST 96
  DEBUG   machine:simulation    TICK: 23     PC: 15    ADDR: 96    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 24     PC: 16    ADDR: 96    MEM_OUT: 2    ALU: 0    ACC: 0    ST 97
  DEBUG   machine:simulation    TICK: 26     PC: 17    ADDR: 97    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 27     PC: 18    ADDR: 97    MEM_OUT: 2    ALU: 0    ACC: 0    ST 98
  DEBUG   machine:simulation    TICK: 29     PC: 19    ADDR: 98    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 30     PC: 20    ADDR: 98    MEM_OUT: 2    ALU: 0    ACC: 0    ST 99
  DEBUG   machine:simulation    TICK: 32     PC: 21    ADDR: 99    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 33     PC: 22    ADDR: 99    MEM_OUT: 2    ALU: 0    ACC: 0    ST 100
  DEBUG   machine:simulation    TICK: 35     PC: 23    ADDR: 100    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 36     PC: 24    ADDR: 100    MEM_OUT: 2    ALU: 0    ACC: 0    ST 101
  DEBUG   machine:simulation    TICK: 38     PC: 25    ADDR: 101    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 39     PC: 26    ADDR: 101    MEM_OUT: 2    ALU: 0    ACC: 0    ST 102
  DEBUG   machine:simulation    TICK: 41     PC: 27    ADDR: 102    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 42     PC: 28    ADDR: 102    MEM_OUT: 2    ALU: 0    ACC: 0    ST 103
  DEBUG   machine:simulation    TICK: 44     PC: 29    ADDR: 103    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 45     PC: 30    ADDR: 103    MEM_OUT: 2    ALU: 0    ACC: 0    ST 104
  DEBUG   machine:simulation    TICK: 47     PC: 31    ADDR: 104    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 48     PC: 32    ADDR: 104    MEM_OUT: 2    ALU: 0    ACC: 0    ST 105
  DEBUG   machine:simulation    TICK: 50     PC: 33    ADDR: 105    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 51     PC: 34    ADDR: 105    MEM_OUT: 2    ALU: 0    ACC: 0    ST 106
  DEBUG   machine:simulation    TICK: 53     PC: 35    ADDR: 106    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 54     PC: 36    ADDR: 106    MEM_OUT: 2    ALU: 0    ACC: 0    ST 107
  DEBUG   machine:simulation    TICK: 56     PC: 37    ADDR: 107    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 57     PC: 38    ADDR: 107    MEM_OUT: 2    ALU: 0    ACC: 0    ST 108
  DEBUG   machine:simulation    TICK: 59     PC: 39    ADDR: 108    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 60     PC: 40    ADDR: 108    MEM_OUT: 2    ALU: 0    ACC: 0    ST 109
  DEBUG   machine:simulation    TICK: 62     PC: 41    ADDR: 109    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 63     PC: 42    ADDR: 109    MEM_OUT: 2    ALU: 0    ACC: 0    ST 110
  DEBUG   machine:simulation    TICK: 65     PC: 43    ADDR: 110    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 66     PC: 44    ADDR: 110    MEM_OUT: 2    ALU: 0    ACC: 0    ST 111
  DEBUG   machine:simulation    TICK: 68     PC: 45    ADDR: 111    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 69     PC: 46    ADDR: 111    MEM_OUT: 2    ALU: 0    ACC: 0    ST 112
  DEBUG   machine:simulation    TICK: 71     PC: 47    ADDR: 112    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 72     PC: 48    ADDR: 112    MEM_OUT: 2    ALU: 0    ACC: 0    ST 113
  DEBUG   machine:simulation    TICK: 74     PC: 49    ADDR: 113    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 75     PC: 50    ADDR: 113    MEM_OUT: 2    ALU: 0    ACC: 0    ST 114
  DEBUG   machine:simulation    TICK: 77     PC: 51    ADDR: 114    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 78     PC: 52    ADDR: 114    MEM_OUT: 2    ALU: 0    ACC: 0    ST 115
  DEBUG   machine:simulation    TICK: 80     PC: 53    ADDR: 115    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 81     PC: 54    ADDR: 115    MEM_OUT: 2    ALU: 0    ACC: 0    ST 116
  DEBUG   machine:simulation    TICK: 83     PC: 55    ADDR: 116    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 84     PC: 56    ADDR: 116    MEM_OUT: 2    ALU: 0    ACC: 0    ST 120
  DEBUG   machine:simulation    TICK: 86     PC: 57    ADDR: 120    MEM_OUT: 2    ALU: 0    ACC: 0    LD #93
  DEBUG   machine:simulation    TICK: 87     PC: 58    ADDR: 120    MEM_OUT: 2    ALU: 93    ACC: 93    ST 121
  DEBUG   machine:simulation    TICK: 89     PC: 59    ADDR: 121    MEM_OUT: 2    ALU: 93    ACC: 93    LD 2046
  DEBUG   machine:signal_latch_acc input: "[102, 111, 111, 0]" >> 93
  DEBUG   machine:simulation    TICK: 91     PC: 60    ADDR: 2046    MEM_OUT: 0    ALU: 0    ACC: 102    CMP #0
  DEBUG   machine:simulation    TICK: 92     PC: 61    ADDR: 2046    MEM_OUT: 0    ALU: 102    ACC: 102    BEQ 73
  DEBUG   machine:simulation    TICK: 93     PC: 62    ADDR: 2046    MEM_OUT: 0    ALU: 102    ACC: 102    ST ~121
  DEBUG   machine:simulation    TICK: 97     PC: 63    ADDR: 93    MEM_OUT: 93    ALU: 102    ACC: 102    LD 120
  DEBUG   machine:simulation    TICK: 99     PC: 64    ADDR: 120    MEM_OUT: 0    ALU: 0    ACC: 0    ADD #1
  DEBUG   machine:simulation    TICK: 100     PC: 65    ADDR: 120    MEM_OUT: 0    ALU: 1    ACC: 1    ST 120
  DEBUG   machine:simulation    TICK: 102     PC: 66    ADDR: 120    MEM_OUT: 0    ALU: 1    ACC: 1    LD 121
  DEBUG   machine:simulation    TICK: 104     PC: 67    ADDR: 121    MEM_OUT: 93    ALU: 93    ACC: 93    ADD #1
  DEBUG   machine:simulation    TICK: 105     PC: 68    ADDR: 121    MEM_OUT: 93    ALU: 94    ACC: 94    ST 121
  DEBUG   machine:simulation    TICK: 107     PC: 69    ADDR: 121    MEM_OUT: 93    ALU: 94    ACC: 94    LD 120
  DEBUG   machine:simulation    TICK: 109     PC: 70    ADDR: 120    MEM_OUT: 1    ALU: 1    ACC: 1    CMP #24
  DEBUG   machine:simulation    TICK: 110     PC: 71    ADDR: 120    MEM_OUT: 1    ALU: -23    ACC: 1    BEQ 73
  DEBUG   machine:simulation    TICK: 111     PC: 72    ADDR: 120    MEM_OUT: 1    ALU: -23    ACC: 1    JMP 59
  DEBUG   machine:simulation    TICK: 112     PC: 59    ADDR: 120    MEM_OUT: 1    ALU: -23    ACC: 1    LD 2046
  DEBUG   machine:signal_latch_acc input: "[111, 111, 0]" >> 1
  DEBUG   machine:simulation    TICK: 114     PC: 60    ADDR: 2046    MEM_OUT: 0    ALU: 0    ACC: 111    CMP #0
  DEBUG   machine:simulation    TICK: 115     PC: 61    ADDR: 2046    MEM_OUT: 0    ALU: 111    ACC: 111    BEQ 73
  DEBUG   machine:simulation    TICK: 116     PC: 62    ADDR: 2046    MEM_OUT: 0    ALU: 111    ACC: 111    ST ~121
  DEBUG   machine:simulation    TICK: 120     PC: 63    ADDR: 94    MEM_OUT: 94    ALU: 111    ACC: 111    LD 120
  DEBUG   machine:simulation    TICK: 122     PC: 64    ADDR: 120    MEM_OUT: 1    ALU: 1    ACC: 1    ADD #1
  DEBUG   machine:simulation    TICK: 123     PC: 65    ADDR: 120    MEM_OUT: 1    ALU: 2    ACC: 2    ST 120
  DEBUG   machine:simulation    TICK: 125     PC: 66    ADDR: 120    MEM_OUT: 1    ALU: 2    ACC: 2    LD 121
  DEBUG   machine:simulation    TICK: 127     PC: 67    ADDR: 121    MEM_OUT: 94    ALU: 94    ACC: 94    ADD #1
  DEBUG   machine:simulation    TICK: 128     PC: 68    ADDR: 121    MEM_OUT: 94    ALU: 95    ACC: 95    ST 121
  DEBUG   machine:simulation    TICK: 130     PC: 69    ADDR: 121    MEM_OUT: 94    ALU: 95    ACC: 95    LD 120
  DEBUG   machine:simulation    TICK: 132     PC: 70    ADDR: 120    MEM_OUT: 2    ALU: 2    ACC: 2    CMP #24
  DEBUG   machine:simulation    TICK: 133     PC: 71    ADDR: 120    MEM_OUT: 2    ALU: -22    ACC: 2    BEQ 73
  DEBUG   machine:simulation    TICK: 134     PC: 72    ADDR: 120    MEM_OUT: 2    ALU: -22    ACC: 2    JMP 59
  DEBUG   machine:simulation    TICK: 135     PC: 59    ADDR: 120    MEM_OUT: 2    ALU: -22    ACC: 2    LD 2046
  DEBUG   machine:signal_latch_acc input: "[111, 0]" >> 2
  DEBUG   machine:simulation    TICK: 137     PC: 60    ADDR: 2046    MEM_OUT: 0    ALU: 0    ACC: 111    CMP #0
  DEBUG   machine:simulation    TICK: 138     PC: 61    ADDR: 2046    MEM_OUT: 0    ALU: 111    ACC: 111    BEQ 73
  DEBUG   machine:simulation    TICK: 139     PC: 62    ADDR: 2046    MEM_OUT: 0    ALU: 111    ACC: 111    ST ~121
  DEBUG   machine:simulation    TICK: 143     PC: 63    ADDR: 95    MEM_OUT: 95    ALU: 111    ACC: 111    LD 120
  DEBUG   machine:simulation    TICK: 145     PC: 64    ADDR: 120    MEM_OUT: 2    ALU: 2    ACC: 2    ADD #1
  DEBUG   machine:simulation    TICK: 146     PC: 65    ADDR: 120    MEM_OUT: 2    ALU: 3    ACC: 3    ST 120
  DEBUG   machine:simulation    TICK: 148     PC: 66    ADDR: 120    MEM_OUT: 2    ALU: 3    ACC: 3    LD 121
  DEBUG   machine:simulation    TICK: 150     PC: 67    ADDR: 121    MEM_OUT: 95    ALU: 95    ACC: 95    ADD #1
  DEBUG   machine:simulation    TICK: 151     PC: 68    ADDR: 121    MEM_OUT: 95    ALU: 96    ACC: 96    ST 121
  DEBUG   machine:simulation    TICK: 153     PC: 69    ADDR: 121    MEM_OUT: 95    ALU: 96    ACC: 96    LD 120
  DEBUG   machine:simulation    TICK: 155     PC: 70    ADDR: 120    MEM_OUT: 3    ALU: 3    ACC: 3    CMP #24
  DEBUG   machine:simulation    TICK: 156     PC: 71    ADDR: 120    MEM_OUT: 3    ALU: -21    ACC: 3    BEQ 73
  DEBUG   machine:simulation    TICK: 157     PC: 72    ADDR: 120    MEM_OUT: 3    ALU: -21    ACC: 3    JMP 59
  DEBUG   machine:simulation    TICK: 158     PC: 59    ADDR: 120    MEM_OUT: 3    ALU: -21    ACC: 3    LD 2046
  DEBUG   machine:signal_latch_acc input: "[0]" >> 3
  DEBUG   machine:simulation    TICK: 160     PC: 60    ADDR: 2046    MEM_OUT: 0    ALU: 0    ACC: 0    CMP #0
  DEBUG   machine:simulation    TICK: 161     PC: 61    ADDR: 2046    MEM_OUT: 0    ALU: 0    ACC: 0    BEQ 73
  DEBUG   machine:simulation    TICK: 162     PC: 73    ADDR: 2046    MEM_OUT: 0    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 163     PC: 74    ADDR: 2046    MEM_OUT: 0    ALU: 0    ACC: 0    ST 122
  DEBUG   machine:simulation    TICK: 165     PC: 75    ADDR: 122    MEM_OUT: 0    ALU: 0    ACC: 0    LD #93
  DEBUG   machine:simulation    TICK: 166     PC: 76    ADDR: 122    MEM_OUT: 0    ALU: 93    ACC: 93    ST 123
  DEBUG   machine:simulation    TICK: 168     PC: 77    ADDR: 123    MEM_OUT: 0    ALU: 93    ACC: 93    LD ~123
  DEBUG   machine:simulation    TICK: 171     PC: 78    ADDR: 93    MEM_OUT: 102    ALU: 102    ACC: 102    CMP #0
  DEBUG   machine:simulation    TICK: 172     PC: 79    ADDR: 93    MEM_OUT: 102    ALU: 102    ACC: 102    BEQ 91
  DEBUG   machine:simulation    TICK: 173     PC: 80    ADDR: 93    MEM_OUT: 102    ALU: 102    ACC: 102    ST 2047
  DEBUG   machine:signal_write  output: "[]" << 102
  DEBUG   machine:simulation    TICK: 175     PC: 81    ADDR: 2047    MEM_OUT: 102    ALU: 102    ACC: 102    LD 122
  DEBUG   machine:simulation    TICK: 177     PC: 82    ADDR: 122    MEM_OUT: 0    ALU: 0    ACC: 0    ADD #1
  DEBUG   machine:simulation    TICK: 178     PC: 83    ADDR: 122    MEM_OUT: 0    ALU: 1    ACC: 1    ST 122
  DEBUG   machine:simulation    TICK: 180     PC: 84    ADDR: 122    MEM_OUT: 0    ALU: 1    ACC: 1    LD 123
  DEBUG   machine:simulation    TICK: 182     PC: 85    ADDR: 123    MEM_OUT: 93    ALU: 93    ACC: 93    ADD #1
  DEBUG   machine:simulation    TICK: 183     PC: 86    ADDR: 123    MEM_OUT: 93    ALU: 94    ACC: 94    ST 123
  DEBUG   machine:simulation    TICK: 185     PC: 87    ADDR: 123    MEM_OUT: 93    ALU: 94    ACC: 94    LD 122
  DEBUG   machine:simulation    TICK: 187     PC: 88    ADDR: 122    MEM_OUT: 1    ALU: 1    ACC: 1    CMP #24
  DEBUG   machine:simulation    TICK: 188     PC: 89    ADDR: 122    MEM_OUT: 1    ALU: -23    ACC: 1    BEQ 91
  DEBUG   machine:simulation    TICK: 189     PC: 90    ADDR: 122    MEM_OUT: 1    ALU: -23    ACC: 1    JMP 77
  DEBUG   machine:simulation    TICK: 190     PC: 77    ADDR: 122    MEM_OUT: 1    ALU: -23    ACC: 1    LD ~123
  DEBUG   machine:simulation    TICK: 193     PC: 78    ADDR: 94    MEM_OUT: 111    ALU: 111    ACC: 111    CMP #0
  DEBUG   machine:simulation    TICK: 194     PC: 79    ADDR: 94    MEM_OUT: 111    ALU: 111    ACC: 111    BEQ 91
  DEBUG   machine:simulation    TICK: 195     PC: 80    ADDR: 94    MEM_OUT: 111    ALU: 111    ACC: 111    ST 2047
  DEBUG   machine:signal_write  output: "[102]" << 111
  DEBUG   machine:simulation    TICK: 197     PC: 81    ADDR: 2047    MEM_OUT: 111    ALU: 111    ACC: 111    LD 122
  DEBUG   machine:simulation    TICK: 199     PC: 82    ADDR: 122    MEM_OUT: 1    ALU: 1    ACC: 1    ADD #1
  DEBUG   machine:simulation    TICK: 200     PC: 83    ADDR: 122    MEM_OUT: 1    ALU: 2    ACC: 2    ST 122
  DEBUG   machine:simulation    TICK: 202     PC: 84    ADDR: 122    MEM_OUT: 1    ALU: 2    ACC: 2    LD 123
  DEBUG   machine:simulation    TICK: 204     PC: 85    ADDR: 123    MEM_OUT: 94    ALU: 94    ACC: 94    ADD #1
  DEBUG   machine:simulation    TICK: 205     PC: 86    ADDR: 123    MEM_OUT: 94    ALU: 95    ACC: 95    ST 123
  DEBUG   machine:simulation    TICK: 207     PC: 87    ADDR: 123    MEM_OUT: 94    ALU: 95    ACC: 95    LD 122
  DEBUG   machine:simulation    TICK: 209     PC: 88    ADDR: 122    MEM_OUT: 2    ALU: 2    ACC: 2    CMP #24
  DEBUG   machine:simulation    TICK: 210     PC: 89    ADDR: 122    MEM_OUT: 2    ALU: -22    ACC: 2    BEQ 91
  DEBUG   machine:simulation    TICK: 211     PC: 90    ADDR: 122    MEM_OUT: 2    ALU: -22    ACC: 2    JMP 77
  DEBUG   machine:simulation    TICK: 212     PC: 77    ADDR: 122    MEM_OUT: 2    ALU: -22    ACC: 2    LD ~123
  DEBUG   machine:simulation    TICK: 215     PC: 78    ADDR: 95    MEM_OUT: 111    ALU: 111    ACC: 111    CMP #0
  DEBUG   machine:simulation    TICK: 216     PC: 79    ADDR: 95    MEM_OUT: 111    ALU: 111    ACC: 111    BEQ 91
  DEBUG   machine:simulation    TICK: 217     PC: 80    ADDR: 95    MEM_OUT: 111    ALU: 111    ACC: 111    ST 2047
  DEBUG   machine:signal_write  output: "[102, 111]" << 111
  DEBUG   machine:simulation    TICK: 219     PC: 81    ADDR: 2047    MEM_OUT: 111    ALU: 111    ACC: 111    LD 122
  DEBUG   machine:simulation    TICK: 221     PC: 82    ADDR: 122    MEM_OUT: 2    ALU: 2    ACC: 2    ADD #1
  DEBUG   machine:simulation    TICK: 222     PC: 83    ADDR: 122    MEM_OUT: 2    ALU: 3    ACC: 3    ST 122
  DEBUG   machine:simulation    TICK: 224     PC: 84    ADDR: 122    MEM_OUT: 2    ALU: 3    ACC: 3    LD 123
  DEBUG   machine:simulation    TICK: 226     PC: 85    ADDR: 123    MEM_OUT: 95    ALU: 95    ACC: 95    ADD #1
  DEBUG   machine:simulation    TICK: 227     PC: 86    ADDR: 123    MEM_OUT: 95    ALU: 96    ACC: 96    ST 123
  DEBUG   machine:simulation    TICK: 229     PC: 87    ADDR: 123    MEM_OUT: 95    ALU: 96    ACC: 96    LD 122
  DEBUG   machine:simulation    TICK: 231     PC: 88    ADDR: 122    MEM_OUT: 3    ALU: 3    ACC: 3    CMP #24
  DEBUG   machine:simulation    TICK: 232     PC: 89    ADDR: 122    MEM_OUT: 3    ALU: -21    ACC: 3    BEQ 91
  DEBUG   machine:simulation    TICK: 233     PC: 90    ADDR: 122    MEM_OUT: 3    ALU: -21    ACC: 3    JMP 77
  DEBUG   machine:simulation    TICK: 234     PC: 77    ADDR: 122    MEM_OUT: 3    ALU: -21    ACC: 3    LD ~123
  DEBUG   machine:simulation    TICK: 237     PC: 78    ADDR: 96    MEM_OUT: 0    ALU: 0    ACC: 0    CMP #0
  DEBUG   machine:simulation    TICK: 238     PC: 79    ADDR: 96    MEM_OUT: 0    ALU: 0    ACC: 0    BEQ 91
  DEBUG   machine:simulation    TICK: 239     PC: 91    ADDR: 96    MEM_OUT: 0    ALU: 0    ACC: 0    JMP 2
  DEBUG   machine:simulation    TICK: 240     PC: 2    ADDR: 96    MEM_OUT: 0    ALU: 0    ACC: 0    LD #2
  DEBUG   machine:simulation    TICK: 241     PC: 3    ADDR: 96    MEM_OUT: 0    ALU: 2    ACC: 2    ST 119
  DEBUG   machine:simulation    TICK: 243     PC: 4    ADDR: 119    MEM_OUT: 0    ALU: 2    ACC: 2    LD 118
  DEBUG   machine:simulation    TICK: 245     PC: 5    ADDR: 118    MEM_OUT: 1    ALU: 1    ACC: 1    CMP 119
  DEBUG   machine:simulation    TICK: 247     PC: 6    ADDR: 119    MEM_OUT: 2    ALU: -1    ACC: 1    BG 92
  DEBUG   machine:simulation    TICK: 248     PC: 7    ADDR: 119    MEM_OUT: 2    ALU: -1    ACC: 1    LD #0
  DEBUG   machine:simulation    TICK: 249     PC: 8    ADDR: 119    MEM_OUT: 2    ALU: 0    ACC: 0    ST 93
  DEBUG   machine:simulation    TICK: 251     PC: 9    ADDR: 93    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 252     PC: 10    ADDR: 93    MEM_OUT: 2    ALU: 0    ACC: 0    ST 94
  DEBUG   machine:simulation    TICK: 254     PC: 11    ADDR: 94    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 255     PC: 12    ADDR: 94    MEM_OUT: 2    ALU: 0    ACC: 0    ST 95
  DEBUG   machine:simulation    TICK: 257     PC: 13    ADDR: 95    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 258     PC: 14    ADDR: 95    MEM_OUT: 2    ALU: 0    ACC: 0    ST 96
  DEBUG   machine:simulation    TICK: 260     PC: 15    ADDR: 96    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 261     PC: 16    ADDR: 96    MEM_OUT: 2    ALU: 0    ACC: 0    ST 97
  DEBUG   machine:simulation    TICK: 263     PC: 17    ADDR: 97    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 264     PC: 18    ADDR: 97    MEM_OUT: 2    ALU: 0    ACC: 0    ST 98
  DEBUG   machine:simulation    TICK: 266     PC: 19    ADDR: 98    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 267     PC: 20    ADDR: 98    MEM_OUT: 2    ALU: 0    ACC: 0    ST 99
  DEBUG   machine:simulation    TICK: 269     PC: 21    ADDR: 99    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 270     PC: 22    ADDR: 99    MEM_OUT: 2    ALU: 0    ACC: 0    ST 100
  DEBUG   machine:simulation    TICK: 272     PC: 23    ADDR: 100    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 273     PC: 24    ADDR: 100    MEM_OUT: 2    ALU: 0    ACC: 0    ST 101
  DEBUG   machine:simulation    TICK: 275     PC: 25    ADDR: 101    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 276     PC: 26    ADDR: 101    MEM_OUT: 2    ALU: 0    ACC: 0    ST 102
  DEBUG   machine:simulation    TICK: 278     PC: 27    ADDR: 102    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 279     PC: 28    ADDR: 102    MEM_OUT: 2    ALU: 0    ACC: 0    ST 103
  DEBUG   machine:simulation    TICK: 281     PC: 29    ADDR: 103    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 282     PC: 30    ADDR: 103    MEM_OUT: 2    ALU: 0    ACC: 0    ST 104
  DEBUG   machine:simulation    TICK: 284     PC: 31    ADDR: 104    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 285     PC: 32    ADDR: 104    MEM_OUT: 2    ALU: 0    ACC: 0    ST 105
  DEBUG   machine:simulation    TICK: 287     PC: 33    ADDR: 105    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 288     PC: 34    ADDR: 105    MEM_OUT: 2    ALU: 0    ACC: 0    ST 106
  DEBUG   machine:simulation    TICK: 290     PC: 35    ADDR: 106    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 291     PC: 36    ADDR: 106    MEM_OUT: 2    ALU: 0    ACC: 0    ST 107
  DEBUG   machine:simulation    TICK: 293     PC: 37    ADDR: 107    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 294     PC: 38    ADDR: 107    MEM_OUT: 2    ALU: 0    ACC: 0    ST 108
  DEBUG   machine:simulation    TICK: 296     PC: 39    ADDR: 108    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 297     PC: 40    ADDR: 108    MEM_OUT: 2    ALU: 0    ACC: 0    ST 109
  DEBUG   machine:simulation    TICK: 299     PC: 41    ADDR: 109    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 300     PC: 42    ADDR: 109    MEM_OUT: 2    ALU: 0    ACC: 0    ST 110
  DEBUG   machine:simulation    TICK: 302     PC: 43    ADDR: 110    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 303     PC: 44    ADDR: 110    MEM_OUT: 2    ALU: 0    ACC: 0    ST 111
  DEBUG   machine:simulation    TICK: 305     PC: 45    ADDR: 111    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 306     PC: 46    ADDR: 111    MEM_OUT: 2    ALU: 0    ACC: 0    ST 112
  DEBUG   machine:simulation    TICK: 308     PC: 47    ADDR: 112    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 309     PC: 48    ADDR: 112    MEM_OUT: 2    ALU: 0    ACC: 0    ST 113
  DEBUG   machine:simulation    TICK: 311     PC: 49    ADDR: 113    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 312     PC: 50    ADDR: 113    MEM_OUT: 2    ALU: 0    ACC: 0    ST 114
  DEBUG   machine:simulation    TICK: 314     PC: 51    ADDR: 114    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 315     PC: 52    ADDR: 114    MEM_OUT: 2    ALU: 0    ACC: 0    ST 115
  DEBUG   machine:simulation    TICK: 317     PC: 53    ADDR: 115    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 318     PC: 54    ADDR: 115    MEM_OUT: 2    ALU: 0    ACC: 0    ST 116
  DEBUG   machine:simulation    TICK: 320     PC: 55    ADDR: 116    MEM_OUT: 2    ALU: 0    ACC: 0    LD #0
  DEBUG   machine:simulation    TICK: 321     PC: 56    ADDR: 116    MEM_OUT: 2    ALU: 0    ACC: 0    ST 120
  DEBUG   machine:simulation    TICK: 323     PC: 57    ADDR: 120    MEM_OUT: 2    ALU: 0    ACC: 0    LD #93
  DEBUG   machine:simulation    TICK: 324     PC: 58    ADDR: 120    MEM_OUT: 2    ALU: 93    ACC: 93    ST 121
  DEBUG   machine:simulation    TICK: 326     PC: 59    ADDR: 121    MEM_OUT: 2    ALU: 93    ACC: 93    LD 2046
  WARNING machine:simulation     Входной буфер пустой!
```

Пример проверки исходного кода:
``` shell
$ poetry run pytest -v
platform win32 -- Python 3.12.5, pytest-8.3.2, pluggy-1.5.0 -- \Users\pypoetry\Cache\virtualenvs\CSA-lab3-xDSnBXcc-py3.12\Scripts\python.exe
cachedir: .pytest_cache
rootdir: \Users\Ruslan\PyProjects\CSA_lab3\CSA-lab3
configfile: pyproject.toml
plugins: golden-0.2.2
collected 3 items                                                                                                                                                

tests/golden_test.py::test_translator_and_machine[golden/cat.yml]         PASSED  [ 33%] 
tests/golden_test.py::test_translator_and_machine[golden/hello_user.yml]  PASSED  [ 66%] 
tests/golden_test.py::test_translator_and_machine[golden/prob1.yml]       PASSED  [100%] 

===================================================== 3 passed in 1.84s =======================================================================
$ poetry run ruff check
All checks passed!
$ poetry run ruff format --check


```

## Статистика
| ФИО                         | алг             | LoC | code байт | code инстр. | инстр. | такт. |
|-----------------------------|-----------------|-----|-----------|-------------|--------|-------|
| Кожемякин Руслан Алексеевич | hello_user      | 7   |    851    |     171     |  644   | 1010  |
| Кожемякин Руслан Алексеевич | cat             | 5   |    461    |     93      |  971   | 1543  |
| Кожемякин Руслан Алексеевич | prob1           | 9   |    181    |     37      |  2571  | 42441 |
