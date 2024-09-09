import logging
import sys

from ..isa import INPUT_CELL, OUTPUT_CELL, AddrMode, Instruction, Opcode, binary2code


class DataPath:
    def __init__(self, memory: list, input_buffer: list):
        self.memory = memory + [0] * (2**11 - len(memory))
        self.memory_output = 0
        self.acc = 0
        self.addr_reg = 0
        self.alu = 0

        self.input_buffer = input_buffer
        self.output_buffer = []

        self.flag_z = True
        self.flag_n = False

    def signal_latch_acc(self, sel_input: bool):
        if sel_input:
            if len(self.input_buffer) == 0:
                raise EOFError
            logging.debug(f"input: \"{"".join(str(self.input_buffer))}\" >> {self.acc}")
            self.acc = self.input_buffer.pop(0)
        else:
            self.acc = self.alu

    def signal_latch_address(self, sel_instr: bool, instr_arg: int | None = None):
        if sel_instr:
            self.addr_reg = instr_arg
        else:
            self.addr_reg = self.alu
        assert 0 <= self.addr_reg <= 2**11, f"Адрес за пределами памяти: {self.addr_reg}"

    def alu_op(self, sel_instr: bool, second_operand: int | None = None, opcode: Opcode | None = None):
        alu_out = self.acc
        if not sel_instr:
            second_operand = self.memory_output

        if opcode is Opcode.LD:
            alu_out = second_operand
        if opcode is Opcode.ST:
            alu_out = second_operand

        if opcode is Opcode.ADD:
            alu_out += second_operand
        if opcode is Opcode.SUB:
            alu_out -= second_operand
        if opcode is Opcode.CMP:
            alu_out -= second_operand
            self.flag_z = alu_out == 0
            self.flag_n = alu_out < 0
        if opcode is Opcode.MUL:
            alu_out *= second_operand
        if opcode is Opcode.DIV:
            alu_out //= second_operand
        if opcode is Opcode.MOD:
            alu_out %= second_operand

        self.alu = alu_out

    def signal_read(self):
        self.memory_output = self.memory[self.addr_reg]

    def signal_write(self):
        if self.addr_reg == OUTPUT_CELL:
            logging.debug(f"output: \"{"".join(str(self.output_buffer))}\" << {self.alu}")
            self.output_buffer.append(self.alu)
        else:
            self.memory[self.addr_reg] = self.alu


class ControlUnit:
    def __init__(self, data_path: DataPath):
        self.data_path = data_path

        self.program_counter = 0
        self._tick = 0

    def tick(self):
        self._tick += 1

    def current_tick(self) -> int:
        return self._tick

    def latch_program_counter(self, sel_next: bool, instr_arg: int | None = None):
        if sel_next:
            self.program_counter += 1
        # для переходов JMP и т.д
        else:
            self.program_counter = instr_arg

    def decode_and_execute_control_flow_instruction(self, instr: Instruction) -> bool:
        if instr.opcode is Opcode.HLT:
            raise StopIteration

        if instr.opcode not in {Opcode.JMP, Opcode.BEQ, Opcode.BNE, Opcode.BGE, Opcode.BG}:
            return False

        sel_next = True

        if instr.opcode is Opcode.JMP:
            sel_next = False
        if instr.opcode is Opcode.BEQ:
            sel_next = not self.data_path.flag_z
        if instr.opcode is Opcode.BNE:
            sel_next = self.data_path.flag_z
        if instr.opcode is Opcode.BGE:
            sel_next = not self.data_path.flag_n
        if instr.opcode is Opcode.BG:
            sel_next = self.data_path.flag_n

        self.latch_program_counter(sel_next=sel_next, instr_arg=instr.arg)
        self.tick()
        return True

    def execute_ld(self, instr: Instruction):
        if instr.arg == INPUT_CELL:
            self.data_path.signal_latch_acc(sel_input=True)
            return
        if instr.addr_mode is AddrMode.DIRECT:
            self.data_path.signal_latch_address(sel_instr=True, instr_arg=instr.arg)  # установить в рег.адреса аргумент
            self.data_path.signal_read()  # подать значение по адресу на выход памяти
            self.data_path.alu_op(sel_instr=False, opcode=instr.opcode)  # получить значение на выход alu
            self.tick()
        elif instr.addr_mode is AddrMode.INDIRECT:
            self.data_path.signal_latch_address(sel_instr=True, instr_arg=instr.arg)
            self.data_path.signal_read()
            self.data_path.alu_op(sel_instr=False, opcode=instr.opcode)
            self.tick()
            self.data_path.signal_latch_address(sel_instr=False)
            self.data_path.signal_read()
            self.tick()
            self.data_path.alu_op(sel_instr=False, opcode=instr.opcode)
            self.data_path.signal_latch_acc(sel_input=False)
        elif instr.addr_mode is AddrMode.IMMEDIATE:
            self.data_path.alu_op(sel_instr=True, second_operand=instr.arg, opcode=instr.opcode)

        self.data_path.signal_latch_acc(sel_input=False)

    def execute_st(self, instr: Instruction):
        if instr.addr_mode is AddrMode.DIRECT:
            self.data_path.signal_latch_address(sel_instr=True, instr_arg=instr.arg)
            self.data_path.alu_op(sel_instr=False)
            self.data_path.signal_write()
            self.tick()
        elif instr.addr_mode is AddrMode.INDIRECT:
            self.data_path.signal_latch_address(sel_instr=True, instr_arg=instr.arg)
            self.data_path.signal_read()
            self.tick()
            self.data_path.alu_op(sel_instr=False, opcode=instr.opcode)
            self.data_path.signal_latch_address(sel_instr=False)
            self.tick()
            self.data_path.alu_op(sel_instr=False)
            self.data_path.signal_write()
            self.tick()

    def execute_math(self, instr: Instruction):
        if instr.addr_mode is AddrMode.DIRECT:
            self.data_path.signal_latch_address(sel_instr=True, instr_arg=instr.arg)
            self.data_path.signal_read()
            self.data_path.alu_op(sel_instr=False, opcode=instr.opcode)
            self.tick()
        elif instr.addr_mode is AddrMode.IMMEDIATE:
            self.data_path.alu_op(sel_instr=True, second_operand=instr.arg, opcode=instr.opcode)
        if instr.opcode is not Opcode.CMP:  # не защелкиваем в acc результат, если выставляли флаги
            self.data_path.signal_latch_acc(sel_input=False)

    def decode_and_execute_instruction(self):
        instr = self.data_path.memory[self.program_counter]

        if self.decode_and_execute_control_flow_instruction(instr):
            return

        if instr.opcode is Opcode.LD:
            self.execute_ld(instr=instr)
        elif instr.opcode is Opcode.ST:
            self.execute_st(instr=instr)
        elif instr.opcode in {Opcode.ADD, Opcode.SUB, Opcode.MUL, Opcode.DIV, Opcode.MOD, Opcode.CMP}:
            self.execute_math(instr=instr)

        self.tick()
        self.latch_program_counter(sel_next=True)

    def __repr__(self):
        return (
            f"TICK: {self._tick:<7}"
            f"PC: {self.program_counter:<7}"
            f"ADDR: {self.data_path.addr_reg:<7}"
            f"MEM_OUT: {self.data_path.memory_output:<7}"
            f"ALU: {self.data_path.alu:<7}"
            f"ACC: {self.data_path.acc:<7}"
            f"{self.data_path.memory[self.program_counter]}"
        )


def simulation(memory: list[Instruction], input_buffer: list, limit: int) -> tuple[str, int, int]:
    data_path = DataPath(memory, input_buffer)
    control_unit = ControlUnit(data_path)
    program_counter = 0

    logging.debug(control_unit)
    try:
        while True:
            assert program_counter < limit, "Слишком много исполнено инструкций"
            control_unit.decode_and_execute_instruction()
            program_counter += 1
            logging.debug(control_unit)
    except EOFError:
        logging.warning(" Входной буфер пустой!")
    except StopIteration:
        pass

    return data_path.output_buffer, program_counter, control_unit.current_tick()


def main(input_file: str, binary_file: str):
    with open(input_file, encoding="utf-8") as file:
        input_text = file.read()
        input_buffer = [char for char in input_text]
        input_buffer = input_buffer[:-1]
        input_buffer.append(chr(0))
        input_buffer = [ord(token) for token in input_buffer]

    memory = binary2code(binary_file)

    output, program_counter, ticks = simulation(memory, input_buffer, 100000)

    # эмуляция ВУ
    if len(output) != 1:
        output = [chr(char) for char in output]
        print(f"output: {"".join(output)}")
    else:
        print(f"output: {output[0]}")
    print("program_counter: ", program_counter)
    print("ticks: ", ticks)


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    assert len(sys.argv) == 3, "Неверные аргументы: machine.py <input_file> <binary_file>"
    _, binary_file, input_file = sys.argv
    main(input_file, binary_file)
