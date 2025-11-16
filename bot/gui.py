import shlex
import subprocess
import sys
import threading
import queue
import time
import os
import traceback
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox


class BotGUI:
    def __init__(self, root):
        self.root = root
        root.title("Clash-Bot Controller")

        self.process = None
        self.thread = None
        self.queue = queue.Queue()

        style = ttk.Style()
        style.theme_use('default')
        main = ttk.Frame(root, padding=10)
        main.grid(sticky="nsew")

        # Command input + presets
        ttk.Label(main, text="Command:").grid(row=0, column=0, sticky="w")
        self.cmd_var = tk.StringVar()
        # Default command runs keyboard_deploy_flow with keys 1-8
        exe = sys.executable
        if ' ' in exe and not (exe.startswith('"') or exe.startswith("'")):
            exe = f'"{exe}"'
        default_cmd = f"{exe} -m bot.keyboard_deploy_flow --keys 1-8"
        self.cmd_var.set(default_cmd)
        self.cmd_entry = ttk.Entry(main, textvariable=self.cmd_var, width=80)
        self.cmd_entry.grid(row=0, column=1, columnspan=2, sticky="we", pady=4)

        # Presets dropdown
        presets = {
            'Keyboard deploy (1-8)': default_cmd,
            'Attack flow (templates)': f"{sys.executable} -m bot.attack_flow --attack-dir templates\\attack_buttons --end-dir templates\\end_screens",
            'ADB template test': f"{sys.executable} -m bot.adb_bot --templates-dir templates --loop"
        }
        self.preset_var = tk.StringVar()
        self.preset_menu = ttk.Combobox(main, textvariable=self.preset_var, values=list(presets.keys()), state='readonly', width=28)
        self.preset_menu.grid(row=0, column=3, sticky='we', padx=(6,0))
        self.preset_menu.set('Keyboard deploy (1-8)')
        def on_preset(evt=None):
            key = self.preset_var.get()
            self.cmd_var.set(presets.get(key, default_cmd))
        self.preset_menu.bind('<<ComboboxSelected>>', on_preset)
        
        # Quick preset start buttons
        def preset_start(key):
            cmd = presets.get(key, default_cmd)
            self.cmd_var.set(cmd)
            self.start()

        preset_frame = ttk.Frame(main)
        preset_frame.grid(row=1, column=0, columnspan=4, sticky='w', pady=(4,0))
        ttk.Button(preset_frame, text='Start Keyboard Deploy', command=lambda: preset_start('Keyboard deploy (1-8)')).grid(row=0, column=0, padx=2)
        ttk.Button(preset_frame, text='Start Attack Flow', command=lambda: preset_start('Attack flow (templates)')).grid(row=0, column=1, padx=2)
        ttk.Button(preset_frame, text='Start ADB Test', command=lambda: preset_start('ADB template test')).grid(row=0, column=2, padx=2)

        # Start / Stop buttons and status
        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=1, column=0, columnspan=4, sticky='we', pady=(6,0))
        self.start_btn = ttk.Button(btn_frame, text="Start", command=self.start, width=12)
        self.start_btn.grid(row=0, column=0, padx=4)
        self.stop_btn = ttk.Button(btn_frame, text="Stop", command=self.stop, state="disabled", width=12)
        self.stop_btn.grid(row=0, column=1, padx=4)
        self.clear_btn = ttk.Button(btn_frame, text="Clear Log", command=self.clear_log, width=12)
        self.clear_btn.grid(row=0, column=2, padx=4)
        self.status_var = tk.StringVar(value='Stopped')
        self.status_lbl = ttk.Label(btn_frame, textvariable=self.status_var, foreground='red')
        self.status_lbl.grid(row=0, column=3, padx=8)

        # Log display
        # Log display (monospace)
        mono_font = ('Consolas', 10) if sys.platform == 'win32' else ('Courier', 11)
        self.log_text = tk.Text(main, width=100, height=30, wrap="none", font=mono_font, bg='#1e1e1e', fg='#dcdcdc')
        self.log_text.grid(row=2, column=0, columnspan=4, sticky="nsew", pady=(8, 0))
        self.log_text.configure(state="disabled")

        # Scrollbars
        yscr = ttk.Scrollbar(main, orient="vertical", command=self.log_text.yview)
        yscr.grid(row=2, column=4, sticky="nsw")
        self.log_text['yscrollcommand'] = yscr.set

        # Resize behavior
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)
        main.columnconfigure(2, weight=0)
        main.columnconfigure(3, weight=0)
        main.rowconfigure(2, weight=1)

        # Periodic queue poll
        self.root.after(150, self.poll_queue)

    def append_log(self, text: str):
        ts = time.strftime('%H:%M:%S')
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{ts}] {text}")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def start(self):
        if self.process is not None:
            messagebox.showinfo("Info", "Bot já em execução")
            return
        cmdline = self.cmd_var.get().strip()
        if not cmdline:
            messagebox.showwarning("Aviso", "Comando vazio")
            return
        try:
            parts = shlex.split(cmdline)
        except Exception:
            parts = cmdline.split()

        # Start subprocess, capture stdout/stderr
        self.append_log(f"[GUI] Iniciando processo: {cmdline}\n")
        try:
            self.append_log(f"[GUI] CWD: {os.getcwd()}\n")
            # Ensure the first token (executable) is quoted if it contains spaces and not already quoted
            parts = cmdline.strip().split()
            if parts:
                first = parts[0]
                if ' ' in first and not (first.startswith('"') or first.startswith("'")):
                    cmdline = cmdline.replace(first, f'"{first}"', 1)
            # Use shell=True for compatibility on Windows while ensuring executable is quoted
            self.process = subprocess.Popen(cmdline, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1, text=True, shell=True)
        except Exception as e:
            tb = traceback.format_exc()
            messagebox.showerror("Erro", f"Falha ao iniciar o processo: {e}")
            self.append_log(f"[GUI] Falha ao iniciar o processo: {e}\n{tb}\n")
            self.process = None
            return
        self.status_var.set('Running')
        self.status_lbl.configure(foreground='green')

        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")

        # Start reader thread
        self.thread = threading.Thread(target=self._reader_thread, daemon=True)
        self.thread.start()
        self.append_log(f"[GUI] Processo iniciado: {cmdline}\n")

    def stop(self):
        if not self.process:
            return
        self.append_log("[GUI] Parando processo...\n")
        try:
            self.process.terminate()
            # wait a short while
            gone, alive = self.process.wait(timeout=3), None
        except Exception:
            try:
                self.process.kill()
            except Exception:
                pass
        self.process = None
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.status_var.set('Stopped')
        self.status_lbl.configure(foreground='red')

    def _reader_thread(self):
        proc = self.process
        try:
            for line in proc.stdout:
                self.queue.put(line)
        except Exception:
            pass
        finally:
            # Ensure process finished
            try:
                rc = proc.wait()
                self.queue.put(f"[GUI] Processo finalizado (rc={rc})\n")
            except Exception:
                self.queue.put("[GUI] Processo finalizado\n")
            # update UI state
            self.queue.put("__PROCESS_EXIT__")

    def poll_queue(self):
        try:
            while True:
                item = self.queue.get_nowait()
                if item == "__PROCESS_EXIT__":
                    self.process = None
                    self.start_btn.configure(state="normal")
                    self.stop_btn.configure(state="disabled")
                    self.status_var.set('Stopped')
                    self.status_lbl.configure(foreground='red')
                else:
                    self.append_log(item)
        except queue.Empty:
            pass
        self.root.after(200, self.poll_queue)


def run_gui():
    root = tk.Tk()
    app = BotGUI(root)
    root.mainloop()


if __name__ == "__main__":
    run_gui()
