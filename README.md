# Shell Emulator

Графический эмулятор командной строки UNIX-подобной ОС
на Python/tkinter. Реализованы Этапы 1–3 (REPL, Конфигурация, VFS).

---

## Требования к окружению
- **Python:** 3.10 или выше
- **ОС:** Windows / Linux / macOS
- **Библиотеки:** только стандартные (tkinter, argparse,
  xml.etree.ElementTree, pathlib)
- **Установка зависимостей не требуется**

---

## Структура проекта

```
shell-emulator/
├── src/
│ └── emulator.py # Основной код (GUI + логика + VFS)
├── tests/
│ ├── test_script.sh # Полный тест всех команд
│ ├── test_vfs_minimal.sh # Минимальный тест VFS
│ └── test_vfs_deep.sh # Тест глубоких уровней и ошибок
├── vfs/
│ └── vfs.xml # Виртуальная файловая система (XML)
├── run.bat # Скрипт запуска (Windows)
├── README.md # Документация
└── .gitignore
```
---

## Функции и настройки

### Общие функции
- GUI-интерфейс в стиле терминала (чёрный фон, зелёный текст).
- Заголовок окна формируется из реальных данных ОС:
  `[username@hostname]`.
- Простой парсер ввода по пробелам.
- Имитация диалога: каждая команда выводится с приглашением
  `user@host:/path$`, ниже — её результат.
- Обработка неизвестных команд с сообщением об ошибке.

### Настройки (параметры CLI)
| Параметр | Описание |
|---|---|
| `--vfs-path` | Путь к XML-файлу виртуальной ФС |
| `--script` | Путь к стартовому скрипту |

---

## Команды оболочки

| Команда | Описание |
|---|---|
| `ls [путь]` | Список файлов и каталогов |
| `cd [путь]` | Смена каталога. Поддерживает `.`, `..`, абсолютные и относительные пути |
| `help` | Справка по командам |
| `exit` | Выход из эмулятора |

### Обработка ошибок
- `cd` в несуществующую папку → «Нет такого файла или каталога»
- `cd` в файл → «Не является каталогом»
- Неизвестная команда → «Ошибка: команда '...' не найдена»

---

## Стартовый скрипт

Скрипт — это текстовый файл с командами (по одной на строку).

### Правила
- Поддерживаются комментарии: строки, начинающиеся с `#`.
- Пустые строки пропускаются.
- Каждая команда выводится в GUI с приглашением `user@host:/path$`,
  затем выполняется — **имитация диалога с пользователем**.
- По завершении выводится сообщение
  `--- Выполнение стартового скрипта завершено ---`.


## Стартовый скрипт

Скрипт — это текстовый файл с командами (по одной на строку).

### Правила
- Поддерживаются комментарии: строки, начинающиеся с `#`.
- Пустые строки пропускаются.
- Каждая команда выводится в GUI с приглашением `user@host:/path$`,
  затем выполняется — **имитация диалога с пользователем**.
- По завершении выводится сообщение
  `--- Выполнение стартового скрипта завершено ---`.

### Пример стартового скрипта (`tests/test_script.sh`)
Полный тест команд эмулятора
ls
cd /home/user
ls
cd documents
ls
cd ..
ls
cd /
ls /etc
cd /var/log
ls
unknown_command
help
exit


---

## Пример XML-файла VFS (`vfs/vfs.xml`)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<filesystem>
    <dir name="/">
        <dir name="home">
            <dir name="user">
                <dir name="documents">
                    <file name="report.txt" content="UmVwb3J0IGRhdGE=" />
                    <file name="notes.md" content="I1Rlc3Qgbm90ZXM=" />
                </dir>
                <file name="readme.txt" content="SGVsbG8gd29ybGQh" />
            </dir>
        </dir>
        <dir name="var">
            <dir name="log">
                <file name="syslog" content="TG9nIGZpbGUgZGF0YQ==" />
                <file name="auth.log" content="QXV0aCBkYXRh" />
            </dir>
        </dir>
        <dir name="etc">
            <file name="hosts" content="MTI3LjAuMC4xIGxvY2FsaG9zdA==" />
            <file name="passwd" content="cm9vdDp4OjA6MDpyb290Oi9yb290Oi9iaW4vYmFzaA==" />
        </dir>
        <dir name="tmp">
        </dir>
    </dir>
</filesystem>
```

### Правила XML
Корень — тег <filesystem>, внутри — <dir name="/">.
Папки: <dir name="имя">...</dir>.
Файлы: <file name="имя" content="base64"/>.
Содержимое файлов хранится в base64.

### Сборка и запуск
Через bat-файл (Windows)
run.bat


### Напрямую через Python

# Со стартовым скриптом
py src/emulator.py --vfs-path ./vfs/vfs.xml --script ./tests/test_script.sh

# Без стартового скрипта (интерактивный режим)
py src/emulator.py --vfs-path ./vfs/vfs.xml

## Запуск тестов в разных режимах
1. Интерактивный режим (ручной ввод)
py src/emulator.py --vfs-path ./vfs/vfs.xml
Команды вводятся вручную в поле ввода внизу окна GUI.

2. Автоматический режим (со скриптом)
py src/emulator.py --vfs-path ./vfs/vfs.xml --script ./tests/test_script.sh
Команды автоматически считываются из указанного файла.

3. Минимальный тест VFS
py src/emulator.py --vfs-path ./vfs/vfs.xml --script ./tests/test_vfs_minimal.sh
4. Тест глубоких уровней и ошибок
py src/emulator.py --vfs-path ./vfs/vfs.xml --script ./tests/test_vfs_deep.sh


### Логирование тестирования параметров командной строки
[DEBUG] Запуск эмулятора...
[DEBUG] Путь к VFS: ./vfs/vfs.xml
[DEBUG] Путь к стартовому скрипту: ./tests/test_script.sh
[DEBUG] VFS успешно загружена: ./vfs/vfs.xml
Если указанный путь не существует — выводится предупреждение:

[WARNING] Путь к VFS не существует: ./vfs/vfs.xml
[WARNING] Стартовый скрипт не найден: ./tests/missing.sh