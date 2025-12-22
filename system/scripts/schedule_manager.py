#!/usr/bin/env python3
"""
Центральный скрипт для управления расписанием задач plan_expo.

Команды:
- setup: Создать/обновить crontab
- status: Показать текущее расписание
- enable: Включить автоматизацию
- disable: Отключить автоматизацию
- run <task>: Запустить задачу вручную
- list: Показать все доступные задачи

Использование:
  python scripts/schedule_manager.py setup
  python scripts/schedule_manager.py status
  python scripts/schedule_manager.py run daily
  python scripts/schedule_manager.py list
"""

import subprocess
import sys
import argparse
from pathlib import Path
import sys

# Добавить system/scripts в sys.path для импорта config_loader
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from config_loader import get_project_root, get_path
from datetime import datetime
import yaml
import tempfile
import os

# Пути
PROJECT_ROOT = get_project_root()
CONFIG_FILE = PROJECT_ROOT / "config"  # config всегда в корне / "schedule.yaml"
LOGS_DIR = get_path("logs") / "cron"

# Маркеры для crontab
CRON_MARKER_START = "# BEGIN plan_expo automation"
CRON_MARKER_END = "# END plan_expo automation"


def load_config():
    """Загрузить конфигурацию."""
    if not CONFIG_FILE.exists():
        print(f"❌ Конфигурация не найдена: {CONFIG_FILE}")
        sys.exit(1)

    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_current_crontab():
    """Получить текущий crontab."""
    try:
        result = subprocess.run(
            ['crontab', '-l'],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            return result.stdout
        else:
            # Crontab пуст или не существует
            return ""
    except Exception as e:
        print(f"❌ Ошибка чтения crontab: {e}")
        return ""


def remove_plan_expo_entries(crontab_content):
    """Удалить существующие записи plan_expo из crontab."""
    lines = crontab_content.split('\n')
    new_lines = []
    skip = False

    for line in lines:
        if CRON_MARKER_START in line:
            skip = True
            continue
        if CRON_MARKER_END in line:
            skip = False
            continue
        if not skip:
            new_lines.append(line)

    # Удалить пустые строки в конце
    while new_lines and not new_lines[-1].strip():
        new_lines.pop()

    return '\n'.join(new_lines)


def time_to_cron(time_str):
    """Конвертировать время HH:MM в cron формат (минуты часы)."""
    hour, minute = time_str.split(':')
    return f"{minute} {hour}"


def generate_cron_entries(config):
    """Сгенерировать cron записи из конфигурации."""
    entries = []
    python_path = config['schedule'].get('python_path', 'python3')
    project_root = config['schedule'].get('project_root', str(PROJECT_ROOT))
    log_dir = LOGS_DIR

    # Создать директорию для логов
    log_dir.mkdir(parents=True, exist_ok=True)

    entries.append(CRON_MARKER_START)
    entries.append(f"# Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    entries.append(f"# Project: {project_root}")
    entries.append("")

    # Утренняя рефлексия
    if config.get('daily', {}).get('morning_reflection', {}).get('enabled', False):
        task = config['daily']['morning_reflection']
        cron_time = time_to_cron(task['time'])
        script_path = Path(project_root) / task['script']
        log_file = log_dir / "morning_reflection.log"

        entries.append(f"# {task['description']}")
        entries.append(f"{cron_time} * * * cd {project_root} && {python_path} {script_path} >> {log_file} 2>&1")
        entries.append("")

    # Вечерний конвейер
    if config.get('daily', {}).get('evening_pipeline', {}).get('enabled', False):
        entries.append("# Evening pipeline")
        for task in config['daily']['evening_pipeline']['tasks']:
            cron_time = time_to_cron(task['time'])
            script_path = Path(project_root) / task['script']
            log_file = log_dir / f"{task['name']}.log"

            args = ' '.join(task.get('args', []))
            cmd = f"{python_path} {script_path} {args}".strip()

            entries.append(f"# {task['description']}")
            entries.append(f"{cron_time} * * * cd {project_root} && {cmd} >> {log_file} 2>&1")

        entries.append("")

    # Еженедельные задачи
    if config.get('weekly', {}).get('enabled', False):
        entries.append("# Weekly tasks (Sunday)")
        day = config['weekly'].get('day', 0)

        for task in config['weekly']['tasks']:
            cron_time = time_to_cron(task['time'])
            script_path = Path(project_root) / task['script']
            log_file = log_dir / f"{task['name']}.log"

            args = ' '.join(task.get('args', []))
            cmd = f"{python_path} {script_path} {args}".strip()

            entries.append(f"# {task['description']}")
            entries.append(f"{cron_time} * * {day} cd {project_root} && {cmd} >> {log_file} 2>&1")

        entries.append("")

    # Проверки здоровья
    if config.get('health_checks', {}).get('enabled', False):
        task = config['health_checks']
        script_path = Path(project_root) / task['script']
        log_file = log_dir / "health_check.log"

        args = ' '.join(task.get('args', []))
        cmd = f"{python_path} {script_path} {args}".strip()

        entries.append(f"# {task['description']}")
        entries.append(f"0 * * * * cd {project_root} && {cmd} >> {log_file} 2>&1")
        entries.append("")

    entries.append(CRON_MARKER_END)

    return '\n'.join(entries)


def install_crontab(config):
    """Установить crontab с записями plan_expo."""
    # Получить текущий crontab
    current_crontab = get_current_crontab()

    # Удалить старые записи plan_expo
    cleaned_crontab = remove_plan_expo_entries(current_crontab)

    # Сгенерировать новые записи
    new_entries = generate_cron_entries(config)

    # Объединить
    if cleaned_crontab.strip():
        new_crontab = cleaned_crontab + '\n\n' + new_entries
    else:
        new_crontab = new_entries

    # Записать через временный файл
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.cron') as f:
        f.write(new_crontab)
        f.write('\n')
        temp_file = f.name

    try:
        # Установить crontab
        result = subprocess.run(
            ['crontab', temp_file],
            capture_output=True,
            text=True,
            check=True
        )
        print("✅ Crontab успешно установлен")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка установки crontab: {e.stderr}")
        return False
    finally:
        # Удалить временный файл
        Path(temp_file).unlink(missing_ok=True)


def remove_crontab():
    """Удалить записи plan_expo из crontab."""
    current_crontab = get_current_crontab()
    cleaned_crontab = remove_plan_expo_entries(current_crontab)

    if cleaned_crontab.strip():
        # Есть другие записи, обновить crontab
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.cron') as f:
            f.write(cleaned_crontab)
            f.write('\n')
            temp_file = f.name

        try:
            subprocess.run(['crontab', temp_file], check=True)
            print("✅ Записи plan_expo удалены из crontab")
        finally:
            Path(temp_file).unlink(missing_ok=True)
    else:
        # Crontab будет пустой, удалить полностью
        try:
            subprocess.run(['crontab', '-r'], check=True)
            print("✅ Crontab полностью удален (был пустой)")
        except subprocess.CalledProcessError:
            print("⚠️ Crontab уже пустой")


def show_status():
    """Показать статус расписания."""
    current_crontab = get_current_crontab()

    if CRON_MARKER_START in current_crontab:
        print("✅ Автоматизация plan_expo: ВКЛЮЧЕНА\n")

        # Извлечь записи plan_expo
        lines = current_crontab.split('\n')
        in_section = False
        entries = []

        for line in lines:
            if CRON_MARKER_START in line:
                in_section = True
                continue
            if CRON_MARKER_END in line:
                break
            if in_section and line.strip():
                entries.append(line)

        print("Запланированные задачи:")
        print("-" * 80)
        for entry in entries:
            print(entry)
        print("-" * 80)
    else:
        print("❌ Автоматизация plan_expo: ОТКЛЮЧЕНА")
        print("\nДля включения выполните:")
        print("  python scripts/schedule_manager.py setup")


def list_tasks(config):
    """Показать все доступные задачи."""
    print("Доступные задачи для ручного запуска:\n")

    # Дневные задачи
    print("ЕЖЕДНЕВНЫЕ ЗАДАЧИ:")
    if config.get('daily', {}).get('morning_reflection', {}).get('enabled', False):
        task = config['daily']['morning_reflection']
        print(f"  - morning_reflection: {task['description']}")

    if config.get('daily', {}).get('evening_pipeline', {}).get('enabled', False):
        for task in config['daily']['evening_pipeline']['tasks']:
            print(f"  - {task['name']}: {task['description']}")

    # Недельные задачи
    print("\nЕЖЕНЕДЕЛЬНЫЕ ЗАДАЧИ:")
    if config.get('weekly', {}).get('enabled', False):
        for task in config['weekly']['tasks']:
            print(f"  - {task['name']}: {task['description']}")

    # Проверки
    print("\nПРОВЕРКИ:")
    if config.get('health_checks', {}).get('enabled', False):
        task = config['health_checks']
        print(f"  - health_check: {task['description']}")

    # Группы
    print("\nГРУППЫ ЗАДАЧ:")
    print("  - daily: Запустить весь вечерний конвейер")
    print("  - weekly: Запустить все недельные задачи")

    print("\nИспользование:")
    print("  python scripts/schedule_manager.py run <task_name>")
    print("  python scripts/schedule_manager.py run daily")


def run_task(task_name, config):
    """Запустить задачу вручную."""
    python_path = config['schedule'].get('python_path', 'python3')
    project_root = Path(config['schedule'].get('project_root', str(PROJECT_ROOT)))

    # Поиск задачи в конфигурации
    task_found = False
    tasks_to_run = []

    # Группа: daily
    if task_name == 'daily':
        if config.get('daily', {}).get('evening_pipeline', {}).get('enabled', False):
            tasks_to_run = config['daily']['evening_pipeline']['tasks']
            task_found = True

    # Группа: weekly
    elif task_name == 'weekly':
        if config.get('weekly', {}).get('enabled', False):
            tasks_to_run = config['weekly']['tasks']
            task_found = True

    # Одиночная задача
    else:
        # Проверить в morning_reflection
        if config.get('daily', {}).get('morning_reflection', {}).get('enabled', False):
            if task_name == 'morning_reflection':
                tasks_to_run = [config['daily']['morning_reflection']]
                task_found = True

        # Проверить в evening_pipeline
        if config.get('daily', {}).get('evening_pipeline', {}).get('enabled', False):
            for task in config['daily']['evening_pipeline']['tasks']:
                if task['name'] == task_name:
                    tasks_to_run = [task]
                    task_found = True
                    break

        # Проверить в weekly
        if config.get('weekly', {}).get('enabled', False):
            for task in config['weekly']['tasks']:
                if task['name'] == task_name:
                    tasks_to_run = [task]
                    task_found = True
                    break

        # Проверить в health_checks
        if task_name == 'health_check' and config.get('health_checks', {}).get('enabled', False):
            tasks_to_run = [config['health_checks']]
            task_found = True

    if not task_found:
        print(f"❌ Задача '{task_name}' не найдена")
        print("\nИспользуйте 'list' для просмотра доступных задач:")
        print("  python scripts/schedule_manager.py list")
        sys.exit(1)

    # Запустить задачи
    print(f"Запуск задачи: {task_name}\n")

    for task in tasks_to_run:
        script_path = project_root / task['script']
        args = task.get('args', [])

        cmd = [python_path, str(script_path)] + args

        print(f"Выполнение: {task.get('description', task.get('name', 'Unknown'))}")
        print(f"  Команда: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                cwd=project_root,
                capture_output=False,
                text=True,
                check=False
            )

            if result.returncode == 0:
                print(f"  ✅ Успешно\n")
            else:
                print(f"  ❌ Ошибка (код выхода: {result.returncode})\n")

        except Exception as e:
            print(f"  ❌ Ошибка выполнения: {e}\n")


def main():
    """Главная функция."""
    parser = argparse.ArgumentParser(
        description='Управление расписанием задач plan_expo',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s setup          # Установить crontab
  %(prog)s status         # Показать статус
  %(prog)s enable         # Включить автоматизацию
  %(prog)s disable        # Отключить автоматизацию
  %(prog)s list           # Показать все задачи
  %(prog)s run daily      # Запустить вечерний конвейер
  %(prog)s run weekly     # Запустить недельные задачи
        """
    )

    parser.add_argument(
        'command',
        choices=['setup', 'status', 'enable', 'disable', 'list', 'run'],
        help='Команда для выполнения'
    )

    parser.add_argument(
        'task',
        nargs='?',
        help='Название задачи для команды run'
    )

    args = parser.parse_args()

    # Загрузить конфигурацию
    config = load_config()

    # Выполнить команду
    if args.command == 'setup' or args.command == 'enable':
        print("Установка расписания plan_expo...\n")
        if install_crontab(config):
            print("\n📅 Расписание установлено:")
            print("  - Утро (07:00): Генерация рефлексии")
            print("  - Вечер (21:00-21:30): Анализ и дашборды")
            print("  - Воскресенье (22:00): Недельный дашборд")
            print("\nЛоги сохраняются в: logs/cron/")
            print("\nДля просмотра расписания:")
            print("  python scripts/schedule_manager.py status")

    elif args.command == 'disable':
        print("Отключение автоматизации plan_expo...\n")
        remove_crontab()

    elif args.command == 'status':
        show_status()

    elif args.command == 'list':
        list_tasks(config)

    elif args.command == 'run':
        if not args.task:
            print("❌ Укажите название задачи для запуска")
            print("\nИспользование:")
            print("  python scripts/schedule_manager.py run <task_name>")
            print("\nДоступные задачи:")
            print("  python scripts/schedule_manager.py list")
            sys.exit(1)

        run_task(args.task, config)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Прервано пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
