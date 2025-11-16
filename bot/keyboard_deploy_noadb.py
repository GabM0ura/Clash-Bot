"""
keyboard_deploy_noadb.py

Versão do fluxo que NÃO usa `adb`. Em vez disso envia eventos de teclado/mouse
diretamente ao sistema operacional usando `pyautogui`. Funciona quando o
emulador aceita entradas de teclado do host (janela em foco).

Uso recomendado:
- Se possível, especifique o título da janela do emulador com `--focus-window`.
- Caso contrário foque manualmente a janela do emulador antes do início.

AVISO: este método depende do emulador mapear teclas do teclado para ações no
jogo. Teste manualmente antes de rodar em conta principal.
"""

import argparse
import time
import sys
import pyautogui

try:
    import pygetwindow as gw
except Exception:
    gw = None


def focus_window(title_substring: str, timeout: float = 5.0) -> bool:
    if not gw:
        return False
    t0 = time.time()
    while time.time() - t0 < timeout:
        wins = gw.getWindowsWithTitle(title_substring)
        if wins:
            w = wins[0]
            try:
                w.activate()
                return True
            except Exception:
                try:
                    w.minimize()
                    w.maximize()
                    w.activate()
                    return True
                except Exception:
                    return False
        time.sleep(0.25)
    return False


def press_and_hold(key: str, duration: float):
    pyautogui.keyDown(key)
    time.sleep(duration)
    pyautogui.keyUp(key)


def press_key(key: str, times: int = 1, delay: float = 0.12):
    for i in range(times):
        pyautogui.press(key)
        time.sleep(delay)


def perform_full_sequence():
    # 1) aguardar 3s
    time.sleep(3)

    # press I, wait 3s, press I
    press_key('i', times=1)
    time.sleep(3)
    press_key('i', times=1)

    # wait 10s
    time.sleep(10)

    # hold K 10 times for 2s each
    for i in range(10):
        press_and_hold('k', 2.0)
        time.sleep(0.15)

    # for digits 1..6: press digit then press J 15 times
    for d in ['1','2','3','4','5','6']:
        press_key(d, times=1)
        press_key('j', times=15, delay=0.08)
        time.sleep(0.25)

    # press 7,8,9,0 once
    for d in ['7','8','9','0']:
        press_key(d, times=1)
        time.sleep(0.12)

    # count 120s
    time.sleep(120)

    # final presses
    press_key('i', times=1)
    time.sleep(2)
    press_key('o', times=1)
    time.sleep(2)
    press_key('v', times=1)


def main():
    parser = argparse.ArgumentParser(description='Fluxo sem ADB usando pyautogui')
    parser.add_argument('--focus-window', help='Substring do título da janela do emulador para ativar')
    parser.add_argument('--start-delay', type=int, default=5, help='Segundos para focar a janela/manualmente antes de iniciar')
    parser.add_argument('--once', action='store_true', help='Executa uma vez e sai')
    args = parser.parse_args()

    pyautogui.FAILSAFE = False

    if args.focus_window:
        ok = focus_window(args.focus_window, timeout=args.start_delay)
        if not ok:
            print(f"Não conseguiu focar janela contendo: {args.focus_window}. Certifique-se de focar a janela manualmente.")
    else:
        print(f"Coloque a janela do emulador em foco nos próximos {args.start_delay} segundos...")
        time.sleep(args.start_delay)

    try:
        while True:
            perform_full_sequence()
            if args.once:
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print('Interrompido pelo usuário')


if __name__ == '__main__':
    if sys.platform.startswith('win'):
        print('Executando em Windows')
    main()
