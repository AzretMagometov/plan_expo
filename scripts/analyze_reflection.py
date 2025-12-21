#!/usr/bin/env python3
"""
Скрипт для анализа заполненной рефлексии и генерации комментариев ИИ-системы.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
import re

# Пути к директориям
PROJECT_ROOT = Path(__file__).parent.parent
GOALS_DIR = PROJECT_ROOT / "goals"
REFLECTIONS_DIR = PROJECT_ROOT / "reflections"
DAILY_DIR = REFLECTIONS_DIR / "daily"

def parse_reflection_file(reflection_path):
    """Парсит файл рефлексии и извлекает данные."""
    with open(reflection_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    reflection_data = {
        'date': reflection_path.stem,
        'operations_done': [],
        'tactics_done': [],
        'evidence_done': [],
        'obstacles': [],
        'helpful_factors': [],
        'rating': None,
        'operations_percent': None,
        'tactics_percent': None,
        'energy': None,
        'motivation': None,
        'focus': None,
        'insights': '',
        'plan_tomorrow': ''
    }
    
    # Извлечение выполненных операций
    operations_section = re.search(r'#### Операции:\s*\n((?:- \[[ x]\] .+\n?)+)', content, re.MULTILINE)
    if operations_section:
        for line in operations_section.group(1).strip().split('\n'):
            if line.strip() and not line.strip().startswith('- [ ]') and not line.strip().startswith('- [x]'):
                continue
            if '[x]' in line or '[X]' in line:
                action = re.sub(r'- \[[xX]\]\s*', '', line).strip()
                if action:
                    reflection_data['operations_done'].append(action)
    
    # Извлечение выполненных тактических задач
    tactics_section = re.search(r'#### Тактика:\s*\n((?:- \[[ x]\] .+\n?)+)', content, re.MULTILINE)
    if tactics_section:
        for line in tactics_section.group(1).strip().split('\n'):
            if '[x]' in line or '[X]' in line:
                task = re.sub(r'- \[[xX]\]\s*', '', line).strip()
                if task:
                    reflection_data['tactics_done'].append(task)
    
    # Извлечение доказательств идентичности
    evidence_section = re.search(r'### Доказательства идентичности\s*\n((?:- \[[ x]\] .+\n?)+)', content, re.MULTILINE)
    if evidence_section:
        for line in evidence_section.group(1).strip().split('\n'):
            if '[x]' in line or '[X]' in line:
                evidence = re.sub(r'- \[[xX]\]\s*', '', line).strip()
                if evidence:
                    reflection_data['evidence_done'].append(evidence)
    
    # Извлечение препятствий
    obstacles_section = re.search(r'\*\*Что помешало:\*\*\s*\n((?:- .+\n?)+)', content, re.MULTILINE)
    if obstacles_section:
        reflection_data['obstacles'] = [
            line.strip('- ').strip() 
            for line in obstacles_section.group(1).strip().split('\n')
            if line.strip() and not line.strip() == '-'
        ]
    
    # Извлечение полезных факторов
    helpful_section = re.search(r'\*\*Что помогло:\*\*\s*\n((?:- .+\n?)+)', content, re.MULTILINE)
    if helpful_section:
        reflection_data['helpful_factors'] = [
            line.strip('- ').strip() 
            for line in helpful_section.group(1).strip().split('\n')
            if line.strip() and not line.strip() == '-'
        ]
    
    # Извлечение оценки
    rating_match = re.search(r'\*\*Общая оценка:\*\*\s*\[?(\d+)\]?', content, re.MULTILINE)
    if rating_match:
        reflection_data['rating'] = int(rating_match.group(1))
    
    # Извлечение процентов
    ops_percent_match = re.search(r'\*\*Выполнение операций:\*\*\s*\[?(\d+)%?\]?', content, re.MULTILINE)
    if ops_percent_match:
        reflection_data['operations_percent'] = int(ops_percent_match.group(1))
    
    tactics_percent_match = re.search(r'\*\*Выполнение тактики:\*\*\s*\[?(\d+)%?\]?', content, re.MULTILINE)
    if tactics_percent_match:
        reflection_data['tactics_percent'] = int(tactics_percent_match.group(1))
    
    # Извлечение энергии, мотивации, фокуса
    energy_match = re.search(r'\*\*Энергия:\*\*\s*\[?([^\]]+)\]?', content, re.MULTILINE)
    if energy_match:
        reflection_data['energy'] = energy_match.group(1).strip()
    
    motivation_match = re.search(r'\*\*Мотивация:\*\*\s*\[?([^\]]+)\]?', content, re.MULTILINE)
    if motivation_match:
        reflection_data['motivation'] = motivation_match.group(1).strip()
    
    focus_match = re.search(r'\*\*Фокус:\*\*\s*\[?([^\]]+)\]?', content, re.MULTILINE)
    if focus_match:
        reflection_data['focus'] = focus_match.group(1).strip()
    
    # Извлечение инсайтов
    insights_section = re.search(r'## Инсайты и наблюдения\s*\n\n(.+?)(?=\n---|\n##|$)', content, re.DOTALL)
    if insights_section:
        reflection_data['insights'] = insights_section.group(1).strip()
    
    # Извлечение плана на завтра
    plan_section = re.search(r'## План на завтра\s*\n\n(.+?)(?=\n---|\n##|$)', content, re.DOTALL)
    if plan_section:
        reflection_data['plan_tomorrow'] = plan_section.group(1).strip()
    
    return reflection_data

def generate_ai_comments(reflection_data, active_goals):
    """Генерирует комментарии ИИ-системы на основе анализа рефлексии."""
    comments = {
        'analysis': [],
        'recommendations': [],
        'adaptations': []
    }
    
    # Анализ выполнения операций
    total_operations = len(reflection_data['operations_done'])
    if reflection_data['operations_percent'] is not None:
        ops_percent = reflection_data['operations_percent']
        if ops_percent >= 80:
            comments['analysis'].append(f"✅ Отличное выполнение операций ({ops_percent}%)! Вы на правильном пути.")
        elif ops_percent >= 60:
            comments['analysis'].append(f"⚠️  Хорошее выполнение операций ({ops_percent}%), но есть потенциал для улучшения.")
        else:
            comments['analysis'].append(f"❌ Низкое выполнение операций ({ops_percent}%). Нужно разобраться в причинах.")
    else:
        if total_operations > 0:
            comments['analysis'].append(f"Выполнено {total_operations} операционных действий.")
        else:
            comments['analysis'].append("⚠️  Не выполнено ни одного операционного действия. Это может замедлить прогресс.")
    
    # Анализ выполнения тактики
    if reflection_data['tactics_percent'] is not None:
        tactics_percent = reflection_data['tactics_percent']
        if tactics_percent >= 80:
            comments['analysis'].append(f"✅ Отличный прогресс по тактическим задачам ({tactics_percent})!")
        elif tactics_percent >= 50:
            comments['analysis'].append(f"⚠️  Умеренный прогресс по тактике ({tactics_percent}%).")
        else:
            comments['analysis'].append(f"❌ Низкий прогресс по тактике ({tactics_percent}%). Возможно, задачи слишком сложные.")
    
    # Анализ доказательств идентичности
    evidence_count = len(reflection_data['evidence_done'])
    if evidence_count > 0:
        comments['analysis'].append(f"🎯 Отлично! Вы накопили {evidence_count} доказательств вашей новой идентичности.")
    else:
        comments['analysis'].append("💡 Не забудьте отмечать действия, которые подтверждают вашу идентичность.")
    
    # Анализ препятствий
    if reflection_data['obstacles']:
        comments['analysis'].append(f"🔍 Выявлено {len(reflection_data['obstacles'])} препятствий. Важно найти решения.")
        for obstacle in reflection_data['obstacles']:
            if obstacle and obstacle != '-':
                comments['recommendations'].append(f"Для препятствия '{obstacle[:50]}...' рассмотрите создание If-Then плана.")
    
    # Анализ полезных факторов
    if reflection_data['helpful_factors']:
        comments['analysis'].append(f"✨ Выделено {len(reflection_data['helpful_factors'])} полезных факторов. Продолжайте их использовать!")
    
    # Анализ энергии, мотивации, фокуса
    if reflection_data['energy'] and 'низкая' in reflection_data['energy'].lower():
        comments['recommendations'].append("💪 Низкая энергия может влиять на выполнение. Рассмотрите изменение времени выполнения задач или добавление восстановительных практик.")
    
    if reflection_data['motivation'] and 'низкая' in reflection_data['motivation'].lower():
        comments['recommendations'].append("🎯 Низкая мотивация? Напомните себе о стратегической идентичности и долгосрочных целях.")
    
    if reflection_data['focus'] and 'низкий' in reflection_data['focus'].lower():
        comments['recommendations'].append("🎯 Низкий фокус? Попробуйте технику Pomodoro или уменьшите количество одновременных задач.")
    
    # Рекомендации на основе оценки
    if reflection_data['rating'] is not None:
        if reflection_data['rating'] < 5:
            comments['recommendations'].append("📉 Низкая оценка дня. Возможно, стоит упростить план или разбить задачи на меньшие шаги.")
        elif reflection_data['rating'] >= 8:
            comments['recommendations'].append("🎉 Высокая оценка дня! Продолжайте в том же духе. Можете даже немного увеличить сложность задач.")
    
    # Адаптации (если нужно)
    if reflection_data['operations_percent'] is not None and reflection_data['operations_percent'] < 50:
        comments['adaptations'].append("💡 Рекомендуется упростить операционные действия или изменить триггеры для лучшего выполнения.")
    
    if reflection_data['tactics_percent'] is not None and reflection_data['tactics_percent'] < 50:
        comments['adaptations'].append("💡 Тактические задачи могут быть слишком сложными. Рассмотрите разбиение на меньшие шаги.")
    
    # Если нет рекомендаций, добавим общие
    if not comments['recommendations']:
        comments['recommendations'].append("Продолжайте отслеживать прогресс и отмечать маленькие победы!")
    
    if not comments['adaptations']:
        comments['adaptations'].append("План работает хорошо, значительных изменений не требуется.")
    
    return comments

def update_reflection_with_comments(reflection_path, comments):
    """Обновляет файл рефлексии, добавляя комментарии ИИ-системы."""
    with open(reflection_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Формируем секцию комментариев
    comments_section = "\n## Комментарии ИИ-системы\n\n"
    comments_section += "*[Автоматически сгенерировано после анализа]*\n\n"
    
    comments_section += "### Анализ прогресса:\n"
    for analysis in comments['analysis']:
        comments_section += f"- {analysis}\n"
    
    comments_section += "\n### Рекомендации:\n"
    for rec in comments['recommendations']:
        comments_section += f"- {rec}\n"
    
    comments_section += "\n### Адаптации:\n"
    for adapt in comments['adaptations']:
        comments_section += f"- {adapt}\n"
    
    # Заменяем или добавляем секцию комментариев
    if "## Комментарии ИИ-системы" in content:
        # Заменяем существующую секцию
        pattern = r'## Комментарии ИИ-системы.*?(?=\n## |$)'
        content = re.sub(pattern, comments_section.strip(), content, flags=re.DOTALL)
    else:
        # Добавляем в конец
        content = content.rstrip() + "\n\n" + comments_section
    
    # Сохраняем
    with open(reflection_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Комментарии ИИ-системы добавлены в {reflection_path}")

def get_active_goals():
    """Получает все активные цели."""
    active_goals = []
    if GOALS_DIR.exists():
        for goal_file in GOALS_DIR.glob("*.md"):
            with open(goal_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if '**Статус:** active' in content:
                    active_goals.append(goal_file.stem)
    return active_goals

def main():
    """Главная функция."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Анализ заполненной рефлексии')
    parser.add_argument('--date', type=str, help='Дата в формате YYYY-MM-DD (по умолчанию сегодня)')
    parser.add_argument('--file', type=str, help='Путь к файлу рефлексии')
    
    args = parser.parse_args()
    
    try:
        if args.file:
            reflection_path = Path(args.file)
        elif args.date:
            date = datetime.strptime(args.date, "%Y-%m-%d")
            year = date.strftime("%Y")
            month = date.strftime("%m")
            reflection_path = DAILY_DIR / year / month / f"{args.date}.md"
        else:
            date = datetime.now()
            year = date.strftime("%Y")
            month = date.strftime("%m")
            reflection_path = DAILY_DIR / year / month / f"{date.strftime('%Y-%m-%d')}.md"
        
        if not reflection_path.exists():
            print(f"❌ Файл рефлексии не найден: {reflection_path}", file=sys.stderr)
            sys.exit(1)
        
        # Парсим рефлексию
        reflection_data = parse_reflection_file(reflection_path)
        
        # Получаем активные цели
        active_goals = get_active_goals()
        
        # Генерируем комментарии
        comments = generate_ai_comments(reflection_data, active_goals)
        
        # Обновляем файл
        update_reflection_with_comments(reflection_path, comments)
        
        print("✅ Анализ завершён!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

