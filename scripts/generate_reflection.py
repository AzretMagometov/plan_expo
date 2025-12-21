#!/usr/bin/env python3
"""
Скрипт для генерации шаблонов рефлексий на основе активных целей.
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import json
import re

# Пути к директориям
PROJECT_ROOT = Path(__file__).parent.parent
GOALS_DIR = PROJECT_ROOT / "goals"
REFLECTIONS_DIR = PROJECT_ROOT / "reflections"
DAILY_DIR = REFLECTIONS_DIR / "daily"

def parse_goal_file(goal_path):
    """Парсит файл цели и извлекает структурированные данные."""
    with open(goal_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    goal_data = {
        'id': goal_path.stem,
        'title': '',
        'status': 'active',
        'identity': '',
        'beliefs': [],
        'evidence': [],
        'operations': {
            'if_then': [],
            'tiny_habits': []
        },
        'tactics': {
            'method': '',
            'objective': '',
            'key_results': [],
            'smart_goal': ''
        }
    }
    
    # Извлечение названия
    title_match = re.search(r'^# Цель:\s*(.+)$', content, re.MULTILINE)
    if title_match:
        goal_data['title'] = title_match.group(1).strip()
    
    # Извлечение статуса
    status_match = re.search(r'\*\*Статус:\*\*\s*(.+)$', content, re.MULTILINE)
    if status_match:
        goal_data['status'] = status_match.group(1).strip()
    
    # Извлечение идентичности
    identity_match = re.search(r'\*\*Идентичность:\*\*\s*(.+)$', content, re.MULTILINE)
    if identity_match:
        goal_data['identity'] = identity_match.group(1).strip()
    
    # Извлечение убеждений
    beliefs_section = re.search(r'\*\*Убеждения:\*\*\s*\n((?:- .+\n?)+)', content, re.MULTILINE)
    if beliefs_section:
        goal_data['beliefs'] = [
            line.strip('- ').strip() 
            for line in beliefs_section.group(1).strip().split('\n')
            if line.strip()
        ]
    
    # Извлечение доказательств
    evidence_section = re.search(r'\*\*Доказательства идентичности:\*\*\s*\n((?:- .+\n?)+)', content, re.MULTILINE)
    if evidence_section:
        goal_data['evidence'] = [
            line.strip('- ').strip() 
            for line in evidence_section.group(1).strip().split('\n')
            if line.strip()
        ]
    
    # Извлечение Implementation Intentions
    if_then_section = re.search(r'### Implementation Intentions:\s*\n((?:- .+\n?)+)', content, re.MULTILINE)
    if if_then_section:
        goal_data['operations']['if_then'] = [
            line.strip('- ').strip() 
            for line in if_then_section.group(1).strip().split('\n')
            if line.strip()
        ]
    
    # Извлечение Tiny Habits
    tiny_habits_section = re.search(r'### Tiny Habits:\s*\n((?:- .+\n?)+)', content, re.MULTILINE)
    if tiny_habits_section:
        goal_data['operations']['tiny_habits'] = [
            line.strip('- ').strip() 
            for line in tiny_habits_section.group(1).strip().split('\n')
            if line.strip()
        ]
    
    # Извлечение метода тактики
    method_match = re.search(r'\*\*Метод:\*\*\s*(OKR|SMART)', content, re.MULTILINE)
    if method_match:
        goal_data['tactics']['method'] = method_match.group(1)
    
    # Извлечение Objective
    objective_match = re.search(r'### Objective \(если OKR\):\s*\n(.+?)(?=\n###|\n\*\*|$)', content, re.DOTALL)
    if objective_match:
        goal_data['tactics']['objective'] = objective_match.group(1).strip()
    
    # Извлечение Key Results
    kr_section = re.search(r'### Key Results:\s*\n((?:- .+\n?)+)', content, re.MULTILINE)
    if kr_section:
        goal_data['tactics']['key_results'] = [
            line.strip('- ').strip() 
            for line in kr_section.group(1).strip().split('\n')
            if line.strip()
        ]
    
    # Извлечение SMART-цели
    smart_section = re.search(r'### SMART-цель \(если SMART\):\s*\n(.+?)(?=\n###|\n\*\*|$)', content, re.DOTALL)
    if smart_section:
        goal_data['tactics']['smart_goal'] = smart_section.group(1).strip()
    
    return goal_data

def get_active_goals():
    """Получает все активные цели из директории goals/."""
    active_goals = []
    
    if not GOALS_DIR.exists():
        return active_goals
    
    for goal_file in GOALS_DIR.glob("*.md"):
        goal_data = parse_goal_file(goal_file)
        if goal_data['status'] == 'active':
            active_goals.append(goal_data)
    
    return active_goals

def generate_daily_reflection_template(date=None):
    """Генерирует шаблон ежедневной рефлексии для указанной даты."""
    if date is None:
        date = datetime.now()
    elif isinstance(date, str):
        date = datetime.strptime(date, "%Y-%m-%d")
    
    # Получаем активные цели
    active_goals = get_active_goals()
    
    if not active_goals:
        print("⚠️  Нет активных целей. Создайте цель перед генерацией рефлексии.")
        return None
    
    # Создаём структуру директорий
    year = date.strftime("%Y")
    month = date.strftime("%m")
    reflection_dir = DAILY_DIR / year / month
    reflection_dir.mkdir(parents=True, exist_ok=True)
    
    # Путь к файлу рефлексии
    reflection_file = reflection_dir / f"{date.strftime('%Y-%m-%d')}.md"
    
    # Генерируем содержимое
    content = f"""# Ежедневная рефлексия: {date.strftime('%d.%m.%Y')}

## Активные цели

"""
    
    for goal in active_goals:
        content += f"- **{goal['title']}**\n"
        if goal['identity']:
            content += f"  - Идентичность: {goal['identity']}\n"
        if goal['tactics']['objective']:
            content += f"  - Objective: {goal['tactics']['objective']}\n"
        elif goal['tactics']['smart_goal']:
            content += f"  - SMART-цель: {goal['tactics']['smart_goal'][:100]}...\n"
        content += "\n"
    
    content += "---\n\n## План на сегодня\n\n### Операционные действия\n\n#### Implementation Intentions:\n"
    
    # Собираем все If-Then планы
    all_if_then = []
    for goal in active_goals:
        all_if_then.extend(goal['operations']['if_then'])
    
    if all_if_then:
        for if_then in all_if_then:
            content += f"- [ ] {if_then}\n"
    else:
        content += "- [ ] (нет активных If-Then планов)\n"
    
    content += "\n#### Tiny Habits:\n"
    
    # Собираем все Tiny Habits
    all_tiny_habits = []
    for goal in active_goals:
        all_tiny_habits.extend(goal['operations']['tiny_habits'])
    
    if all_tiny_habits:
        for habit in all_tiny_habits:
            content += f"- [ ] {habit}\n"
    else:
        content += "- [ ] (нет активных Tiny Habits)\n"
    
    content += "\n### Тактические задачи\n\n"
    
    # Собираем задачи из Key Results
    for goal in active_goals:
        if goal['tactics']['key_results']:
            content += f"**{goal['title']}:**\n"
            for kr in goal['tactics']['key_results']:
                # Извлекаем только описание KR без метрик
                kr_desc = kr.split('|')[0].strip() if '|' in kr else kr.strip()
                content += f"- [ ] {kr_desc}\n"
            content += "\n"
    
    content += "---\n\n## Выполнение\n\n### Что сделано\n\n#### Операции:\n"
    content += "- [ ] \n\n#### Тактика:\n"
    content += "- [ ] \n\n### Доказательства идентичности\n\n"
    
    # Собираем все доказательства
    all_evidence = []
    for goal in active_goals:
        all_evidence.extend(goal['evidence'])
    
    if all_evidence:
        for evidence in all_evidence:
            content += f"- [ ] {evidence}\n"
    else:
        content += "- [ ] (нет активных доказательств для отслеживания)\n"
    
    content += "\n### Препятствия и решения\n\n**Что помешало:**\n"
    content += "- \n\n**Что помогло:**\n"
    content += "- \n\n---\n\n## Оценка дня\n\n"
    content += "**Общая оценка:** [1-10]\n\n"
    content += "**Выполнение операций:** [%]\n"
    content += "**Выполнение тактики:** [%]\n\n"
    content += "**Энергия:** [высокая | средняя | низкая]\n"
    content += "**Мотивация:** [высокая | средняя | низкая]\n"
    content += "**Фокус:** [высокий | средний | низкий]\n\n"
    content += "---\n\n## Инсайты и наблюдения\n\n"
    content += "[Свободные заметки о дне, что узнал, что изменилось]\n\n"
    content += "---\n\n## План на завтра\n\n"
    content += "[Ключевые действия на следующий день]\n\n"
    content += "---\n\n## Комментарии ИИ-системы\n\n"
    content += "*[Автоматически генерируется после анализа заполненной рефлексии]*\n\n"
    content += "### Анализ прогресса:\n"
    content += "- \n\n### Рекомендации:\n"
    content += "- \n\n### Адаптации:\n"
    content += "- \n"
    
    # Сохраняем файл
    with open(reflection_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Шаблон рефлексии создан: {reflection_file}")
    return reflection_file

def main():
    """Главная функция."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Генерация шаблона ежедневной рефлексии')
    parser.add_argument('--date', type=str, help='Дата в формате YYYY-MM-DD (по умолчанию сегодня)')
    
    args = parser.parse_args()
    
    try:
        generate_daily_reflection_template(args.date)
    except Exception as e:
        print(f"❌ Ошибка: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

