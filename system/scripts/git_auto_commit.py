#!/usr/bin/env python3
"""
Скрипт для автоматических Git коммитов.

Функциональность:
- Фильтрация файлов (только reflections/, dashboards/, goals/)
- Формирование commit message по шаблонам
- Опциональный auto-push

Использование:
- python scripts/git_auto_commit.py
"""

import subprocess
import sys
from pathlib import Path
import sys

# Добавить system/scripts в sys.path для импорта config_loader
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from config_loader import get_project_root, get_path
from datetime import datetime
import yaml

# Пути
PROJECT_ROOT = get_project_root()
CONFIG_FILE = PROJECT_ROOT / "config"  # config всегда в корне / "git_auto_commit.yaml"


def load_config():
    """Загрузить конфигурацию."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    else:
        # Конфигурация по умолчанию
        return {
            'git': {
                'auto_commit': True,
                'auto_push': False,
                'include_files': ['reflections/', 'dashboards/', 'goals/'],
                'templates': {
                    'daily_reflection': '📝 Daily reflection: {date}',
                    'daily_dashboard': '📊 Daily dashboard: {date}',
                    'weekly_dashboard': '📈 Weekly dashboard: week {week} {year}',
                    'goals_update': '🎯 Goals update: metrics auto-update',
                    'validation': '✅ Validation: structure fix'
                }
            }
        }


def run_git_command(command):
    """Запустить git команду."""
    try:
        result = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка git команды: {e.stderr}", file=sys.stderr)
        return None


def get_changed_files():
    """Получить список измененных файлов."""
    output = run_git_command(['git', 'status', '--porcelain'])
    if not output:
        return []

    files = []
    for line in output.split('\n'):
        if line.strip():
            # Формат: "M  file.txt" или "?? file.txt"
            parts = line.strip().split(maxsplit=1)
            if len(parts) == 2:
                files.append(parts[1])

    return files


def filter_files(files, include_patterns):
    """Фильтровать файлы по паттернам."""
    filtered = []
    for file in files:
        for pattern in include_patterns:
            if file.startswith(pattern):
                filtered.append(file)
                break
    return filtered


def determine_commit_type(files):
    """Определить тип коммита по файлам."""
    today = datetime.now()

    # Проверить какие файлы изменены
    has_reflection = any('reflections/daily/' in f for f in files)
    has_dashboard_daily = any('dashboards/daily/' in f for f in files)
    has_dashboard_weekly = any('dashboards/weekly/' in f for f in files)
    has_goals = any('goals/' in f for f in files)
    has_validation = any('dashboards/validation/' in f for f in files)

    # Определить приоритет
    if has_dashboard_weekly:
        week = today.isocalendar()[1]
        year = today.year
        return 'weekly_dashboard', {'week': week, 'year': year}
    elif has_dashboard_daily:
        date = today.strftime('%Y-%m-%d')
        return 'daily_dashboard', {'date': date}
    elif has_reflection:
        date = today.strftime('%Y-%m-%d')
        return 'daily_reflection', {'date': date}
    elif has_goals:
        return 'goals_update', {}
    elif has_validation:
        return 'validation', {}
    else:
        # Общий коммит
        return 'general', {}


def create_commit_message(commit_type, params, templates):
    """Создать commit message по шаблону."""
    template = templates.get(commit_type, '📝 Update: {date}')

    # Добавить дату если не указана
    if '{date}' in template and 'date' not in params:
        params['date'] = datetime.now().strftime('%Y-%m-%d')

    try:
        return template.format(**params)
    except KeyError:
        # Если не хватает параметров, вернуть базовый
        return f"📝 Update: {datetime.now().strftime('%Y-%m-%d')}"


def main():
    """Главная функция."""
    print("Проверка изменений для коммита...\n")

    # Загрузить конфигурацию
    config = load_config()
    git_config = config.get('git', {})

    if not git_config.get('auto_commit', True):
        print("⚠️ Автокоммиты отключены в конфигурации")
        return

    # Получить измененные файлы
    changed_files = get_changed_files()

    if not changed_files:
        print("✅ Нет изменений для коммита")
        return

    print(f"Найдено измененных файлов: {len(changed_files)}\n")

    # Фильтровать файлы
    include_patterns = git_config.get('include_files', ['reflections/', 'dashboards/', 'goals/'])
    filtered_files = filter_files(changed_files, include_patterns)

    if not filtered_files:
        print("⚠️ Нет файлов соответствующих фильтрам")
        print(f"Фильтры: {', '.join(include_patterns)}")
        return

    print(f"Файлы для коммита ({len(filtered_files)}):")
    for f in filtered_files:
        print(f"  - {f}")
    print()

    # Определить тип коммита
    commit_type, params = determine_commit_type(filtered_files)
    print(f"Тип коммита: {commit_type}")

    # Создать commit message
    templates = git_config.get('templates', {})
    commit_message = create_commit_message(commit_type, params, templates)
    print(f"Сообщение: {commit_message}\n")

    # Добавить файлы
    print("Добавление файлов в staged...")
    for file in filtered_files:
        result = run_git_command(['git', 'add', file])
        if result is None:
            print(f"❌ Не удалось добавить {file}")
            return

    # Создать коммит
    print("Создание коммита...")
    result = run_git_command(['git', 'commit', '-m', commit_message])

    if result is None:
        print("❌ Не удалось создать коммит")
        return

    print(f"✅ Коммит создан: {commit_message}")

    # Опциональный push
    if git_config.get('auto_push', False):
        print("\nPush в remote...")
        result = run_git_command(['git', 'push', 'origin', 'main'])

        if result is None:
            print("❌ Не удалось выполнить push")
            print("💡 Выполните push вручную: git push origin main")
        else:
            print("✅ Push выполнен успешно")
    else:
        print("\n💡 Auto-push отключен. Выполните вручную: git push origin main")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
