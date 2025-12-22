#!/usr/bin/env python3
"""
Скрипт для генерации недельного HTML дашборда.

Создает:
- Аналитику за неделю
- Сравнение с предыдущей неделей
- Топ достижения и области для улучшения
- Инсайты и рекомендации

Использование:
- python scripts/generate_weekly_dashboard.py  # текущая неделя
- python scripts/generate_weekly_dashboard.py --week 50 --year 2025
"""

import json
import sys
import statistics
from pathlib import Path
import sys

# Добавить system/scripts в sys.path для импорта config_loader
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from config_loader import get_project_root, get_path
from datetime import datetime, timedelta
import argparse
from string import Template
from collections import defaultdict

# Импорт функций
sys.path.append(str(Path(__file__).parent))
from analyze_reflection import parse_reflection_file

# Пути
PROJECT_ROOT = get_project_root()
REFLECTIONS_DIR = get_path("reflections")
DAILY_DIR = REFLECTIONS_DIR / "daily"
DASHBOARDS_DIR = get_path("dashboards") / "weekly"


def get_week_dates(year, week_number):
    """Получить даты начала и конца недели."""
    # Первый день года
    jan_1 = datetime(year, 1, 1)
    # Найти первый понедельник
    days_to_monday = (7 - jan_1.weekday()) % 7
    first_monday = jan_1 + timedelta(days=days_to_monday)

    # Начало нужной недели
    week_start = first_monday + timedelta(weeks=week_number - 1)
    week_end = week_start + timedelta(days=6)

    return week_start, week_end


def get_reflection_path(date):
    """Получить путь к рефлексии."""
    year = date.strftime("%Y")
    month = date.strftime("%m")
    filename = date.strftime("%Y-%m-%d")
    return DAILY_DIR / year / month / f"{filename}.md"


def collect_week_data(week_start, week_end):
    """Собрать данные за неделю."""
    week_data = []
    current_date = week_start

    while current_date <= week_end:
        reflection_path = get_reflection_path(current_date)

        if reflection_path.exists():
            try:
                data = parse_reflection_file(reflection_path)

                # Вычислить метрики
                operations_percent = data.get('operations_percent', 0)
                if operations_percent == 0:
                    operations_done = len(data.get('operations_done', []))
                    operations_percent = min(100, int((operations_done / 8) * 100))

                tactics_percent = data.get('tactics_percent', 0)
                evidence_count = len(data.get('evidence_done', []))

                week_data.append({
                    'date': current_date,
                    'day_name': current_date.strftime('%A'),
                    'operations_percent': operations_percent,
                    'tactics_percent': tactics_percent,
                    'evidence_count': evidence_count,
                    'rating': data.get('rating', 0)
                })
            except:
                week_data.append({
                    'date': current_date,
                    'day_name': current_date.strftime('%A'),
                    'operations_percent': 0,
                    'tactics_percent': 0,
                    'evidence_count': 0,
                    'rating': 0
                })

        current_date += timedelta(days=1)

    return week_data


def calculate_week_stats(week_data):
    """Вычислить статистику за неделю."""
    if not week_data:
        return {}

    operations_values = [d['operations_percent'] for d in week_data if d['operations_percent'] > 0]
    tactics_values = [d['tactics_percent'] for d in week_data if d['tactics_percent'] > 0]
    evidence_values = [d['evidence_count'] for d in week_data]

    return {
        'avg_operations': round(statistics.mean(operations_values), 1) if operations_values else 0,
        'avg_tactics': round(statistics.mean(tactics_values), 1) if tactics_values else 0,
        'avg_evidence_per_day': round(statistics.mean(evidence_values), 1) if evidence_values else 0,
        'total_evidence': sum(evidence_values),
        'days_tracked': len(week_data),
        'best_day': max(week_data, key=lambda d: d['operations_percent']) if week_data else None,
        'worst_day': min(week_data, key=lambda d: d['operations_percent']) if week_data else None
    }


def compare_weeks(current_stats, previous_stats):
    """Сравнить текущую и предыдущую неделю."""
    if not previous_stats:
        return {}

    return {
        'operations_change': round(current_stats['avg_operations'] - previous_stats['avg_operations'], 1),
        'tactics_change': round(current_stats['avg_tactics'] - previous_stats['avg_tactics'], 1),
        'evidence_change': round(current_stats['avg_evidence_per_day'] - previous_stats['avg_evidence_per_day'], 1)
    }


def generate_insights(week_data, current_stats, comparison):
    """Генерировать инсайты и рекомендации."""
    insights = []
    recommendations = []

    # Анализ выполнения операций
    if current_stats['avg_operations'] >= 80:
        insights.append("Отличное выполнение операций - вы на правильном пути!")
    elif current_stats['avg_operations'] < 60:
        recommendations.append("Упростите операционные действия или уменьшите их количество")

    # Сравнение с предыдущей неделей
    if comparison.get('operations_change', 0) > 5:
        insights.append(f"Прогресс! Выполнение операций выросло на {comparison['operations_change']}%")
    elif comparison.get('operations_change', 0) < -5:
        recommendations.append("Выполнение снизилось. Проанализируйте что изменилось")

    # Анализ по дням недели
    day_stats = defaultdict(list)
    for day_data in week_data:
        day_stats[day_data['day_name']].append(day_data['operations_percent'])

    weak_days = [day for day, values in day_stats.items() if statistics.mean(values) < 60]
    if weak_days:
        recommendations.append(f"Слабые дни: {', '.join(weak_days)}. Упростите план на эти дни")

    # Лучший и худший день
    if current_stats['best_day']:
        best = current_stats['best_day']
        insights.append(f"Лучший день: {best['date'].strftime('%A')} ({best['operations_percent']}%)")

    if current_stats['worst_day']:
        worst = current_stats['worst_day']
        if worst['operations_percent'] < 50:
            recommendations.append(f"Худший день: {worst['date'].strftime('%A')} ({worst['operations_percent']}%). Пересмотрите план")

    return insights, recommendations


def generate_html_dashboard(week_number, year, week_data, current_stats, previous_stats, comparison):
    """Генерировать HTML дашборд."""

    week_start = week_data[0]['date'] if week_data else datetime.now()
    week_end = week_data[-1]['date'] if week_data else datetime.now()

    # Инсайты и рекомендации
    insights, recommendations = generate_insights(week_data, current_stats, comparison)

    # Таблица сравнения
    ops_change = comparison.get('operations_change', 0)
    tactics_change = comparison.get('tactics_change', 0)
    evidence_change = comparison.get('evidence_change', 0)

    ops_arrow = "↑" if ops_change > 0 else "↓" if ops_change < 0 else "→"
    tactics_arrow = "↑" if tactics_change > 0 else "↓" if tactics_change < 0 else "→"
    evidence_arrow = "↑" if evidence_change > 0 else "↓" if evidence_change < 0 else "→"

    prev_ops = previous_stats.get('avg_operations', 0) if previous_stats else 0
    prev_tactics = previous_stats.get('avg_tactics', 0) if previous_stats else 0
    prev_evidence = previous_stats.get('avg_evidence_per_day', 0) if previous_stats else 0

    # График по дням недели
    day_chart_bars = ""
    for day_data in week_data:
        day_name_short = day_data['date'].strftime('%a')
        ops_percent = day_data['operations_percent']
        bar_width = ops_percent
        color = '#34c759' if ops_percent >= 80 else '#ffcc00' if ops_percent >= 60 else '#ff3b30'

        day_chart_bars += f'''
        <div style="margin-bottom: 10px;">
            <div style="display: flex; align-items: center;">
                <span style="width: 50px; font-size: 13px; color: #666;">{day_name_short}:</span>
                <div style="flex: 1; height: 25px; background: #e0e0e0; border-radius: 12px; overflow: hidden;">
                    <div style="width: {bar_width}%; height: 100%; background: {color}; display: flex; align-items: center; padding-left: 10px; color: white; font-size: 12px; font-weight: 600;">
                        {ops_percent}%
                    </div>
                </div>
            </div>
        </div>
        '''

    # Топ достижения
    achievements = []
    if current_stats['avg_operations'] >= 80:
        achievements.append("🎉 Отличный процент выполнения операций!")
    if current_stats['total_evidence'] >= 10:
        achievements.append(f"📈 Накоплено {current_stats['total_evidence']} доказательств идентичности")
    if ops_change > 10:
        achievements.append(f"💪 Прогресс вырос на {ops_change}%")

    achievements_html = ""
    for i, achievement in enumerate(achievements[:3], 1):
        achievements_html += f"<li>{achievement}</li>\n"

    if not achievements_html:
        achievements_html = "<li>Продолжайте работать над своими целями!</li>"

    # Рекомендации
    recommendations_html = ""
    for recommendation in recommendations[:3]:
        recommendations_html += f"<li>{recommendation}</li>\n"

    if not recommendations_html:
        recommendations_html = "<li>План работает хорошо, значительных изменений не требуется</li>"

    # Инсайты
    insights_html = ""
    for insight in insights[:3]:
        insights_html += f"<li>{insight}</li>\n"

    html_template = Template('''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Недельный дашборд: Неделя $week_number, $year</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #f5f5f7;
            padding: 20px;
            line-height: 1.6;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        header {
            background: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        h1 {
            font-size: 28px;
            color: #1d1d1f;
            margin-bottom: 10px;
        }
        .period {
            color: #86868b;
            font-size: 16px;
        }
        .card {
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .section-title {
            font-size: 22px;
            font-weight: 600;
            color: #1d1d1f;
            margin-bottom: 15px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        th, td {
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid #e0e0e0;
        }
        th {
            font-weight: 600;
            color: #1d1d1f;
            font-size: 14px;
        }
        td {
            color: #515154;
            font-size: 14px;
        }
        .change-positive {
            color: #34c759;
            font-weight: 600;
        }
        .change-negative {
            color: #ff3b30;
            font-weight: 600;
        }
        .change-neutral {
            color: #86868b;
        }
        ul {
            list-style-position: inside;
            color: #515154;
        }
        li {
            margin-bottom: 8px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📈 Недельный дашборд: Неделя $week_number, $year</h1>
            <p class="period">Период: $week_start — $week_end</p>
        </header>

        <div class="card">
            <h2 class="section-title">Сводка недели</h2>
            <table>
                <thead>
                    <tr>
                        <th>Показатель</th>
                        <th>Эта неделя</th>
                        <th>Прошлая неделя</th>
                        <th>Изменение</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>Операции</strong></td>
                        <td>$current_operations%</td>
                        <td>$previous_operations%</td>
                        <td class="$ops_change_class">$ops_arrow $ops_change_abs%</td>
                    </tr>
                    <tr>
                        <td><strong>Тактика</strong></td>
                        <td>$current_tactics%</td>
                        <td>$previous_tactics%</td>
                        <td class="$tactics_change_class">$tactics_arrow $tactics_change_abs%</td>
                    </tr>
                    <tr>
                        <td><strong>Доказательства/день</strong></td>
                        <td>$current_evidence</td>
                        <td>$previous_evidence</td>
                        <td class="$evidence_change_class">$evidence_arrow $evidence_change_abs</td>
                    </tr>
                </tbody>
            </table>
        </div>

        <div class="card">
            <h2 class="section-title">График выполнения по дням</h2>
            $day_chart_bars
        </div>

        <div class="card">
            <h2 class="section-title">Топ-3 достижения</h2>
            <ul>
                $achievements_html
            </ul>
        </div>

        <div class="card">
            <h2 class="section-title">Области для улучшения</h2>
            <ul>
                $recommendations_html
            </ul>
        </div>

        <div class="card">
            <h2 class="section-title">Инсайты</h2>
            <ul>
                $insights_html
            </ul>
        </div>
    </div>
</body>
</html>''')

    # Классы для изменений
    ops_change_class = "change-positive" if ops_change > 0 else "change-negative" if ops_change < 0 else "change-neutral"
    tactics_change_class = "change-positive" if tactics_change > 0 else "change-negative" if tactics_change < 0 else "change-neutral"
    evidence_change_class = "change-positive" if evidence_change > 0 else "change-negative" if evidence_change < 0 else "change-neutral"

    html = html_template.substitute(
        week_number=week_number,
        year=year,
        week_start=week_start.strftime('%d.%m.%Y'),
        week_end=week_end.strftime('%d.%m.%Y'),
        current_operations=current_stats['avg_operations'],
        current_tactics=current_stats['avg_tactics'],
        current_evidence=current_stats['avg_evidence_per_day'],
        previous_operations=prev_ops,
        previous_tactics=prev_tactics,
        previous_evidence=prev_evidence,
        ops_arrow=ops_arrow,
        ops_change_abs=abs(ops_change),
        ops_change_class=ops_change_class,
        tactics_arrow=tactics_arrow,
        tactics_change_abs=abs(tactics_change),
        tactics_change_class=tactics_change_class,
        evidence_arrow=evidence_arrow,
        evidence_change_abs=abs(evidence_change),
        evidence_change_class=evidence_change_class,
        day_chart_bars=day_chart_bars,
        achievements_html=achievements_html,
        recommendations_html=recommendations_html,
        insights_html=insights_html
    )

    return html


def generate_markdown_dashboard(week_number, year, week_data, current_stats, previous_stats, comparison):
    """Генерировать markdown дашборд."""

    week_start = week_data[0]['date'] if week_data else datetime.now()
    week_end = week_data[-1]['date'] if week_data else datetime.now()

    md = f"# Недельный дашборд: Неделя {week_number}, {year}\n\n"
    md += f"**Период:** {week_start.strftime('%d.%m.%Y')} — {week_end.strftime('%d.%m.%Y')}\n\n"

    md += "## Сводка недели\n\n"
    md += "| Показатель | Эта неделя | Прошлая неделя | Изменение |\n"
    md += "|------------|------------|----------------|----------|\n"

    ops_change = comparison.get('operations_change', 0)
    ops_arrow = "↑" if ops_change > 0 else "↓" if ops_change < 0 else "→"
    md += f"| Операции | {current_stats['avg_operations']}% | {previous_stats.get('avg_operations', 0)}% | {ops_arrow} {abs(ops_change)}% |\n"

    tactics_change = comparison.get('tactics_change', 0)
    tactics_arrow = "↑" if tactics_change > 0 else "↓" if tactics_change < 0 else "→"
    md += f"| Тактика | {current_stats['avg_tactics']}% | {previous_stats.get('avg_tactics', 0)}% | {tactics_arrow} {abs(tactics_change)}% |\n"

    evidence_change = comparison.get('evidence_change', 0)
    evidence_arrow = "↑" if evidence_change > 0 else "↓" if evidence_change < 0 else "→"
    md += f"| Доказательства/день | {current_stats['avg_evidence_per_day']} | {previous_stats.get('avg_evidence_per_day', 0)} | {evidence_arrow} {abs(evidence_change)} |\n\n"

    md += "## График выполнения\n\n"
    md += "```\n"
    for day_data in week_data:
        day_short = day_data['date'].strftime('%a')
        ops_bar = '█' * int(day_data['operations_percent'] / 10)
        md += f"{day_short}: {ops_bar:<10} {day_data['operations_percent']}%\n"
    md += "```\n\n"

    # Инсайты и рекомендации
    insights, recommendations = generate_insights(week_data, current_stats, comparison)

    md += "## Инсайты\n\n"
    for insight in insights:
        md += f"- {insight}\n"

    md += "\n## Рекомендации\n\n"
    for rec in recommendations:
        md += f"- {rec}\n"

    return md


def main():
    """Главная функция."""
    parser = argparse.ArgumentParser(description='Генерация недельного дашборда')
    parser.add_argument('--week', type=int, help='Номер недели')
    parser.add_argument('--year', type=int, help='Год')

    args = parser.parse_args()

    # Определить неделю и год
    if args.week and args.year:
        week_number = args.week
        year = args.year
    else:
        today = datetime.now()
        week_number = today.isocalendar()[1]
        year = today.year

    print(f"Генерация недельного дашборда: Неделя {week_number}, {year}...\n")

    # Получить даты недели
    week_start, week_end = get_week_dates(year, week_number)

    # Собрать данные за текущую неделю
    week_data = collect_week_data(week_start, week_end)

    if not week_data:
        print("❌ Нет данных за эту неделю")
        sys.exit(1)

    # Вычислить статистику
    current_stats = calculate_week_stats(week_data)

    # Собрать данные за предыдущую неделю
    prev_week_start = week_start - timedelta(weeks=1)
    prev_week_end = week_end - timedelta(weeks=1)
    prev_week_data = collect_week_data(prev_week_start, prev_week_end)
    previous_stats = calculate_week_stats(prev_week_data)

    # Сравнить
    comparison = compare_weeks(current_stats, previous_stats)

    # Генерировать HTML
    html = generate_html_dashboard(week_number, year, week_data, current_stats, previous_stats, comparison)

    # Сохранить HTML
    DASHBOARDS_DIR.mkdir(parents=True, exist_ok=True)
    html_path = DASHBOARDS_DIR / f"week_{week_number:02d}_{year}.html"

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ HTML дашборд: {html_path}")

    # Генерировать markdown
    markdown = generate_markdown_dashboard(week_number, year, week_data, current_stats, previous_stats, comparison)

    # Сохранить markdown
    md_path = DASHBOARDS_DIR / f"week_{week_number:02d}_{year}.md"

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(markdown)

    print(f"✅ Markdown дашборд: {md_path}")
    print("\n🎉 Недельный дашборд создан успешно!")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
