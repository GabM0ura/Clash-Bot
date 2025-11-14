import argparse
import glob
import io
import os
import random
import subprocess
import sys
import time
from typing import Optional, Tuple

import cv2
import numpy as np
from PIL import Image


def run_adb(cmd: list, capture_output=True) -> subprocess.CompletedProcess:
    full = ["adb"] + cmd
    return subprocess.run(full, stdout=subprocess.PIPE if capture_output else None, stderr=subprocess.PIPE)


def ensure_device_connected() -> bool:
    p = run_adb(["devices"]) 
    if p.returncode != 0:
        print("adb not found or returned error:", p.stderr.decode(errors='ignore'))
        return False
    out = p.stdout.decode(errors='ignore')
    lines = [l for l in out.splitlines() if l.strip()]
    # first line is "List of devices attached"
    if len(lines) <= 1:
        print("No devices attached. Start emulator and ensure adb can see it.")
        return False
    # basic check: at least one device with "device" state
    for l in lines[1:]:
        if "device" in l:
            return True
    print("No active device in `adb devices` output:\n", out)
    return False


def screencap_pil() -> Optional[Image.Image]:
    # Use exec-out screencap -p to get PNG bytes
    p = subprocess.run(["adb", "exec-out", "screencap", "-p"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0 or not p.stdout:
        print("Failed to capture screen:", p.stderr.decode(errors='ignore'))
        return None
    try:
        img = Image.open(io.BytesIO(p.stdout)).convert("RGB")
        return img
    except Exception as e:
        print("Error decoding screencap PNG:", e)
        return None


def pil_to_cv(img: Image.Image) -> np.ndarray:
    arr = np.array(img)
    # PIL gives RGB, convert to BGR for OpenCV
    return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)


def find_template(screen_cv: np.ndarray, template_path: str, threshold: float = 0.8,
                  scale_min: float = 0.8, scale_max: float = 1.2, steps: int = 7) -> Optional[Tuple[int, int, float, int, int]]:
    tpl_orig = cv2.imread(template_path)
    if tpl_orig is None:
        print(f"Template not found or unreadable: {template_path}")
        return None
    h_s, w_s = screen_cv.shape[:2]

    best = None  # (score, center_x, center_y, w_t, h_t)
    # Try multiple scales for the template (multi-escala)
    for scale in np.linspace(scale_min, scale_max, steps):
        w_t = int(tpl_orig.shape[1] * scale)
        h_t = int(tpl_orig.shape[0] * scale)
        if w_t < 6 or h_t < 6:
            continue
        if w_t > w_s or h_t > h_s:
            # skip scales that make template bigger than screen
            continue
        tpl = cv2.resize(tpl_orig, (w_t, h_t), interpolation=cv2.INTER_AREA)
        res = cv2.matchTemplate(screen_cv, tpl, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        if max_val >= threshold:
            top_left = max_loc
            center_x = top_left[0] + w_t // 2
            center_y = top_left[1] + h_t // 2
            if best is None or max_val > best[0]:
                best = (float(max_val), int(center_x), int(center_y), int(w_t), int(h_t))

    if best:
        score, cx, cy, w_t, h_t = best
        return cx, cy, score, w_t, h_t
    return None


def find_template_in_dir(screen_cv: np.ndarray, dir_path: str, threshold: float = 0.8,
                         scale_min: float = 0.8, scale_max: float = 1.2, steps: int = 7) -> Optional[Tuple[str, int, int, float, int, int]]:
    # Iterate over image files in dir and try to find best match
    patterns = ["*.png", "*.jpg", "*.jpeg", "*.bmp"]
    files = []
    for p in patterns:
        files.extend(glob.glob(os.path.join(dir_path, p)))
    files = sorted(files)
    best_overall = None  # (score, path, cx, cy, w_t, h_t)
    for f in files:
        found = find_template(screen_cv, f, threshold, scale_min, scale_max, steps)
        if found:
            cx, cy, score, w_t, h_t = found
            if best_overall is None or score > best_overall[0]:
                best_overall = (score, f, cx, cy, w_t, h_t)
    if best_overall:
        score, path, cx, cy, w_t, h_t = best_overall
        return path, cx, cy, score, w_t, h_t
    return None


def adb_tap(x: int, y: int) -> bool:
    p = run_adb(["shell", "input", "tap", str(int(x)), str(int(y))], capture_output=False)
    return p.returncode == 0


def adb_tap_randomized(center_x: int, center_y: int, w: int = 0, h: int = 0, jitter: int = 20) -> bool:
    # If width/height provided, choose random point inside bounding box centered at (center_x, center_y)
    if w > 0 and h > 0:
        left = center_x - w // 2
        top = center_y - h // 2
        x = random.randint(left + 1, left + w - 1)
        y = random.randint(top + 1, top + h - 1)
    else:
        x = int(center_x + random.randint(-jitter, jitter))
        y = int(center_y + random.randint(-jitter, jitter))
    return adb_tap(x, y)


def main():
    parser = argparse.ArgumentParser(description="ADB bot: capture screen, find template and tap")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--template", "-t", help="Path to template image (PNG/JPG)")
    group.add_argument("--templates-dir", "-d", help="Path to a directory with templates to try")
    parser.add_argument("--threshold", type=float, default=0.85, help="Match threshold (0-1)")
    parser.add_argument("--interval", type=float, default=1.0, help="Seconds between checks when looping")
    parser.add_argument("--loop", action="store_true", help="Keep searching and tapping in a loop")
    parser.add_argument("--once", action="store_true", help="Tap only once and exit after successful hit")
    parser.add_argument("--randomize", action="store_true", help="Randomize tap location within template area")
    parser.add_argument("--jitter", type=int, default=24, help="Pixel jitter for randomized taps when no template bbox available")
    parser.add_argument("--scale-min", type=float, default=0.8, help="Minimum template scale factor to try")
    parser.add_argument("--scale-max", type=float, default=1.2, help="Maximum template scale factor to try")
    parser.add_argument("--scale-steps", type=int, default=9, help="Number of scales to try between min and max")
    args = parser.parse_args()

    if not ensure_device_connected():
        sys.exit(1)

    if args.template:
        print("Starting. Template:", args.template)
    else:
        print("Starting. Templates dir:", args.templates_dir)

    try:
        while True:
            img = screencap_pil()
            if img is None:
                time.sleep(args.interval)
                continue
            screen_cv = pil_to_cv(img)
            found = None
            tpl_path = None
            if args.template:
                found = find_template(screen_cv, args.template, args.threshold, args.scale_min, args.scale_max, args.scale_steps)
                tpl_path = args.template
            else:
                res = find_template_in_dir(screen_cv, args.templates_dir, args.threshold, args.scale_min, args.scale_max, args.scale_steps)
                if res:
                    tpl_path, cx, cy, score, w_t, h_t = res
                    found = (cx, cy, score, w_t, h_t)

            if found:
                cx, cy, score, w_t, h_t = found
                print(f"Found template '{tpl_path or args.template}' at ({cx},{cy}) score={score:.3f}")
                if args.randomize:
                    ok = adb_tap_randomized(cx, cy, w_t, h_t, args.jitter)
                else:
                    ok = adb_tap(cx, cy)
                if not ok:
                    print("adb tap failed")
                if args.once:
                    break
                # safety: small randomized sleep after action
                time.sleep(0.5 + random.random() * 0.7)
            else:
                print("Template not found — waiting")
            if not args.loop and not args.once:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("Interrupted by user")


if __name__ == "__main__":
    main()
