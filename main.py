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
        pywebio.output.put_button('开启/关闭自动战斗', lambda: switch_auto_battle(cg))

        class UI(hcg.observer.Observer):
            def update(self):
                pywebio.output.clear(scope='battle')
                pywebio.output.put_grid([
                    [pywebio.output.put_text(cg.battle.get_position_info_str(14)),
                     pywebio.output.put_text(
                         cg.battle.get_position_info_str(12)),
                     pywebio.output.put_text(
                         cg.battle.get_position_info_str(10)),
                     pywebio.output.put_text(
                         cg.battle.get_position_info_str(11)),
                     pywebio.output.put_text(cg.battle.get_position_info_str(13))],
                    [pywebio.output.put_text(cg.battle.get_position_info_str(19)),
                     pywebio.output.put_text(
                         cg.battle.get_position_info_str(17)),
                     pywebio.output.put_text(
                         cg.battle.get_position_info_str(15)),
                     pywebio.output.put_text(
                         cg.battle.get_position_info_str(16)),
                     pywebio.output.put_text(cg.battle.get_position_info_str(18))],
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
    if cg.battle.auto_battle:
        cg.battle.auto_battle = False
        pywebio.output.toast('自动战斗已关闭')
    else:
        cg.battle.auto_battle = True
        pywebio.output.toast('自动战斗已开启')


pywebio.platform.start_server(
    [index, main], auto_open_webbrowser=True)
