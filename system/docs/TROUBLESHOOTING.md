# План экспо: Решение проблем

Руководство по решению распространенных проблем при работе с системой автоматизации plan_expo.

## Содержание

1. [Проблемы с cron](#проблемы-с-cron)
2. [Проблемы с уведомлениями](#проблемы-с-уведомлениями)
3. [Проблемы со скриптами](#проблемы-со-скриптами)
4. [Проблемы с Git](#проблемы-с-git)
5. [Проблемы с данными](#проблемы-с-данными)
6. [Проблемы производительности](#проблемы-производительности)
7. [Диагностика](#диагностика)

---

## Проблемы с cron

### Проблема: cron задачи не запускаются

**Симптомы:**
- `schedule_manager.py status` показывает "ВКЛЮЧЕНА"
- Но скрипты не выполняются по расписанию
- Логи пустые или устаревшие

**Диагностика:**

```bash
# 1. Проверить crontab
crontab -l | grep "plan_expo"

# 2. Проверить что cron запущен (macOS)
sudo launchctl list | grep cron

# 3. Проверить логи cron (macOS)
log show --predicate 'process == "cron"' --last 1h
```

**Решения:**

#### Решение 1: Разрешения на macOS

macOS Big Sur+ требует разрешения для cron:

```bash
# 1. Системные настройки → Безопасность и конфиденциальность
# 2. Конфиденциальность → Full Disk Access
# 3. Добавить: /usr/sbin/cron
```

#### Решение 2: Абсолютные пути

Убедитесь что в `config/schedule.yaml` указаны абсолютные пути:

```yaml
schedule:
  python_path: "/usr/local/bin/python3"  # Не просто "python3"
  project_root: "/Users/azretmagometov/Projects/plan_expo"  # Абсолютный путь
```

Найти правильные пути:
```bash
which python3    # Путь к python
pwd              # Путь к проекту
```

#### Решение 3: Переустановить расписание

```bash
# Удалить старое
python3 scripts/schedule_manager.py disable

# Установить новое
python3 scripts/schedule_manager.py setup

# Проверить
crontab -l
```

### Проблема: Логи недоступны или пустые

**Симптомы:**
- Файлы логов не создаются
- Логи существуют но пустые

**Решения:**

#### Создать директории логов

```bash
mkdir -p logs/cron
chmod 755 logs/cron
```

#### Проверить перенаправление в crontab

```bash
crontab -l | grep plan_expo
# Должно быть: >> /path/to/logs/file.log 2>&1
```

#### Тестовый запуск

```bash
# Запустить скрипт вручную
python3 scripts/schedule_manager.py run daily

# Проверить создались ли логи
ls -lh logs/cron/
```

### Проблема: cron выполняет старую версию скрипта

**Причина:** cron не видит изменения в файлах

**Решение:**

```bash
# 1. Убедиться что изменения сохранены
git status

# 2. Переустановить crontab
python3 scripts/schedule_manager.py setup

# 3. Проверить что путь правильный
crontab -l | grep "analyze_reflection"
```

---

## Проблемы с уведомлениями

### Проблема: macOS уведомления не приходят

**Симптомы:**
- Скрипт выполняется без ошибок
- Но уведомления не отображаются

**Решения:**

#### Решение 1: Разрешения для Terminal

```bash
# 1. Системные настройки → Уведомления
# 2. Найти Terminal (или iTerm)
# 3. Включить "Разрешить уведомления"
# 4. Установить стиль: "Баннеры" или "Предупреждения"
```

#### Решение 2: Тестовое уведомление

```bash
# Отправить тестовое уведомление
osascript -e 'display notification "Test" with title "plan_expo"'
```

Если тест работает, но уведомления от скрипта нет:

```bash
# Запустить скрипт вручную
python3 scripts/notification_system.py daily

# Проверить вывод
```

#### Решение 3: Проверить конфигурацию

```bash
# Открыть конфигурацию
cat config/notifications.yaml

# Убедиться что:
notifications:
  enabled: true
macos:
  enabled: true
```

### Проблема: Telegram уведомления не приходят

**Симптомы:**
- Ошибка: "❌ Ошибка отправки Telegram уведомления"

**Решения:**

#### Проверить bot_token и chat_id

```bash
# Тест через curl
curl "https://api.telegram.org/bot<BOT_TOKEN>/sendMessage?chat_id=<CHAT_ID>&text=Test"
```

Если ошибка:
- Проверить токен (получить новый у @BotFather)
- Проверить chat_id (получить у @userinfobot)

#### Установить requests

```bash
pip3 install requests
```

#### Проверить доступ к API

```bash
# Проверить что есть интернет
ping api.telegram.org

# Проверить что нет прокси/firewall блокировки
```

### Проблема: Slack уведомления не приходят

**Решения:**

#### Проверить webhook URL

```bash
# Тест через curl
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Test from plan_expo"}' \
  <WEBHOOK_URL>
```

#### Обновить webhook

Если webhook устарел:
1. Slack → Settings & Administration → Manage apps
2. Custom Integrations → Incoming Webhooks
3. Создать новый или обновить существующий

---

## Проблемы со скриптами

### Проблема: TypeError: 'NoneType' и подобные ошибки

**Причина:** Отсутствуют данные в рефлексиях

**Решение:**

#### Для generate_daily_dashboard.py

Проблема уже исправлена в коде, но если встречается:

```python
# Убедиться что значения проверяются на None
if value is None:
    value = 0
```

#### Для auto_update_metrics.py

```bash
# Проверить что рефлексия заполнена
cat reflections/daily/$(date +%Y/%m/%Y-%m-%d).md

# Убедиться что есть секции:
# ## ОПЕРАЦИОННЫЙ УРОВЕНЬ
# ## ТАКТИЧЕСКИЙ УРОВЕНЬ
```

### Проблема: "Нет данных за эту неделю"

**Симптомы:**
- `generate_weekly_dashboard.py` завершается с ошибкой

**Причина:** Недостаточно рефлексий за неделю

**Решение:**

```bash
# Заполнить рефлексии за всю неделю
# Неделя начинается с понедельника (ISO формат)

# Проверить какие рефлексии есть
ls -lR reflections/daily/$(date +%Y/%m/)

# Недельный дашборд требует минимум 3 дня данных
```

### Проблема: validate_goals.py находит ошибки после --fix

**Причина:** Некоторые ошибки требуют ручного исправления

**Решение:**

```bash
# 1. Просмотреть отчет
cat dashboards/validation/*_validation_report.md

# 2. Исправить вручную указанные проблемы

# 3. Запустить снова
python3 scripts/validate_goals.py --fix
```

### Проблема: ImportError или ModuleNotFoundError

**Симптомы:**
```
ImportError: cannot import name 'parse_reflection_file'
```

**Решение:**

#### Проверить структуру проекта

```bash
# Убедиться что вы в корне проекта
ls scripts/
# Должны быть: analyze_reflection.py, generate_reflection.py, и т.д.
```

#### Проверить PYTHONPATH

```bash
# Если запускаете не из корня проекта
cd /path/to/plan_expo
python3 scripts/<script>.py
```

---

## Проблемы с Git

### Проблема: Git автокоммиты создают конфликты

**Симптомы:**
- Ошибка: "Updates were rejected"
- Pull shows conflicts

**Решение:**

#### Отключить auto_push

```yaml
# config/git_auto_commit.yaml
git:
  auto_push: false  # Отключить
```

#### Ручной push

```bash
# После автокоммита
git pull origin main
# Решить конфликты если есть
git push origin main
```

### Проблема: Коммиты пустые или содержат не те файлы

**Решение:**

#### Проверить фильтры

```yaml
# config/git_auto_commit.yaml
git:
  include_files:
    - "reflections/"
    - "dashboards/"
    - "goals/"
```

#### Проверить git status

```bash
# Перед запуском git_auto_commit.py
git status

# Убедиться что есть изменения в нужных файлах
```

### Проблема: ".gitignore не игнорирует файлы"

**Решение:**

#### Очистить кэш Git

```bash
# Файлы уже отслеживаются, нужно удалить из индекса
git rm -r --cached .
git add .
git commit -m "Update .gitignore"
```

---

## Проблемы с данными

### Проблема: Неправильная структура рефлексий

**Симптомы:**
- Файлы в `reflections/daily/` вместо `reflections/daily/YYYY/MM/`

**Решение:**

```bash
# Автоматическое исправление
python3 scripts/validate_goals.py --fix

# Проверка
ls -R reflections/daily/
```

### Проблема: Метрики не обновляются

**Симптомы:**
- `auto_update_metrics.py` выполняется но метрики не меняются

**Решения:**

#### Проверить рефлексию

```bash
# Убедиться что рефлексия заполнена
cat reflections/daily/$(date +%Y/%m/%Y-%m-%d).md

# Должны быть выполненные операции и тактика
```

#### Проверить логи

```bash
tail -50 logs/metrics_update_$(date +%Y-%m-%d).log

# Искать:
# "Нет изменений для ..."
# "Обновлено целей: X/Y"
```

#### Проверить формат цели

```bash
# Открыть файл цели
cat goals/goal_*.md

# Убедиться что есть секции:
# ## Identity Evidence List
# ## OKR/SMART Tracker
# ## Daily Habits Tracker
```

### Проблема: Streaks не считаются

**Симптомы:**
- `track_habit_streaks.py` показывает 0 для всех привычек

**Решение:**

#### Проверить формат привычек в целях

```markdown
# Должны быть в формате:

# Tiny Habits:
- После утреннего кофе → connection request
- После обеда → 15 мин чтения

# Implementation Intentions:
- ЕСЛИ 9:00 → ТО пишу connection request
- ЕСЛИ утром встаю → ТО делаю зарядку
```

#### Проверить что в рефлексиях есть выполненные операции

```bash
cat reflections/daily/$(date +%Y/%m/%Y-%m-%d).md | grep "✅"
```

---

## Проблемы производительности

### Проблема: Скрипты работают медленно

**Симптомы:**
- Вечерний конвейер занимает > 1 минута

**Решения:**

#### Оптимизация чтения файлов

```bash
# Проверить количество рефлексий
find reflections/daily -name "*.md" | wc -l

# Если > 1000, рассмотреть архивирование старых
```

#### Проверить размер дашбордов

```bash
du -sh dashboards/
# Если > 100MB, удалить старые
```

### Проблема: HTML дашборды слишком большие

**Решение:**

```bash
# Удалить старые дашборды (> 30 дней)
find dashboards/daily -name "*.html" -mtime +30 -delete
find dashboards/weekly -name "*.html" -mtime +90 -delete
```

---

## Диагностика

### Общая диагностика системы

```bash
#!/bin/bash
# Скрипт диагностики plan_expo

echo "=== План экспо: Диагностика ==="
echo ""

echo "1. Проверка Python:"
which python3
python3 --version
echo ""

echo "2. Проверка структуры проекта:"
ls -l scripts/ | head -5
ls -l config/
echo ""

echo "3. Проверка crontab:"
crontab -l | grep -A5 "BEGIN plan_expo" || echo "Crontab не установлен"
echo ""

echo "4. Проверка логов (последние 5):"
ls -lt logs/cron/ | head -6
echo ""

echo "5. Проверка последних рефлексий:"
find reflections/daily -name "*.md" -mtime -7 | wc -l
echo "рефлексий за последние 7 дней"
echo ""

echo "6. Проверка дашбордов:"
ls -lt dashboards/daily/*.html 2>/dev/null | head -3 || echo "Дашборды не найдены"
echo ""

echo "7. Проверка Git:"
git status --short
echo ""

echo "8. Проверка конфигурации:"
cat config/schedule.yaml | grep "enabled:"
echo ""

echo "=== Диагностика завершена ==="
```

Сохранить как `scripts/diagnose.sh` и запустить:

```bash
chmod +x scripts/diagnose.sh
./scripts/diagnose.sh
```

### Проверка отдельных компонентов

#### Проверка валидации

```bash
python3 scripts/validate_goals.py
# Ожидается: 0 критических ошибок
```

#### Проверка автообновления метрик

```bash
python3 scripts/auto_update_metrics.py
tail -20 logs/metrics_update_$(date +%Y-%m-%d).log
```

#### Проверка генерации дашбордов

```bash
python3 scripts/generate_daily_dashboard.py
open dashboards/daily/$(date +%Y-%m-%d).html
```

#### Проверка уведомлений

```bash
python3 scripts/notification_system.py check
# Должно показать: "Все проверки пройдены" или warnings
```

---

## Чек-лист перед обращением в поддержку

Перед созданием issue соберите следующую информацию:

### 1. Информация о системе

```bash
# macOS версия
sw_vers

# Python версия
python3 --version

# Git версия
git --version
```

### 2. Логи ошибок

```bash
# Последние ошибки из логов
grep -r "ERROR\|❌" logs/cron/ | tail -20

# Последние 50 строк проблемного скрипта
tail -50 logs/cron/<problem_script>.log
```

### 3. Конфигурация

```bash
# Расписание
cat config/schedule.yaml

# Уведомления (без секретов!)
cat config/notifications.yaml | grep -v "token\|chat_id\|webhook"

# Git автокоммиты
cat config/git_auto_commit.yaml
```

### 4. Crontab

```bash
crontab -l | grep "plan_expo"
```

### 5. Последние коммиты

```bash
git log --oneline -10
```

---

## Часто задаваемые вопросы (FAQ)

### Q: Могу ли я изменить время запуска задач?

**A:** Да, отредактируйте `config/schedule.yaml` и переустановите crontab:

```bash
# 1. Изменить время в config/schedule.yaml
# 2. Переустановить:
python3 scripts/schedule_manager.py setup
```

### Q: Можно ли запускать некоторые задачи вручную, а другие автоматически?

**A:** Да, отключите ненужные задачи в конфигурации:

```yaml
daily:
  morning_reflection:
    enabled: false  # Отключить
```

### Q: Как архивировать старые рефлексии?

**A:**

```bash
# Создать архив за 2024 год
tar -czf archive_2024.tar.gz reflections/daily/2024/

# Удалить оригиналы (осторожно!)
rm -rf reflections/daily/2024/
```

### Q: Можно ли использовать систему на нескольких компьютерах?

**A:** Да, через Git синхронизацию:

1. Компьютер A: установить расписание
2. Компьютер B: клонировать репозиторий, обновить пути в config/schedule.yaml
3. Синхронизировать через git pull/push

### Q: Как удалить автоматизацию полностью?

**A:**

```bash
# 1. Отключить crontab
python3 scripts/schedule_manager.py disable

# 2. Удалить скрипты (опционально)
rm -rf scripts/

# 3. Удалить конфигурацию (опционально)
rm -rf config/
```

### Q: Сколько места занимает система?

**A:**

```bash
# Проверить размер
du -sh .

# Типичный размер:
# - Скрипты: ~100KB
# - Рефлексии (год): ~5-10MB
# - Дашборды (год): ~20-50MB
# - Логи: ~1-5MB
```

---

## Получение помощи

### Создание issue

Если проблема не решена, создайте issue с:

1. **Заголовок:** Краткое описание проблемы
2. **Описание:**
   - Что пытались сделать
   - Что произошло
   - Что ожидали
3. **Воспроизведение:**
   - Шаги для воспроизведения
   - Команды которые запускали
4. **Окружение:**
   - macOS версия
   - Python версия
5. **Логи:**
   - Вывод ошибок
   - Релевантные логи

### Полезные ресурсы

- [AUTOMATION.md](./AUTOMATION.md) - Руководство по автоматизации
- [SCRIPTS.md](./SCRIPTS.md) - Документация скриптов
- [DATA_STRUCTURE.md](../DATA_STRUCTURE.md) - Структура данных
- [README.md](../README.md) - Общее описание проекта
