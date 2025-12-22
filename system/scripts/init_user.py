#!/usr/bin/env python3
"""
Скрипт инициализации plan_expo для нового пользователя.

Выполняет:
1. Создание config/user_settings.yaml с авто-определением путей
2. Копирование config/*.example в config/*.yaml
3. Создание структуры директорий user_data/
4. Интерактивную настройку .env (Telegram/Slack токены)
5. Выбор AI модели (Claude/GPT/Gemini/Local)
6. Обновление config/ai_model.yaml

Режимы:
- interactive: Интерактивная настройка с вопросами (по умолчанию)
- quick: Быстрая настройка с дефолтными значениями
- minimal: Минимальная настройка (только необходимое)

Использование:
  python system/scripts/init_user.py
  python system/scripts/init_user.py --mode quick
  python system/scripts/init_user.py --mode minimal
"""

import argparse
import os
import shutil
from pathlib import Path
import yaml
import sys

# Добавить system/scripts в sys.path для импорта config_loader
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from config_loader import get_project_root, get_config_dir

PROJECT_ROOT = get_project_root()
CONFIG_DIR = get_config_dir()
USER_DATA_DIR = PROJECT_ROOT / "user_data"


def print_header(text: str):
    """Печать заголовка."""
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}\n")


def print_step(number: int, text: str):
    """Печать номера шага."""
    print(f"\n{number}. {text}")
    print("-" * 60)


def create_user_settings(timezone="UTC", interactive=True):
    """
    Создать config/user_settings.yaml с настройками пользователя.

    Args:
        timezone: Часовой пояс по умолчанию
        interactive: Интерактивный режим с вопросами
    """
    print_step(1, "Создание пользовательских настроек")

    if interactive:
        print("Настройка базовых параметров проекта:\n")
        timezone_input = input(f"  Ваш часовой пояс (по умолчанию '{timezone}'): ").strip()
        timezone = timezone_input if timezone_input else timezone

        project_name = input("  Название проекта (по умолчанию 'My Plan Expo'): ").strip() or "My Plan Expo"
    else:
        project_name = "My Plan Expo"
        print(f"  Использую настройки по умолчанию:")
        print(f"  - Часовой пояс: {timezone}")
        print(f"  - Название проекта: {project_name}")

    settings = {
        'project': {
            'root': str(PROJECT_ROOT),
            'name': project_name,
            'timezone': timezone
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
            'commit_user_data': False,  # По умолчанию не коммитим (приватность)
            'auto_commit': True
        }
    }

    settings_file = CONFIG_DIR / "user_settings.yaml"
    with open(settings_file, 'w', encoding='utf-8') as f:
        yaml.dump(settings, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    print(f"\n  ✅ Создан {settings_file.relative_to(PROJECT_ROOT)}")


def copy_config_examples():
    """Скопировать .example конфиги в рабочие файлы."""
    print_step(2, "Создание конфигурационных файлов")

    configs = [
        'schedule.yaml',
        'notifications.yaml',
        'git_auto_commit.yaml'
    ]

    for config in configs:
        example_file = CONFIG_DIR / f"{config}.example"
        target_file = CONFIG_DIR / config

        if example_file.exists():
            if not target_file.exists():
                shutil.copy(example_file, target_file)
                print(f"  ✅ Создан config/{config}")
            else:
                print(f"  ⚠️  config/{config} уже существует, пропускаю")
        else:
            print(f"  ⚠️  config/{config}.example не найден, пропускаю")


def create_user_directories():
    """Создать структуру директорий для пользовательских данных."""
    print_step(3, "Создание директорий для данных")

    dirs = [
        USER_DATA_DIR / "goals",
        USER_DATA_DIR / "reflections/daily",
        USER_DATA_DIR / "reflections/weekly",
        USER_DATA_DIR / "reflections/monthly",
        USER_DATA_DIR / "reflections/quarterly",
        USER_DATA_DIR / "reflections/yearly",
        USER_DATA_DIR / "dashboards/daily",
        USER_DATA_DIR / "dashboards/weekly",
        USER_DATA_DIR / "dashboards/streaks",
        USER_DATA_DIR / "dashboards/validation",
        USER_DATA_DIR / "logs/cron"
    ]

    created = 0
    for dir_path in dirs:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created += 1

    print(f"  ✅ Создано директорий: {created}")


def setup_env_file(interactive=True):
    """
    Настроить .env файл с секретами.

    Args:
        interactive: Интерактивный режим с вопросами
    """
    print_step(4, "Настройка переменных окружения (.env)")

    env_file = PROJECT_ROOT / ".env"

    if env_file.exists():
        print(f"  ⚠️  .env уже существует, пропускаю")
        return

    if not interactive:
        # Просто скопировать .env.example
        env_example = PROJECT_ROOT / ".env.example"
        if env_example.exists():
            shutil.copy(env_example, env_file)
            print(f"  ✅ Создан .env (заполните секреты вручную)")
        return

    print("Настройка уведомлений (опционально, можно пропустить):\n")
    print("  Для Telegram бота:")
    print("  - Создайте бота через @BotFather: https://t.me/BotFather")
    print("  - Получите chat_id через @userinfobot: https://t.me/userinfobot\n")

    telegram_token = input("  Telegram Bot Token (Enter для пропуска): ").strip()
    telegram_chat_id = input("  Telegram Chat ID (Enter для пропуска): ").strip()

    print("\n  Для Slack:")
    print("  - Создайте Incoming Webhook: https://api.slack.com/messaging/webhooks\n")

    slack_webhook = input("  Slack Webhook URL (Enter для пропуска): ").strip()

    # Создать .env файл
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write("# plan_expo Environment Variables\n")
        f.write("# Созд automatically by init_user.py\n\n")

        f.write("# Telegram Bot Configuration\n")
        f.write(f"TELEGRAM_BOT_TOKEN={telegram_token}\n")
        f.write(f"TELEGRAM_CHAT_ID={telegram_chat_id}\n\n")

        f.write("# Slack Configuration\n")
        f.write(f"SLACK_WEBHOOK_URL={slack_webhook}\n\n")

        f.write("# AI API Keys (optional)\n")
        f.write("OPENAI_API_KEY=\n")
        f.write("ANTHROPIC_API_KEY=\n")
        f.write("GOOGLE_AI_API_KEY=\n")

    print(f"\n  ✅ Создан .env")


def select_ai_model(interactive=True):
    """
    Выбрать AI модель и обновить config/ai_model.yaml.

    Args:
        interactive: Интерактивный режим с вопросами
    """
    print_step(5, "Выбор AI модели")

    ai_config_file = CONFIG_DIR / "ai_model.yaml"

    if not interactive:
        print(f"  ℹ️  AI модель по умолчанию: Claude")
        print(f"  ℹ️  Можно изменить в {ai_config_file.relative_to(PROJECT_ROOT)}")
        return

    print("Выберите AI модель для работы с системой:\n")
    print("  1. Claude (Anthropic) - Рекомендуется")
    print("     • Лучшее понимание структурированных промптов")
    print("     • Отличная работа с .cursorrules")
    print("     • Длинный контекст (200k+ токенов)")
    print()
    print("  2. ChatGPT (GPT-4)")
    print("     • Широкая доступность")
    print("     • Хорошее качество ответов")
    print("     • API через OpenAI")
    print()
    print("  3. Gemini Pro (Google)")
    print("     • Бесплатный доступ")
    print("     • Хорошая работа с русским языком")
    print("     • Длинный контекст")
    print()
    print("  4. Локальная модель (Ollama/LMStudio)")
    print("     • Полная приватность")
    print("     • Офлайн работа")
    print("     • Требуется мощное железо")
    print()

    choice = input("Выбор (1-4, по умолчанию 1): ").strip() or "1"

    models_map = {
        "1": "claude",
        "2": "gpt",
        "3": "gemini",
        "4": "local"
    }

    selected_model = models_map.get(choice, "claude")

    # Загрузить текущую конфигурацию AI моделей
    if ai_config_file.exists():
        with open(ai_config_file, 'r', encoding='utf-8') as f:
            ai_config = yaml.safe_load(f)
    else:
        # Создать дефолтную конфигурацию
        ai_config = {
            'current_model': 'claude',
            'models': {
                'claude': {
                    'name': 'Claude (Anthropic)',
                    'recommended_model': 'claude-sonnet-4-5',
                    'cursorrules_file': '.cursorrules.example'
                },
                'gpt': {
                    'name': 'ChatGPT (OpenAI)',
                    'recommended_model': 'gpt-4',
                    'cursorrules_file': '.cursorrules.gpt.example'
                },
                'gemini': {
                    'name': 'Gemini (Google)',
                    'recommended_model': 'gemini-pro',
                    'cursorrules_file': '.cursorrules.gemini.example'
                },
                'local': {
                    'name': 'Local Model',
                    'recommended_model': 'mistral',
                    'cursorrules_file': '.cursorrules.local.example'
                }
            }
        }

    # Обновить выбранную модель
    ai_config['current_model'] = selected_model

    # Сохранить конфигурацию
    with open(ai_config_file, 'w', encoding='utf-8') as f:
        yaml.dump(ai_config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    model_name = ai_config['models'][selected_model]['name']
    print(f"\n  ✅ Выбрана AI модель: {model_name}")

    # Подсказка по .cursorrules
    cursorrules_file = ai_config['models'][selected_model].get('cursorrules_file')
    if cursorrules_file:
        source_file = PROJECT_ROOT / cursorrules_file
        target_file = PROJECT_ROOT / ".cursorrules"

        if source_file.exists() and not target_file.exists():
            print(f"\n  💡 Рекомендация:")
            print(f"     Скопируйте {cursorrules_file} в .cursorrules:")
            print(f"     cp {cursorrules_file} .cursorrules")


def print_next_steps():
    """Вывести следующие шаги для пользователя."""
    print_header("✅ Инициализация завершена!")

    print("Следующие шаги:\n")
    print("  1. Установите зависимости:")
    print("     pip3 install -r requirements.txt\n")

    print("  2. Если используете Cursor или Claude Desktop:")
    print("     • Откройте проект в Cursor")
    print("     • .cursorrules автоматически загрузится\n")

    print("  3. Создайте первую цель:")
    print("     • Обратитесь к AI-коучу: 'Я хочу достичь [ваша цель]'")
    print("     • AI проведет вас через процесс создания цели\n")

    print("  4. Настройте автоматизацию (опционально):")
    print("     python3 system/scripts/schedule_manager.py setup\n")

    print("Документация:")
    print("  • README.md - Обзор системы")
    print("  • SETUP.md - Детальная инструкция по установке")
    print("  • CLAUDE.md - Гайд для AI-коуча")
    print("  • system/docs/AI_MODELS.md - Руководство по AI моделям")
    print()


def main():
    """Главная функция."""
    parser = argparse.ArgumentParser(
        description="Инициализация plan_expo для нового пользователя",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Режимы:
  interactive  - Интерактивная настройка с вопросами (по умолчанию)
  quick        - Быстрая настройка с дефолтными значениями
  minimal      - Минимальная настройка (только необходимое)

Примеры:
  python system/scripts/init_user.py
  python system/scripts/init_user.py --mode quick
  python system/scripts/init_user.py --mode minimal
        """
    )
    parser.add_argument(
        '--mode',
        choices=['interactive', 'quick', 'minimal'],
        default='interactive',
        help='Режим инициализации'
    )
    args = parser.parse_args()

    interactive = args.mode == 'interactive'
    minimal = args.mode == 'minimal'

    print_header("🚀 Инициализация plan_expo")

    # 1. Создать user_settings.yaml
    create_user_settings(interactive=interactive)

    # 2. Скопировать конфиги
    copy_config_examples()

    # 3. Создать директории
    create_user_directories()

    # 4. Настроить .env
    if not minimal:
        setup_env_file(interactive=interactive)
    else:
        print_step(4, "Настройка .env (пропущено в минимальном режиме)")

    # 5. Выбрать AI модель
    if not minimal:
        select_ai_model(interactive=interactive)
    else:
        print_step(5, "Выбор AI модели (пропущено в минимальном режиме)")

    # 6. Вывести следующие шаги
    print_next_steps()


if __name__ == "__main__":
    main()
