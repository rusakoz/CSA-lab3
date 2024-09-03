import struct
from ..isa import AddrMode, Instruction, Opcode

def machine_to_binary(machine_code: list) -> bytes:
    binary = b''
    for code in machine_code:
        if isinstance(code, Instruction):
            # print("tut")
            if code.opcode.name == "HLT":
                binary += struct.pack(">B", (code.opcode.value << 2))
                continue
            binary += struct.pack(">Bi", (code.opcode.value << 2 | code.addr_mode.value), code.arg)
            continue
        binary += struct.pack(">i", code)
    # print(binary)
    return binary

if __name__ == '__main__':
    machine_to_binary([Instruction(Opcode(2), AddrMode(1), 0), Instruction(Opcode(13), 2, None), 2100000000])