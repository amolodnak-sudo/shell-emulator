import argparse
import tkinter as tk
import socket
import getpass
import xml.etree.ElementTree as et       # ← ДОБАВИТЬ (было: import os — удаляем, не нужен)
from pathlib import Path
from tkinter import scrolledtext


class ShellEmulator:
    def __init__(self, root, vfs_path=None, script_path=None):
        self.root = root
        self.vfs_path = vfs_path
        self.script_path = script_path
        self.cwd = "/"
        self.vfs_root = None

        if self.vfs_path:
            self._load_vfs(self.vfs_path)

        self._setup_window()
        self._setup_widgets()
        self._show_welcome()

        if self.script_path:
            self._run_startup_script()

    # ---------- VFS ----------

    def _load_vfs(self, path):
        try:
            tree = et.parse(path)
            self.vfs_root = tree.getroot()
            print(f"[DEBUG] VFS успешно загружена: {path}")
        except FileNotFoundError:
            print(f"[ERROR] Файл VFS не найден: {path}")
            self.vfs_root = None
        except et.ParseError as e:
            print(f"[ERROR] Ошибка парсинга XML: {e}")
            self.vfs_root = None

    def _get_root_dir(self):
        if self.vfs_root is None:
            return None
        for d in self.vfs_root.findall("dir"):
            if d.get("name") == "/":
                return d
        return None

    def _normalize_path(self, path):
        if not path.startswith("/"):
            if self.cwd == "/":
                path = "/" + path
            else:
                path = self.cwd + "/" + path

        stack = []
        for part in path.split("/"):
            if part in ("", "."):
                continue
            if part == "..":
                if stack:
                    stack.pop()
            else:
                stack.append(part)

        return "/" + "/".join(stack)

    def _find_node(self, abs_path):
        root_dir = self._get_root_dir()
        if root_dir is None:
            return None, None

        if abs_path == "/":
            return root_dir, "dir"

        parts = [p for p in abs_path.split("/") if p]
        current = root_dir
        for part in parts:
            found = None
            for child in current:
                if child.tag in ("dir", "file") and child.get("name") == part:
                    found = child
                    break
            if found is None:
                return None, None
            current = found

        return current, current.tag

    def _get_prompt(self):
        user = getpass.getuser()
        host = socket.gethostname()
        return f"{user}@{host}:{self.cwd}$"

    def _run_startup_script(self):
        script_path = Path(self.script_path)
        if not script_path.exists():
            self._print(f"Ошибка: стартовый скрипт не найден: {script_path}\n")
            return
        try:
            lines = script_path.read_text(encoding="utf-8-sig").splitlines()
        except Exception as e:
            self._print(f"Ошибка чтения скрипта: {e}\n")
            return

        for line_number, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()

            if not line or line.startswith("#"):
                continue
            self._print(f"{self._get_prompt()} {line}\n")
            cmd, args = self._parse(line)

            if cmd is None:
                continue
            self._dispatch(cmd, args)

            if cmd == "exit":
                break

        self._print("\n--- Выполнение стартового скрипта завершено ---\n")
    def _setup_window(self):
        user = getpass.getuser()
        host = socket.gethostname()
        title = f"Эмулятор - [{user}@{host}]"
        self.root.title(title)
        self.root.geometry("700x500")
        self.root.configure(bg="black")

    def _setup_widgets(self):
        self.output = scrolledtext.ScrolledText(
            self.root,
            bg="black",
            fg="green",
            font=("Courier New", 12),
            state=tk.DISABLED,
            wrap=tk.WORD,
        )
        self.output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.input_field = tk.Entry(
            self.root,
            bg="black",
            fg="green",
            font=("Courier New", 12),
            insertbackground="green",
        )
        self.input_field.pack(fill=tk.X, padx=5, pady=(0, 5))
        self.input_field.bind("<Return>", self._on_enter)
        self.input_field.focus_set()

    def _show_welcome(self):
        user = getpass.getuser()
        host = socket.gethostname()
        msg = (
            f"Добро пожаловать, {user}@{host}!\n"
            "Введите 'help' для списка команд.\n\n"
        )
        self._print(msg)

    def _on_enter(self, event):
        raw = self.input_field.get()
        self.input_field.delete(0, tk.END)
        self._print(f"{self._get_prompt()} {raw}\n")
        cmd, args = self._parse(raw)
        if cmd is None:
            return
        self._dispatch(cmd, args)

    @staticmethod
    def _parse(raw_input):
        parts = raw_input.strip().split()
        if not parts:
            return None, []
        return parts[0], parts[1:]

    def _dispatch(self, cmd, args):
        handlers = {
            "ls": self._cmd_ls,
            "cd": self._cmd_cd,
            "exit": self._cmd_exit,
            "help": self._cmd_help,
        }
        handler = handlers.get(cmd)
        if handler:
            handler(args)
        else:
            self._print(f"Ошибка: команда '{cmd}' не найдена.\n")

    def _print(self, text):
        self.output.configure(state=tk.NORMAL)
        self.output.insert(tk.END, text)
        self.output.see(tk.END)
        self.output.configure(state=tk.DISABLED)

    def _cmd_ls(self, args):
        if self.vfs_root is None:
            self._print("ls: VFS не загружена\n")
            return

        positional = [a for a in args if not a.startswith("-")]
        target = self._normalize_path(positional[0]) if positional else self.cwd
        node, kind = self._find_node(target)

        if node is None:
            self._print(f"ls: {positional[0] if positional else target}: "
                        f"Нет такого файла или каталога\n")
            return

        if kind == "file":
            self._print(f"{node.get('name')}\n")
            return

        names = sorted(
            child.get("name", "?")
            for child in node
            if child.tag in ("dir", "file")
        )
        if names:
            self._print("  ".join(names) + "\n")
        else:
            self._print("(пусто)\n")

    def _cmd_cd(self, args):
        if self.vfs_root is None:
            self._print("cd: VFS не загружена\n")
            return

        target = self._normalize_path(args[0]) if args else "/"
        node, kind = self._find_node(target)

        if node is None:
            self._print(f"cd: {args[0] if args else ''}: "
                        f"Нет такого файла или каталога\n")
            return
        if kind != "dir":
            self._print(f"cd: {args[0]}: Не является каталогом\n")
            return

        self.cwd = target

    def _cmd_exit(self, args):
        self._print("Выход из эмулятора.\n")
        self.root.after(2000, self.root.destroy)

    def _cmd_help(self, args):
        self._print(
            "Доступные команды:\n"
            "  ls [путь]   — список файлов и каталогов\n"
            "  cd [путь]   — смена текущего каталога\n"
            "  exit        — выход из эмулятора\n"
            "  help        — эта справка\n"
        )

def parse_args():
    parser = argparse.ArgumentParser(description="Эмулятор Shell")
    parser.add_argument("--vfs-path", type=str, help="Путь к XML-файлу VFS")
    parser.add_argument("--script", type=str, help="Путь к стартовому скрипту")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    print("[DEBUG] Запуск эмулятора...")
    print(f"[DEBUG] Путь к VFS: {args.vfs_path}")
    print(f"[DEBUG] Путь к стартовому скрипту: {args.script}")

    if args.vfs_path and not Path(args.vfs_path).exists():
        print(f"[WARNING] Путь к VFS не существует: {args.vfs_path}")
    if args.script and not Path(args.script).exists():
        print(f"[WARNING] Стартовый скрипт не найден: {args.script}")

    root = tk.Tk()
    app = ShellEmulator(root, vfs_path=args.vfs_path, script_path=args.script)
    root.mainloop()