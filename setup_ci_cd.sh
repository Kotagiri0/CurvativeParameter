#!/bin/bash

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Настройка CI/CD для CurvativeParameter${NC}\n"

# Проверка наличия Git
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git не установлен. Установите Git и повторите попытку.${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Git установлен"

# Создание структуры директорий
echo -e "\n${BLUE}📁 Создание структуры директорий...${NC}"

mkdir -p .github/workflows
mkdir -p main/tests
mkdir -p htmlcov

echo -e "${GREEN}✓${NC} Структура директорий создана"

# Создание __init__.py в tests
echo -e "\n${BLUE}📝 Создание файла main/tests/__init__.py...${NC}"
touch main/tests/__init__.py
echo -e "${GREEN}✓${NC} Файл создан"

# Проверка наличия requirements.txt
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ Файл requirements.txt не найден!${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Файл requirements.txt найден"

# Установка зависимостей для разработки
echo -e "\n${BLUE}📦 Хотите установить зависимости для тестирования? (y/n)${NC}"
read -r install_deps

if [ "$install_deps" = "y" ]; then
    echo -e "${BLUE}Установка зависимостей...${NC}"
    pip install pytest pytest-django pytest-cov coverage black isort flake8 pylint pylint-django
    echo -e "${GREEN}✓${NC} Зависимости установлены"
fi

# Создание .gitignore если его нет
if [ ! -f ".gitignore" ]; then
    echo -e "\n${BLUE}📝 Создание .gitignore...${NC}"
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Django
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal
/media
/staticfiles

# Environment
.env
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Testing
.coverage
htmlcov/
.pytest_cache/
.tox/

# OS
.DS_Store
Thumbs.db
EOF
    echo -e "${GREEN}✓${NC} .gitignore создан"
fi

# Проверка наличия .env
if [ ! -f ".env" ]; then
    echo -e "\n${BLUE}📝 Создание .env файла...${NC}"
    cat > .env << EOF
SECRET_KEY=your-secret-key-here
DEBUG=1
ALLOWED_HOSTS=localhost,127.0.0.1
CLOUDINARY_URL=cloudinary://your-cloudinary-url-here
DB_NAME=curvative_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
EOF
    echo -e "${GREEN}✓${NC} Файл .env создан"
    echo -e "${RED}⚠️  ВАЖНО: Обновите значения в .env файле!${NC}"
fi

# Проверка наличия pytest.ini
if [ -f "pytest.ini" ]; then
    echo -e "\n${GREEN}✓${NC} pytest.ini найден"
else
    echo -e "\n${RED}⚠️  pytest.ini не найден. Скопируйте его из артефактов.${NC}"
fi

# Проверка наличия .flake8
if [ -f ".flake8" ]; then
    echo -e "${GREEN}✓${NC} .flake8 найден"
else
    echo -e "${RED}⚠️  .flake8 не найден. Скопируйте его из артефактов.${NC}"
fi

# Запуск тестов
echo -e "\n${BLUE}🧪 Хотите запустить тесты? (y/n)${NC}"
read -r run_tests

if [ "$run_tests" = "y" ]; then
    echo -e "${BLUE}Запуск тестов...${NC}"
    python manage.py test
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} Все тесты прошли успешно!"
    else
        echo -e "${RED}❌ Некоторые тесты провалились${NC}"
    fi
fi

# Git настройки
echo -e "\n${BLUE}📤 Хотите добавить файлы в Git? (y/n)${NC}"
read -r git_add

if [ "$git_add" = "y" ]; then
    echo -e "${BLUE}Добавление файлов в Git...${NC}"
    git add .github/
    git add main/tests/
    git add pytest.ini 2>/dev/null || true
    git add .flake8 2>/dev/null || true
    git add Makefile 2>/dev/null || true
    git add .gitignore
    echo -e "${GREEN}✓${NC} Файлы добавлены в Git"

    echo -e "\n${BLUE}📝 Хотите сделать коммит? (y/n)${NC}"
    read -r git_commit

    if [ "$git_commit" = "y" ]; then
        git commit -m "Add CI/CD pipeline and tests"
        echo -e "${GREEN}✓${NC} Коммит создан"

        echo -e "\n${BLUE}📤 Хотите запушить изменения? (y/n)${NC}"
        read -r git_push

        if [ "$git_push" = "y" ]; then
            git push origin main
            echo -e "${GREEN}✓${NC} Изменения запушены"
        fi
    fi
fi

# Финальные инструкции
echo -e "\n${GREEN}════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Настройка завершена!${NC}"
echo -e "${GREEN}════════════════════════════════════════════${NC}\n"

echo -e "${BLUE}📋 Следующие шаги:${NC}\n"
echo -e "1. Обновите .env файл с реальными значениями"
echo -e "2. Настройте секреты в GitHub:"
echo -e "   - Перейдите в Settings → Secrets and variables → Actions"
echo -e "   - Добавьте SECRET_KEY, CLOUDINARY_URL и другие секреты"
echo -e "3. Запустите тесты локально: ${GREEN}make test${NC}"
echo -e "4. Проверьте линтеры: ${GREEN}make lint${NC}"
echo -e "5. Запушьте изменения в GitHub"
echo -e "6. Проверьте Actions в GitHub репозитории\n"

echo -e "${BLUE}📚 Полезные команды:${NC}\n"
echo -e "  ${GREEN}make help${NC}          - Список всех команд"
echo -e "  ${GREEN}make test${NC}          - Запуск тестов"
echo -e "  ${GREEN}make test-coverage${NC} - Тесты с покрытием"
echo -e "  ${GREEN}make lint${NC}          - Проверка кода"
echo -e "  ${GREEN}make format${NC}        - Форматирование кода"
echo -e "  ${GREEN}make docker-up${NC}     - Запуск Docker\n"

echo -e "${BLUE}📖 Документация: ${NC}CI_CD_SETUP.md\n"