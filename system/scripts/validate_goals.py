#!/usr/bin/env python3
"""
Скрипт для валидации структуры целей и рефлексий.

Проверяет:
- Структуру файлов целей (обязательные секции, форматы)
- Структуру директорий рефлексий
- Корректность метаданных и метрик

Опции:
- --fix: Автоматически исправлять проблемы (миграция файлов)
"""

import re
import sys
from pathlib import Path
import sys

# Добавить system/scripts в sys.path для импорта config_loader
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from config_loader import get_project_root, get_path
from datetime import datetime
import argparse

# Пути к директориям
PROJECT_ROOT = get_project_root()
GOALS_DIR = get_path("goals")
REFLECTIONS_DIR = get_path("reflections")
DAILY_DIR = REFLECTIONS_DIR / "daily"
DASHBOARDS_DIR = get_path("dashboards") / "validation"

# Типы проблем
class ValidationIssue:
    CRITICAL = "critical"
    WARNING = "warning"
    RECOMMENDATION = "recommendation"

class ValidationReport:
    """Отчет валидации."""
    def __init__(self):
        self.issues = {
            ValidationIssue.CRITICAL: [],
            ValidationIssue.WARNING: [],
            ValidationIssue.RECOMMENDATION: []
        }

    def add_issue(self, level, message, file_path=None, fix_command=None):
        """Добавить проблему в отчет."""
        issue = {
            "message": message,
            "file": file_path,
            "fix": fix_command
        }
        self.issues[level].append(issue)

    def has_critical(self):
        """Есть ли критические ошибки."""
        return len(self.issues[ValidationIssue.CRITICAL]) > 0

    def print_summary(self):
        """Вывести краткую сводку."""
        print("\n" + "="*60)
        print("СВОДКА ВАЛИДАЦИИ")
        print("="*60)
        print(f"❌ Критических ошибок: {len(self.issues[ValidationIssue.CRITICAL])}")
        print(f"⚠️  Предупреждений: {len(self.issues[ValidationIssue.WARNING])}")
        print(f"💡 Рекомендаций: {len(self.issues[ValidationIssue.RECOMMENDATION])}")
        print("="*60 + "\n")

    def generate_markdown_report(self, output_path):
        """Генерировать markdown отчет."""
        today = datetime.now().strftime("%Y-%m-%d")

        content = f"# Отчет валидации: {today}\n\n"

        # Критические ошибки
        content += f"## Критические ошибки ({len(self.issues[ValidationIssue.CRITICAL])})\n\n"
        if self.issues[ValidationIssue.CRITICAL]:
            for issue in self.issues[ValidationIssue.CRITICAL]:
                content += f"- ❌ {issue['message']}\n"
                if issue['file']:
                    content += f"  - Файл: `{issue['file']}`\n"
                if issue['fix']:
                    content += f"  - Исправление: `{issue['fix']}`\n"
                content += "\n"
        else:
            content += "Не найдено\n\n"

        # Предупреждения
        content += f"## Предупреждения ({len(self.issues[ValidationIssue.WARNING])})\n\n"
        if self.issues[ValidationIssue.WARNING]:
            for issue in self.issues[ValidationIssue.WARNING]:
                content += f"- ⚠️  {issue['message']}\n"
                if issue['file']:
                    content += f"  - Файл: `{issue['file']}`\n"
                content += "\n"
        else:
            content += "Не найдено\n\n"

        # Рекомендации
        content += f"## Рекомендации ({len(self.issues[ValidationIssue.RECOMMENDATION])})\n\n"
        if self.issues[ValidationIssue.RECOMMENDATION]:
            for issue in self.issues[ValidationIssue.RECOMMENDATION]:
                content += f"- 💡 {issue['message']}\n"
                if issue['file']:
                    content += f"  - Файл: `{issue['file']}`\n"
                content += "\n"
        else:
            content += "Не найдено\n\n"

        # Сохранить
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✅ Отчет сохранен: {output_path}")


def validate_goal_file(goal_path, report):
    """Валидация файла цели."""
    try:
        with open(goal_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Проверка обязательных секций
        required_sections = [
            ("## СТРАТЕГИЧЕСКИЙ УРОВЕНЬ", "Стратегический уровень"),
            ("## ТАКТИЧЕСКИЙ УРОВЕНЬ", "Тактический уровень"),
            ("## ОПЕРАЦИОННЫЙ УРОВЕНЬ", "Операционный уровень"),
            ("## ИСТОРИЯ ИЗМЕНЕНИЙ", "История изменений")
        ]

        for pattern, name in required_sections:
            if pattern not in content:
                report.add_issue(
                    ValidationIssue.CRITICAL,
                    f"Отсутствует секция '{name}'",
                    file_path=goal_path
                )

        # Проверка метаданных
        # Статус
        status_match = re.search(r'\*\*Статус:\*\*\s+(active|completed|paused|cancelled)', content)
        if not status_match:
            report.add_issue(
                ValidationIssue.CRITICAL,
                "Некорректный или отсутствующий статус (должен быть: active|completed|paused|cancelled)",
                file_path=goal_path
            )

        # Дата создания
        created_match = re.search(r'\*\*Дата создания:\*\*\s+(\d{4}-\d{2}-\d{2})', content)
        if not created_match:
            report.add_issue(
                ValidationIssue.WARNING,
                "Отсутствует или некорректна дата создания (формат: YYYY-MM-DD)",
                file_path=goal_path
            )

        # Последнее обновление
        updated_match = re.search(r'\*\*Последнее обновление:\*\*\s+(\d{4}-\d{2}-\d{2})', content)
        if not updated_match:
            report.add_issue(
                ValidationIssue.WARNING,
                "Отсутствует или некорректно последнее обновление (формат: YYYY-MM-DD)",
                file_path=goal_path
            )

        # Проверка процентов (должны быть 0-100)
        percent_matches = re.findall(r'(\d+)%', content)
        for percent in percent_matches:
            if int(percent) > 100:
                report.add_issue(
                    ValidationIssue.WARNING,
                    f"Процент выше 100%: {percent}%",
                    file_path=goal_path
                )

    except Exception as e:
        report.add_issue(
            ValidationIssue.CRITICAL,
            f"Ошибка чтения файла: {str(e)}",
            file_path=goal_path
        )


def validate_reflections_structure(report, fix=False):
    """Валидация структуры директорий рефлексий."""
    if not DAILY_DIR.exists():
        report.add_issue(
            ValidationIssue.CRITICAL,
            f"Директория рефлексий не существует: {DAILY_DIR}"
        )
        return

    # Найти файлы в неправильной структуре
    misplaced_files = []
    for file_path in DAILY_DIR.glob("*.md"):
        # Файлы не должны быть напрямую в daily/
        misplaced_files.append(file_path)

    for file_path in misplaced_files:
        # Извлечь дату из имени файла
        filename = file_path.stem
        date_match = re.match(r'(\d{4})-(\d{2})-(\d{2})', filename)

        if date_match:
            year, month, day = date_match.groups()
            correct_path = DAILY_DIR / year / month / f"{filename}.md"

            report.add_issue(
                ValidationIssue.CRITICAL,
                f"Неправильная структура директорий рефлексии",
                file_path=file_path,
                fix_command="python scripts/validate_goals.py --fix"
            )

            # Если включен --fix, переместить файл
            if fix:
                correct_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.rename(correct_path)
                print(f"✅ Перемещено: {file_path} → {correct_path}")
        else:
            report.add_issue(
                ValidationIssue.WARNING,
                f"Некорректное имя файла рефлексии (ожидается YYYY-MM-DD.md): {filename}",
                file_path=file_path
            )


def validate_reflection_file(reflection_path, report):
    """Валидация файла рефлексии."""
    try:
        with open(reflection_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Проверка основных секций (не все обязательны, но полезно знать)
        recommended_sections = [
            "## УТРО",
            "## ДЕНЬ",
            "## ВЕЧЕР",
            "## ПРОГРЕСС ЗА ДЕНЬ",
            "## РЕФЛЕКСИЯ"
        ]

        missing_sections = []
        for section in recommended_sections:
            if section not in content:
                missing_sections.append(section)

        if missing_sections:
            report.add_issue(
                ValidationIssue.RECOMMENDATION,
                f"Рекомендуется добавить секции: {', '.join(missing_sections)}",
                file_path=reflection_path
            )

    except Exception as e:
        report.add_issue(
            ValidationIssue.WARNING,
            f"Ошибка чтения файла рефлексии: {str(e)}",
            file_path=reflection_path
        )


def validate_all(fix=False):
    """Основная функция валидации."""
    report = ValidationReport()

    print("Начинаю валидацию проекта plan_expo...\n")

    # Валидация целей
    print("📋 Проверка файлов целей...")
    if GOALS_DIR.exists():
        goal_files = list(GOALS_DIR.glob("*.md"))
        print(f"   Найдено целей: {len(goal_files)}")

        for goal_file in goal_files:
            validate_goal_file(goal_file, report)
    else:
        report.add_issue(
            ValidationIssue.CRITICAL,
            f"Директория целей не существует: {GOALS_DIR}"
        )

    # Валидация структуры рефлексий
    print("\n📝 Проверка структуры рефлексий...")
    validate_reflections_structure(report, fix=fix)

    # Валидация файлов рефлексий
    print("\n📅 Проверка файлов рефлексий...")
    reflection_files = list(DAILY_DIR.rglob("*.md"))
    print(f"   Найдено рефлексий: {len(reflection_files)}")

    for reflection_file in reflection_files:
        validate_reflection_file(reflection_file, report)

    # Вывод результатов
    report.print_summary()

    # Детали
    if report.issues[ValidationIssue.CRITICAL]:
        print("КРИТИЧЕСКИЕ ОШИБКИ:\n")
        for issue in report.issues[ValidationIssue.CRITICAL]:
            print(f"  ❌ {issue['message']}")
            if issue['file']:
                print(f"     Файл: {issue['file']}")
            if issue['fix']:
                print(f"     Исправление: {issue['fix']}")
            print()

    if report.issues[ValidationIssue.WARNING]:
        print("\nПРЕДУПРЕЖДЕНИЯ:\n")
        for issue in report.issues[ValidationIssue.WARNING]:
            print(f"  ⚠️  {issue['message']}")
            if issue['file']:
                print(f"     Файл: {issue['file']}")
            print()

    if report.issues[ValidationIssue.RECOMMENDATION]:
        print("\nРЕКОМЕНДАЦИИ:\n")
        for issue in report.issues[ValidationIssue.RECOMMENDATION]:
            print(f"  💡 {issue['message']}")
            if issue['file']:
                print(f"     Файл: {issue['file']}")
            print()

    # Сохранить отчет
    today = datetime.now().strftime("%Y-%m-%d")
    report_path = DASHBOARDS_DIR / f"{today}_validation_report.md"
    report.generate_markdown_report(report_path)

    # Exit code
    if report.has_critical():
        return 1
    return 0


def main():
    """Главная функция."""
    parser = argparse.ArgumentParser(description='Валидация структуры целей и рефлексий')
    parser.add_argument('--fix', action='store_true', help='Автоматически исправить проблемы')

    args = parser.parse_args()

    try:
        exit_code = validate_all(fix=args.fix)
        sys.exit(exit_code)
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
