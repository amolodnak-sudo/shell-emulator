import argparse
import base64
import getpass
import socket
import tkinter as tk
import xml.etree.ElementTree as et
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

    def _load_vfs(self, path):
        try:
            tree = et.parse(path)
            self.vfs_root = tree.getroot()
            print(f"[DEBUG] VFS успешно загружена: {path}")
        except FileNotFoundError:
            print(f"[ERROR] Файл VFS не найден: {path}")
        except et.ParseError as e:
            print(f"[ERROR] Ошибка парсинга XML: {e}")

    def _get_root_dir(self):
        if self.vfs_root is None:
            return None
        for d in self.vfs_root.findall("dir"):
            if d.get("name") == "/":
                return d
        return None

    def _get_prompt(self):
        user = getpass.getuser()
        host = socket.gethostname()
        return f"{user}@{host}:{self.cwd}$"

    def _make_absolute(self, path):
        if path.startswith("/"):
            return path
        base = "" if self.cwd == "/" else self.cwd
        return base + "/" + path

    def _normalize_path(self, path):
        absolute = self._make_absolute(path)
        stack = self._resolve_stack(absolute.split("/"))
        return "/" + "/".join(stack)

    def _resolve_stack(self, parts):
        stack = []
        for part in parts:
            self._apply_part(stack, part)
        return stack

    def _apply_part(self, stack, part):
        if part in ("", "."):
            return
        if part == "..":
            self._pop_safe(stack)
            return
        stack.append(part)

    def _pop_safe(self, stack):
        if stack:
            stack.pop()

    def _get_parent_path(self, abs_path):
        if abs_path == "/":
            return "/"
        parent = abs_path.rsplit("/", 1)[0]
        return parent if parent else "/"

    def _find_node(self, abs_path):
        root_dir = self._get_root_dir()
        if root_dir is None:
            return None, None
        if abs_path == "/":
            return root_dir, "dir"
        node = self._walk_path(root_dir, abs_path)
        if node is None:
            return None, None
        return node, node.tag

    def _walk_path(self, root, abs_path):
        current = root
        for part in abs_path.split("/"):
            if not part:
                continue
            current = self._find_child(current, part)
            if current is None:
                return None
        return current

    def _find_child(self, parent, name):
        for child in parent:
            if child.tag in ("dir", "file") and child.get("name") == name:
                return child
        return None

    def _read_file_content(self, node):
        encoded = node.get("content", "")
        if not encoded:
            return ""
        try:
            return base64.b64decode(encoded).decode("utf-8", errors="replace")
        except Exception:
            return ""

    def _setup_window(self):
        user = getpass.getuser()
        host = socket.gethostname()
        self.root.title(f"Эмулятор - [{user}@{host}]")
        self.root.geometry("700x500")
        self.root.configure(bg="black")

    def _setup_widgets(self):
        self.output = scrolledtext.ScrolledText(
            self.root, bg="black", fg="green",
            font=("Courier New", 12), state=tk.DISABLED, wrap=tk.WORD,
        )
        self.output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.input_field = tk.Entry(
            self.root, bg="black", fg="green",
            font=("Courier New", 12), insertbackground="green",
        )
        self.input_field.pack(fill=tk.X, padx=5, pady=(0, 5))
        self.input_field.bind("<Return>", self._on_enter)
        self.input_field.focus_set()

    def _show_welcome(self):
        user = getpass.getuser()
        host = socket.gethostname()
        self._print(
            f"Добро пожаловать, {user}@{host}!\n"
            "Введите 'help' для списка команд.\n\n"
        )

    def _print(self, text):
        self.output.configure(state=tk.NORMAL)
        self.output.insert(tk.END, text)
        self.output.see(tk.END)
        self.output.configure(state=tk.DISABLED)

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
            "tail": self._cmd_tail,
            "uniq": self._cmd_uniq,
            "rm": self._cmd_rm,
            "exit": self._cmd_exit,
            "help": self._cmd_help,
        }
        handler = handlers.get(cmd)
        if handler:
            handler(args)
            return
        self._print(f"Ошибка: команда '{cmd}' не найдена.\n")

    def _cmd_ls(self, args):
        if self.vfs_root is None:
            self._print("ls: VFS не загружена\n")
            return
        target = self._resolve_ls_target(args)
        node, kind = self._find_node(target)
        if node is None:
            self._print(f"ls: {target}: Нет такого файла или каталога\n")
            return
        self._print(self._format_ls_output(node, kind))

    def _resolve_ls_target(self, args):
        positional = self._get_positional_args(args)
        if positional:
            return self._normalize_path(positional[0])
        return self.cwd

    def _get_positional_args(self, args):
        result = []
        for a in args:
            if not a.startswith("-"):
                result.append(a)
        return result

    def _format_ls_output(self, node, kind):
        if kind == "file":
            return f"{node.get('name')}\n"
        names = self._collect_child_names(node)
        if not names:
            return "(пусто)\n"
        return "  ".join(names) + "\n"

    def _collect_child_names(self, node):
        result = []
        for child in node:
            if child.tag in ("dir", "file"):
                result.append(child.get("name", "?"))
        result.sort()
        return result

    def _cmd_cd(self, args):
        if self.vfs_root is None:
            self._print("cd: VFS не загружена\n")
            return
        target = self._resolve_cd_target(args)
        node, kind = self._find_node(target)
        error = self._get_cd_error(args, node, kind)
        if error:
            self._print(error)
            return
        self.cwd = target

    def _resolve_cd_target(self, args):
        if not args:
            return "/"
        return self._normalize_path(args[0])

    def _get_cd_error(self, args, node, kind):
        if node is None:
            name = args[0] if args else ""
            return f"cd: {name}: Нет такого файла или каталога\n"
        if kind != "dir":
            return f"cd: {args[0]}: Не является каталогом\n"
        return None

    def _cmd_tail(self, args):
        if self.vfs_root is None:
            self._print("tail: VFS не загружена\n")
            return
        n, filepath = self._parse_tail_args(args)
        node = self._require_file(filepath, "tail")
        if node is None:
            return
        content = self._read_file_content(node)
        self._print_last_lines(content, n)

    def _parse_tail_args(self, args):
        n = 10
        filepath = None
        i = 0
        while i < len(args):
            n, filepath, consumed = self._consume_tail_arg(args, i, n, filepath)
            i += consumed
        return n, filepath

    def _consume_tail_arg(self, args, i, n, filepath):
        arg = args[i]
        if arg == "-n":
            return self._consume_n_value(args, i, filepath)
        if self._is_numeric_flag(arg):
            return int(arg[1:]), filepath, 1
        return n, arg, 1

    def _consume_n_value(self, args, i, filepath):
        if i + 1 < len(args):
            return int(args[i + 1]), filepath, 2
        return 10, filepath, 1

    def _is_numeric_flag(self, arg):
        if not arg.startswith("-"):
            return False
        return arg[1:].isdigit()

    def _print_last_lines(self, content, n):
        for line in content.splitlines()[-n:]:
            self._print(line + "\n")

    def _cmd_uniq(self, args):
        if self.vfs_root is None:
            self._print("uniq: VFS не загружена\n")
            return
        show_count, filepath = self._parse_uniq_args(args)
        node = self._require_file(filepath, "uniq")
        if node is None:
            return
        content = self._read_file_content(node)
        self._print_uniq_result(content.splitlines(), show_count)

    def _parse_uniq_args(self, args):
        show_count = False
        filepath = None
        for a in args:
            if a == "-c":
                show_count = True
                continue
            if not a.startswith("-"):
                filepath = a
        return show_count, filepath

    def _print_uniq_result(self, lines, show_count):
        if not lines:
            return
        prev = lines[0]
        count = 1
        for line in lines[1:]:
            if line == prev:
                count += 1
                continue
            self._print_uniq_line(prev, count, show_count)
            prev = line
            count = 1
        self._print_uniq_line(prev, count, show_count)

    def _print_uniq_line(self, line, count, show_count):
        if show_count:
            self._print(f"{count:>4} {line}\n")
            return
        self._print(line + "\n")

    def _cmd_rm(self, args):
        if self.vfs_root is None:
            self._print("rm: VFS не загружена\n")
            return
        recursive, filepath = self._parse_rm_args(args)
        if filepath is None:
            self._print("rm: не указан файл или каталог\n")
            return
        target = self._normalize_path(filepath)
        error = self._get_rm_error(filepath, target, recursive)
        if error:
            self._print(error)
            return
        self._remove_node(target)

    def _parse_rm_args(self, args):
        recursive = False
        filepath = None
        for a in args:
            if a.startswith("-"):
                if "r" in a.lower():
                    recursive = True
                continue
            filepath = a
        return recursive, filepath

    def _get_rm_error(self, filepath, target, recursive):
        if target == "/":
            return "rm: нельзя удалить корневой каталог\n"
        node, kind = self._find_node(target)
        if node is None:
            return f"rm: {filepath}: Нет такого файла или каталога\n"
        if kind == "dir" and not recursive:
            return f"rm: {filepath}: Это каталог. Используйте -r\n"
        return None

    def _remove_node(self, target):
        node, _ = self._find_node(target)
        parent_path = self._get_parent_path(target)
        parent_node, _ = self._find_node(parent_path)
        if parent_node is None:
            self._print("rm: не удалось найти родительский каталог\n")
            return
        parent_node.remove(node)
        self._print(f"Удалён: {target}\n")

    def _require_file(self, filepath, cmd):
        if filepath is None:
            self._print(f"{cmd}: не указан файл\n")
            return None
        target = self._normalize_path(filepath)
        node, kind = self._find_node(target)
        if node is None:
            self._print(f"{cmd}: {filepath}: Нет такого файла или каталога\n")
            return None
        if kind != "file":
            self._print(f"{cmd}: {filepath}: Не является файлом\n")
            return None
        return node

    def _cmd_exit(self, args):
        self._print("Выход из эмулятора.\n")
        self.root.after(2000, self.root.destroy)

    def _cmd_help(self, args):
        self._print(
            "Доступные команды:\n"
            "  ls [путь]            — список файлов и каталогов\n"
            "  cd [путь]            — смена текущего каталога\n"
            "  uniq [-c] <файл>     — убрать подряд идущие дубликаты строк\n"
            "  tail [-n N] <файл>   — последние N строк файла (по умолч. 10)\n"
            "  rm [-r] <путь>       — удалить файл или каталог\n"
            "  exit                 — выход из эмулятора\n"
            "  help                 — эта справка\n"
        )

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
        self._execute_lines(lines)
        self._print("\n--- Выполнение стартового скрипта завершено ---\n")

    def _execute_lines(self, lines):
        for raw_line in lines:
            if self._execute_single_line(raw_line):
                return

    def _execute_single_line(self, raw_line):
        line = raw_line.strip()
        if self._should_skip_line(line):
            return False
        self._print(f"{self._get_prompt()} {line}\n")
        cmd, args = self._parse(line)
        if cmd is None:
            return False
        self._dispatch(cmd, args)
        return cmd == "exit"

    def _should_skip_line(self, line):
        if not line:
            return True
        return line.startswith("#")


def parse_args():
    parser = argparse.ArgumentParser(description="Эмулятор Shell (Вариант 17)")
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