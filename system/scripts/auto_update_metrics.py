#!/usr/bin/env python3
"""
Скрипт для автоматического обновления метрик целей на основе рефлексий.

Обновляет:
- Identity Evidence List (подсчет доказательств)
- OKR/SMART Tracker (прогресс)
- Daily Habits Tracker (streak, процент выполнения)
- ИСТОРИЯ ИЗМЕНЕНИЙ

Использование:
- python scripts/auto_update_metrics.py               # за сегодня
- python scripts/auto_update_metrics.py --date 2025-12-21  # за дату
- python scripts/auto_update_metrics.py --period week      # за неделю
"""

import re
import sys
from pathlib import Path
import sys

# Добавить system/scripts в sys.path для импорта config_loader
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from config_loader import get_project_root, get_path
from datetime import datetime, timedelta
import argparse
import logging

# Импорт функций из существующих скриптов
sys.path.append(str(Path(__file__).parent))
from analyze_reflection import parse_reflection_file

# Пути к директориям
PROJECT_ROOT = get_project_root()
GOALS_DIR = get_path("goals")
REFLECTIONS_DIR = get_path("reflections")
DAILY_DIR = REFLECTIONS_DIR / "daily"
LOGS_DIR = get_path("logs")


def get_active_goals():
    """Получить все активные цели."""
    active_goals = []
    if GOALS_DIR.exists():
        for goal_file in GOALS_DIR.glob("*.md"):
            with open(goal_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if '**Статус:** active' in content:
                    active_goals.append(goal_file)
    return active_goals


def get_reflection_path(date):
    """Получить путь к рефлексии за дату."""
    year = date.strftime("%Y")
    month = date.strftime("%m")
    filename = date.strftime("%Y-%m-%d")
    return DAILY_DIR / year / month / f"{filename}.md"


def count_evidence_from_reflection(reflection_data):
    """Подсчитать количество доказательств идентичности из рефлексии."""
    return len(reflection_data.get('evidence_done', []))


def calculate_operations_percentage(reflection_data):
    """Вычислить процент выполнения операций."""
    if reflection_data.get('operations_percent') is not None:
        return reflection_data['operations_percent']

    # Если явно не указан, подсчитать из выполненных операций
    operations_done = len(reflection_data.get('operations_done', []))
    if operations_done > 0:
        # Предполагаем что в рефлексии ~8 операций (5 tiny habits + 3 IF-THEN)
        return min(100, int((operations_done / 8) * 100))
    return 0


def calculate_tactics_percentage(reflection_data):
    """Вычислить процент выполнения тактики."""
    if reflection_data.get('tactics_percent') is not None:
        return reflection_data['tactics_percent']
    return 0


def update_goal_metrics(goal_path, reflection_data, date):
    """Обновить метрики в файле цели."""
    with open(goal_path, 'r', encoding='utf-8') as f:
        content = f.read()

    updated = False

    # 1. Обновить Identity Evidence List
    evidence_count = count_evidence_from_reflection(reflection_data)
    if evidence_count > 0:
        # Найти текущий прогресс
        evidence_pattern = r'\*\*Текущий прогресс:\*\* (\d+)/10'
        evidence_match = re.search(evidence_pattern, content)

        if evidence_match:
            current_progress = int(evidence_match.group(1))
            new_progress = min(10, current_progress + evidence_count)

            content = re.sub(
                evidence_pattern,
                f'**Текущий прогресс:** {new_progress}/10',
                content
            )
            updated = True
            logging.info(f"Identity Evidence: {current_progress} → {new_progress} (+{evidence_count})")

    # 2. Обновить Daily Habits Tracker - Выполнение
    operations_percent = calculate_operations_percentage(reflection_data)
    if operations_percent > 0:
        # Обновить процент выполнения
        habits_pattern = r'\*\*Выполнение:\*\* (\d+)%'
        content = re.sub(
            habits_pattern,
            f'**Выполнение:** {operations_percent}%',
            content
        )
        updated = True
        logging.info(f"Выполнение операций: {operations_percent}%")

    # 3. Обновить Последнее обновление
    today = datetime.now().strftime("%Y-%m-%d")
    content = re.sub(
        r'\*\*Последнее обновление:\*\* \d{4}-\d{2}-\d{2}',
        f'**Последнее обновление:** {today}',
        content
    )

    # 4. Добавить запись в ИСТОРИЯ ИЗМЕНЕНИЙ
    if updated:
        history_entry = f"""- {today}: [PROGRESS] Автообновление метрик на основе рефлексии за {date.strftime("%Y-%m-%d")}
  - **Детали:** Обновлены метрики: доказательств идентичности +{evidence_count}, выполнение операций {operations_percent}%
"""

        # Найти секцию ИСТОРИЯ ИЗМЕНЕНИЙ и добавить запись
        history_pattern = r'(## ИСТОРИЯ ИЗМЕНЕНИЙ\s*\n)'
        if re.search(history_pattern, content):
            content = re.sub(
                history_pattern,
                f'\\1\n{history_entry}\n',
                content
            )
        else:
            # Если секции нет, добавить в конец
            content += f"\n## ИСТОРИЯ ИЗМЕНЕНИЙ\n\n{history_entry}\n"

    # Сохранить обновленный файл
    if updated:
        with open(goal_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logging.info(f"Файл обновлен: {goal_path}")
        return True
    else:
        logging.info(f"Нет изменений для {goal_path}")
        return False


def update_metrics_for_date(date):
    """Обновить метрики за конкретную дату."""
    logging.info(f"Обработка рефлексии за {date.strftime('%Y-%m-%d')}")

    # Получить путь к рефлексии
    reflection_path = get_reflection_path(date)

    if not reflection_path.exists():
        logging.warning(f"Рефлексия не найдена: {reflection_path}")
        return False

    # Парсить рефлексию
    try:
        reflection_data = parse_reflection_file(reflection_path)
    except Exception as e:
        logging.error(f"Ошибка парсинга рефлексии: {e}")
        return False

    # Получить активные цели
    active_goals = get_active_goals()

    if not active_goals:
        logging.warning("Нет активных целей для обновления")
        return False

    logging.info(f"Найдено активных целей: {len(active_goals)}")

    # Обновить каждую цель
    updated_count = 0
    for goal_path in active_goals:
        logging.info(f"Обработка цели: {goal_path.stem}")
        if update_goal_metrics(goal_path, reflection_data, date):
            updated_count += 1

    logging.info(f"Обновлено целей: {updated_count}/{len(active_goals)}")
    return updated_count > 0


def update_metrics_for_period(period_days):
    """Обновить метрики за период."""
    today = datetime.now()

    for i in range(period_days):
        date = today - timedelta(days=i)
        update_metrics_for_date(date)


def main():
    """Главная функция."""
    parser = argparse.ArgumentParser(description='Автообновление метрик целей из рефлексий')
    parser.add_argument('--date', type=str, help='Дата в формате YYYY-MM-DD (по умолчанию сегодня)')
    parser.add_argument('--period', type=str, choices=['week', 'month'], help='Обновить за период')

    args = parser.parse_args()

    # Настройка логирования
    today = datetime.now().strftime("%Y-%m-%d")
    LOGS_DIR.mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOGS_DIR / f"metrics_update_{today}.log", encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    try:
        logging.info("Начало обновления метрик")

        if args.period:
            # Обновить за период
            period_days = 7 if args.period == 'week' else 30
            logging.info(f"Обновление за период: {period_days} дней")
            update_metrics_for_period(period_days)
        else:
            # Обновить за конкретную дату
            if args.date:
                date = datetime.strptime(args.date, "%Y-%m-%d")
            else:
                date = datetime.now()

            if update_metrics_for_date(date):
                logging.info("Обновление завершено успешно")
            else:
                logging.warning("Не было обновлений")

        logging.info("Завершено")

    except Exception as e:
        logging.error(f"Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
