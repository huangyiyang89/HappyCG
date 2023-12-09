import pymem
import time


class Pymem(pymem.Pymem):
    # 重写支持big编码
    def read_string(handle, address, byte=50):
        buff = pymem.Pymem.read_bytes(handle, address, byte)
        i = buff.find(b'\x00')
        if i != -1:
            buff = buff[:i]
        buff = buff.decode('big5')
        return buff


class Hcg:

    opened_cg_processIDs = []

    def __init__(self, processID):
        self.mem = Pymem(processID)
        self.stop = False
        self.player_battle_order = 'H|A\0'
        self.pet_battle_order = 'W|0|E\0'
        Hcg.opened_cg_processIDs.append(processID)

    def get_all_processID(process_name=b'bluecg.exe'):
        list = pymem.process.list_processes()
        for process in list:
            if process.szExeFile == process_name:
                yield process.th32ProcessID

    def open(process_name=b'bluecg.exe'):
        ids = Hcg.get_all_processID()
        for id in ids:
            if id not in Hcg.opened_cg_processIDs:
                cg = Hcg(id)
                return cg

    def start_loop(self):
        while not self.stop:
            time.sleep(1)
            if self.is_fighting():
                self.on_fighting()

    def on_fighting(self):
        pass

    def stop_loop(self):
        self.stop = True

    def close(self):
        self.stop_loop()
        Hcg.opened_cg_processIDs.remove(self.mem.process_id)

    def get_player_name(self):
        name = self.mem.read_string(0x00F4C3F8)
        return name

    def is_fighting(self):
        return self.mem.read_int(0x0072B9D0) == 3

    # 人物1 宠物4 行动结束5 登出以后再进游戏都为1
    def battle_turn_flag(self):
        return self.mem.read_int(0x00598974)

    def set_battle_order(self, player_order, pet_order='W|0|E\0'):
        self.player_battle_order = player_order
        self.pet_battle_order = pet_order

    def get_skill(self):
        for i in range(0, 14):
            name = self.mem.read_string(0x00E8D6EC+0x4C4C*i)
            if len(name) > 0:
                yield name

    def move_to(self):
        # 走路
        # 0046845D  原A3 C8 C2 C0 00 改90 90 90 90 90
        # 00468476  原89 0D C4 C2 C0 00 改90 90 90 90 90 90
        # 00C0C2C4 X 00C0C2C8 Y 00C0C2DC 置1
        pass

    def auto_battle(self, switcher, player_order, pet_order='W|0|E\0'):
        self.set_battle_order(player_order, pet_order)
        ADDR_PlAYER_BUFFER = 0x00543F84
        ADDR_PlAYER_FLAG = 0x0048F9F7
        ADDR_PET_BUFFER = 0x00543EC0
        ADDR_PET_FLAG = 0x00475A8C
        ADDR_PET_SELECT = 0x00CB0AB0
        ADDR_PET_SELECTED = 0x00543DE4

        if switcher:
            self.mem.write_bytes(ADDR_PlAYER_FLAG, bytes.fromhex('90 90'), 2)
            self.mem.write_bytes(ADDR_PET_FLAG, bytes.fromhex('90 90'), 2)
            self.mem.write_string(ADDR_PlAYER_BUFFER,
                                  self.player_battle_order+'\0')
            self.mem.write_string(ADDR_PET_BUFFER, 'W|0|E\0')
            self.mem.write_int(ADDR_PET_SELECT, 0xFFFFFFFF)
            self.mem.write_int(ADDR_PET_SELECTED, 1)
        else:
            self.mem.write_bytes(ADDR_PlAYER_FLAG, bytes.fromhex('74 5E'), 2)
            self.mem.write_bytes(ADDR_PET_FLAG, bytes.fromhex('74 73'), 2)
            self.mem.write_string(ADDR_PlAYER_BUFFER, 'G\0')
            self.mem.write_string(ADDR_PET_BUFFER, r'W|%X|%X\0')
