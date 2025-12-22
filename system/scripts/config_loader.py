#!/usr/bin/env python3
"""
Универсальный загрузчик конфигурации для plan_expo.

Обеспечивает:
- Автоматическое определение корня проекта
- Загрузку пользовательских настроек из config/user_settings.yaml
- Получение путей к директориям (goals, reflections, dashboards и т.д.)
- Загрузку переменных окружения из .env
- Загрузку конфигурационных файлов

Использование:
    from config_loader import get_project_root, get_path, load_user_settings

    PROJECT_ROOT = get_project_root()
    GOALS_DIR = get_path('goals')
    settings = load_user_settings()
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

# Определение корня проекта относительно этого файла
# system/scripts/config_loader.py -> plan_expo/
_PROJECT_ROOT = Path(__file__).parent.parent.parent


def get_project_root() -> Path:
    """
    Получить корневую директорию проекта.

    Returns:
        Path: Абсолютный путь к корню проекта
    """
    return _PROJECT_ROOT


def get_config_dir() -> Path:
    """
    Получить директорию с конфигурационными файлами.

    Returns:
        Path: Путь к config/
    """
    return _PROJECT_ROOT / "config"


def load_env_vars() -> Dict[str, str]:
    """
    Загрузить переменные окружения из .env файла.

    Returns:
        Dict[str, str]: Словарь с переменными окружения
    """
    env_vars = {}
    env_file = _PROJECT_ROOT / ".env"

    if not env_file.exists():
        return env_vars

    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Пропускаем комментарии и пустые строки
                if not line or line.startswith('#'):
                    continue

                # Парсим KEY=VALUE
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()

                    # Убираем кавычки если есть
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]

                    env_vars[key] = value
                    # Устанавливаем в os.environ для совместимости
                    os.environ[key] = value
    except Exception as e:
        print(f"⚠️  Ошибка при загрузке .env: {e}", file=sys.stderr)

    return env_vars


def load_user_settings() -> Dict[str, Any]:
    """
    Загрузить пользовательские настройки из config/user_settings.yaml.

    Если файл не существует, возвращает настройки по умолчанию.

    Returns:
        Dict[str, Any]: Словарь с настройками пользователя
    """
    settings_file = get_config_dir() / "user_settings.yaml"

    # Настройки по умолчанию
    default_settings = {
        'project': {
            'root': str(_PROJECT_ROOT),
            'name': 'My Plan Expo',
            'timezone': 'UTC'
        },
        'paths': {
            'goals': 'user_data/goals',
            'reflections': 'user_data/reflections',
            'dashboards': 'user_data/dashboards',
            'logs': 'user_data/logs',
            'scripts': 'system/scripts',
            'prompts': 'system/prompts',
            'templates': 'system/templates',
            'docs': 'system/docs'
        },
        'git': {
            'commit_user_data': False,
            'auto_commit': True
        }
    }

    # Если файл не существует, вернуть настройки по умолчанию
    if not settings_file.exists():
        return default_settings

    # Загрузить настройки из файла
    try:
        with open(settings_file, 'r', encoding='utf-8') as f:
            settings = yaml.safe_load(f)

        # Обновить root path если он null или не задан
        if settings.get('project', {}).get('root') is None:
            settings['project']['root'] = str(_PROJECT_ROOT)

        return settings
    except Exception as e:
        print(f"⚠️  Ошибка при загрузке user_settings.yaml: {e}", file=sys.stderr)
        print(f"   Используются настройки по умолчанию", file=sys.stderr)
        return default_settings


def get_path(path_name: str) -> Path:
    """
    Получить абсолютный путь к директории по имени.

    Args:
        path_name: Имя пути из конфигурации (goals, reflections, dashboards и т.д.)

    Returns:
        Path: Абсолютный путь к директории

    Raises:
        KeyError: Если path_name не найден в конфигурации
    """
    settings = load_user_settings()

    if path_name not in settings.get('paths', {}):
        raise KeyError(f"Путь '{path_name}' не найден в конфигурации user_settings.yaml")

    relative_path = settings['paths'][path_name]
    return _PROJECT_ROOT / relative_path


def get_all_paths() -> Dict[str, Path]:
    """
    Получить все пути из конфигурации.

    Returns:
        Dict[str, Path]: Словарь {имя: абсолютный_путь}
    """
    settings = load_user_settings()
    paths = {}

    for name, relative_path in settings.get('paths', {}).items():
        paths[name] = _PROJECT_ROOT / relative_path

    return paths


def load_config(config_name: str) -> Optional[Dict[str, Any]]:
    """
    Загрузить конфигурационный файл из config/.

    Args:
        config_name: Имя файла без расширения (например, 'schedule', 'notifications')

    Returns:
        Optional[Dict[str, Any]]: Содержимое конфига или None если файл не найден
    """
    config_file = get_config_dir() / f"{config_name}.yaml"

    if not config_file.exists():
        # Попробовать .example версию
        config_file = get_config_dir() / f"{config_name}.yaml.example"
        if not config_file.exists():
            return None

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(f"⚠️  Ошибка при загрузке {config_name}.yaml: {e}", file=sys.stderr)
        return None


def get_timezone() -> str:
    """
    Получить часовой пояс пользователя из настроек.

    Returns:
        str: Часовой пояс (например, 'UTC', 'Europe/Moscow')
    """
    settings = load_user_settings()
    return settings.get('project', {}).get('timezone', 'UTC')


def get_project_name() -> str:
    """
    Получить название проекта из настроек.

    Returns:
        str: Название проекта
    """
    settings = load_user_settings()
    return settings.get('project', {}).get('name', 'My Plan Expo')


def should_commit_user_data() -> bool:
    """
    Проверить, нужно ли коммитить пользовательские данные в git.

    Returns:
        bool: True если нужно коммитить, False иначе
    """
    settings = load_user_settings()
    return settings.get('git', {}).get('commit_user_data', False)


def should_auto_commit() -> bool:
    """
    Проверить, включен ли авто-коммит.

    Returns:
        bool: True если авто-коммит включен, False иначе
    """
    settings = load_user_settings()
    return settings.get('git', {}).get('auto_commit', True)


def get_env_var(var_name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Получить переменную окружения из .env или os.environ.

    Args:
        var_name: Имя переменной
        default: Значение по умолчанию если переменная не найдена

    Returns:
        Optional[str]: Значение переменной или default
    """
    # Загрузить .env если еще не загружен
    load_env_vars()

    return os.environ.get(var_name, default)


# Автоматически загрузить .env при импорте модуля
load_env_vars()


if __name__ == "__main__":
    # Тестирование модуля
    print("=== Config Loader Test ===\n")

    print(f"Project Root: {get_project_root()}")
    print(f"Config Dir: {get_config_dir()}\n")

    print("User Settings:")
    settings = load_user_settings()
    print(f"  Project Name: {settings['project']['name']}")
    print(f"  Timezone: {settings['project']['timezone']}\n")

    print("Paths:")
    for name, path in get_all_paths().items():
        print(f"  {name}: {path}")

    print("\nEnvironment Variables:")
    env_vars = load_env_vars()
    if env_vars:
        for key, value in env_vars.items():
            # Не показываем полные токены
            if 'TOKEN' in key or 'KEY' in key or 'SECRET' in key:
                display_value = value[:10] + '...' if len(value) > 10 else '***'
            else:
                display_value = value
            print(f"  {key}: {display_value}")
    else:
        print("  (no .env file found)")
