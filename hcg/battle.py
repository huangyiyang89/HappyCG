import time
import random
import hcg
import hcg.observer


class Battle(hcg.observer.Observer):
    def __init__(self, hcg: 'hcg.Hcg') -> None:
        self.hcg = hcg
        self.mem = hcg.mem
        self._enemies = []
        self._friends = []
        self._player_skills = []
        self.auto_battle = False

    def update_units(self):
        self._enemies.clear()
        self._friends.clear()
        unit_str = self.mem.read_string(0x00590758, 1024)
        if len(unit_str) < 12:
            return
        split_list = unit_str[4:].split('|')
        for i in range(0, len(split_list)-12, 12):
            u = Unit(split_list[i:i+12])
            if u.is_enemy:
                self._enemies.append(u)
            else:
                self._friends.append(u)

    def update_player_skills(self):
        self._player_skills.clear()
        for i in range(0, 14):
            name = self.mem.read_string(0x00E8D6EC+0x4C4C*i)
            level = self.mem.read_int(0x00E8D6EC+0x4C4C*i+0x1C)
            skill = PlayerSkill(i, name, level)
            self._player_skills.append(skill)

    def get_position_info_str(self, pos):
        """获取位置上怪物信息文本，用来输出"""
        for enemy in self.enemies:
            if enemy.pos == pos:
                return enemy.info_str()
        return '空'

    @property
    def player_skills(self):
        self.update_player_skills()
        return self._player_skills

    def get_aoe_skill(self):
        for skill in self.player_skills:
            if skill.name in ['亂射', '氣功彈', '刀刃亂舞']:
                return skill
        return None

    @property
    def enemies(self):
        return self._enemies

    @property
    def friends(self):
        return self._friends

    def print_units(self):
        for unit in self.enemies:
            unit.print()
        for unit in self.friends:
            unit.print()

    @property
    def battle_turn_flag(self):
        """人物行动时为1 宠物行动时为4 行动结束为5 登出以后再进游戏都为1"""
        return self.mem.read_int(0x00598974)

    @property
    def is_player_turn(self):
        """人物行动时为1 宠物行动时为4 行动结束为5 登出以后再进游戏都为1"""
        return self.mem.read_int(0x00598974) == 1

    @property
    def is_pet_turn(self):
        """人物行动时为1 宠物行动时为4 行动结束为5 登出以后再进游戏都为1"""
        return self.mem.read_int(0x00598974) == 4

    def execute_player_command(self, player_battle_order='G\0'):
        ADDR_PLAYER_BUFFER = 0x00543F84
        ADDR_PLAYER_FLAG = 0x0048F9F7
        # hook
        self.mem.write_string(ADDR_PLAYER_BUFFER, player_battle_order+'\0')
        self.mem.write_bytes(ADDR_PLAYER_FLAG, bytes.fromhex('90 90'), 2)
        time.sleep(0.1)
        # 还原
        self.mem.write_string(ADDR_PLAYER_BUFFER, 'G\0')
        self.mem.write_bytes(ADDR_PLAYER_FLAG, bytes.fromhex('74 5E'), 2)

    def player_skill_command(self, index, lv, pos):
        self.execute_player_command(f"S|{index:X}|{lv-1:X}|{pos:X}")

    def player_attack_command(self, pos):
        self.execute_player_command(f"H|{pos:X}")

    def pet_command(self, index, pos):
        self.execute_pet_command(f"W|{index:X}|{pos:X}")

    def execute_pet_command(self, pet_battle_order='W|0|E'):
        ADDR_PET_BUFFER = 0x00543EC0
        ADDR_PET_FLAG = 0x00475A8C
        ADDR_PET_SELECT = 0x00CB0AB0
        ADDR_PET_SELECTED = 0x00543DE4
        # hook
        self.mem.write_string(ADDR_PET_BUFFER, pet_battle_order+'\0')
        self.mem.write_bytes(ADDR_PET_FLAG, bytes.fromhex('90 90'), 2)
        self.mem.write_int(ADDR_PET_SELECT, 0xFFFFFFFF)
        self.mem.write_int(ADDR_PET_SELECTED, 255)
        time.sleep(0.1)
        # 还原
        self.mem.write_string(ADDR_PET_BUFFER, r'W|%X|%X'+'\0')
        self.mem.write_bytes(ADDR_PET_FLAG, bytes.fromhex('74 73'), 2)

    def on_fighting(self):
        """战斗中每一秒触发一次"""

        if not self.auto_battle:
            return

        if self.is_player_turn:
            aoe_skill = self.get_aoe_skill()
            enemies_count = len(self.enemies)
            random_enemy = random.choice(self.enemies)

            if aoe_skill is None or enemies_count < 3:
                self.player_attack_command(random_enemy.pos)
            else:
                self.player_skill_command(
                    aoe_skill.index, aoe_skill.level, random_enemy.pos)

        if self.is_pet_turn:
            random_enemy = random.choice(self.enemies)
            self.pet_command(0, random_enemy.pos)

    def update(self):
        self.update_units()
        self.update_player_skills()


class Unit:
    # C|0|0|���뷬��|19ABB|0|4A|60A|627|470|666|6000005|0|0|1|�����q|197DE|0|4D|40B|552|D5|24C|8000005|0|0|
    # //14 12 10 11 13
    # // 19 17 15 16 18
    # //
    # // 9 7 5 6 8
    # // 4 2 0 1 3
    def __init__(self, data_list: []) -> None:
        if not isinstance(data_list, list) or len(data_list) != 12:
            raise Exception('unit init error')
        self.pos = int(data_list[0], 16)
        self.pos_hex = data_list[0]
        self.name = data_list[1]
        self.level = int(data_list[4], 16)
        self.hp = int(data_list[5], 16)
        self.max_hp = int(data_list[6], 16)
        self.mp = int(data_list[7], 16)
        self.max_mp = int(data_list[8], 16)
        self.is_enemy = True if self.pos > 9 else False

    def print(self):
        print(self.pos, self.level, self.name, self.hp,
              self.max_hp, self.mp, self.max_mp)

    def info_str(self):
        return self.name+' LV:'+str(self.level)+'\r\n'+str(
            self.hp)+'/'+str(self.max_hp)+'\r\n'+str(
                self.mp)+'/'+str(self.max_mp)


class PlayerSkill:
    def __init__(self, index, name, level) -> None:
        self.index = index
        self.name = name
        self.level = level
