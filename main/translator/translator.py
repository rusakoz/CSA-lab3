import struct
import re
from typing import NamedTuple
import uuid
from ..isa import AddrMode, Instruction, Opcode

def symbols():
    return {"+", "-", "*", "/", "%", ">", "<", ">=", "<=", "==", "!="}


def symbol2opcode(symbol) -> Opcode:
    return {
        "+": Opcode.ADD,
        "-": Opcode.SUB,
        "*": Opcode.MUL,
        "/": Opcode.DIV,
        "%": Opcode.MOD,
        ">": Opcode.CMP,
        "<": Opcode.CMP,
        ">=": Opcode.CMP,
        "<=": Opcode.CMP,
        "==": Opcode.CMP,
        "!=": Opcode.CMP
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
    In: int

def count_end_blocks(text: str) -> int:
    count = 0
    for elem in text.splitlines():
        elem = get_main(elem)
        if elem == "}": count += 1
    return count

def text2instructions(text: str) -> list[Instruction]:
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
        #  *\d* *([<>] | >= | <= | == | !=) *\d* *(\|\|) *[_a-zA-Z]\w* *(\+\-\/\%\*) *\d* *([<>] | >= | <= | == | !=) *\d* *\) *{
        type_int = re.search(r"^int *[_a-zA-Z]\w* *= *[-+]?[0-9]+", str(elem))
        type_str = re.search(r"^str *[_a-zA-Z]\w* *= *(['\"])(?:(?!(?:\\|\1)).|\\.)*\1", str(elem))
        math_op = re.search(r"^[_a-zA-Z]\w* *= *[_a-zA-Z]\w* *[\+\-\/\%\*] *([_a-zA-Z]\w*|\d*) *", str(elem))

        if_statement = re.search(r"^if *\( *[_a-zA-Z]\w* *[\+\-\/\%\*] *\d* *([<>]|>=|<=|==|!=) *\d* *(\|\|) *[_a-zA-Z]\w* *[\+\-\/\%\*] *\d* *([<>]|>=|<=|==|!=) *\d* *\) *{", str(elem))

        while_statement = re.search(r"while *\( *[_a-zA-Z]\w* *([<>]|>=|<=|==|!=) *\d* *\) *{", str(elem))
        end_block = re.search(r"^}", str(elem))
        input_ = re.search(r"^<< *[_a-zA-Z]\w*", str(elem))
        output_ = re.search(r"^>> *[_a-zA-Z]\w*", str(elem))
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
            without_tab = del_tab(type_str[0])
            split_str = without_tab.split(" ", 3)
            # print(split_str)
            ascii_code = list(split_str[3][1:-1].encode('cp1251'))
            start_pos = count_var
            var_name_addr[split_str[1]] = Addr(start_pos, False)
            for code in ascii_code:
                count_var += 1
                instructions.append(Instruction(Opcode.LD, AddrMode.IMMEDIATE, code))
                instructions.append(Instruction(Opcode.ST, AddrMode.DIRECT, count_var))
            str_length = count_var - start_pos
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

            if split_str[2].isdigit():
                count_var += 1
                name_reused_mem = str(uuid.uuid4().hex)
                reused_mem = count_var
                for i in var_name_addr.items():
                    # print(i)
                    # print(i[1].reused)
                    if i[1].reused:
                        count_var -= 1
                        reused_mem = i[1].addr
                        name_reused_mem = i[0]
                        break
                to_unlock.append(name_reused_mem)
                var_name_addr[name_reused_mem] = Addr(reused_mem, False)
                # print("HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH")
                # print(split_str[2])
                instructions.append(Instruction(Opcode.LD, AddrMode.IMMEDIATE, split_str[2]))
                instructions.append(Instruction(Opcode.ST, AddrMode.DIRECT, reused_mem))
                first_addr = reused_mem
            else:
                first_addr = var_name_addr[split_str[2]].addr

            if split_str[4].isdigit():
                count_var += 1
                name_reused_mem = str(uuid.uuid4().hex)
                reused_mem = count_var
                for i in var_name_addr.items():
                    # print(i)
                    # print(i[1].reused)
                    if i[1].reused:
                        count_var -= 1
                        reused_mem = i[1].addr
                        name_reused_mem = i[0]
                        break
                # print("OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO")
                # print(split_str[4])
                to_unlock.append(name_reused_mem)
                var_name_addr[name_reused_mem] = Addr(reused_mem, False)
                instructions.append(Instruction(Opcode.LD, AddrMode.IMMEDIATE, split_str[4]))
                instructions.append(Instruction(Opcode.ST, AddrMode.DIRECT, reused_mem))
                second_addr = reused_mem
            else:
                # print(second_addr)
                second_addr = var_name_addr[split_str[4]].addr
            # print("JJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJsf")
            # print(first_addr)
            # print(second_addr)
            instructions.append(Instruction(Opcode.LD, AddrMode.DIRECT, first_addr))
            instructions.append(Instruction(symbol2opcode(split_str[3]), AddrMode.DIRECT, second_addr))

            for name in to_unlock:
                var_name_addr[name] = Addr(var_name_addr[name].addr, True)
            to_unlock.clear()
            
            # print(f"переменная: {split_str[0]} в памяти тут: {var_name_addr[split_str[0]]}")
            # print("end=====math_op=====")
        elif if_statement:
            # print("start=====if_statement=====")
            without_tab = del_tab(if_statement[0])
            split_str = without_tab.split(" ")
            start = 0
            In = 0
            print(if_statement[0])

            list_of_while_if.append(While_statement("if", start, In))
            # count_var += 1
        elif while_statement:
            print("start=====while_statement=====")
            without_tab = del_tab(while_statement[0])
            split_str = without_tab.split(" ")
            print(split_str)

            first_addr = 0
            second_addr = 0
            to_unlock = []
            start = 0
            end = 0
            if split_str[1][1:].isdigit():
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
                instructions.append(Instruction(Opcode.LD, AddrMode.IMMEDIATE, split_str[1][1:]))
                start = len(instructions) - 1
                instructions.append(Instruction(Opcode.ST, AddrMode.DIRECT, reused_mem))
                first_addr = reused_mem
            else:
                first_addr = var_name_addr[split_str[1][1:]].addr
            
            if split_str[3][:-1].isdigit():
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
                instructions.append(Instruction(Opcode.LD, AddrMode.IMMEDIATE, split_str[3][:-1]))
                if start == 0: start = len(instructions) - 1
                instructions.append(Instruction(Opcode.ST, AddrMode.DIRECT, reused_mem))
                second_addr = reused_mem
            else:
                second_addr = var_name_addr[split_str[3][:-1]].addr

            instructions.append(Instruction(Opcode.LD, AddrMode.DIRECT, first_addr))

            if start == 0: start = len(instructions) - 1
            instructions.append(Instruction(symbol2opcode(split_str[2]), AddrMode.DIRECT, second_addr))

            for name in to_unlock:
                var_name_addr[name] = Addr(var_name_addr[name].addr, True)
            to_unlock.clear()

            instructions.append(Instruction(Opcode.BGE, AddrMode.DIRECT, 7777777))
            end = len(instructions) - 1

            list_of_while_if.append(While_statement("while", start, end))

            # count_var += 1
            print("end=====while_statement=====")
        elif input_:
            continue
            # print("start=====input=====")
        elif output_:
            # print("start=====output=====")
            continue
        elif end_block:
            # print("start======end_block=====")
            counter_end_block += 1
            pos = len(list_of_while_if) - counter_end_block
            obj_by_pos = list_of_while_if[pos]
            print(obj_by_pos)
            if obj_by_pos.typ == "while":
                last_pos_inst = len(instructions) + 1
                instructions[obj_by_pos.end] = Instruction(instructions[obj_by_pos.end].opcode, instructions[obj_by_pos.end].addr_mode, last_pos_inst)
                instructions.append(Instruction(Opcode.JMP, AddrMode.DIRECT, obj_by_pos.start))
            if obj_by_pos == "if":
                last_pos_inst = len(instructions) - 1
                instructions[obj_by_pos.end] = Instruction(instructions[obj_by_pos.end].opcode, instructions[obj_by_pos.end].addr_mode, last_pos_inst)
            # print("end======end_block=====")
        else:
            assert False, "Невалидный синтаксис программы"
        # print(type_int)
        # assert if_statement, "Невалидный синтаксис программы" + str(if_statement)
        # print(if_statement)
        # print(while_statement)
    print(var_name_addr)
    print(str_name_length)
    print(instructions)
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
    # machine2binary([Instruction(Opcode(2), AddrMode(1), 0), Instruction(Opcode(13), 2, None), 2100000000])
    # print(get_main("   if(x < 1){x = x + 1} // fsdafgusgdfog gdfgjjdf ghkfgj fg jgfd gdfjgj djg d //"))
    sstr =  "int  sum  =  321\n"+"int x = 143\n"+"while (x < 1000) {\n"+"    if (x % 3 == 0 || x % 5 == 0) {\n"+"        sum = sum + x\n"+"    }\n"+"    x = x + 1\n"+"}\n"+">> sum"

    # print("if (x < 1) {\n    x = x + 1\n}")
    text2instructions(sstr)