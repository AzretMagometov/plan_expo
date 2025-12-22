#!/usr/bin/env python3
"""
Скрипт для отслеживания непрерывных цепочек (streaks) выполнения привычек.

Вычисляет:
- Текущий streak для каждой привычки
- Максимальный streak
- Процент выполнения за 7/30 дней
- Паттерны (лучшие/худшие дни недели)

Сохраняет:
- JSON с данными для дашбордов
- Markdown отчет
"""

import json
import re
import sys
from pathlib import Path
import sys

# Добавить system/scripts в sys.path для импорта config_loader
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from config_loader import get_project_root, get_path
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import statistics

# Импорт функций из существующих скриптов
sys.path.append(str(Path(__file__).parent))
from analyze_reflection import parse_reflection_file

# Пути к директориям
PROJECT_ROOT = get_project_root()
GOALS_DIR = get_path("goals")
REFLECTIONS_DIR = get_path("reflections")
DAILY_DIR = REFLECTIONS_DIR / "daily"
DASHBOARDS_DIR = get_path("dashboards") / "streaks"


def get_active_goals():
    """Получить все активные цели."""
    active_goals = []
    if GOALS_DIR.exists():
        for goal_file in GOALS_DIR.glob("*.md"):
            with open(goal_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if '**Статус:** active' in content:
                    active_goals.append((goal_file.stem, content))
    return active_goals


def extract_habits(goal_content):
    """Извлечь привычки из содержимого цели."""
    habits = []

    # Implementation Intentions
    if_then_pattern = r'- ЕСЛИ (.+?) → ТО (.+?)(?:\n|$)'
    for match in re.finditer(if_then_pattern, goal_content):
        trigger = match.group(1).strip()
        action = match.group(2).strip()
        habits.append({
            'name': f"ЕСЛИ {trigger} → ТО {action}",
            'type': 'implementation_intention',
            'trigger': trigger,
            'action': action
        })

    # Tiny Habits
    tiny_pattern = r'- После (.+?) → (.+?)(?:\n|$)'
    for match in re.finditer(tiny_pattern, goal_content):
        anchor = match.group(1).strip()
        action = match.group(2).strip()

        # Удалить празднование если есть
        action = re.sub(r' → праздную:.*$', '', action)

        habits.append({
            'name': f"После {anchor} → {action}",
            'type': 'tiny_habit',
            'anchor': anchor,
            'action': action
        })

    return habits


def check_habit_completion(habit, reflection_data):
    """Проверить выполнение привычки в рефлексии."""
    # Проверить в выполненных операциях
    operations_done = reflection_data.get('operations_done', [])

    for operation in operations_done:
        operation_lower = operation.lower()
        habit_lower = habit['name'].lower()

        # Простое совпадение по ключевым словам
        habit_keywords = set(re.findall(r'\w+', habit_lower))
        operation_keywords = set(re.findall(r'\w+', operation_lower))

        # Если есть пересечение ключевых слов (хотя бы 50% от привычки)
        if len(habit_keywords & operation_keywords) >= len(habit_keywords) * 0.5:
            return True

    # Также проверить процент выполнения операций
    if reflection_data.get('operations_percent', 0) >= 80:
        # Если общий процент высокий, считаем что привычка выполнена
        return True

    return False


def get_reflection_path(date):
    """Получить путь к рефлексии за дату."""
    year = date.strftime("%Y")
    month = date.strftime("%m")
    filename = date.strftime("%Y-%m-%d")
    return DAILY_DIR / year / month / f"{filename}.md"


def calculate_streaks(habit, days_back=90):
    """Вычислить streaks для привычки."""
    today = datetime.now()
    completion_history = []

    # Собрать историю выполнения
    for i in range(days_back):
        date = today - timedelta(days=i)
        reflection_path = get_reflection_path(date)

        if reflection_path.exists():
            try:
                reflection_data = parse_reflection_file(reflection_path)
                completed = check_habit_completion(habit, reflection_data)
                completion_history.append({
                    'date': date,
                    'completed': completed,
                    'day_of_week': date.strftime('%A')
                })
            except:
                # Если ошибка парсинга, считаем не выполненным
                completion_history.append({
                    'date': date,
                    'completed': False,
                    'day_of_week': date.strftime('%A')
                })
        else:
            # Рефлексия не существует
            completion_history.append({
                'date': date,
                'completed': False,
                'day_of_week': date.strftime('%A')
            })

    # Обратить порядок (от старых к новым)
    completion_history.reverse()

    # 1. Текущий streak
    current_streak = 0
    for entry in reversed(completion_history):
        if entry['completed']:
            current_streak += 1
        else:
            break

    # 2. Максимальный streak
    max_streak = 0
    temp_streak = 0
    for entry in completion_history:
        if entry['completed']:
            temp_streak += 1
            max_streak = max(max_streak, temp_streak)
        else:
            temp_streak = 0

    # 3. Процент выполнения за периоды
    last_7_days = completion_history[-7:] if len(completion_history) >= 7 else completion_history
    last_30_days = completion_history[-30:] if len(completion_history) >= 30 else completion_history

    completion_rate_7d = sum(1 for e in last_7_days if e['completed']) / len(last_7_days) * 100 if last_7_days else 0
    completion_rate_30d = sum(1 for e in last_30_days if e['completed']) / len(last_30_days) * 100 if last_30_days else 0
    completion_rate_all = sum(1 for e in completion_history if e['completed']) / len(completion_history) * 100 if completion_history else 0

    # 4. Паттерны по дням недели
    day_completion = defaultdict(list)
    for entry in completion_history:
        day_completion[entry['day_of_week']].append(entry['completed'])

    day_stats = {}
    for day, completions in day_completion.items():
        if completions:
            day_stats[day] = sum(completions) / len(completions) * 100

    # Лучшие и худшие дни
    if day_stats:
        sorted_days = sorted(day_stats.items(), key=lambda x: x[1], reverse=True)
        best_days = [day for day, rate in sorted_days[:2] if rate >= 50]
        worst_days = [day for day, rate in sorted_days[-2:] if rate < 50]
    else:
        best_days = []
        worst_days = []

    # 5. Средняя частота в неделю
    weeks = len(completion_history) // 7
    if weeks > 0:
        total_completions = sum(1 for e in completion_history if e['completed'])
        avg_per_week = total_completions / weeks
    else:
        avg_per_week = 0

    return {
        'current_streak': current_streak,
        'max_streak': max_streak,
        'completion_rate_7d': round(completion_rate_7d, 1),
        'completion_rate_30d': round(completion_rate_30d, 1),
        'completion_rate_all': round(completion_rate_all, 1),
        'avg_per_week': round(avg_per_week, 1),
        'best_days': best_days,
        'worst_days': worst_days,
        'day_stats': day_stats
    }


def generate_streaks_data():
    """Генерировать данные о streaks для всех привычек."""
    # Получить активные цели
    active_goals = get_active_goals()

    all_habits = []

    for goal_name, goal_content in active_goals:
        # Извлечь привычки
        habits = extract_habits(goal_content)

        for habit in habits:
            # Вычислить streaks
            streaks = calculate_streaks(habit)

            habit_data = {
                'name': habit['name'],
                'type': habit['type'],
                'goal': goal_name,
                **streaks
            }

            all_habits.append(habit_data)

    return {
        'generated_at': datetime.now().isoformat(),
        'habits': all_habits
    }


def save_json_report(data, output_path):
    """Сохранить JSON отчет."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ JSON сохранен: {output_path}")


def generate_markdown_report(data, output_path):
    """Генерировать markdown отчет."""
    today = datetime.now().strftime("%Y-%m-%d")

    content = f"# Отчет по Streaks: {today}\n\n"

    habits = data['habits']

    # Топ-5 стабильных привычек
    content += "## Топ-5 стабильных привычек\n\n"
    top_habits = sorted(habits, key=lambda h: h['current_streak'], reverse=True)[:5]

    for i, habit in enumerate(top_habits, 1):
        emoji = "🔥" if habit['current_streak'] >= 7 else "⚡"
        content += f"{i}. {emoji} \"{habit['name'][:50]}...\" - Streak: {habit['current_streak']} дней ({habit['completion_rate_7d']}%)\n"

    content += "\n"

    # Требуют внимания
    content += "## Требуют внимания\n\n"
    attention_habits = [h for h in habits if h['current_streak'] == 0 and h['completion_rate_30d'] < 60]

    if attention_habits:
        for habit in attention_habits[:5]:
            content += f"1. ⚠️ \"{habit['name'][:50]}...\" - Streak: {habit['current_streak']} дней ({habit['completion_rate_30d']}%)\n"
            content += f"   - Рекомендация: Попробуйте изменить триггер или упростить действие\n\n"
    else:
        content += "Все привычки в хорошем состоянии!\n\n"

    # Паттерны
    content += "## Паттерны\n\n"

    # Общая статистика по дням недели
    day_stats_all = defaultdict(list)
    for habit in habits:
        for day, rate in habit.get('day_stats', {}).items():
            day_stats_all[day].append(rate)

    if day_stats_all:
        avg_by_day = {day: statistics.mean(rates) for day, rates in day_stats_all.items()}
        sorted_days = sorted(avg_by_day.items(), key=lambda x: x[1], reverse=True)

        best_day = sorted_days[0][0] if sorted_days else "N/A"
        worst_day = sorted_days[-1][0] if sorted_days else "N/A"

        content += f"- Лучший день недели: {best_day} ({avg_by_day.get(best_day, 0):.0f}% выполнение)\n"
        content += f"- Худший день: {worst_day} ({avg_by_day.get(worst_day, 0):.0f}% выполнение)\n"

    content += "\n"

    # Сохранить
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ Markdown отчет сохранен: {output_path}")


def main():
    """Главная функция."""
    print("Отслеживание streaks привычек...\n")

    try:
        # Генерировать данные
        data = generate_streaks_data()

        if not data['habits']:
            print("⚠️ Не найдено привычек в активных целях")
            return

        print(f"Найдено привычек: {len(data['habits'])}\n")

        # Сохранить JSON
        today = datetime.now().strftime("%Y-%m-%d")
        json_path = DASHBOARDS_DIR / "streaks_data.json"
        save_json_report(data, json_path)

        # Сохранить markdown отчет
        md_path = DASHBOARDS_DIR / f"{today}_streaks.md"
        generate_markdown_report(data, md_path)

        print("\n✅ Отслеживание завершено успешно")

    except Exception as e:
        print(f"❌ Ошибка: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
