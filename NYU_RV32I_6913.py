import os
import argparse

# memory size, in reality, the memory size should be 2^32, but for this lab, for the space reason,
# we keep it as this large number, but the memory is still 32-bit addressable.
MemSize = 1000


class InsMem(object):
    def __init__(self, name, ioDir):
        self.id = name

        with open(ioDir + "\\imem.txt") as im:
            self.IMem = [data.replace("\n", "") for data in im.readlines()]

    def readInstr(self, ReadAddress):
        # read instruction memory
        # return 32 bit hex val
        Instruction = 0
        for i in range(0, 4):  # 4 lines for an instruction
            Instruction <<= 8  # left shift
            Instruction = Instruction + int(self.IMem[ReadAddress + i], 2)
        return Instruction


class DataMem(object):
    def __init__(self, name, ioDir):
        self.id = name
        self.ioDir = ioDir
        with open(ioDir + "\\dmem.txt") as dm:
            self.DMem = [data.replace("\n", "") for data in dm.readlines()]

    def readInstr(self, ReadAddress):
        # read data memory
        # return 32 bit hex val
        Instruction = 0
        for i in range(0, 4):  # 4 lines for an instruction
            Instruction <<= 8  # left shift
            Instruction = Instruction + int(self.DMem[ReadAddress + i], 2)
        return Instruction

    def writeDataMem(self, Address, WriteData):
        # write data into byte addressable memory
        WriteData = str(bin(WriteData))[2:]
        WriteData = WriteData.zfill(32)
        for i in range(0, 4):  # 4 lines for an instruction
            self.DMem[Address + i] = WriteData[0 + 8 * i: 8 + 8 * i]  # WriteData is Str

    def outputDataMem(self):
        resPath = self.ioDir + "\\" + self.id + "_DMEMResult.txt"
        with open(resPath, "w") as rp:
            rp.writelines([str(data) + "\n" for data in self.DMem])


class RegisterFile(object):
    def __init__(self, ioDir):
        self.outputFile = ioDir + "RFResult.txt"
        self.Registers = [0x0 for i in range(32)]

    def readRF(self, Reg_addr):
        # Fill in
        Reg_data = self.Registers[Reg_addr]
        return Reg_data

    def writeRF(self, Reg_addr, Wrt_reg_data):
        # Fill in
        Reg_addr = int(Reg_addr, 2)
        self.Registers[Reg_addr] = Wrt_reg_data

    def outputRF(self, cycle):
        op = ["-"*70+"\n", "State of RF after executing cycle:" + str(cycle) + "\n"]
        # TODO: changed "str(val)" to "[str(bin(val))[2:].zfill(32)"
        op.extend([str(bin(val))[2:].zfill(32)+"\n" for val in self.Registers])
        if (cycle == 0): perm = "w"
        else: perm = "a"
        with open(self.outputFile, perm) as file:
            file.writelines(op)


class State(object):
    def __init__(self):
        self.IF = {"nop": False, "PC": 0}
        self.ID = {"nop": False, "Instr": 0}
        self.EX = {"nop": False, "Read_data1": 0, "Read_data2": 0, "Imm": 0, "Rs": 0, "Rt": 0, "Wrt_reg_addr": 0, "is_I_type": False, "rd_mem": 0,
                   "wrt_mem": 0, "alu_op": 0, "wrt_enable": 0}
        self.MEM = {"nop": False, "ALUresult": 0, "Store_data": 0, "Rs": 0, "Rt": 0, "Wrt_reg_addr": 0, "rd_mem": 0,
                   "wrt_mem": 0, "wrt_enable": 0}
        self.WB = {"nop": False, "Wrt_data": 0, "Rs": 0, "Rt": 0, "Wrt_reg_addr": 0, "wrt_enable": 0}


class Core(object):
    def __init__(self, ioDir, imem, dmem):
        self.myRF = RegisterFile(ioDir)
        self.cycle = 0
        self.halted = False
        self.ioDir = ioDir
        self.state = State()
        self.nextState = State()
        self.ext_imem = imem
        self.ext_dmem = dmem


def ALUOperation(ALUop, oprand1, oprand2):
    oprand1 = int(oprand1, 2)
    oprand2 = int(oprand2, 2)
    print("oprand1: " + str(bin(oprand1))[2:].zfill(32))
    print("oprand2: " + str(bin(oprand2))[2:].zfill(32))
    result = 0
    if ALUop == 0:
        return result
    if ALUop == 1:
        result = oprand1 + oprand2
    if ALUop == 2:
        result = oprand1 - oprand2
    if ALUop == 3:
        result = oprand1 ^ oprand2
    if ALUop == 4:
        result = oprand1 or oprand2
    if ALUop == 5:
        result = oprand1 and oprand2
    return result


def signProcess(imm):
    if imm[0] == "0":
        str = "00000000000000000000" + imm
    else:
        str = "11111111111111111111" + imm
    return str


class SingleStageCore(Core):
    def __init__(self, ioDir, imem, dmem):
        super(SingleStageCore, self).__init__(ioDir + "\\SS_", imem, dmem)
        self.opFilePath = ioDir + "\\StateResult_SS.txt"

    def step(self):
        # Your implementation
        if self.state.IF["nop"]:
            self.halted = True

        print("PC: " + str(self.state.IF["PC"]))
        Instruction = imem.readInstr(self.state.IF["PC"])

        # halted if instruction is 0xffffffff
        if Instruction == 0xffffffff:
            print("meet 0xffffffff")
            self.nextState.IF["nop"] = True
        else:
            self.nextState.IF["nop"] = False

            self.nextState.IF["PC"] = self.state.IF["PC"] + 4

            instr = str(bin(Instruction))[2:]
            instr = instr.zfill(32)
            print("instr:   " + instr)
            opcode = instr[25:]

            RType = (opcode == "0110011")
            IType = (opcode == "0010011" or opcode == "0000011")
            JType = (opcode == "1101111")
            BType = (opcode == "1100011")
            SType = (opcode == "0100011")

            isBranch = (opcode == "1100011")
            isLoad = (opcode == "0000011")
            isStore = (opcode == "0100011")
            wrtEnable = not (isStore or isBranch or JType)

            funct7 = instr[:7]
            imm = instr[:12]
            if SType or BType:
                imm = imm[:7] + instr[20:25]
            if JType:
                imm = imm + instr[7:20]
            rs2 = instr[7:12]
            rs1 = instr[12:17]
            funct3 = instr[17:20]
            rd = instr[20:25]
            ALUop = 0

            print("rs1: " + rs1 + " -> " + str(int(rs1, 2)))
            print("rs2: " + rs2 + " -> " + str(int(rs2, 2)))

            readData1 = self.myRF.readRF(int(rs1, 2))
            readData2 = self.myRF.readRF(int(rs2, 2))

            # EX
            ALUin1 = str(bin(readData1))[2:]
            if IType or SType:
                ALUin2 = signProcess(imm)
            else:
                ALUin2 = str(bin(readData2))[2:]

            if RType:
                if funct7 == "0100000": ALUop = 2
                else:
                    if funct3 == "000": ALUop = 1
                    if funct3 == "100": ALUop = 3
                    if funct3 == "110": ALUop = 4
                    if funct3 == "111": ALUop = 5
            if IType:
                if opcode == "0010011":
                    if funct3 == "000": ALUop = 1
                    if funct3 == "100": ALUop = 3
                    if funct3 == "110": ALUop = 4
                    if funct3 == "111": ALUop = 5
                if opcode == "0000011": ALUop = 1
            if SType:
                ALUop = 1

            ALUout = ALUOperation(ALUop, ALUin1, ALUin2)
            print("ALUout:  " + str(bin(ALUout))[2:].zfill(32))

            # MEM
            DMAddr = ALUout
            wrtData = readData2
            readMem = isLoad
            writeMem = isStore

            readData = 0

            print("IsLoad: " + str(isLoad))
            print("IsStore: " + str(isStore))
            if readMem:
                readData = dmem_ss.readInstr(DMAddr)
            elif writeMem:
                dmem_ss.writeDataMem(DMAddr, wrtData)

            # WB
            if isLoad:
                regData = readData
            else:
                regData = ALUout

            if wrtEnable:
                self.myRF.writeRF(rd, regData)

            print("----------------------------------------")

        self.myRF.outputRF(self.cycle)  # dump RF
        self.printState(self.nextState, self.cycle)  # print states after executing cycle 0, cycle 1, cycle 2 ...

        self.state = self.nextState  # The end of the cycle and updates the current state with the values calculated in this cycle
        self.cycle += 1

    def printState(self, state, cycle):
        printstate = ["-"*70+"\n", "State after executing cycle: " + str(cycle) + "\n"]
        printstate.append("IF.PC: " + str(state.IF["PC"]) + "\n")
        printstate.append("IF.nop: " + str(state.IF["nop"]) + "\n")

        if cycle == 0: perm = "w"
        else: perm = "a"
        with open(self.opFilePath, perm) as wf:
            wf.writelines(printstate)


class FiveStageCore(Core):
    def __init__(self, ioDir, imem, dmem):
        super(FiveStageCore, self).__init__(ioDir + "\\FS_", imem, dmem)
        self.opFilePath = ioDir + "\\StateResult_FS.txt"

    def step(self):
        # Your implementation
        # --------------------- WB stage ---------------------
        if not self.state.WB["nop"]:
            if self.state.WB["wrt_enable"]:
                self.myRF.writeRF(self.state.WB["Wrt_reg_addr"], self.state.WB["Wrt_data"])
        self.state.WB["nop"] = self.state.MEM["nop"]

        # --------------------- MEM stage --------------------



        # --------------------- EX stage ---------------------



        # --------------------- ID stage ---------------------



        # --------------------- IF stage ---------------------
        # IF
        if not self.state.IF["nop"]:
            Instruction = imem.readInstr(self.state.IF["PC"])
            # halted if instruction is 0xffffffff
            if Instruction == 0xffffffff:
                self.halted = True
            else:
                self.halted = False
                self.nextState.ID["Instr"] = Instruction
                self.nextState.IF["PC"] = self.state.IF["PC"] + 4

        # if self.state.IF["nop"]:
        #     self.halted = True

        # ID
        if not self.state.ID["nop"]:
            instr = str(bin(self.state.ID["Instr"]))[2:]
            opcode = instr[25:]

            funct7 = ""
            rs2 = ""
            rs1 = ""
            funct3 = ""
            rd = ""
            imm = ""

            RType = (opcode == "0110011")
            IType = (opcode == "0010011" or opcode == "0000011")
            JType = (opcode == "1101111")
            BType = (opcode == "1100011")
            SType = (opcode == "0100011")

            if RType:
                funct7 = instr[:7]
                rs2 = instr[7:12]
                rs1 = instr[12:17]
                funct3 = instr[17:20]
                rd = instr[20:25]

            if IType:
                imm = instr[:12]
                rs1 = instr[12:17]
                funct3 = instr[17:20]
                rd = instr[20:25]

            if JType:
                imm = instr[:20]
                rd = instr[20:25]

            if BType or SType:
                imm = instr[:7] + instr[20:25]
                rs2 = instr[7:12]
                rs1 = instr[12:17]
                funct3 = instr[17:20]

            self.nextState.EX["Read_data1"] = 0
            self.nextState.EX["Read_data2"] = 0
            self.nextState.EX["Imm"] = int(imm, 2)
            self.nextState.EX["Rs"] = int(rs1, 2)
            self.nextState.EX["Rt"] = int(rs2, 2)
            self.nextState.EX["Wrt_reg_addr"] = 0
            self.nextState.EX["is_I_type"] = False
            self.nextState.EX["rd_mem"] = 0
            self.nextState.EX["wrt_mem"] = 0
            self.nextState.EX["alu_op"] = 0
            self.nextState.EX["wrt_enable"] = 0

            res = 0
            rnull = 0
            if RType:
                if funct7 == "0100000":
                    ALUop = 0
                    res = ALUOperation(ALUop, rs1, rs2)
                else:
                    if funct3 == "000":
                        ALUop = 1
                        res = ALUOperation(ALUop, rs1, rs2)
                    if funct3 == "100":
                        ALUop = 2
                        res = ALUOperation(ALUop, rs1, rs2)
                    if funct3 == "110":
                        ALUop = 3
                        res = ALUOperation(ALUop, rs1, rs2)
                    if funct3 == "111":
                        ALUop = 4
                        res = ALUOperation(ALUop, rs1, rs2)
            if IType:
                if opcode == "0000011":
                    ALUop = 9
                    res = ALUOperation(ALUop, rs1, rs2)
                else:
                    if funct3 == "000":
                        ALUop = 5
                        res = ALUOperation(ALUop, rs1, imm)
                    if funct3 == "100":
                        ALUop = 6
                        res = ALUOperation(ALUop, rs1, imm)
                    if funct3 == "110":
                        ALUop = 7
                        res = ALUOperation(ALUop, rs1, imm)
                    if funct3 == "111":
                        ALUop = 8
                        res = ALUOperation(ALUop, rs1, imm)
            # under determined
            # if JType:
            #     ALUop = 9
            #     res = ALUOperation(ALUop, rnull, imm)
            #
            # if BType or SType:
            #     if funct3 == "000":
            #         ALUop = 10
            #         res = ALUOperation(ALUop, rs1, imm)
            #     if funct3 == "001":
            #         ALUop = 11
            #         res = ALUOperation(ALUop, rs1, imm)
            #     if funct3 == "010":
            #         ALUop = 12
            #         res = ALUOperation(ALUop, rs1, imm)




        self.halted = True
        if self.state.IF["nop"] and self.state.ID["nop"] and self.state.EX["nop"] and self.state.MEM["nop"] and self.state.WB["nop"]:
            self.halted = True

        self.myRF.outputRF(self.cycle)  # dump RF
        self.printState(self.nextState, self.cycle)  # print states after executing cycle 0, cycle 1, cycle 2 ...

        self.state = self.nextState  # The end of the cycle and updates the current state with the values calculated in this cycle
        self.cycle += 1

    def printState(self, state, cycle):
        printstate = ["-"*70+"\n", "State after executing cycle: " + str(cycle) + "\n"]
        printstate.extend(["IF." + key + ": " + str(val) + "\n" for key, val in state.IF.items()])
        printstate.extend(["ID." + key + ": " + str(val) + "\n" for key, val in state.ID.items()])
        printstate.extend(["EX." + key + ": " + str(val) + "\n" for key, val in state.EX.items()])
        printstate.extend(["MEM." + key + ": " + str(val) + "\n" for key, val in state.MEM.items()])
        printstate.extend(["WB." + key + ": " + str(val) + "\n" for key, val in state.WB.items()])

        if (cycle == 0): perm = "w"
        else: perm = "a"
        with open(self.opFilePath, perm) as wf:
            wf.writelines(printstate)


if __name__ == "__main__":
    # parse arguments for input file location
    parser = argparse.ArgumentParser(description='RV32I processor')
    parser.add_argument('--iodir', default="", type=str, help='Directory containing the input files.')
    args = parser.parse_args()

    ioDir = os.path.abspath(args.iodir)
    print("IO Directory:", ioDir)

    imem = InsMem("Imem", ioDir)
    dmem_ss = DataMem("SS", ioDir)
    dmem_fs = DataMem("FS", ioDir)

    # TODO: changed memory size to 1000
    while len(dmem_ss.DMem) < 1000:
        dmem_ss.DMem.append("00000000")

    ssCore = SingleStageCore(ioDir, imem, dmem_ss)
    fsCore = FiveStageCore(ioDir, imem, dmem_fs)

    while(True):
        if not ssCore.halted:
            ssCore.step()
        # if not fsCore.halted:
        #     print(fsCore.halted)
        #     fsCore.step()
        # if ssCore.halted and fsCore.halted:
        #     break

        if ssCore.halted:
            break

    # dump SS and FS data mem.
    dmem_ss.outputDataMem()
    # dmem_fs.outputDataMem()
