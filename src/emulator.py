import getpass
import socket
import tkinter as tk
from tkinter import scrolledtext

class ShellEmulator:
    def __init__(self, root):
        self.root = root
        self._setup_window()
        self._setup_widgets()
        self._show_welcome()

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
        self._print(f"$ {raw}\n")

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
        self._print(f"[заглушка ls] аргументы: {args}\n")

    def _cmd_cd(self, args):
        self._print(f"[заглушка cd] аргументы: {args}\n")

    def _cmd_exit(self, args):
        self._print("Выход из эмулятора.\n")
        self.root.after(500, self.root.destroy)

    def _cmd_help(self, args):
        text = (
            "Доступные команды:\n"
            "  ls [аргументы]  — список файлов (заглушка)\n"
            "  cd [аргументы]  — смена директории (заглушка)\n"
            "  exit            — выход из эмулятора\n"
            "  help            — эта справка\n"
        )
        self._print(text)


if __name__ == "__main__":
    root = tk.Tk()
    app = ShellEmulator(root)
    root.mainloop()