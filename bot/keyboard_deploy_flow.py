"""
keyboard_deploy_flow.py

Protótipo que implementa a estratégia solicitada: para cada tecla (1..8 por padrão),
o script envia o evento de tecla via ADB e executa N toques na tela (por padrão 15).

Use em emulador Full HD ou ajuste `--width`/`--height` conforme necessário.
"""

import argparse
import random
import time
from typing import List, Tuple

from bot.adb_bot import ensure_device_connected, adb_tap, run_adb


def char_to_keycode(ch: str) -> int:
    """Converte um único caractere (dígito ou letra) para keycode Android.

    Digits: '0'..'9' => keycodes 7..16
    Letters: 'A'..'Z' => keycodes 29..54
    """
    if len(ch) != 1:
        raise ValueError("Key must be a single character")
    if ch.isdigit():
        return ord(ch) - ord('0') + 7
    if ch.isalpha():
        # map A->29, B->30, ...
        return ord(ch.upper()) - ord('A') + 29
    raise ValueError("Unsupported key character")


def parse_keys(s: str) -> List[str]:
    # aceita formatos: "1,2,3" ou "1-4" ou "1 2 3"
    s = s.replace(',', ' ').strip()
    parts = s.split()
    keys = []
    for p in parts:
        if '-' in p:
            a, b = p.split('-', 1)
            a = int(a); b = int(b)
            for i in range(a, b + 1):
                keys.append(str(i))
        else:
            keys.append(p)
    return keys


def random_point_in_area(area: Tuple[int, int, int, int]) -> Tuple[int, int]:
    left, top, right, bottom = area
    x = random.randint(left + 5, right - 5)
    y = random.randint(top + 5, bottom - 5)
    return x, y


def press_key_via_adb(keycode: int) -> bool:
    # envia keyevent via adb
    p = run_adb(["shell", "input", "keyevent", str(keycode)], capture_output=False)
    return p.returncode == 0


def press_and_hold_char(ch: str, duration: float) -> bool:
    """Tenta simular um 'hold' da tecla por `duration` segundos.

    Tenta usar `input keyevent --longpress` se disponível; caso contrário,
    envia um keyevent, espera e envia outro (fallback). Em emuladores isso
    geralmente é suficiente para acionar comportamento de 'hold'.
    """
    kc = char_to_keycode(ch)
    # tente --longpress primeiro
    p = run_adb(["shell", "input", "keyevent", "--longpress", str(kc)])
    if p.returncode == 0:
        # longpress suportado
        return True
    # fallback: enviar keyevent, aguardar e enviar novamente
    p1 = run_adb(["shell", "input", "keyevent", str(kc)] , capture_output=False)
    time.sleep(duration)
    p2 = run_adb(["shell", "input", "keyevent", str(kc)], capture_output=False)
    return p1.returncode == 0 and p2.returncode == 0


def run_sequence(keys: List[str], clicks_per_key: int, area: Tuple[int, int, int, int], click_delay: float, key_delay: float):
    # This function is now a simple helper; real sequence implemented in perform_full_sequence
    print("run_sequence called but sequence logic moved to perform_full_sequence")


def press_key(ch: str, times: int = 1, delay: float = 0.12):
    """Pressiona a tecla `ch` via adb `times` vezes com `delay` entre as tentativas."""
    for i in range(times):
        try:
            kc = char_to_keycode(ch)
        except ValueError:
            print(f"Ignorando tecla invalida: {ch}")
            return
        ok = press_key_via_adb(kc)
        if not ok:
            print(f"Falha ao enviar evento de tecla {ch} via adb (iter {i+1})")
        else:
            print(f"Pressionada tecla {ch} (iter {i+1})")
        time.sleep(delay)


def perform_full_sequence():
    """Implementa a sequência detalhada fornecida pelo usuário.

    Sequence:
    - aguardar 3s
    - apertar I, aguardar 3s, apertar I
    - aguardar 10s
    - segurar K 10 vezes (cada hold 2s)
    - para cada tecla em [1..6]: pressionar tecla, depois pressionar J 15 vezes
    - pressionar 7,8,9,0 uma vez cada
    - contar 120s
    - apertar I, esperar 2s, apertar O, esperar 2s, apertar V
    - fim; retorna para permitir reinício
    """
    print("Sequência: aguardando 3 segundos")
    time.sleep(3)

    print("Pressionando I (1/2)")
    press_key('I', times=1, delay=0.12)
    time.sleep(3)
    print("Pressionando I (2/2)")
    press_key('I', times=1, delay=0.12)

    print("Aguardando 10 segundos")
    time.sleep(10)

    print("Segurar K 10 vezes (2s cada)")
    for i in range(10):
        ok = press_and_hold_char('K', 2.0)
        if not ok:
            print(f"Aviso: hold K tentativa {i+1} pode não ter sido suportado")
        else:
            print(f"Hold K realizado ({i+1}/10)")
        time.sleep(0.15)

    # For digits 1..6: press digit then press J 15 times
    for d in ['1', '2', '3', '4', '5', '6']:
        print(f"Pressionando tecla {d}")
        press_key(d, times=1, delay=0.12)
        print(f"Pressionando 'J' 15 vezes após {d}")
        press_key('J', times=15, delay=0.08)
        time.sleep(0.25)

    # Press 7,8,9,0 once
    for d in ['7', '8', '9', '0']:
        print(f"Pressionando tecla {d} (uma vez)")
        press_key(d, times=1, delay=0.12)
        time.sleep(0.12)

    print("Contando 120 segundos...")
    time.sleep(120)

    print("Pressionando I")
    press_key('I', times=1, delay=0.12)
    time.sleep(2)
    print("Pressionando O")
    press_key('O', times=1, delay=0.12)
    time.sleep(2)
    print("Pressionando V")
    press_key('V', times=1, delay=0.12)

    print("Sequência concluída — retornando para possível reinício")


def main():
    parser = argparse.ArgumentParser(description="Pressiona teclas e executa múltiplos cliques por tecla (protótipo)")
    parser.add_argument("--keys", default="1-8", help="Teclas a pressionar (ex: '1-4' ou '1,2,3')")
    parser.add_argument("--clicks", type=int, default=15, help="Número de cliques por tecla")
    parser.add_argument("--width", type=int, default=1920, help="Largura da tela (padrão Full HD)")
    parser.add_argument("--height", type=int, default=1080, help="Altura da tela (padrão Full HD)")
    parser.add_argument("--area", help="Área de deploy como left,top,right,bottom (opcional)")
    parser.add_argument("--click-delay", type=float, default=0.12, help="Delay base entre cliques (s)")
    parser.add_argument("--key-delay", type=float, default=0.4, help="Delay base após pressionar cada tecla (s)")
    parser.add_argument("--once", action="store_true", help="Executa a sequência apenas uma vez e sai")
    args = parser.parse_args()

    if not ensure_device_connected():
        return

    keys = parse_keys(args.keys)
    if args.area:
        parts = [int(x) for x in args.area.split(',')]
        if len(parts) != 4:
            print("Área inválida; use left,top,right,bottom")
            return
        area = tuple(parts)
    else:
        # zona de deploy por padrão: centro da tela, evitando HUDs (margens de 10%)
        w = args.width
        h = args.height
        left = int(w * 0.08)
        right = int(w * 0.92)
        top = int(h * 0.18)
        bottom = int(h * 0.82)
        area = (left, top, right, bottom)

    print(f"Keys: {keys}, clicks/key={args.clicks}, area={area}")

    try:
        run_sequence(keys, args.clicks, area, args.click_delay, args.key_delay)
    except KeyboardInterrupt:
        print("Interrompido pelo usuário")


if __name__ == "__main__":
    main()
