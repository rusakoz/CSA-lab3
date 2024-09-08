import logging
import struct
import re
import sys
import uuid
from typing import NamedTuple
from ..isa import AddrMode, Instruction, Opcode, INPUT_CELL, OUTPUT_CELL


def symbols():
    return {"+", "-", "*", "/", "%", ">", "<", "==", "!="}


def symbol2opcode(symbol) -> Opcode:
    return {
        "+": Opcode.ADD,
        "-": Opcode.SUB,
        "*": Opcode.MUL,
        "/": Opcode.DIV,
        "%": Opcode.MOD,
        ">": Opcode.BGE,
        "<": Opcode.BG,
        "==": Opcode.BEQ,
        "!=": Opcode.BNE,
    }.get(symbol)


def get_main(str: str) -> str:
    return str.split("//", 1)[0].strip()


def del_tab(str: str) -> str:
    return " ".join([k for k in str.split(" ") if k])


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
        if elem == "}":
            count += 1
    return count


def get_addr_var(
    instructions: list, var_name_addr: dict, to_unlock: list, var: str, count_var: int, start: int | None = None
):
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
        instructions.append(Instruction(Opcode.LD, AddrMode.IMMEDIATE, int(var)))
        if start == 0:
            start = len(instructions) - 1
        instructions.append(Instruction(Opcode.ST, AddrMode.DIRECT, reused_mem))
        addr = reused_mem
    else:
        addr = var_name_addr[var].addr
    return count_var, addr, start


def code2instructions(text: str) -> list[Instruction]:
    STR_MAX_LENGTH = 24
    counter_end_block = 0
    list_of_while_if = []
    instructions = []
    var_name_addr = {}
    str_name_length = {}
    move_addr = []
    count_var = -1
    count = -1
    for elem in text.splitlines():
        elem = get_main(elem)
        count += 1

        name_or_digit = r"([_a-zA-Z]\w*|[-+]?[0-9]+)"
        type_int = re.search(r"^int *[_a-zA-Z]\w* *= *[-+]?[0-9]+", elem)
        type_str = re.search(r"^str *[_a-zA-Z]\w* *= *(['\"])(?:(?!(?:\\|\1)).|\\.)*\1", elem)
        math_op = re.search(r"^[_a-zA-Z]\w* *= *" + name_or_digit + r" *[\+\-\/\%\*] *" + name_or_digit + r" *", elem)

        if_statement = re.search(
            r"^if *\( *"
            + name_or_digit
            + r" *[\+\-\/\%\*] *"
            + name_or_digit
            + r" *([<>]|>=|<=|==|!=) *"
            + name_or_digit
            + r" *(\|\|) *"
            + name_or_digit
            + r" *[\+\-\/\%\*] *"
            + name_or_digit
            + r" *([<>]|>=|<=|==|!=) *"
            + name_or_digit
            + r" *\) *{",
            elem,
        )

        while_statement = re.search(
            r"while *\( *" + name_or_digit + r" *([<>]|>=|<=|==|!=) *" + name_or_digit + r" *\) *{", elem
        )
        end_block = re.search(r"^}", elem)
        input_ = re.search(r"^<< *[_a-zA-Z]\w*", elem)
        output_ = re.search(r"^>> *[_a-zA-Z]\w*", elem)

        if type_int:
            count_var += 1
            without_tab = del_tab(type_int[0])
            split_str = without_tab.split(" ")

            var_name_addr[split_str[1]] = Addr(count_var, False)
            instructions.append(Instruction(Opcode.LD, AddrMode.IMMEDIATE, int(split_str[3])))
            instructions.append(Instruction(Opcode.ST, AddrMode.DIRECT, count_var))

        elif type_str:
            count_var += 1
            without_tab = del_tab(type_str[0])
            split_str = without_tab.split(" ", 3)

            assert (
                len(split_str[3][1:-1]) <= STR_MAX_LENGTH
            ), f'Превышен лимит {STR_MAX_LENGTH} строки "{split_str[3][1:-1]}"'

            ascii_code = list(split_str[3][1:-1].encode("cp1251"))
            start_pos = count_var
            var_name_addr[split_str[1]] = Addr(start_pos, False)
            for code in ascii_code:
                instructions.append(Instruction(Opcode.LD, AddrMode.IMMEDIATE, code))
                instructions.append(Instruction(Opcode.ST, AddrMode.DIRECT, count_var))
                count_var += 1
            str_length = count_var - start_pos
            if str_length < STR_MAX_LENGTH:
                count_var += STR_MAX_LENGTH - str_length
            str_name_length[split_str[1]] = str_length
        elif math_op:
            without_tab = del_tab(math_op[0])
            split_str = without_tab.split(" ")

            first_addr = 0
            second_addr = 0
            to_unlock = []

            count_var, first_addr, foo = get_addr_var(instructions, var_name_addr, to_unlock, split_str[2], count_var)

            count_var, second_addr, foo = get_addr_var(instructions, var_name_addr, to_unlock, split_str[4], count_var)

            instructions.append(Instruction(Opcode.LD, AddrMode.DIRECT, first_addr))
            instructions.append(Instruction(symbol2opcode(split_str[3]), AddrMode.DIRECT, second_addr))
            instructions.append(Instruction(Opcode.ST, AddrMode.DIRECT, first_addr))

            for name in to_unlock:
                var_name_addr[name] = Addr(var_name_addr[name].addr, True)
            to_unlock.clear()
        elif if_statement:
            without_tab = del_tab(if_statement[0])
            split_str = without_tab.split(" ")

            addr1, addr2, addr3, addr4, addr5, addr6 = 0, 0, 0, 0, 0, 0
            end = 0
            to_unlock = []

            count_var, addr1, none = get_addr_var(instructions, var_name_addr, to_unlock, split_str[1][1:], count_var)
            count_var, addr2, none = get_addr_var(instructions, var_name_addr, to_unlock, split_str[3], count_var)
            count_var, addr3, none = get_addr_var(instructions, var_name_addr, to_unlock, split_str[5], count_var)

            instructions.append(Instruction(Opcode.LD, AddrMode.DIRECT, addr1))
            instructions.append(Instruction(symbol2opcode(split_str[2]), AddrMode.DIRECT, addr2))
            instructions.append(Instruction(Opcode.CMP, AddrMode.DIRECT, addr3))
            instructions.append(Instruction(Opcode.BEQ, AddrMode.DIRECT, 7777777))
            BEQ_pos = len(instructions) - 1

            count_var, addr4, none = get_addr_var(instructions, var_name_addr, to_unlock, split_str[7], count_var)
            count_var, addr5, none = get_addr_var(instructions, var_name_addr, to_unlock, split_str[9], count_var)
            count_var, addr6, none = get_addr_var(instructions, var_name_addr, to_unlock, split_str[11][:-1], count_var)

            instructions.append(Instruction(Opcode.LD, AddrMode.DIRECT, addr4))
            instructions.append(Instruction(symbol2opcode(split_str[8]), AddrMode.DIRECT, addr5))
            instructions.append(Instruction(Opcode.CMP, AddrMode.DIRECT, addr6))
            instructions.append(Instruction(Opcode.BNE, AddrMode.DIRECT, 7777777))
            end = len(instructions) - 1

            instructions[BEQ_pos] = Instruction(instructions[BEQ_pos].opcode, instructions[BEQ_pos].addr_mode, end + 1)

            list_of_while_if.append(If_statement("if", end))
        elif while_statement:
            without_tab = del_tab(while_statement[0])
            split_str = without_tab.split(" ")

            first_addr = 0
            second_addr = 0
            to_unlock = []
            start = 0
            end = 0

            count_var, first_addr, start = get_addr_var(
                instructions, var_name_addr, to_unlock, split_str[1][1:], count_var, start
            )
            count_var, second_addr, start = get_addr_var(
                instructions, var_name_addr, to_unlock, split_str[3][:-1], count_var, start
            )

            instructions.append(Instruction(Opcode.LD, AddrMode.DIRECT, first_addr))

            if start == 0:
                start = len(instructions) - 1
            instructions.append(Instruction(Opcode.CMP, AddrMode.DIRECT, second_addr))

            for name in to_unlock:
                var_name_addr[name] = Addr(var_name_addr[name].addr, True)
            to_unlock.clear()

            instructions.append(Instruction(symbol2opcode(split_str[2]), AddrMode.DIRECT, 7777777))
            end = len(instructions) - 1

            list_of_while_if.append(While_statement("while", start, end))
        elif input_:
            count_var += 1
            without_tab = del_tab(input_[0])
            split_str = without_tab.split(" ")
            first_cell = var_name_addr[split_str[1]].addr

            # очищаем пространство старой строки
            for i in range(first_cell, first_cell + STR_MAX_LENGTH, 1):
                instructions.append(Instruction(Opcode.LD, AddrMode.IMMEDIATE, 0))
                instructions.append(Instruction(Opcode.ST, AddrMode.DIRECT, i))

            instructions.append(Instruction(Opcode.LD, AddrMode.IMMEDIATE, 0))  # счетчик длины слова
            instructions.append(Instruction(Opcode.ST, AddrMode.DIRECT, count_var))

            instructions.append(Instruction(Opcode.LD, AddrMode.IMMEDIATE, first_cell))  # адрес первой ячейки строки
            move_addr.append(len(instructions) - 1)  # для сдвига адреса
            instructions.append(Instruction(Opcode.ST, AddrMode.DIRECT, count_var + 1))

            instructions.append(Instruction(Opcode.LD, AddrMode.DIRECT, INPUT_CELL))  # получили входные данные
            instructions.append(Instruction(Opcode.CMP, AddrMode.IMMEDIATE, 0))  # проверили на ноль
            instructions.append(Instruction(Opcode.BEQ, AddrMode.DIRECT, len(instructions) + 12))  # если ноль, то в конец всех эппэндов
            instructions.append(Instruction(Opcode.ST, AddrMode.INDIRECT, count_var + 1))  # сохранили в первую ячейку введенный символ
            instructions.append(Instruction(Opcode.LD, AddrMode.DIRECT, count_var))
            instructions.append(Instruction(Opcode.ADD, AddrMode.IMMEDIATE, 1))  # увеличили счетчик длины слова
            instructions.append(Instruction(Opcode.ST, AddrMode.DIRECT, count_var))
            instructions.append(Instruction(Opcode.LD, AddrMode.DIRECT, count_var + 1))
            instructions.append(Instruction(Opcode.ADD, AddrMode.IMMEDIATE, 1))  # увеличили адрес ячейки на 1(указываем на следующую)
            instructions.append(Instruction(Opcode.ST, AddrMode.DIRECT, count_var + 1))
            instructions.append(Instruction(Opcode.LD, AddrMode.DIRECT, count_var))
            instructions.append(Instruction(Opcode.CMP, AddrMode.IMMEDIATE, STR_MAX_LENGTH))  # проверяем, чтобы строка была до пределов
            instructions.append(Instruction(Opcode.BEQ, AddrMode.DIRECT, len(instructions) + 2))
            instructions.append(Instruction(Opcode.JMP, AddrMode.DIRECT, len(instructions) - 13))

            count_var += 1
        elif output_:
            without_tab = del_tab(output_[0])
            split_str = without_tab.split(" ")
            if output_:
                str_length = None
                try:
                    if len(str_name_length) != 0:
                        str_length = str_name_length[split_str[1]]
                except KeyError:
                    pass
                # вывод строки
                count_var += 1
                if str_length != None:
                    first_cell = var_name_addr[split_str[1]].addr

                    instructions.append(Instruction(Opcode.LD, AddrMode.IMMEDIATE, 0))  # счетчик длины слова
                    instructions.append(Instruction(Opcode.ST, AddrMode.DIRECT, count_var))

                    instructions.append(Instruction(Opcode.LD, AddrMode.IMMEDIATE, first_cell))  # адрес первой ячейки строки
                    move_addr.append(len(instructions) - 1)  # для сдвига адреса
                    instructions.append(Instruction(Opcode.ST, AddrMode.DIRECT, count_var + 1))

                    instructions.append(Instruction(Opcode.LD, AddrMode.INDIRECT, count_var + 1))  # загружаем значение первой ячейки в ACC
                    instructions.append(Instruction(Opcode.CMP, AddrMode.IMMEDIATE, 0))  # проверяем на ноль
                    instructions.append(Instruction(Opcode.BEQ, AddrMode.DIRECT, len(instructions) + 12))  # если ноль, то в конец всех эппэндов
                    instructions.append(Instruction(Opcode.ST, AddrMode.DIRECT, OUTPUT_CELL))  # записываем значение в ячейку вывода
                    instructions.append(Instruction(Opcode.LD, AddrMode.DIRECT, count_var))
                    instructions.append(Instruction(Opcode.ADD, AddrMode.IMMEDIATE, 1))  # увеличили счетчик длины слова
                    instructions.append(Instruction(Opcode.ST, AddrMode.DIRECT, count_var))
                    instructions.append(Instruction(Opcode.LD, AddrMode.DIRECT, count_var + 1))
                    instructions.append(Instruction(Opcode.ADD, AddrMode.IMMEDIATE, 1))  # увеличили адрес ячейки на 1(указываем на следующую)
                    instructions.append(Instruction(Opcode.ST, AddrMode.DIRECT, count_var + 1))
                    instructions.append(Instruction(Opcode.LD, AddrMode.DIRECT, count_var))
                    instructions.append(Instruction(Opcode.CMP, AddrMode.IMMEDIATE, STR_MAX_LENGTH))  # проверяем, чтобы строка была до 16 символов
                    instructions.append(Instruction(Opcode.BEQ, AddrMode.DIRECT, len(instructions) + 2))
                    instructions.append(Instruction(Opcode.JMP, AddrMode.DIRECT, len(instructions) - 13))
                    count_var += 1
                # вывод числа
                else:
                    instructions.append(Instruction(Opcode.LD, AddrMode.DIRECT, var_name_addr[split_str[1]].addr))
                    instructions.append(Instruction(Opcode.ST, AddrMode.DIRECT, OUTPUT_CELL))
        elif end_block:
            counter_end_block += 1
            pos = len(list_of_while_if) - counter_end_block
            obj_by_pos = list_of_while_if[pos]
            if obj_by_pos.typ == "while":
                last_pos_inst = len(instructions) + 1
                instructions[obj_by_pos.end] = Instruction(instructions[obj_by_pos.end].opcode, instructions[obj_by_pos.end].addr_mode, last_pos_inst)
                instructions.append(Instruction(Opcode.JMP, AddrMode.DIRECT, obj_by_pos.start))
            if obj_by_pos.typ == "if":
                last_pos_inst = len(instructions)
                instructions[obj_by_pos.end] = Instruction(instructions[obj_by_pos.end].opcode, instructions[obj_by_pos.end].addr_mode, last_pos_inst)
        else:
            assert False, "Невалидный синтаксис программы"

    instructions.append(Instruction(Opcode.HLT, None, None))

    # перенос адресаций данных в конец инструкций
    for e, i in enumerate(instructions):
        if (
            (
                i.opcode == Opcode.LD
                or i.opcode == Opcode.ST
                or i.opcode == Opcode.ADD
                or i.opcode == Opcode.SUB
                or i.opcode == Opcode.DIV
                or i.opcode == Opcode.MUL
                or i.opcode == Opcode.MOD
                or i.opcode == Opcode.CMP
            )
            and (i.addr_mode == AddrMode.DIRECT or i.addr_mode == AddrMode.INDIRECT)
            and i.arg != INPUT_CELL
            and i.arg != OUTPUT_CELL
        ):
            instructions[e] = Instruction(i.opcode, i.addr_mode, i.arg + len(instructions))
    for i in move_addr:
        instructions[i] = Instruction(
            instructions[i].opcode, instructions[i].addr_mode, instructions[i].arg + len(instructions)
        )
    return instructions


def instructions2binary(instructions: list) -> bytes:
    binary = b""
    for code in instructions:
        if isinstance(code, Instruction):
            if code.opcode == Opcode.HLT:
                binary += struct.pack(">B", (code.opcode.value << 2))
                continue
            if code.addr_mode == AddrMode.DIRECT or code.addr_mode == AddrMode.INDIRECT:
                binary += struct.pack(">BI", (code.opcode.value << 2 | code.addr_mode.value), code.arg)
            else:
                binary += struct.pack(">Bi", (code.opcode.value << 2 | code.addr_mode.value), code.arg)
            continue
        binary += struct.pack(">i", code)
    return binary


def main(input_file: str, output_file: str, debug_file: str):
    with open(input_file, encoding="utf-8") as file:
        code = file.read()

    instructions = code2instructions(code)
    binary = instructions2binary(instructions)

    with open(output_file, "wb") as file:
        file.write(binary)
    code_bytes = 0
    with open(debug_file, "w", encoding="utf-8") as file:
        file.write("=============INSTRUCTIONS============\n")
        file.write(f"{"<address>":<16}{"<HEXCODE>":<13}<mnemonic>\n")
        for e, i in enumerate(instructions):
            if i.opcode == Opcode.HLT:
                file.write(f"{"":<3}{e:<11}{binary[e * 5 : e * 5 + 1].hex():<17}{i}\n")
                code_bytes += 1
                continue
            file.write(f"{"":<3}{e:<11}{binary[e * 5 : e * 5 + 5].hex():<17}{i}\n")
            code_bytes += 5
    print(f"source LoC: {code.count('\n') + 1} code instr: {len(instructions)} code bytes: {code_bytes}")


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    assert len(sys.argv) == 4, "Неверные аргументы: translator.py <input_file> <binary_file> <debug_file>"
    _, input_file, output_file, debug_file = sys.argv
    main(input_file, output_file, debug_file)
