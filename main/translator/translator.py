import logging
import re
import struct
import sys
import uuid
from typing import NamedTuple

import pytest

from ..isa import INPUT_CELL, OUTPUT_CELL, AddrMode, Instruction, Opcode

STR_MAX_LENGTH = 24

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


def get_main(string: str) -> str:
    return string.split("//", 1)[0].strip()


def del_tab(string: str) -> str:
    return " ".join([k for k in string.split(" ") if k])


class Addr(NamedTuple):
    addr: int
    reused: bool


class WhileStatement(NamedTuple):
    typ: str
    start: int
    end: int


class IfStatement(NamedTuple):
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

def translate_type_int(count_var: int, type_int: str, var_name_addr: dict, instructions: list[Instruction]) -> int:
    count_var += 1
    without_tab = del_tab(type_int)
    split_str = without_tab.split(" ")

    var_name_addr[split_str[1]] = Addr(count_var, False)
    instructions.append(Instruction(Opcode.LD, AddrMode.IMMEDIATE, int(split_str[3])))
    instructions.append(Instruction(Opcode.ST, AddrMode.DIRECT, count_var))
    return count_var

def translate_type_str(count_var: int, type_str: str, var_name_addr: dict, instructions: list[Instruction], str_name_length: dict) -> int:
    count_var += 1
    without_tab = del_tab(type_str)
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
    return count_var

def translate_math_op(count_var: int, math_op: str, var_name_addr: dict, instructions: list[Instruction]) -> int:
    without_tab = del_tab(math_op)
    split_str = without_tab.split(" ")

    addr_to_unlock = []

    count_var, first_addr, foo = get_addr_var(instructions, var_name_addr, addr_to_unlock, split_str[2], count_var)

    count_var, second_addr, foo = get_addr_var(instructions, var_name_addr, addr_to_unlock, split_str[4], count_var)

    instructions.append(Instruction(Opcode.LD, AddrMode.DIRECT, first_addr))
    instructions.append(Instruction(symbol2opcode(split_str[3]), AddrMode.DIRECT, second_addr))
    instructions.append(Instruction(Opcode.ST, AddrMode.DIRECT, first_addr))

    for name in addr_to_unlock:
        var_name_addr[name] = Addr(var_name_addr[name].addr, True)
    return count_var

def translate_if_statement(count_var: int, if_statement: str, var_name_addr: dict, instructions: list[Instruction], list_of_while_if: list) -> int:
    without_tab = del_tab(if_statement)
    split_str = without_tab.split(" ")

    to_unlock = []

    count_var, addr1, none = get_addr_var(instructions, var_name_addr, to_unlock, split_str[1][1:], count_var)
    count_var, addr2, none = get_addr_var(instructions, var_name_addr, to_unlock, split_str[3], count_var)
    count_var, addr3, none = get_addr_var(instructions, var_name_addr, to_unlock, split_str[5], count_var)

    instructions.append(Instruction(Opcode.LD, AddrMode.DIRECT, addr1))
    instructions.append(Instruction(symbol2opcode(split_str[2]), AddrMode.DIRECT, addr2))
    instructions.append(Instruction(Opcode.CMP, AddrMode.DIRECT, addr3))
    instructions.append(Instruction(Opcode.BEQ, AddrMode.DIRECT, 7777777))
    beq_pos = len(instructions) - 1

    count_var, addr4, none = get_addr_var(instructions, var_name_addr, to_unlock, split_str[7], count_var)
    count_var, addr5, none = get_addr_var(instructions, var_name_addr, to_unlock, split_str[9], count_var)
    count_var, addr6, none = get_addr_var(instructions, var_name_addr, to_unlock, split_str[11][:-1], count_var)

    instructions.append(Instruction(Opcode.LD, AddrMode.DIRECT, addr4))
    instructions.append(Instruction(symbol2opcode(split_str[8]), AddrMode.DIRECT, addr5))
    instructions.append(Instruction(Opcode.CMP, AddrMode.DIRECT, addr6))
    instructions.append(Instruction(Opcode.BNE, AddrMode.DIRECT, 7777777))
    end = len(instructions) - 1

    instructions[beq_pos] = Instruction(instructions[beq_pos].opcode, instructions[beq_pos].addr_mode, end + 1)

    list_of_while_if.append(IfStatement("if", end))
    return count_var

def translate_while_statement(count_var: int, while_statement: str, var_name_addr: dict, instructions: list[Instruction], list_of_while_if: list) -> int:
    without_tab = del_tab(while_statement)
    split_str = without_tab.split(" ")

    start = 0
    to_unlock = []

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

    instructions.append(Instruction(symbol2opcode(split_str[2]), AddrMode.DIRECT, 7777777))
    end = len(instructions) - 1

    list_of_while_if.append(WhileStatement("while", start, end))
    return count_var

def translate_input(count_var: int, _input: str, var_name_addr: dict, instructions: list[Instruction], move_addr: list) -> int:
    count_var += 1
    without_tab = del_tab(_input)
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
    return count_var

def translate_output(count_var: int, _output: str, var_name_addr: dict, str_name_length: dict, instructions: list[Instruction], move_addr: list) -> int:
    without_tab = del_tab(_output)
    split_str = without_tab.split(" ")

    str_length = None
    try:
        if len(str_name_length) != 0:
            str_length = str_name_length[split_str[1]]
    except KeyError:
        pass

    # вывод строки
    count_var += 1
    if str_length is not None:
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
    return count_var

def translate_end_block(counter_end_block: int, instructions: list[Instruction], list_of_while_if: list) -> int:
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
    return counter_end_block

def move_addr_data_before_instrs(instructions: list[Instruction], move_addr: list):
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


def code2instructions(text: str) -> list[Instruction]:
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
        _input = re.search(r"^<< *[_a-zA-Z]\w*", elem)
        _output = re.search(r"^>> *[_a-zA-Z]\w*", elem)

        if type_int:
            count_var = translate_type_int(
                count_var=count_var, type_int=type_int[0], var_name_addr=var_name_addr, instructions=instructions
            )
        elif type_str:
            count_var = translate_type_str(
                count_var=count_var, type_str=type_str[0], var_name_addr=var_name_addr, instructions=instructions, str_name_length=str_name_length
            )
        elif math_op:
            count_var = translate_math_op(
                count_var=count_var, math_op=math_op[0], var_name_addr=var_name_addr, instructions=instructions
            )
        elif if_statement:
            count_var = translate_if_statement(
                count_var=count_var, if_statement=if_statement[0], var_name_addr=var_name_addr, instructions=instructions,
                list_of_while_if=list_of_while_if
            )
        elif while_statement:
            count_var = translate_while_statement(
                count_var=count_var, while_statement=while_statement[0], var_name_addr=var_name_addr, instructions=instructions,
                list_of_while_if=list_of_while_if
            )
        elif _input:
            count_var = translate_input(
                count_var=count_var, _input=_input[0], var_name_addr=var_name_addr, instructions=instructions,
                move_addr=move_addr
            )
        elif _output:
            count_var = translate_output(
                count_var=count_var, _output=_output[0], var_name_addr=var_name_addr, str_name_length=str_name_length,
                instructions=instructions, move_addr=move_addr
            )
        elif end_block:
            counter_end_block = translate_end_block(
                counter_end_block=counter_end_block, instructions=instructions, list_of_while_if=list_of_while_if
            )
        else:
            pytest.fail("Невалидный синтаксис программы")

    instructions.append(Instruction(Opcode.HLT, None, None))

    # перенос адресаций данных в конец инструкций
    move_addr_data_before_instrs(instructions=instructions, move_addr=move_addr)

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
