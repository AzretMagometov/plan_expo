#!/usr/bin/env python3
"""
Скрипт для генерации дневного HTML дашборда.

Создает:
- Интерактивный HTML дашборд с визуализацией
- SVG графики трендов
- Адаптивный дизайн
- Также markdown версию

Использование:
- python scripts/generate_daily_dashboard.py                # сегодня
- python scripts/generate_daily_dashboard.py --date 2025-12-21  # за дату
"""

import json
import sys
from pathlib import Path
import sys

# Добавить system/scripts в sys.path для импорта config_loader
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from config_loader import get_project_root, get_path
from datetime import datetime, timedelta
import argparse
from string import Template

# Импорт функций
sys.path.append(str(Path(__file__).parent))
from analyze_reflection import parse_reflection_file

# Пути
PROJECT_ROOT = get_project_root()
REFLECTIONS_DIR = get_path("reflections")
DAILY_DIR = REFLECTIONS_DIR / "daily"
DASHBOARDS_DIR = get_path("dashboards") / "daily"
STREAKS_DIR = get_path("dashboards") / "streaks"


def get_reflection_path(date):
    """Получить путь к рефлексии."""
    year = date.strftime("%Y")
    month = date.strftime("%m")
    filename = date.strftime("%Y-%m-%d")
    return DAILY_DIR / year / month / f"{filename}.md"


def load_streaks_data():
    """Загрузить данные о streaks."""
    streaks_file = STREAKS_DIR / "streaks_data.json"
    if streaks_file.exists():
        with open(streaks_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'habits': []}


def calculate_metrics(reflection_data):
    """Вычислить показатели из рефлексии."""
    # Операции
    operations_percent = reflection_data.get('operations_percent', 0)
    if operations_percent == 0:
        # Вычислить из выполненных операций
        operations_done = len(reflection_data.get('operations_done', []))
        operations_percent = min(100, int((operations_done / 8) * 100))

    # Тактика
    tactics_percent = reflection_data.get('tactics_percent', 0)

    # Доказательства
    evidence_count = len(reflection_data.get('evidence_done', []))

    # Оценки
    rating = reflection_data.get('rating', 0)
    energy = reflection_data.get('energy', 'средняя')
    motivation = reflection_data.get('motivation', 'средняя')
    focus = reflection_data.get('focus', 'средний')

    return {
        'operations_percent': operations_percent,
        'tactics_percent': tactics_percent,
        'evidence_count': evidence_count,
        'rating': rating,
        'energy': energy,
        'motivation': motivation,
        'focus': focus
    }


def get_color_for_percentage(percent):
    """Получить цвет для процента."""
    if percent is None:
        percent = 0
    if percent >= 80:
        return '#34c759'  # Зеленый
    elif percent >= 60:
        return '#ffcc00'  # Желтый
    else:
        return '#ff3b30'  # Красный


def calculate_trends(date, days=7):
    """Вычислить тренды за последние дни."""
    trends = []

    for i in range(days):
        trend_date = date - timedelta(days=days - 1 - i)
        reflection_path = get_reflection_path(trend_date)

        if reflection_path.exists():
            try:
                data = parse_reflection_file(reflection_path)
                metrics = calculate_metrics(data)
                trends.append({
                    'date': trend_date.strftime('%d.%m'),
                    'operations': metrics['operations_percent'],
                    'tactics': metrics['tactics_percent']
                })
            except:
                trends.append({
                    'date': trend_date.strftime('%d.%m'),
                    'operations': 0,
                    'tactics': 0
                })
        else:
            trends.append({
                'date': trend_date.strftime('%d.%m'),
                'operations': 0,
                'tactics': 0
            })

    return trends


def generate_svg_chart(trends, width=800, height=200):
    """Генерировать SVG график трендов."""
    if not trends:
        return ""

    # Параметры
    padding = 40
    chart_width = width - 2 * padding
    chart_height = height - 2 * padding

    # Масштабирование
    max_value = 100
    x_step = chart_width / (len(trends) - 1) if len(trends) > 1 else 0

    # Точки для операций
    operations_points = []
    for i, trend in enumerate(trends):
        x = padding + i * x_step
        operations_value = trend['operations'] if trend['operations'] is not None else 0
        y = padding + chart_height - (operations_value / max_value * chart_height)
        operations_points.append(f"{x},{y}")

    # Точки для тактики
    tactics_points = []
    for i, trend in enumerate(trends):
        x = padding + i * x_step
        tactics_value = trend['tactics'] if trend['tactics'] is not None else 0
        y = padding + chart_height - (tactics_value / max_value * chart_height)
        tactics_points.append(f"{x},{y}")

    # SVG
    svg = f'''<svg width="{width}" height="{height}" style="background: #f5f5f7; border-radius: 8px;">
        <!-- Оси -->
        <line x1="{padding}" y1="{padding}" x2="{padding}" y2="{padding + chart_height}" stroke="#666" stroke-width="1"/>
        <line x1="{padding}" y1="{padding + chart_height}" x2="{padding + chart_width}" y2="{padding + chart_height}" stroke="#666" stroke-width="1"/>

        <!-- Горизонтальные линии (сетка) -->
        <line x1="{padding}" y1="{padding + chart_height * 0.25}" x2="{padding + chart_width}" y2="{padding + chart_height * 0.25}" stroke="#ddd" stroke-width="1" stroke-dasharray="5,5"/>
        <line x1="{padding}" y1="{padding + chart_height * 0.5}" x2="{padding + chart_width}" y2="{padding + chart_height * 0.5}" stroke="#ddd" stroke-width="1" stroke-dasharray="5,5"/>
        <line x1="{padding}" y1="{padding + chart_height * 0.75}" x2="{padding + chart_width}" y2="{padding + chart_height * 0.75}" stroke="#ddd" stroke-width="1" stroke-dasharray="5,5"/>

        <!-- Метки на оси Y -->
        <text x="{padding - 10}" y="{padding}" text-anchor="end" font-size="12" fill="#666">100%</text>
        <text x="{padding - 10}" y="{padding + chart_height * 0.5}" text-anchor="end" font-size="12" fill="#666">50%</text>
        <text x="{padding - 10}" y="{padding + chart_height}" text-anchor="end" font-size="12" fill="#666">0%</text>

        <!-- Линия операций -->
        <polyline points="{' '.join(operations_points)}" fill="none" stroke="#007aff" stroke-width="3"/>

        <!-- Линия тактики -->
        <polyline points="{' '.join(tactics_points)}" fill="none" stroke="#ff6b35" stroke-width="3"/>

        <!-- Метки на оси X -->
'''

    for i, trend in enumerate(trends):
        x = padding + i * x_step
        svg += f'<text x="{x}" y="{padding + chart_height + 20}" text-anchor="middle" font-size="11" fill="#666">{trend["date"]}</text>\n'

    # Легенда
    svg += f'''
        <!-- Легенда -->
        <rect x="{width - 150}" y="10" width="15" height="15" fill="#007aff"/>
        <text x="{width - 130}" y="22" font-size="12" fill="#333">Операции</text>

        <rect x="{width - 150}" y="30" width="15" height="15" fill="#ff6b35"/>
        <text x="{width - 130}" y="42" font-size="12" fill="#333">Тактика</text>
    </svg>'''

    return svg


def generate_html_dashboard(date, metrics, trends, streaks_data):
    """Генерировать HTML дашборд."""

    # Вычислить общий streak
    current_streak = 0
    if streaks_data and streaks_data.get('habits'):
        # Взять максимальный streak
        current_streak = max((h.get('current_streak', 0) for h in streaks_data['habits']), default=0)

    # Цвета для прогресс-баров
    operations_color = get_color_for_percentage(metrics['operations_percent'])
    tactics_color = get_color_for_percentage(metrics['tactics_percent'])

    # SVG график
    svg_chart = generate_svg_chart(trends)

    # HTML
    html_template = Template('''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Дашборд: $date_formatted</title>
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
        .streak {
            color: #ff6b35;
            font-size: 48px;
            font-weight: bold;
            margin-top: 10px;
        }
        .cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .card {
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .card h3 {
            font-size: 16px;
            color: #86868b;
            margin-bottom: 15px;
            font-weight: 500;
        }
        .progress-bar {
            height: 30px;
            background: #e0e0e0;
            border-radius: 15px;
            overflow: hidden;
            margin-bottom: 10px;
        }
        .progress-fill {
            height: 100%;
            transition: width 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 14px;
        }
        .value-large {
            font-size: 48px;
            font-weight: bold;
            color: #1d1d1f;
            margin-bottom: 5px;
        }
        .value-label {
            color: #86868b;
            font-size: 14px;
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
        .section-title {
            font-size: 22px;
            font-weight: 600;
            color: #1d1d1f;
            margin-bottom: 15px;
        }
        .chart-container {
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        @media (max-width: 768px) {
            .cards {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Дашборд: $date_formatted</h1>
            <p class="streak">🔥 Streak: $current_streak дней</p>
        </header>

        <div class="cards">
            <div class="card">
                <h3>Операции</h3>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: $operations_percent%; background: $operations_color;">
                        $operations_percent%
                    </div>
                </div>
                <p class="value-label">выполнено</p>
            </div>

            <div class="card">
                <h3>Тактика</h3>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: $tactics_percent%; background: $tactics_color;">
                        $tactics_percent%
                    </div>
                </div>
                <p class="value-label">выполнено</p>
            </div>

            <div class="card">
                <h3>Доказательств идентичности</h3>
                <div class="value-large" style="color: #34c759;">$evidence_count</div>
                <p class="value-label">за сегодня</p>
            </div>
        </div>

        <div class="chart-container">
            <h2 class="section-title">Тренды (7 дней)</h2>
            $svg_chart
        </div>

        <div class="card">
            <h2 class="section-title">Топ-5 привычек</h2>
            <table>
                <tr>
                    <th>Привычка</th>
                    <th>Streak</th>
                    <th>7 дней</th>
                </tr>
                $habits_rows
            </table>
        </div>

        <div class="card" style="margin-top: 20px;">
            <h2 class="section-title">Оценки дня</h2>
            <table>
                <tr><td><strong>Общая оценка:</strong></td><td>$rating/10</td></tr>
                <tr><td><strong>Энергия:</strong></td><td>$energy</td></tr>
                <tr><td><strong>Мотивация:</strong></td><td>$motivation</td></tr>
                <tr><td><strong>Фокус:</strong></td><td>$focus</td></tr>
            </table>
        </div>
    </div>
</body>
</html>''')

    # Таблица привычек
    habits_rows = ""
    if streaks_data and streaks_data.get('habits'):
        top_habits = sorted(
            streaks_data['habits'],
            key=lambda h: h.get('current_streak', 0),
            reverse=True
        )[:5]

        for habit in top_habits:
            name = habit.get('name', '')[:40]
            streak = habit.get('current_streak', 0)
            rate_7d = habit.get('completion_rate_7d', 0)
            emoji = "🔥" if streak >= 7 else "⚡" if streak >= 3 else "💪"

            habits_rows += f'<tr><td>{name}...</td><td>{emoji} {streak}</td><td>{rate_7d}%</td></tr>\n'

    if not habits_rows:
        habits_rows = '<tr><td colspan="3">Нет данных о привычках</td></tr>'

    # Подставить значения
    html = html_template.substitute(
        date_formatted=date.strftime('%d.%m.%Y'),
        current_streak=current_streak,
        operations_percent=metrics['operations_percent'],
        operations_color=operations_color,
        tactics_percent=metrics['tactics_percent'],
        tactics_color=tactics_color,
        evidence_count=metrics['evidence_count'],
        svg_chart=svg_chart,
        habits_rows=habits_rows,
        rating=metrics['rating'] if metrics['rating'] else '—',
        energy=metrics['energy'],
        motivation=metrics['motivation'],
        focus=metrics['focus']
    )

    return html


def generate_markdown_dashboard(date, metrics, trends):
    """Генерировать markdown дашборд."""

    md = f"# Дашборд: {date.strftime('%d.%m.%Y')}\n\n"

    md += "## Основные показатели\n\n"
    md += f"- **Операции:** {metrics['operations_percent']}%\n"
    md += f"- **Тактика:** {metrics['tactics_percent']}%\n"
    md += f"- **Доказательств:** {metrics['evidence_count']}\n\n"

    md += "## Тренды (7 дней)\n\n"
    md += "```\n"
    for trend in trends:
        operations_value = trend['operations'] if trend['operations'] is not None else 0
        ops_bar = '█' * int(operations_value / 10)
        md += f"{trend['date']}: {ops_bar:<10} {operations_value}%\n"
    md += "```\n\n"

    md += "## Оценки\n\n"
    md += f"- **Общая оценка:** {metrics['rating']}/10\n"
    md += f"- **Энергия:** {metrics['energy']}\n"
    md += f"- **Мотивация:** {metrics['motivation']}\n"
    md += f"- **Фокус:** {metrics['focus']}\n"

    return md


def main():
    """Главная функция."""
    parser = argparse.ArgumentParser(description='Генерация дневного дашборда')
    parser.add_argument('--date', type=str, help='Дата в формате YYYY-MM-DD')

    args = parser.parse_args()

    # Дата
    if args.date:
        date = datetime.strptime(args.date, "%Y-%m-%d")
    else:
        date = datetime.now()

    print(f"Генерация дашборда за {date.strftime('%Y-%m-%d')}...\n")

    # Загрузить рефлексию
    reflection_path = get_reflection_path(date)

    if not reflection_path.exists():
        print(f"❌ Рефлексия не найдена: {reflection_path}")
        sys.exit(1)

    try:
        reflection_data = parse_reflection_file(reflection_path)
    except Exception as e:
        print(f"❌ Ошибка парсинга рефлексии: {e}")
        sys.exit(1)

    # Вычислить метрики
    metrics = calculate_metrics(reflection_data)

    # Вычислить тренды
    trends = calculate_trends(date)

    # Загрузить данные о streaks
    streaks_data = load_streaks_data()

    # Генерировать HTML
    html = generate_html_dashboard(date, metrics, trends, streaks_data)

    # Сохранить HTML
    DASHBOARDS_DIR.mkdir(parents=True, exist_ok=True)
    html_path = DASHBOARDS_DIR / f"{date.strftime('%Y-%m-%d')}.html"

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ HTML дашборд: {html_path}")

    # Генерировать markdown
    markdown = generate_markdown_dashboard(date, metrics, trends)

    # Сохранить markdown
    md_path = DASHBOARDS_DIR / f"{date.strftime('%Y-%m-%d')}.md"

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(markdown)

    print(f"✅ Markdown дашборд: {md_path}")
    print("\n🎉 Дашборд создан успешно!")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
