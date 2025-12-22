#!/usr/bin/env python3
"""
Система уведомлений для plan_expo.

Типы уведомлений:
- daily: Утренние/вечерние уведомления
- weekly: Недельный отчет
- check: Проверки здоровья системы

Каналы:
- macOS Notification Center
- Telegram (опционально)
- Slack (опционально)

Использование:
  python scripts/notification_system.py daily
  python scripts/notification_system.py weekly
  python scripts/notification_system.py check
"""

import subprocess
import sys
import argparse
import json
from pathlib import Path
import sys

# Добавить system/scripts в sys.path для импорта config_loader
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from config_loader import get_project_root, get_path
from datetime import datetime, timedelta
import yaml

# Пути
PROJECT_ROOT = get_project_root()
CONFIG_FILE = PROJECT_ROOT / "config"  # config всегда в корне / "notifications.yaml"
REFLECTIONS_DIR = get_path("reflections") / "daily"
DASHBOARDS_DIR = get_path("dashboards")
STREAKS_FILE = DASHBOARDS_DIR / "streaks" / "streaks_data.json"


def load_config():
    """Загрузить конфигурацию."""
    if not CONFIG_FILE.exists():
        print(f"⚠️ Конфигурация не найдена: {CONFIG_FILE}")
        return None

    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def send_macos_notification(title, message, sound=None):
    """Отправить уведомление через macOS Notification Center."""
    try:
        # Базовая команда
        script = f'display notification "{message}" with title "{title}"'

        # Добавить звук если указан
        if sound and sound != "null":
            script += f' sound name "{sound}"'

        # Выполнить osascript
        subprocess.run(
            ['osascript', '-e', script],
            check=True,
            capture_output=True
        )
        return True
    except Exception as e:
        print(f"❌ Ошибка отправки macOS уведомления: {e}")
        return False


def send_telegram_notification(title, message, config):
    """Отправить уведомление через Telegram."""
    try:
        import requests

        bot_token = config.get('bot_token', '')
        chat_id = config.get('chat_id', '')

        if not bot_token or not chat_id:
            print("⚠️ Telegram не настроен (нет bot_token или chat_id)")
            return False

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        text = f"*{title}*\n\n{message}"

        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'Markdown'
        }

        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return True

    except ImportError:
        print("⚠️ requests не установлен. Установите: pip install requests")
        return False
    except Exception as e:
        print(f"❌ Ошибка отправки Telegram уведомления: {e}")
        return False


def send_slack_notification(title, message, config):
    """Отправить уведомление через Slack."""
    try:
        import requests

        webhook_url = config.get('webhook_url', '')

        if not webhook_url:
            print("⚠️ Slack не настроен (нет webhook_url)")
            return False

        payload = {
            'text': f"*{title}*\n{message}"
        }

        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        return True

    except ImportError:
        print("⚠️ requests не установлен. Установите: pip install requests")
        return False
    except Exception as e:
        print(f"❌ Ошибка отправки Slack уведомления: {e}")
        return False


def send_notification(title, message, channels, config, sound=None):
    """Отправить уведомление по указанным каналам."""
    sent_count = 0

    for channel in channels:
        if channel == 'macos':
            macos_config = config.get('macos', {})
            if macos_config.get('enabled', True):
                # Использовать звук из параметра или из конфига
                notification_sound = sound or macos_config.get('sound', 'default')
                if send_macos_notification(title, message, notification_sound):
                    sent_count += 1

        elif channel == 'telegram':
            telegram_config = config.get('telegram', {})
            if telegram_config.get('enabled', False):
                if send_telegram_notification(title, message, telegram_config):
                    sent_count += 1

        elif channel == 'slack':
            slack_config = config.get('slack', {})
            if slack_config.get('enabled', False):
                if send_slack_notification(title, message, slack_config):
                    sent_count += 1

    return sent_count > 0


def get_reflection_path(date):
    """Получить путь к рефлексии за дату."""
    year = date.strftime("%Y")
    month = date.strftime("%m")
    filename = date.strftime("%Y-%m-%d")
    return REFLECTIONS_DIR / year / month / f"{filename}.md"


def is_reflection_filled(date):
    """Проверить заполнена ли рефлексия."""
    reflection_path = get_reflection_path(date)

    if not reflection_path.exists():
        return False

    # Проверить размер файла (заполненная рефлексия > 1KB)
    return reflection_path.stat().st_size > 1024


def load_latest_dashboard_data():
    """Загрузить данные последнего дашборда."""
    today = datetime.now().strftime("%Y-%m-%d")
    daily_dashboard_dir = DASHBOARDS_DIR / "daily"

    # Поиск последнего дашборда
    if daily_dashboard_dir.exists():
        dashboards = sorted(daily_dashboard_dir.glob("*.md"), reverse=True)
        if dashboards:
            # Парсить markdown для извлечения метрик
            with open(dashboards[0], 'r', encoding='utf-8') as f:
                content = f.read()

            # Извлечь метрики (упрощенный парсинг)
            import re

            operations_match = re.search(r'Операции:\s*(\d+)%', content)
            tactics_match = re.search(r'Тактика:\s*(\d+)%', content)
            streak_match = re.search(r'Streak:\s*(\d+)', content)

            return {
                'operations': int(operations_match.group(1)) if operations_match else 0,
                'tactics': int(tactics_match.group(1)) if tactics_match else 0,
                'streak': int(streak_match.group(1)) if streak_match else 0
            }

    return {'operations': 0, 'tactics': 0, 'streak': 0}


def load_weekly_dashboard_data():
    """Загрузить данные недельного дашборда."""
    weekly_dashboard_dir = DASHBOARDS_DIR / "weekly"

    if weekly_dashboard_dir.exists():
        dashboards = sorted(weekly_dashboard_dir.glob("*.md"), reverse=True)
        if dashboards:
            with open(dashboards[0], 'r', encoding='utf-8') as f:
                content = f.read()

            import re

            # Извлечь средние показатели
            avg_ops_match = re.search(r'Средний % операций:\s*(\d+\.?\d*)%', content)
            avg_tac_match = re.search(r'Средний % тактики:\s*(\d+\.?\d*)%', content)

            return {
                'avg_operations': float(avg_ops_match.group(1)) if avg_ops_match else 0,
                'avg_tactics': float(avg_tac_match.group(1)) if avg_tac_match else 0
            }

    return {'avg_operations': 0, 'avg_tactics': 0}


def load_streaks_data():
    """Загрузить данные о streaks."""
    if STREAKS_FILE.exists():
        with open(STREAKS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'habits': []}


def notify_daily(config):
    """Отправить дневное уведомление."""
    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")

    channels = config['notifications'].get('default_channels', ['macos'])
    templates = config.get('templates', {})

    # Определить тип уведомления
    current_hour = today.hour

    # Утренее уведомление (если рефлексия создана недавно)
    if current_hour < 12:
        template = templates.get('morning', {})
        title = template.get('title', 'plan_expo: Утренняя рефлексия')
        message = template.get('message', 'Шаблон рефлексии создан').format(date=today_str)
        sound = template.get('sound', 'Glass')

        if send_notification(title, message, channels, config, sound):
            print(f"✅ Утреннее уведомление отправлено")
        else:
            print(f"⚠️ Не удалось отправить утреннее уведомление")

    # Вечернее уведомление (дашборд создан)
    else:
        # Загрузить данные дашборда
        dashboard_data = load_latest_dashboard_data()

        template = templates.get('evening', {})
        title = template.get('title', 'plan_expo: Дашборд готов')
        message = template.get('message', 'Дневной дашборд создан').format(
            operations=dashboard_data['operations'],
            tactics=dashboard_data['tactics'],
            streak=dashboard_data['streak']
        )
        sound = template.get('sound', 'Hero')

        if send_notification(title, message, channels, config, sound):
            print(f"✅ Вечернее уведомление отправлено")
        else:
            print(f"⚠️ Не удалось отправить вечернее уведомление")


def notify_weekly(config):
    """Отправить недельное уведомление."""
    channels = config['notifications'].get('default_channels', ['macos'])
    templates = config.get('templates', {})

    # Загрузить данные недельного дашборда
    weekly_data = load_weekly_dashboard_data()

    template = templates.get('weekly', {})
    title = template.get('title', 'plan_expo: Недельный отчет')
    message = template.get('message', 'Недельный дашборд готов').format(
        avg_operations=weekly_data['avg_operations'],
        avg_tactics=weekly_data['avg_tactics']
    )
    sound = template.get('sound', 'Hero')

    if send_notification(title, message, channels, config, sound):
        print(f"✅ Недельное уведомление отправлено")
    else:
        print(f"⚠️ Не удалось отправить недельное уведомление")


def check_and_notify(config):
    """Проверить условия и отправить предупреждения."""
    channels = config['notifications'].get('default_channels', ['macos'])
    templates = config.get('templates', {})
    health_checks = config.get('health_checks', {})

    today = datetime.now()
    warnings = []

    # 1. Проверить заполнена ли рефлексия
    if not is_reflection_filled(today):
        deadline_hours = health_checks.get('reflection_fill_deadline_hours', 12)
        current_hour = today.hour

        if current_hour >= deadline_hours:
            warnings.append("Рефлексия за сегодня еще не заполнена!")

    # 2. Проверить streak (загрузить данные)
    streaks_data = load_streaks_data()
    streak_threshold = health_checks.get('streak_warning_threshold', 3)

    low_streaks = [
        h for h in streaks_data.get('habits', [])
        if h.get('current_streak', 0) < streak_threshold
    ]

    if low_streaks:
        habit_names = ', '.join([h['name'][:30] + '...' for h in low_streaks[:3]])
        warnings.append(f"Streak под угрозой для {len(low_streaks)} привычек: {habit_names}")

    # 3. Проверить низкую производительность
    low_perf_days = health_checks.get('low_performance_days', 3)
    low_perf_threshold = health_checks.get('low_performance_threshold', 50)

    # Проверить последние N дней
    low_performance_count = 0
    for i in range(low_perf_days):
        date = today - timedelta(days=i)
        if is_reflection_filled(date):
            # Упрощенная проверка (нужно парсить рефлексию для точных данных)
            # Пока пропускаем
            pass

    # Отправить предупреждения если есть
    if warnings:
        template = templates.get('warning', {})
        title = template.get('title', 'plan_expo: Предупреждение')
        sound = template.get('sound', 'Basso')

        for warning in warnings:
            message = template.get('message', '{warning_text}').format(warning_text=warning)

            if send_notification(title, message, channels, config, sound):
                print(f"✅ Предупреждение отправлено: {warning}")
            else:
                print(f"⚠️ Не удалось отправить предупреждение: {warning}")
    else:
        print("✅ Все проверки пройдены. Предупреждений нет.")


def main():
    """Главная функция."""
    parser = argparse.ArgumentParser(
        description='Система уведомлений plan_expo',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Типы уведомлений:
  daily   - Дневные уведомления (утро/вечер)
  weekly  - Недельный отчет
  check   - Проверки здоровья системы

Примеры использования:
  %(prog)s daily   # Отправить дневное уведомление
  %(prog)s weekly  # Отправить недельный отчет
  %(prog)s check   # Проверить условия и отправить предупреждения
        """
    )

    parser.add_argument(
        'notification_type',
        choices=['daily', 'weekly', 'check'],
        help='Тип уведомления'
    )

    args = parser.parse_args()

    # Загрузить конфигурацию
    config = load_config()

    if not config:
        print("❌ Не удалось загрузить конфигурацию")
        sys.exit(1)

    # Проверить включены ли уведомления
    if not config.get('notifications', {}).get('enabled', True):
        print("⚠️ Уведомления отключены в конфигурации")
        sys.exit(0)

    # Отправить уведомление по типу
    if args.notification_type == 'daily':
        notify_daily(config)
    elif args.notification_type == 'weekly':
        notify_weekly(config)
    elif args.notification_type == 'check':
        check_and_notify(config)


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
