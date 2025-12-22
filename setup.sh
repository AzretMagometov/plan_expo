#!/bin/bash
# Быстрая установка plan_expo
# Поддержка: macOS, Linux

set -e  # Выход при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для вывода
print_header() {
    echo -e "\n${BLUE}============================================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}============================================================${NC}\n"
}

print_step() {
    echo -e "${GREEN}▶${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_success() {
    echo -e "${GREEN}✔${NC} $1"
}

# Заголовок
print_header "🚀 Установка plan_expo"

# Проверка Python
print_step "Проверка Python..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 не найден"
    echo "Установите Python 3.8 или выше:"
    echo "  macOS: brew install python3"
    echo "  Ubuntu: sudo apt install python3 python3-pip"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
print_success "Python $PYTHON_VERSION установлен"

# Проверка pip
print_step "Проверка pip..."
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 не найден"
    echo "Установите pip3:"
    echo "  macOS: python3 -m ensurepip --upgrade"
    echo "  Ubuntu: sudo apt install python3-pip"
    exit 1
fi
print_success "pip3 установлен"

# Установка зависимостей
print_step "Установка Python зависимостей..."
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt --quiet
    print_success "Зависимости установлены (PyYAML, requests, python-dotenv)"
else
    print_warning "requirements.txt не найден, пропускаю установку зависимостей"
fi

# Запуск инициализации
print_step "Запуск инициализации..."
echo ""

if [ -f "system/scripts/init_user.py" ]; then
    python3 system/scripts/init_user.py --mode quick
else
    print_error "system/scripts/init_user.py не найден"
    print_warning "Запустите инициализацию вручную:"
    echo "  python3 system/scripts/init_user.py"
    exit 1
fi

# Успешное завершение
print_header "✅ Установка завершена!"

echo "Следующие шаги:"
echo ""
echo "  1. Настройте .env файл (для Telegram/Slack уведомлений):"
echo "     nano .env"
echo ""
echo "  2. Выберите AI модель (если пропустили):"
echo "     python3 system/scripts/init_user.py"
echo ""
echo "  3. Создайте первую цель:"
echo "     Обратитесь к AI-коучу: 'Я хочу достичь [ваша цель]'"
echo ""
echo "  4. Настройте автоматизацию (опционально):"
echo "     python3 system/scripts/schedule_manager.py setup"
echo ""
echo "Документация:"
echo "  • README.md - Обзор системы"
echo "  • SETUP.md - Детальные инструкции"
echo "  • system/docs/AI_MODELS.md - Руководство по AI моделям"
echo ""

print_success "Готово к работе!"
