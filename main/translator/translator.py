import struct
import re
from typing import NamedTuple
import uuid
from ..isa import AddrMode, Instruction, Opcode

def symbols():
    return {"+", "-", "*", "/", "%", ">", "<", "==", "!="}


def symbol2opcode(symbol) -> Opcode:
    return {
        "+": Opcode.ADD,
        "-": Opcode.SUB,
        "*": Opcode.MUL,
        "/": Opcode.DIV,
        "%": Opcode.MOD,
        ">": Opcode.BG,
        "<": Opcode.BGE,
        "==": Opcode.BEQ,
        "!=": Opcode.BNE
    }.get(symbol)

def get_main(str: str) -> str:
    return str.split("//", 1)[0].strip()

def del_tab(str: str) -> str:
    return ' '.join([k for k in str.split(" ") if k])

class Addr(NamedTuple):
    addr: int
    reused: bool

class While_statement(NamedTuple):
    typ: str
    start: int
    end: int

class If_statement(NamedTuple):
    typ: str
    end: int

def count_end_blocks(text: str) -> int:
    count = 0
    for elem in text.splitlines():
        elem = get_main(elem)
        if elem == "}": count += 1
    return count

def get_addr_var(instructions: list, var_name_addr: dict, to_unlock: list, var: str, count_var: int, start = None):
    count_var = count_var
    start = start
    addr = 0
    if var.isdigit():
        count_var += 1
        name_reused_mem = str(uuid.uuid4().hex)
        reused_mem = count_var
        for i in var_name_addr.items():
            if i[1].reused:
                count_var -= 1
                reused_mem = i[1].addr
                name_reused_mem = i[0]
                break
        to_unlock.append(name_reused_mem)
        var_name_addr[name_reused_mem] = Addr(reused_mem, False)
        instructions.append(Instruction(Opcode.LD, AddrMode.IMMEDIATE, var))
        if start == 0: start = len(instructions) - 1
        instructions.append(Instruction(Opcode.ST, AddrMode.DIRECT, reused_mem))
        addr = reused_mem
    else:
        addr = var_name_addr[var].addr
    return count_var, addr, start

def text2instructions(text: str) -> list[Instruction]:
    STR_MAX_LENGTH = 16
    end_blocks = count_end_blocks(text)
    counter_end_block = 0
    list_of_while_if = []
    instructions = []
    var_name_addr = {}
    str_name_length = {}
    move_addr = 0
    count_var = -1
    count = -1
    for elem in text.splitlines():
        elem = get_main(elem)
        # print(str(count) + " " + elem)
        count += 1

        name_or_digit = r"([_a-zA-Z]\w*|[-+]?[0-9]+)"
        type_int = re.search(r"^int *[_a-zA-Z]\w* *= *[-+]?[0-9]+", elem)
        type_str = re.search(r"^str *[_a-zA-Z]\w* *= *(['\"])(?:(?!(?:\\|\1)).|\\.)*\1", elem)
        math_op = re.search(r"^[_a-zA-Z]\w* *= *"+name_or_digit+r" *[\+\-\/\%\*] *"+name_or_digit+r" *", elem)

        if_statement = re.search(r"^if *\( *"+name_or_digit+r" *[\+\-\/\%\*] *"+name_or_digit+r" *([<>]|>=|<=|==|!=) *"+name_or_digit+r" *(\|\|) *"+name_or_digit+r" *[\+\-\/\%\*] *"+name_or_digit+r" *([<>]|>=|<=|==|!=) *"+name_or_digit+r" *\) *{", elem)

        while_statement = re.search(r"while *\( *"+name_or_digit+r" *([<>]|>=|<=|==|!=) *"+name_or_digit+r" *\) *{", elem)
        end_block = re.search(r"^}", elem)
        input_ = re.search(r"^<< *[_a-zA-Z]\w*", elem)
        output_ = re.search(r"^>> *[_a-zA-Z]\w*", elem)
        # print(math_op)
        # print(if_statement)
        # print(math_op)
        # print(while_statement)
        if type_int:
            # print(while_statement)
            # print("start=====type_int=====")
            count_var += 1
            without_tab = del_tab(type_int[0])
            split_str = without_tab.split(" ")
            # print(split_str)
            var_name_addr[split_str[1]] = Addr(count_var, False)
            instructions.append(Instruction(Opcode.LD, AddrMode.IMMEDIATE, split_str[3]))
            instructions.append(Instruction(Opcode.ST, AddrMode.DIRECT, count_var))
            # print("end=====type_int=====")
        elif type_str:
            # print(type_str)
            # print("start=====type_str=====")
            count_var += 1
            without_tab = del_tab(type_str[0])
            split_str = without_tab.split(" ", 3)
            # print(split_str)
            ascii_code = list(split_str[3][1:-1].encode('cp1251'))
            start_pos = count_var
            var_name_addr[split_str[1]] = Addr(start_pos, False)
            for code in ascii_code:
                instructions.append(Instruction(Opcode.LD, AddrMode.IMMEDIATE, code))
                instructions.append(Instruction(Opcode.ST, AddrMode.DIRECT, count_var))
                count_var += 1
            str_length = count_var - start_pos
            if str_length < 16: count_var += (16 - str_length)
            str_name_length[split_str[1]] = str_length
            # print(ascii_code)
            # print("end=====type_str=====")
        elif math_op:
            # print("start=====math_op=====")
            without_tab = del_tab(math_op[0])
            split_str = without_tab.split(" ")
            # print(split_str)
            # print(split_str[2].isdigit())
            first_addr = 0
            second_addr = 0
            to_unlock = []

            count_var, first_addr, foo = get_addr_var(instructions, var_name_addr, to_unlock, split_str[2], count_var)
            # if split_str[2].isdigit():
            #     count_var += 1
            #     name_reused_mem = str(uuid.uuid4().hex)
            #     reused_mem = count_var
            #     for i in var_name_addr.items():
            #         if i[1].reused:
            #             count_var -= 1
            #             reused_mem = i[1].addr
            #             name_reused_mem = i[0]
            #             break
            #     to_unlock.append(name_reused_mem)
            #     var_name_addr[name_reused_mem] = Addr(reused_mem, False)
            #     instructions.append(Instruction(Opcode.LD, AddrMode.IMMEDIATE, split_str[2]))
            #     instructions.append(Instruction(Opcode.ST, AddrMode.DIRECT, reused_mem))
            #     first_addr = reused_mem
            # else:
            #     first_addr = var_name_addr[split_str[2]].addr
            count_var, second_addr, foo = get_addr_var(instructions, var_name_addr, to_unlock, split_str[4], count_var)
            # if split_str[4].isdigit():
            #     count_var += 1
            #     name_reused_mem = str(uuid.uuid4().hex)
            #     reused_mem = count_var
            #     for i in var_name_addr.items():
            #         if i[1].reused:
            #             count_var -= 1
            #             reused_mem = i[1].addr
            #             name_reused_mem = i[0]
            #             break
            #     to_unlock.append(name_reused_mem)
            #     var_name_addr[name_reused_mem] = Addr(reused_mem, False)
            #     instructions.append(Instruction(Opcode.LD, AddrMode.IMMEDIATE, split_str[4]))
            #     instructions.append(Instruction(Opcode.ST, AddrMode.DIRECT, reused_mem))
            #     second_addr = reused_mem
            # else:
            #     second_addr = var_name_addr[split_str[4]].addr

            instructions.append(Instruction(Opcode.LD, AddrMode.DIRECT, first_addr))
            instructions.append(Instruction(symbol2opcode(split_str[3]), AddrMode.DIRECT, second_addr))
            instructions.append(Instruction(Opcode.ST, AddrMode.DIRECT, first_addr))

            for name in to_unlock:
                var_name_addr[name] = Addr(var_name_addr[name].addr, True)
            to_unlock.clear()
            
            # print(f"переменная: {split_str[0]} в памяти тут: {var_name_addr[split_str[0]]}")
            # print("end=====math_op=====")
        elif if_statement:
            # print("start=====if_statement=====")
            without_tab = del_tab(if_statement[0])
            split_str = without_tab.split(" ")

            addr1, addr2, addr3, addr4, addr5, addr6 = 0, 0, 0, 0, 0, 0
            end = 0
            to_unlock = []

            count_var, addr1, none = get_addr_var(instructions, var_name_addr, to_unlock, split_str[1][1:], count_var, start)
            count_var, addr2, none = get_addr_var(instructions, var_name_addr, to_unlock, split_str[3], count_var, start)
            count_var, addr3, none = get_addr_var(instructions, var_name_addr, to_unlock, split_str[5], count_var, start)

            instructions.append(Instruction(Opcode.LD, AddrMode.DIRECT, addr1))
            instructions.append(Instruction(symbol2opcode(split_str[2]), AddrMode.DIRECT, addr2))
            instructions.append(Instruction(Opcode.CMP, AddrMode.DIRECT, addr3))
            instructions.append(Instruction(Opcode.BEQ, AddrMode.DIRECT, 7777777))
            BEQ_pos = len(instructions) - 1

            count_var, addr4, none = get_addr_var(instructions, var_name_addr, to_unlock, split_str[7], count_var, start)
            count_var, addr5, none = get_addr_var(instructions, var_name_addr, to_unlock, split_str[9], count_var, start)
            count_var, addr6, none = get_addr_var(instructions, var_name_addr, to_unlock, split_str[11][:-1], count_var, start)

            instructions.append(Instruction(Opcode.LD, AddrMode.DIRECT, addr4))
            instructions.append(Instruction(symbol2opcode(split_str[8]), AddrMode.DIRECT, addr5))
            instructions.append(Instruction(symbol2opcode(Opcode.CMP), AddrMode.DIRECT, addr6))
            instructions.append(Instruction(Opcode.BNE, AddrMode.DIRECT, 7777777))
            end = len(instructions) - 1

            instructions[BEQ_pos] = Instruction(instructions[BEQ_pos].opcode, instructions[BEQ_pos].addr_mode, end+1)

            # print(split_str)

            list_of_while_if.append(If_statement("if", end))
            # count_var += 1
        elif while_statement:
            # print("start=====while_statement=====")
            without_tab = del_tab(while_statement[0])
            split_str = without_tab.split(" ")
            # print(split_str)

            first_addr = 0
            second_addr = 0
            to_unlock = []
            start = 0
            end = 0
            count_var, first_addr, start = get_addr_var(instructions, var_name_addr, to_unlock, split_str[1][1:], count_var, start)
            # if split_str[1][1:].isdigit():
            #     count_var += 1
            #     name_reused_mem = str(uuid.uuid4().hex)
            #     reused_mem = count_var
            #     for i in var_name_addr.items():
            #         if i[1].reused:
            #             count_var -= 1
            #             reused_mem = i[1].addr
            #             name_reused_mem = i[0]
            #             break
            #     to_unlock.append(name_reused_mem)
            #     var_name_addr[name_reused_mem] = Addr(reused_mem, False)
            #     instructions.append(Instruction(Opcode.LD, AddrMode.IMMEDIATE, split_str[1][1:]))
            #     if start == 0: start = len(instructions) - 1
            #     instructions.append(Instruction(Opcode.ST, AddrMode.DIRECT, reused_mem))
            #     first_addr = reused_mem
            # else:
            #     first_addr = var_name_addr[split_str[1][1:]].addr
            count_var, second_addr, start = get_addr_var(instructions, var_name_addr, to_unlock, split_str[3][:-1], count_var, start)
            # if split_str[3][:-1].isdigit():
            #     count_var += 1
            #     name_reused_mem = str(uuid.uuid4().hex)
            #     reused_mem = count_var
            #     for i in var_name_addr.items():
            #         if i[1].reused:
            #             count_var -= 1
            #             reused_mem = i[1].addr
            #             name_reused_mem = i[0]
            #             break
            #     to_unlock.append(name_reused_mem)
            #     var_name_addr[name_reused_mem] = Addr(reused_mem, False)
            #     instructions.append(Instruction(Opcode.LD, AddrMode.IMMEDIATE, split_str[3][:-1]))
            #     if start == 0: start = len(instructions) - 1
            #     instructions.append(Instruction(Opcode.ST, AddrMode.DIRECT, reused_mem))
            #     second_addr = reused_mem
            # else:
            #     second_addr = var_name_addr[split_str[3][:-1]].addr

            instructions.append(Instruction(Opcode.LD, AddrMode.DIRECT, first_addr))

            if start == 0: start = len(instructions) - 1
            instructions.append(Instruction(Opcode.CMP, AddrMode.DIRECT, second_addr))
            # instructions.append(Instruction(symbol2opcode(split_str[2]), AddrMode.DIRECT, second_addr))

            for name in to_unlock:
                var_name_addr[name] = Addr(var_name_addr[name].addr, True)
            to_unlock.clear()

            instructions.append(Instruction(symbol2opcode(split_str[2]), AddrMode.DIRECT, 7777777))
            end = len(instructions) - 1

            list_of_while_if.append(While_statement("while", start, end))

            # count_var += 1
            # print("end=====while_statement=====")
        elif input_:
            count_var += 1
            without_tab = del_tab(input_[0])
            split_str = without_tab.split(" ")
            first_cell = var_name_addr[split_str[1]].addr

            # TODO очищаем полностью пространство старой строки + вывод длины строки в константу
            # for i in range(first_cell, first_cell + STR_MAX_LENGTH, 1):
            #     instructions.append(Instruction(Opcode.LD, AddrMode.IMMEDIATE, 0))
            #     instructions.append(Instruction(Opcode.ST, AddrMode.DIRECT, i))

            instructions.append(Instruction(Opcode.LD, AddrMode.IMMEDIATE, 0)) # счетчик длины слова
            instructions.append(Instruction(Opcode.ST, AddrMode.DIRECT, count_var))

            instructions.append(Instruction(Opcode.LD, AddrMode.IMMEDIATE, first_cell)) # адрес первой ячейки строки
            instructions.append(Instruction(Opcode.ST, AddrMode.DIRECT, count_var + 1))

            instructions.append(Instruction(Opcode.LD, AddrMode.DIRECT, 2**32 - 1)) # получили входные данные
            instructions.append(Instruction(Opcode.CMP, AddrMode.IMMEDIATE, 0)) # проверили на ноль
            instructions.append(Instruction(Opcode.BEQ, AddrMode.DIRECT, len(instructions) + 11)) # если ноль, то в конец всех эппэндов
            instructions.append(Instruction(Opcode.ST, AddrMode.DIRECT, count_var + 1)) # сохранили в первую ячейку введенный символ
            instructions.append(Instruction(Opcode.LD, AddrMode.DIRECT, count_var))
            instructions.append(Instruction(Opcode.ADD, AddrMode.IMMEDIATE, 1)) # увеличили счетчик длины слова
            instructions.append(Instruction(Opcode.ST, AddrMode.DIRECT, count_var))
            instructions.append(Instruction(Opcode.LD, AddrMode.DIRECT, count_var + 1))
            instructions.append(Instruction(Opcode.ADD, AddrMode.IMMEDIATE, 1)) # увеличили адрес ячейки на 1(указываем на следующую)
            instructions.append(Instruction(Opcode.ST, AddrMode.DIRECT, count_var + 1))
            instructions.append(Instruction(Opcode.CMP, AddrMode.IMMEDIATE, STR_MAX_LENGTH)) # проверяем, чтобы строка была до 16 символов
            instructions.append(Instruction(Opcode.BEQ, AddrMode.DIRECT, len(instructions) + 2))
            instructions.append(Instruction(Opcode.JMP, AddrMode.DIRECT, len(instructions) - 12))

            count_var += 1
            # print("start=====input=====")
        elif output_:
            # print("start=====output=====")
            without_tab = del_tab(output_[0])
            split_str = without_tab.split(" ")
            print(output_[0])
            if output_:
                str_length = None
                is_str = False
                try:
                    print(len(str_name_length))
                    print(str_name_length[split_str[1]])
                    print(str_name_length)
                    if len(str_name_length) != 0: str_length = str_name_length[split_str[1]]
                except KeyError:
                    pass
                # вывод строки
                # TODO переделать вывод строк
                count_var += 1
                if str_length != None:
                    print("вывод строки")
                    print(var_name_addr[split_str[1]].addr)
                    print(str_length)
                    print(var_name_addr)

                    first_cell = var_name_addr[split_str[1]].addr

                    instructions.append(Instruction(Opcode.LD, AddrMode.IMMEDIATE, 0)) # счетчик длины слова
                    instructions.append(Instruction(Opcode.ST, AddrMode.DIRECT, count_var))

                    instructions.append(Instruction(Opcode.LD, AddrMode.IMMEDIATE, first_cell)) # адрес первой ячейки строки
                    instructions.append(Instruction(Opcode.ST, AddrMode.DIRECT, count_var + 1))

                    instructions.append(Instruction(Opcode.LD, AddrMode.DIRECT, count_var + 1)) # загружаем значение первой ячейки в ACC
                    instructions.append(Instruction(Opcode.CMP, AddrMode.IMMEDIATE, 0)) # проверяем на ноль
                    instructions.append(Instruction(Opcode.BEQ, AddrMode.DIRECT, len(instructions) + 11)) # если ноль, то в конец всех эппэндов
                    instructions.append(Instruction(Opcode.ST, AddrMode.DIRECT, 2**32)) # записываем значение в ячейку вывода
                    instructions.append(Instruction(Opcode.LD, AddrMode.DIRECT, count_var))
                    instructions.append(Instruction(Opcode.ADD, AddrMode.IMMEDIATE, 1)) # увеличили счетчик длины слова
                    instructions.append(Instruction(Opcode.ST, AddrMode.DIRECT, count_var))
                    instructions.append(Instruction(Opcode.LD, AddrMode.DIRECT, count_var + 1))
                    instructions.append(Instruction(Opcode.ADD, AddrMode.IMMEDIATE, 1)) # увеличили адрес ячейки на 1(указываем на следующую)
                    instructions.append(Instruction(Opcode.ST, AddrMode.DIRECT, count_var + 1))
                    instructions.append(Instruction(Opcode.CMP, AddrMode.IMMEDIATE, STR_MAX_LENGTH)) # проверяем, чтобы строка была до 16 символов
                    instructions.append(Instruction(Opcode.BEQ, AddrMode.DIRECT, len(instructions) + 2))
                    instructions.append(Instruction(Opcode.JMP, AddrMode.DIRECT, len(instructions) - 12))
                    count_var += 1
                # вывод числа
                else:
                    print("вывод числа")
                    instructions.append(Instruction(Opcode.LD, AddrMode.DIRECT, var_name_addr[split_str[1]].addr))
                    instructions.append(Instruction(Opcode.ST, AddrMode.DIRECT, 2**32))
            

        elif end_block:
            # print("start======end_block=====")
            counter_end_block += 1
            pos = len(list_of_while_if) - counter_end_block
            obj_by_pos = list_of_while_if[pos]
            # print(obj_by_pos)
            if obj_by_pos.typ == "while":
                last_pos_inst = len(instructions) + 1
                instructions[obj_by_pos.end] = Instruction(instructions[obj_by_pos.end].opcode, instructions[obj_by_pos.end].addr_mode, last_pos_inst)
                instructions.append(Instruction(Opcode.JMP, AddrMode.DIRECT, obj_by_pos.start))
            if obj_by_pos.typ == "if":
                last_pos_inst = len(instructions)
                # print("lol")
                # print(instructions[obj_by_pos.end])
                instructions[obj_by_pos.end] = Instruction(instructions[obj_by_pos.end].opcode, instructions[obj_by_pos.end].addr_mode, last_pos_inst)
            # print("end======end_block=====")
        else:
            assert False, "Невалидный синтаксис программы"

        # assert if_statement, "Невалидный синтаксис программы" + str(if_statement)

    # print(var_name_addr)
    # print(str_name_length)
    print(instructions)
    for e, i in enumerate(instructions):
        print(e, i)
    # return instructions

def machine2binary(machine_code: list) -> bytes:
    binary = b''
    for code in machine_code:
        if isinstance(code, Instruction):
            # print("was here")
            if code.opcode == Opcode.HLT:
                binary += struct.pack(">B", (code.opcode.value << 2))
                continue
            binary += struct.pack(">Bi", (code.opcode.value << 2 | code.addr_mode.value), code.arg)
            continue
        binary += struct.pack(">i", code)
    print(binary)
    return binary

if __name__ == '__main__':

    prob1 =  "int  sum  =  321\n"+"int x = 143\n"+"while (x < 1000) {\n"+"    if (x % 3 == 0 || x % 5 == 0) {\n"+"        sum = sum + x\n"+"    }\n"+"    x = x + 1\n"+"}\n"+">> sum"
    int_print = "int num = 4324\n"+">> num"
    # text2instructions(int_print)

    cat = "str string = \"\"\n"+"while (1 < 2) {\n"+"<< string\n"+">> string\n"+"}"
    hello_world = "str string = \"Hello, world!\"\n"+">> string"
    whats_name = "str str = \"What's your name?\"\n"+"str str_two = \"Hello, \"\n"+"str name = \"\"\n"+"<< name\n"+">> str_two\n"+">> name"
    # print("if (x < 1) {\n    x = x + 1\n}")

    # text2instructions(cat)
    # text2instructions(hello_world)
    text2instructions(whats_name)
    # text2instructions(prob1)
