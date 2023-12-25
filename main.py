import pywebio
import time
import hcg
import hcg.observer


def main():
    cg = hcg.Hcg.open()
    if isinstance(cg, hcg.Hcg):

        # 会话关闭释放对象
        pywebio.session.defer_call(
            lambda: cg.close())

        # 设置窗口标题
        pywebio.session.set_env(title=cg.player_name)
        pywebio.output.put_text(cg.player_name).style(
            'font-size:24px;font-weight:bold')
        pywebio.output.put_button(
            '开启/关闭自动战斗', lambda: switch_auto_battle(cg)
        ).style('margin-bottom:20px;margin-right:20px;display:inline-block')
        pywebio.output.put_button(
            '开启/关闭高速战斗', lambda: switch_speed_battle(cg)
        ).style('margin-bottom:20px;display:inline-block')

        if cg.battle.hcg.job_name in ['見習魔術師', '魔術師', '王宮魔術師',
                                      '魔導士', '大魔導士']:
            pywebio.output.put_button(
                '選擇魔術技能', lambda: add_select_skill_ui(cg)
            ).style('margin-bottom:20px;margin-left:20px, display:inline-block')

        class UI(hcg.observer.Observer):
            def on_battle_buffer_changed(self):
                pywebio.output.clear(scope='battle')
                pywebio.output.put_grid([
                    [pywebio.output.put_text(
                        cg.battle.get_position_info_str(14)),
                        pywebio.output.put_text(
                            cg.battle.get_position_info_str(12)),
                        pywebio.output.put_text(
                            cg.battle.get_position_info_str(10)),
                        pywebio.output.put_text(
                            cg.battle.get_position_info_str(11)),
                        pywebio.output.put_text(
                            cg.battle.get_position_info_str(13))],
                    [pywebio.output.put_text(
                        cg.battle.get_position_info_str(19)),
                        pywebio.output.put_text(
                            cg.battle.get_position_info_str(17)),
                        pywebio.output.put_text(
                            cg.battle.get_position_info_str(15)),
                        pywebio.output.put_text(
                            cg.battle.get_position_info_str(16)),
                        pywebio.output.put_text(
                            cg.battle.get_position_info_str(18))],
                ], cell_width='200px', cell_height='100px', scope='battle')

        pywebio.output.set_scope('battle')
        ui = UI()
        cg.observers.append(ui)
        cg.start_loop()
    else:
        pywebio.output.put_warning('全部游戏窗口已打开，此页面将自动关闭。')
        pywebio.session.run_js(r'setInterval("window.close()", 3000);')


def index():
    pywebio.session.set_env(title='HappyCG')
    pywebio.output.put_button(
        'Open BlueCG', lambda: pywebio.session.go_app('main'))
    while True:
        time.sleep(1)


def switch_auto_battle(cg: hcg.Hcg):
    if cg.battle.enable_auto_battle:
        cg.battle.enable_auto_battle = False
        pywebio.output.toast('自动战斗已关闭', color='warn')
    else:
        cg.battle.enable_auto_battle = True
        pywebio.output.toast('自动战斗已开启', color='success')


def switch_speed_battle(cg: hcg.Hcg):
    if cg.battle.enable_speed_battle:
        cg.battle.enable_speed_battle = False
        pywebio.output.toast('高速战斗已关闭', color='warn')
    else:
        cg.battle.enable_speed_battle = True
        pywebio.output.toast('高速战斗已开启', color='success')


def selected_skill(name, cg: hcg.Hcg, mode=0):
    cg.battle.set_selected_skill(name, mode)


def add_select_skill_ui(cg: hcg.Hcg):
    skills_names = [i.name for i in cg.battle.player_skills]
    with pywebio.output.use_scope('select_skill', clear=True):
        pywebio.output.put_table([
            ['aoe: ', pywebio.input.select('選擇超強魔法', skills_names,
                                           value=skills_names[0],
                                           validate=lambda name: selected_skill(
                                               name, cg, 0))],
            ['單體', pywebio.input.select('選擇單體魔法', skills_names,
                                          value=skills_names[0],
                                          validate=lambda name: selected_skill(
                                              name, cg, 1))]
        ])


pywebio.platform.start_server(
    [index, main], auto_open_webbrowser=True)
