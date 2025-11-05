from django import template

register = template.Library()

@register.filter
def split(value, delimiter):
    """
    Разделяет строку по указанному разделителю.
    Использование в шаблоне: {{ value|split:"delimiter" }}
    """
    if value is None:
        return []
    return value.split(delimiter)

@register.filter
def startswith(value, prefix):
    """
    Проверяет, начинается ли строка с указанного префикса.
    Использование в шаблоне: {% if value|startswith:"prefix" %}
    """
    if value is None:
        return False
    return value.startswith(prefix)

@register.filter
def strip(value):
    """
    Удаляет лишние пробелы
    """

    if value is None:
        return ""
    return str(value).strip()

@register.filter
def get_calculation_title(content):
    """
    Извлекает название расчета из содержимого поста.
    Ищет строку, начинающуюся с 'Название:', и возвращает её значение.
    """
    if not content:
        return "Без названия"

    lines = content.split('\n')
    for line in lines:
        if line.startswith("Название:"):
            title = line.replace("Название:", "").strip()
            return title if title else "Без названия"
    return "Без названия"

@register.filter
def get_algorithm(content):
    """
    Извлекает алгоритм из содержимого поста.
    Ищет строку, начинающуюся с 'Алгоритм:', и возвращает её значение.
    """
    if not content:
        return "Не указан"

    lines = content.split('\n')
    for line in lines:
        if line.startswith("Алгоритм:"):
            value = line.replace("Алгоритм:", "").strip()
            return value if value else "Не указан"
    return "Не указан"

@register.filter
def get_param_a(content):
    """
    Извлекает параметр A (A12) из содержимого поста.
    Ищет строку, начинающуюся с 'Параметр A:', и возвращает её значение.
    """
    if not content:
        return "N/A"

    lines = content.split('\n')
    for line in lines:
        if line.startswith("Параметр A:"):
            value = line.replace("Параметр A:", "").strip()
            return value if value else "N/A"
    return "N/A"

@register.filter
def get_param_b(content):
    """
    Извлекает параметр B (A21) из содержимого поста.
    Ищет строку, начинающуюся с 'Параметр B:', и возвращает её значение.
    """
    if not content:
        return "N/A"

    lines = content.split('\n')
    for line in lines:
        if line.startswith("Параметр B:"):
            value = line.replace("Параметр B:", "").strip()
            return value if value else "N/A"
    return "N/A"

@register.filter
def get_iterations(content):
    """
    Извлекает количество итераций из содержимого поста.
    Ищет строку, начинающуюся с 'Итерации:', и возвращает её значение.
    """
    if not content:
        return "N/A"

    lines = content.split('\n')
    for line in lines:
        if line.startswith("Итерации:"):
            value = line.replace("Итерации:", "").strip()
            return value if value else "N/A"
    return "N/A"

@register.filter
def get_execution_time(content):
    """
    Извлекает время выполнения из содержимого поста.
    Ищет строку, начинающуюся с 'Время выполнения:', и возвращает её значение.
    """
    if not content:
        return "N/A"

    lines = content.split('\n')
    for line in lines:
        if line.startswith("Время выполнения:"):
            value = line.replace("Время выполнения:", "").strip()
            return value if value else "N/A"
    return "N/A"

@register.filter
def get_average_error(content):
    """
    Извлекает среднюю погрешность из содержимого поста.
    Ищет строку, начинающуюся с 'Средняя погрешность:', и возвращает её значение.
    """
    if not content:
        return "N/A"

    lines = content.split('\n')
    for line in lines:
        if line.startswith("Средняя погрешность:"):
            value = line.replace("Средняя погрешность:", "").strip()
            return value if value else "N/A"
    return "N/A"


@register.filter
def extract_comment(content):
    """
    Извлекает пользовательский комментарий из post.content, игнорируя технические данные.
    Возвращает комментарий или пустую строку, если его нет.
    """
    if not content:
        return ""

    lines = content.split("\n")

    table_data_index = -1
    for i, line in enumerate(lines):
        if line.startswith("Данные таблицы:"):
            table_data_index = i
            break

    if table_data_index == -1:
        return ""

    comment_lines = []
    for line in lines[table_data_index + 1:]:
        if line.strip() and not line.strip().replace(",", "").replace(".", "").isdigit():
            comment_lines.append(line)

    print("comm:", comment_lines)
    if len(comment_lines)==2:
        comment_lines.pop(0)
    return "\n".join(comment_lines).strip() if comment_lines else ""