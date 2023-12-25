import time
import random
import hcg
import hcg.observer


class BattleManager(hcg.observer.Observer):
    def __init__(self, hcg: 'hcg.Hcg') -> None:
        self.hcg = hcg
        self.mem = hcg.mem
        self.player = None
        self.pet = None
        self._enemies = []
        self._friends = []
        self._player_skills = []
        self._pets = []
        self.enable_auto_battle = False
        self.enable_speed_battle = False
        self._selected_aoe_skill = None
        self._selected_single_skill = None

    @property
    def battle_units_buffer(self):
        return self.mem.read_string(0x00590758, 1024)

    @property
    def recv_message_buffer(self):
        return self.mem.read_string(0x00580CF0, encoding='utf-8')

    def update_units(self):
        self._enemies.clear()
        self._friends.clear()
        unit_str = self.battle_units_buffer
        if len(unit_str) < 12:
            return

        split_list = unit_str[4:].split('|')
        for i in range(0, len(split_list) - 12, 12):
            u = Unit(split_list[i:i + 12])
            player_pos = self.mem.read_int(0x005989DC)
            pet_pos = player_pos - 5 if player_pos > 4 else player_pos + 5
            if u.pos == player_pos:
                self.player = u
            if u.pos == pet_pos:
                self.pet = u
            if u.is_enemy:
                self._enemies.append(u)
            else:
                self._friends.append(u)

    def update_player_skills(self):
        self._player_skills.clear()
        for i in range(0, 14):
            name = self.mem.read_string(0x00E8D6EC + 0x4C4C * i)
            level = self.mem.read_int(0x00E8D6EC + 0x4C4C * i + 0x1C)
            pos = self.mem.read_int(0x00E8D724 + 0x4C4C * i)
            if len(name) > 0:
                skill = Skill(i, name, level, pos)
                for j in range(level):
                    sub_skill_name = self.mem.read_string(
                        0x00E8D6EC + 0x4C4C * i + 0x3C + 0x94 * j)
                    sub_skill_mp_cost = self.mem.read_int(
                        0x00E8D6EC + 0x4C4C * i + 0xB8 + 0x94 * j)
                    sub_skill = SubSkill(
                        j, sub_skill_name, sub_skill_mp_cost)
                    skill.sub_skill.append(sub_skill)
                self._player_skills.append(skill)
        pass

    def update_pets(self):
        self._pets.clear()
        for i in range(5):
            name = self.mem.read_string(0x00ED5694 + i * 0x5110)
            battle_flag = self.mem.read_short(0x00ED5692 + i * 0x5110)
            if (len(name) < 2):
                continue
            pet = Pet(i, name, battle_flag)
            self._pets.append(pet)
            if battle_flag == 2:
                # self.pet = pet
                pass
            for j in range(10):
                skill_name = self.mem.read_string(0x00ED50C6 + i * 0x5110 + j * 0x8C)
                skill_cost = self.mem.read_int(0x00ED5144 + i * 0x5110 + j * 0x8C)
                if (len(skill_name) > 0):
                    skill = PetSkill(j, skill_name, skill_cost)
                    pet.skills.append(skill)

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

    def set_selected_skill(self, name, mode=0):
        '''
        :param name: 技能名稱
        :param mode: 0:aoe, 1:single
        :return:
        '''
        if mode == 0:
            self._selected_aoe_skill = name
        else:
            self._selected_single_skill = name

    def get_aoe_skill(self):
        for skill in self.player_skills:
            if skill.name in ['亂射', '氣功彈', '刀刃亂舞', '因果報應', '連擊']:
                return skill
        return None

    def get_first_skill(self):
        for skill in self.player_skills:
            if skill.pos == 0:
                return skill
        return None

    @property
    def battle_petskills(self):
        for pet in self._pets:
            if pet.battle_flag == 2:
                return pet.skills
        return None

    @property
    def enemies(self):
        return self._enemies

    @property
    def friends(self):
        return self._friends

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
        self.mem.write_string(ADDR_PLAYER_BUFFER, player_battle_order + '\0')
        self.mem.write_bytes(ADDR_PLAYER_FLAG, bytes.fromhex('90 90'), 2)
        time.sleep(0.1)
        # 还原
        self.mem.write_string(ADDR_PLAYER_BUFFER, 'G\0')
        self.mem.write_bytes(ADDR_PLAYER_FLAG, bytes.fromhex('74 5E'), 2)

    def player_skill_command(self, index, lv, pos):
        self.execute_player_command(f"S|{index:X}|{lv - 1:X}|{pos:X}")

    def player_attack_command(self, pos):
        self.execute_player_command(f"H|{pos:X}")

    def pet_command(self, index, pos):
        command_str = f"W|{index:X}|{pos:X}"
        print(command_str)
        self.execute_pet_command(command_str)

    def execute_pet_command(self, pet_battle_order='W|0|E'):
        ADDR_PET_BUFFER = 0x00543EC0
        ADDR_PET_FLAG = 0x00475A8C

        # hook
        self.mem.write_string(ADDR_PET_BUFFER, pet_battle_order + '\0')
        self.mem.write_bytes(ADDR_PET_FLAG, bytes.fromhex('90 90'), 2)
        # self.mem.write_int(ADDR_PET_SELECT, 0xFFFFFFFF)
        # self.mem.write_int(ADDR_PET_SELECTED, 255)
        self.mem.write_bytes(0x00CDA984, bytes.fromhex('02'), 1)
        time.sleep(0.1)
        # 还原
        self.mem.write_string(ADDR_PET_BUFFER, r'W|%X|%X' + '\0')
        self.mem.write_bytes(ADDR_PET_FLAG, bytes.fromhex('74 73'), 2)

    def get_skill(self, name):
        for skill in self.player_skills:
            if skill.name == name:
                return skill
        return None

    def on_fighting(self):
        """战斗中持续触发"""

        if not self.enable_auto_battle:
            return
        if self.is_player_turn:
            if 'M|' in self.recv_message_buffer \
                    or 'C|' in self.recv_message_buffer:
                print('waiting anime...')

            else:
                if self.hcg.job_name in ['見習傳教士', '傳教士', '牧師', '主教', '大主教']:
                    count_below_85per = sum(
                        1 for friend in self.friends if friend.per_hp <= 85)
                    cross_pos = self.cross_heal_pos()
                    lowest_friend = min(
                        self.friends, key=lambda unit: unit.per_hp)
                    if count_below_85per > 4:
                        skill = self.get_skill('超強補血魔法')
                        self.player_skill_command(
                            skill.index, skill.level, 0x28)
                    elif cross_pos >= 0:
                        skill = self.get_skill('強力補血魔法')
                        self.player_skill_command(
                            skill.index, skill.level, cross_pos + 20)
                    elif lowest_friend.per_hp <= 80:
                        skill = self.get_skill('補血魔法')
                        self.player_skill_command(
                            skill.index, skill.level, lowest_friend.pos)
                    else:
                        random_enemy = random.choice(self.enemies)
                        self.player_attack_command(random_enemy.pos)
                elif self.hcg.job_name in ['見習魔術師', '魔術師', '王宮魔術師', '魔導士', '大魔導士']:
                    enemies_count = len(self.enemies)
                    random_enemy = random.choice(self.enemies)
                    if self._selected_aoe_skill is None or enemies_count < 3:
                        skill = self.get_skill(self._selected_single_skill)
                        self.player_skill_command(
                            skill.index, skill.level, random_enemy.pos)
                    else:
                        skill = self.get_skill(self._selected_aoe_skill)
                        self.player_skill_command(
                            skill.index, skill.level, 0x29)
                else:
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
            heal_skill = next(
                (skill for skill in self.battle_petskills if skill.name in '吸血'), None)
            attack = next(
                (skill for skill in self.battle_petskills if skill.name in '攻擊'), None)
            if self.pet.per_hp <= 80 and heal_skill is not None:
                self.pet_command(heal_skill.index, random_enemy.pos)
            elif self.pet.mp > self.battle_petskills[0].cost:
                self.pet_command(0, random_enemy.pos)
            else:
                self.pet_command(attack.index, random_enemy.pos)

        if self.enable_speed_battle:
            t0 = self.mem.read_double(0x0072B9D8)
            self.mem.write_double(0x0072B9D8, t0 - 100)

    def on_update(self):
        self.update_units()
        self.update_player_skills()
        self.update_pets()
        pass

    def cross_heal_pos(self, hp_lower_than_per=85):

        def count_set_bits(n):
            count = 0
            while n:
                count += n & 1
                n >>= 1
            return count

        # 强力位二进制表示
        crosses = [0b1110010000, 0b1101001000, 0b1010100100, 0b0101000010,
                   0b0010100001, 0b1000011100, 0b0100011010, 0b0010010101,
                   0b0001001010, 0b0000100101]

        # 场上存在符合条件的友方单位二进制表示是否存在
        units_bit = 0

        # 指定位置单位是否存在
        exists_list = [0] * 10

        for unit in self.friends:
            exists_list[unit.pos] = True
            if unit.per_hp <= hp_lower_than_per:
                # 单位如果血量符合条件则移位存入units_bit
                units_bit += 1 << (9 - unit.pos)

        ret_pos = -1
        # 检查友方10个位置，返回单位存在且强力位符合条件的目标数大于3的位置，没有返回-1
        for i in range(10):
            if exists_list[i]:
                count = count_set_bits(units_bit & crosses[i])
                if count == 4:
                    return i
                if count == 3:
                    ret_pos = i
        return ret_pos


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
        self.per_hp = self.hp / self.max_hp
        self.per_mp = self.mp / self.max_mp
        self.los_hp = self.max_hp - self.hp
        self.los_mp = self.max_mp - self.mp
        self.is_enemy = True if self.pos > 9 else False

    def info_str(self):
        return self.name + ' LV:' + str(self.level) + '\r\n' + str(
            self.hp) + '/' + str(self.max_hp) + '\r\n' + str(
            self.mp) + '/' + str(self.max_mp)


class Skill:
    def __init__(self, index, name, level, pos) -> None:
        self.index = index
        self.name = name
        self.level = level
        self.pos = pos
        self.sub_skill = []


class SubSkill:
    def __init__(self, index, name, mp_cost) -> None:
        self.index = index
        self.name = name
        self.mp_cost = mp_cost


class Pet:
    def __init__(self, index, name, battle_flag) -> None:
        self.index = index
        self.name = name
        self.battle_flag = battle_flag
        self.skills = []


class PetSkill:
    def __init__(self, index, name, cost) -> None:
        self.index = index
        self.name = name
        self.cost = cost
