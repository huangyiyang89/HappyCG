import pymem
import time

import hcg.battle


class Pymem(pymem.Pymem):
    # 重写支持big编码
    def read_string(handle, address, byte=50, encoding='big5', end=b'\x00'):
        buff = pymem.Pymem.read_bytes(handle, address, byte)
        i = buff.find(end)
        if i != -1:
            buff = buff[:i]
        buff = buff.decode(encoding, 'replace')
        return buff


class Hcg(object):
    # 保存已打开的游戏的process id
    __opened_cg_processIDs = []

    def __init__(self, processID):
        self.mem = Pymem(processID)
        self.stop = False
        self.last_battle_buffer = ''

        Hcg.__opened_cg_processIDs.append(processID)

        self.battle = hcg.battle.BattleManager(self)
        self.observers = []
        self.observers.append(self.battle)


    def get_all_processID(process_name=b'bluecg.exe'):
        list = pymem.process.list_processes()
        for process in list:
            if process.szExeFile == process_name:
                yield process.th32ProcessID

    def open(process_name=b'bluecg.exe'):
        ids = Hcg.get_all_processID()
        for id in ids:
            if id not in Hcg.__opened_cg_processIDs:
                cg = Hcg(id)
                return cg

    def start_loop(self):
        while not self.stop:
            time.sleep(0.1)
            for ob in self.observers:
                ob.on_update()
            if self.battle.battle_units_buffer != self.last_battle_buffer:
                self.last_battle_buffer = self.battle.battle_units_buffer
                for ob in self.observers:
                    ob.on_battle_buffer_changed()
            if self.is_fighting:
                for ob in self.observers:
                    ob.on_fighting()

    def stop_loop(self):
        self.stop = True

    def close(self):
        self.stop_loop()
        Hcg.__opened_cg_processIDs.remove(self.mem.process_id)

        self.battle = None

    @property
    def job_name(self):
        return self.mem.read_string(0x00E8D6D0)

    @property
    def player_name(self):
        return self.mem.read_string(0x00F4C3F8)

    @property
    def is_fighting(self):
        return self.mem.read_short(0x0072B9D0) == 3

    def go_to(self, x, y):
        # 走路
        # 0046845D  原A3 C8 C2 C0 00 改90 90 90 90 90
        # 00468476  原89 0D C4 C2 C0 00 改90 90 90 90 90 90
        # 00C0C2C4 X 00C0C2C8 Y 00C0C2DC 置1
        self.mem.write_bytes(0x0046845D, bytes.fromhex('90 90 90 90 90'), 5)
        self.mem.write_bytes(0x00468476, bytes.fromhex('90 90 90 90 90 90'), 6)
        self.mem.write_int(0x00C0C2C4, x)
        self.mem.write_int(0x00C0C2C8, y)
        self.mem.write_int(0x00C0C2DC, 1)
        time.sleep(0.1)

        # 还原
        self.mem.write_int(0x00C0C2DC, 0)
        self.mem.write_bytes(0x0046845D, bytes.fromhex('A3 C8 C2 C0 00'), 5)
        self.mem.write_bytes(0x00468476, bytes.fromhex('89 0D C4 C2 C0 00'), 6)
