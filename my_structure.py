import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class StructureChecker:
    """Класс для проверки структуры проекта."""

    def __init__(self, root_path: Path, show_hidden: bool = True, max_depth: int = 10):
        self.root_path = root_path.resolve()
        self.show_hidden = show_hidden
        self.max_depth = max_depth
        self.structure_lines: List[str] = []

        # Только самые необходимые директории для игнорирования
        self.ignore_dirs = {
            '__pycache__', '.git', '.pytest_cache', '.ruff_cache',
            'mypy_cache', '.idea', '.vscode', '.mypy_cache',
            'node_modules', 'venv', 'virtualenv',
            'logs', 'staticfiles', '__pycache__', '.venv'  # Добавлен .venv
        }

        # Не игнорируем никакие файлы, кроме бинарных
        self.ignore_files = {
            '.DS_Store', 'Thumbs.db', 'desktop.ini'
        }

        # Расширения бинарных файлов (не показываем содержимое, но показываем сами файлы)
        self.binary_extensions = {
            '.pyc', '.pyo', '.so', '.dll', '.dylib', '.exe',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico',
            '.mp3', '.mp4', '.avi', '.mov', '.pdf', '.zip', '.tar', '.gz',
            '.lock', '.db'
        }

    def should_ignore_dir(self, dir_path: Path) -> bool:
        """Проверяет, нужно ли игнорировать директорию."""
        dir_name = dir_path.name

        # Игнорируем только указанные служебные директории
        if dir_name in self.ignore_dirs:
            return True

        # Показываем скрытые директории (включая .venv, но он уже в ignore_dirs)
        # Скрытые директории НЕ игнорируем, если show_hidden=True (по умолчанию)
        if not self.show_hidden and dir_name.startswith('.'):
            return True

        return False

    def should_ignore_file(self, file_path: Path) -> bool:
        """Проверяет, нужно ли игнорировать файл."""
        file_name = file_path.name

        # Игнорируем только системные файлы
        if file_name in self.ignore_files:
            return True

        # Показываем все файлы, включая .env, .gitignore и т.д.
        # Не игнорируем скрытые файлы
        return False

    def format_size(self, size: int) -> str:
        """Форматирует размер файла."""
        if size == 0:
            return "0 B"

        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

    def collect_structure(self, path: Optional[Path] = None, prefix: str = "",
                          level: int = 0):
        """Рекурсивный сбор актуальной структуры проекта."""
        if path is None:
            path = self.root_path
            # Показываем корневую директорию
            self.structure_lines.append(f"{path.name}/")
            prefix = "    "
            level = 0

        # Проверяем максимальную глубину
        if level >= self.max_depth:
            if any(path.iterdir()):
                self.structure_lines.append(f"{prefix}    ... (еще содержимое)")
            return

        try:
            # Получаем все элементы в директории
            items = []
            for item in sorted(path.iterdir()):
                if item.is_dir():
                    if not self.should_ignore_dir(item):
                        items.append(item)
                else:  # файл
                    if not self.should_ignore_file(item):
                        items.append(item)

            # Обрабатываем каждый элемент
            for i, item in enumerate(items):
                is_last_item = (i == len(items) - 1)
                connector = "└── " if is_last_item else "├── "

                if item.is_dir():
                    # Отображаем директорию
                    self.structure_lines.append(f"{prefix}{connector}{item.name}/")

                    # Рекурсивно обрабатываем поддиректорию
                    next_prefix = prefix + ("    " if is_last_item else "│   ")
                    self.collect_structure(item, next_prefix, level + 1)
                else:
                    # Отображаем файл с размером
                    try:
                        size = item.stat().st_size
                        size_str = self.format_size(size)
                        self.structure_lines.append(f"{prefix}{connector}{item.name} ({size_str})")
                    except (PermissionError, OSError):
                        self.structure_lines.append(f"{prefix}{connector}{item.name} (доступ запрещен)")

        except PermissionError:
            self.structure_lines.append(f"{prefix}    ⚠️ Нет доступа к директории")

    def count_items(self) -> Dict[str, int]:
        """Подсчитывает количество файлов и директорий в структуре."""
        files_count = 0
        dirs_count = 0

        for line in self.structure_lines:
            # Строки директорий (заканчиваются на /)
            if line.strip().endswith('/'):
                dirs_count += 1
            # Строки файлов (содержат размер в скобках)
            elif ' (' in line and line.strip().endswith(')'):
                files_count += 1

        return {'files': files_count, 'dirs': dirs_count}

    def save_to_file(self, output_file: Path):
        """Сохраняет структуру в файл."""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("STRUCTURE OF PROJECT\n")
            f.write(f"Path: {self.root_path}\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Show hidden: {'Yes' if self.show_hidden else 'No'}\n")
            f.write(f"Max depth: {self.max_depth}\n")
            f.write("=" * 80 + "\n\n")
            f.write("\n".join(self.structure_lines))
            f.write("\n\n" + "=" * 80 + "\n")

            stats = self.count_items()
            f.write("STATISTICS:\n")
            f.write(f"  Directories: {stats['dirs']}\n")
            f.write(f"  Files: {stats['files']}\n")
            f.write(f"  Total: {stats['dirs'] + stats['files']}\n")
            f.write("=" * 80 + "\n")

    def print_structure(self, max_lines: int = 1000):
        """Выводит структуру в консоль."""
        print("\n".join(self.structure_lines[:max_lines]))
        if len(self.structure_lines) > max_lines:
            print(f"\n... and {len(self.structure_lines) - max_lines} more lines")


def main():
    """Основная функция."""
    parser = argparse.ArgumentParser(description='Project Structure Analysis')
    parser.add_argument('path', nargs='?', default='.',
                        help='Path to project (default: current directory)')
    parser.add_argument('--hidden', action='store_true', default=True,
                        help='Show hidden files and directories (default: True)')
    parser.add_argument('--depth', type=int, default=10,
                        help='Maximum depth (default: 10)')
    parser.add_argument('--output', '-o', type=str, default='project_structure.txt',
                        help='Output file name (default: project_structure.txt)')
    parser.add_argument('--no-hidden', action='store_true',
                        help='Hide hidden files and directories')

    args = parser.parse_args()

    # Если указан --no-hidden, то скрываем скрытые файлы
    show_hidden = not args.no_hidden

    # Определяем путь к проекту
    project_path = Path(args.path).resolve()

    if not project_path.exists():
        print(f"Error: Path {project_path} does not exist!")
        return

    print("=" * 60)
    print("Project Structure Analysis")
    print("=" * 60)
    print(f"Path: {project_path}")
    print(f"Settings: depth={args.depth}, hidden={'Yes' if show_hidden else 'No'}")
    print("=" * 60)
    print()

    # Собираем структуру
    checker = StructureChecker(project_path, show_hidden=show_hidden, max_depth=args.depth)
    checker.collect_structure()

    # Выводим структуру
    checker.print_structure()

    # Сохраняем в файл
    output_file = project_path / args.output
    checker.save_to_file(output_file)
    print(f"\n[OK] Full structure saved to: {output_file}")

    # Статистика
    stats = checker.count_items()
    print("\n" + "=" * 60)
    print("STATISTICS:")
    print(f"  Directories: {stats['dirs']}")
    print(f"  Files: {stats['files']}")
    print(f"  Total: {stats['dirs'] + stats['files']}")
    print("=" * 60)


if __name__ == '__main__':
    main()
