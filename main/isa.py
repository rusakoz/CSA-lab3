import struct
from enum import Enum
from typing import NamedTuple

INPUT_CELL = 2**11 - 2
OUTPUT_CELL = 2**11 - 1


class Opcode(Enum):
    LD: int = 0
    ST: int = 1
    ADD: int = 2
    SUB: int = 3
    DIV: int = 4
    MUL: int = 5
    MOD: int = 6
    CMP: int = 7
    JMP: int = 8
    BEQ: int = 9
    BNE: int = 10
    BGE: int = 11
    BG: int = 12
    HLT: int = 13


class AddrMode(Enum):
    DIRECT: int = 0
    INDIRECT: int = 1
    IMMEDIATE: int = 2


class Instruction(NamedTuple):
    opcode: Opcode
    addr_mode: AddrMode
    arg: int

    def __repr__(self):
        if self.opcode == Opcode.HLT:
            return self.opcode.name
        if (
            self.opcode == Opcode.JMP
            or self.opcode == Opcode.BEQ
            or self.opcode == Opcode.BNE
            or self.opcode == Opcode.BGE
            or self.opcode == Opcode.BG
        ):
            return f"{self.opcode.name} {self.arg}"
        return f"{self.opcode.name} {['', '~', '#'][self.addr_mode.value]}{self.arg}"


def binary2code(filename) -> list:
    machine_code = []
    with open(filename, "rb") as file:
        while bin_code_instr := file.read(1):
            assert len(bin_code_instr) == 1, "Бинарный файл невалиден"

            op_and_mode = struct.unpack(">B", bin_code_instr)

            op = op_and_mode[0] >> 2

            if op == Opcode.HLT.value:
                machine_code.append(Instruction(Opcode(op), None, None))
                break
            mode = op_and_mode[0] & 0b11
            arg = file.read(4)
            assert len(arg) == 4, "Бинарный файл невалиден"

            if AddrMode(mode) == AddrMode.DIRECT:
                arg = struct.unpack(">I", arg)
            else:
                arg = struct.unpack(">i", arg)
            machine_code.append(Instruction(Opcode(op), AddrMode(mode), arg[0]))

    return machine_code
