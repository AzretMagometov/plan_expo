# Структура данных и архитектура проекта

Этот документ описывает архитектуру и структуру хранения данных в системе целеполагания plan_expo.

## Общая архитектура

plan_expo использует **разделение на системную логику и пользовательские данные**:

```
plan_expo/
├── system/                    # СИСТЕМНАЯ ЛОГИКА (темплейт)
│   ├── scripts/              # Python скрипты
│   ├── prompts/              # AI промпты
│   ├── templates/            # Шаблоны
│   └── docs/                 # Документация
│
├── user_data/                # ПОЛЬЗОВАТЕЛЬСКИЕ ДАННЫЕ
│   ├── goals/               # Цели
│   ├── reflections/         # Рефлексии
│   ├── dashboards/          # Дашборды
│   └── logs/                # Логи
│
└── config/                   # КОНФИГУРАЦИЯ
    ├── ai_model.yaml        # Выбор AI модели
    ├── user_settings.yaml   # Настройки пользователя
    └── *.yaml.example       # Примеры конфигов
```

## Системные компоненты (`system/`)

### `system/scripts/` — Python скрипты

Все скрипты используют **централизованное управление путями** через `config_loader.py`:

```python
from config_loader import get_project_root, get_path

PROJECT_ROOT = get_project_root()
GOALS_DIR = get_path('goals')           # user_data/goals
REFLECTIONS_DIR = get_path('reflections')  # user_data/reflections
```

**Ключевые скрипты:**
- `config_loader.py` - Центральная система управления конфигами и путями
- `init_user.py` - Интерактивная инициализация новых пользователей
- `generate_reflection.py` - Генерация шаблонов рефлексий
- `analyze_reflection.py` - Анализ рефлексий
- `auto_update_metrics.py` - Автообновление метрик
- `track_habit_streaks.py` - Отслеживание серий привычек
- `generate_daily_dashboard.py` - Генерация дневных дашбордов
- `generate_weekly_dashboard.py` - Генерация недельных дашбордов
- `schedule_manager.py` - Управление автоматизацией (cron)
- `notification_system.py` - Система уведомлений
- `git_auto_commit.py` - Автокоммиты в Git
- `validate_goals.py` - Валидация структуры целей

### `system/prompts/` — AI промпты

Универсальные промпты для работы с любыми AI моделями (Claude, GPT-4, Gemini, локальные):

- `goal_formulation.md` - Формулировка цели
- `strategy_level.md` - Стратегический уровень
- `tactics_level.md` - Тактический уровень
- `operations_level.md` - Операционный уровень
- `goal_management.md` - Управление целями
- `reflection_management.md` - Управление рефлексиями
- `progress_tracking.md` - Отслеживание прогресса
- `goal_change_tracking.md` - Классификация изменений целей
- `dashboard_generation.md` - Генерация дашбордов
- `checklist_creation.md` - Создание чеклистов

### `system/docs/` — Документация

- `AI_MODELS.md` - Руководство по выбору и настройке AI моделей
- `SCRIPTS.md` - Подробная документация всех скриптов
- `AUTOMATION.md` - Настройка автоматизации
- `TROUBLESHOOTING.md` - Решение проблем

### `system/templates/` — Шаблоны

Шаблоны для создания новых файлов (в разработке).

## Пользовательские данные (`user_data/`)

### `user_data/goals/` — Цели пользователя

Каждая цель сохраняется в отдельном файле.

**Формат ID цели:** `goal_YYYY_MM_DD_[краткое_описание].md`

**Пример:** `goal_2025_01_15_income_100k_monthly.md`

**Структура файла цели:**
- Метаданные (ID, дата создания, статус, последнее обновление)
- Стратегический уровень (идентичность, убеждения, доказательства)
- Тактический уровень (OKR или SMART)
- Операционный уровень (Implementation Intentions, Tiny Habits)
- Критические события
- История изменений

**Статусы:** `active`, `paused`, `completed`, `cancelled`

Подробнее см. `system/prompts/goal_management.md`

### `user_data/reflections/` — Рефлексии пользователя

Рефлексии организованы по типам и датам:

```
user_data/reflections/
├── daily/YYYY/MM/YYYY-MM-DD.md
├── weekly/YYYY/week_NN_YYYY.md
├── monthly/YYYY/YYYY-MM.md
├── quarterly/YYYY/QN_YYYY.md
└── yearly/YYYY.md
```

**Ежедневная рефлексия содержит:**
- Активные цели на день
- План операционных действий (If-Then, Tiny Habits)
- План тактических задач (Key Results)
- Выполнение (отмеченные чекбоксы)
- Доказательства идентичности
- Препятствия и решения
- Оценка дня (оценка 1-10, энергия, мотивация, фокус)
- Инсайты и наблюдения
- План на завтра
- Комментарии ИИ-системы (генерируются автоматически)

Подробнее см. `system/prompts/reflection_management.md`

### `user_data/dashboards/` — Дашборды и визуализации

```
user_data/dashboards/
├── daily/YYYY-MM-DD.{html,md}          # Дневные дашборды
├── weekly/week_NN_YYYY.{html,md}       # Недельные дашборды
├── streaks/YYYY-MM-DD_streaks.md       # Отчеты по сериям
└── validation/YYYY-MM-DD_validation_report.md  # Отчеты валидации
```

**Дашборды содержат:**
- Статистику выполнения операций и тактики
- Графики прогресса Key Results
- Анализ серий привычек (current streak, max streak)
- Паттерны по дням недели
- Тренды и инсайты
- Рекомендации для оптимизации

Подробнее см. `system/prompts/dashboard_generation.md`

### `user_data/logs/` — Логи системы

```
user_data/logs/
└── cron/                     # Логи автоматических задач
    ├── analyze_reflection_YYYY-MM-DD.log
    ├── daily_dashboard_YYYY-MM-DD.log
    └── ...
```

## Конфигурация (`config/`)

### `config/user_settings.yaml`

Создается автоматически при `init_user.py`. Содержит:

```yaml
project:
  root: /path/to/plan_expo      # Авто-определяется
  name: "My Plan Expo"
  timezone: "UTC"

paths:
  goals: "user_data/goals"              # Относительные пути
  reflections: "user_data/reflections"
  dashboards: "user_data/dashboards"
  logs: "user_data/logs"
  scripts: "system/scripts"
  prompts: "system/prompts"
  templates: "system/templates"

git:
  commit_user_data: false      # По умолчанию не коммитим (приватность)
  auto_commit: true
```

### `config/ai_model.yaml`

Конфигурация выбранной AI модели:

```yaml
current_model: "claude"  # claude | gpt | gemini | local

models:
  claude:
    name: "Claude (Anthropic)"
    recommended_model: "claude-sonnet-4-5"
  gpt:
    name: "ChatGPT (OpenAI)"
    recommended_model: "gpt-4"
  gemini:
    name: "Gemini (Google)"
    recommended_model: "gemini-pro"
  local:
    name: "Local Model"
    recommended_model: "mistral"
```

### Другие конфиги

- `config/schedule.yaml` - Расписание автоматизации (cron)
- `config/notifications.yaml` - Настройки уведомлений (Telegram, Slack)
- `config/git_auto_commit.yaml` - Настройки автокоммитов

**Важно:** Реальные конфиги не коммитятся (защищены `.gitignore`). Коммитятся только `.example` версии.

## Рабочий процесс

### 1. Инициализация нового пользователя

```bash
# Быстрая установка
./setup.sh

# Или вручную
python3 system/scripts/init_user.py
```

**Что происходит:**
1. Создается `config/user_settings.yaml` с авто-определением путей
2. Копируются примеры конфигов (`*.example` → `*.yaml`)
3. Создается структура директорий `user_data/`
4. Интерактивно настраивается `.env` (токены Telegram/Slack)
5. Выбирается AI модель (Claude/GPT/Gemini/Local)

### 2. Создание цели

1. Пользователь формулирует цель с помощью ИИ-коуча
2. ИИ использует промпты последовательно:
   - `system/prompts/goal_formulation.md`
   - `system/prompts/strategy_level.md`
   - `system/prompts/tactics_level.md`
   - `system/prompts/operations_level.md`
3. Цель сохраняется в `user_data/goals/[goal_id].md`

### 3. Ежедневная работа

**Утро:**
```bash
python3 system/scripts/generate_reflection.py
```
Генерируется шаблон рефлексии с планом на день из активных целей.

**В течение дня:**
Пользователь заполняет рефлексию, отмечая выполненные действия.

**Вечер:**
```bash
# Ручной анализ
python3 system/scripts/analyze_reflection.py

# Или через AI-коуча
"Проанализируй рефлексию за сегодня"
```

ИИ анализирует рефлексию, добавляет комментарии, обновляет метрики.

### 4. Автоматизация

```bash
# Настроить автоматизацию
python3 system/scripts/schedule_manager.py setup
```

**Автоматический пайплайн (ежедневно 21:00-21:25):**
- 21:00 - Анализ рефлексии
- 21:05 - Обновление метрик
- 21:10 - Подсчет серий привычек
- 21:15 - Генерация дашборда
- 21:20 - Git auto-commit
- 21:25 - Отправка уведомлений

**Еженедельный пайплайн (воскресенье 22:00):**
- Генерация недельного дашборда
- Валидация структуры целей
- Отправка недельного отчета

## Интеграция компонентов

```
┌──────────────────┐
│  config_loader   │ ← Центральное управление путями
└────────┬─────────┘
         │
         ├─────────────────────────┐
         │                         │
         ▼                         ▼
┌─────────────────┐       ┌──────────────┐
│   Цели          │       │  Рефлексии   │
│ (user_data/     │◄──────┤(user_data/   │
│  goals/)        │       │ reflections/)│
└────────┬────────┘       └──────┬───────┘
         │                       │
         │                       │
         ▼                       ▼
┌─────────────────┐       ┌──────────────┐
│  Дашборды       │       │  Анализ и    │
│ (user_data/     │◄──────┤  адаптация   │
│  dashboards/)   │       │  целей       │
└─────────────────┘       └──────────────┘
```

## Принципы работы с путями

### Старый подход (до универсализации)
```python
PROJECT_ROOT = Path(__file__).parent.parent
GOALS_DIR = PROJECT_ROOT / "goals"
```

### Новый подход (после универсализации)
```python
from config_loader import get_project_root, get_path

PROJECT_ROOT = get_project_root()
GOALS_DIR = get_path('goals')           # Автоматически → user_data/goals
REFLECTIONS_DIR = get_path('reflections')  # Автоматически → user_data/reflections
```

**Преимущества:**
- Нет абсолютных путей в конфигах
- Легко изменить структуру через `config/user_settings.yaml`
- Переносимость между машинами
- Поддержка разных пользователей

## Git и приватность

По умолчанию **пользовательские данные НЕ коммитятся** для приватности:

```gitignore
# user_data/ защищен в .gitignore
user_data/goals/*.md
user_data/reflections/**/*.md
user_data/dashboards/**/*
user_data/logs/**/*
```

**Если хотите коммитить свои данные:**
```yaml
# config/user_settings.yaml
git:
  commit_user_data: true
```

## Рекомендации

1. **Регулярность:** Генерируй рефлексии ежедневно
2. **Анализ:** Анализируй рефлексии сразу после заполнения
3. **Автоматизация:** Используй `schedule_manager.py` для автоматизации
4. **Приватность:** Храни секреты в `.env`, не коммить user_data по умолчанию
5. **Резервное копирование:** Регулярно делай бэкап `user_data/` и `config/`

## Ссылки на документацию

- **CLAUDE.md** - Полное руководство для AI-коуча
- **SETUP.md** - Детальная инструкция по установке
- **system/docs/AI_MODELS.md** - Выбор и настройка AI моделей
- **system/docs/SCRIPTS.md** - Документация скриптов
- **system/docs/AUTOMATION.md** - Настройка автоматизации
