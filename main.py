import pywebio
import time
from hcg.cg import Hcg


def app():
    cg = Hcg.open()
    if isinstance(cg, Hcg):
        pywebio.session.defer_call(
            lambda: cg.close())
        pywebio.session.set_env(title=cg.get_player_name())
        pywebio.output.put_text('自动战斗设置：').style(
            'font-size:24px;font-weight:bold')
        for name in cg.get_skill():
            pywebio.output.put_text(name)
        pywebio.output.put_text('设置战斗指令：').style(
            'font-size:24px;font-weight:bold;margin')
        pywebio.pin.put_input('battle_order', value='S|0|0|D')

        pywebio.output.put_button(
            '开启', lambda: cg.auto_battle(True, pywebio.pin.pin.battle_order)).style('display:inline-block;')
        pywebio.output.put_button(
            '关闭', lambda: cg.auto_battle(False, pywebio.pin.pin.battle_order)).style('display:inline-block;margin-left:20px')
        cg.start_loop()
    else:
        pywebio.output.put_warning('全部游戏窗口已打开，此页面将自动关闭。')
        pywebio.session.run_js(r'setInterval("window.close()", 3000);')


def index():

    pywebio.output.put_button(
        'Open BlueCG', lambda: pywebio.session.go_app('app'))
    while True:
        time.sleep(1)


pywebio.platform.start_server(
    [index, app], auto_open_webbrowser=True)
