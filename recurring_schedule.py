# -*- coding: utf-8 -*-
"""
recurring_schedule.py — Повторяющиеся задачи для графика работы

Автоматически назначает повторяющиеся задачи:
- Протирка полок — каждый вторник (сереневый цвет)
- Ревизия — 1 и 16 число каждого месяца
- Проверка ценников — 2 и 17 число
- Сроки годности, Акции — 5 и 20 число
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Стандартные повторяющиеся задачи
RECURRING_TASKS = [
    {
        "id": 1001,
        "name": "Протирка полок",
        "color": "#B39DDB",  # сиреневый
        "schedule_type": "weekly",  # еженедельно
        "weekday": 1,  # вторник (0=понедельник, 6=воскресенье)
        "description": "Влажная уборка всех полок в торговом зале"
    },
    {
        "id": 1002,
        "name": "Ревизия",
        "color": "#FF9800",  # оранжевый
        "schedule_type": "monthly_days",
        "days": [1, 16],  # 1 и 16 число
        "description": "Полная инвентаризация товара"
    },
    {
        "id": 1003,
        "name": "Проверка ценников",
        "color": "#FFEB3B",  # желтый
        "schedule_type": "monthly_days",
        "days": [2, 17],  # 2 и 17 число
        "description": "Сверка ценников с базой данных"
    },
    {
        "id": 1004,
        "name": "Сроки годности, Акции",
        "color": "#9C27B0",  # фиолетовый
        "schedule_type": "monthly_days",
        "days": [5, 20],  # 5 и 20 число
        "description": "Проверка сроков годности и акционных товаров"
    },
    {
        "id": 1005,
        "name": "Уборка влажная",
        "color": "#4CAF50",  # зеленый
        "schedule_type": "weekly",
        "weekday": 4,  # пятница
        "description": "Влажная уборка всего помещения"
    }
]


def get_recurring_tasks() -> List[Dict[str, Any]]:
    """
    Получить список всех повторяющихся задач.
    
    Returns:
        Список словарей с задачами
    """
    return RECURRING_TASKS.copy()


def get_recurring_for_month(year: int, month: int) -> List[Dict[str, Any]]:
    """
    Получить все повторяющиеся задачи для указанного месяца.
    
    Args:
        year: Год (например, 2026)
        month: Месяц (1-12)
    
    Returns:
        Список словарей вида:
        [
            {
                "day": 1,
                "tasks": [{"id": 1002, "name": "Ревизия", "color": "#FF9800"}]
            },
            ...
        ]
    """
    result = {}
    
    # Определяем количество дней в месяце
    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year
    
    first_day_of_month = datetime(year, month, 1)
    first_day_of_next_month = datetime(next_year, next_month, 1)
    days_in_month = (first_day_of_next_month - first_day_of_month).days
    
    for task in RECURRING_TASKS:
        if task.get("schedule_type") == "monthly_days":
            # Задачи по конкретным дням месяца
            for day in task.get("days", []):
                if day <= days_in_month:
                    if day not in result:
                        result[day] = {"day": day, "tasks": []}
                    result[day]["tasks"].append({
                        "id": task["id"],
                        "name": task["name"],
                        "color": task["color"],
                        "description": task.get("description", ""),
                        "is_recurring": True
                    })
        
        elif task.get("schedule_type") == "weekly":
            # Еженедельные задачи по дню недели
            weekday = task.get("weekday", 0)  # 0=понедельник
            for day in range(1, days_in_month + 1):
                current_date = datetime(year, month, day)
                # Python: 0=понедельник, 6=воскресенье
                if current_date.weekday() == weekday:
                    if day not in result:
                        result[day] = {"day": day, "tasks": []}
                    result[day]["tasks"].append({
                        "id": task["id"],
                        "name": task["name"],
                        "color": task["color"],
                        "description": task.get("description", ""),
                        "is_recurring": True
                    })
    
    # Преобразуем в отсортированный список
    sorted_result = [result[day] for day in sorted(result.keys())]
    return sorted_result


def get_recurring_for_day(year: int, month: int, day: int) -> List[Dict[str, Any]]:
    """
    Получить повторяющиеся задачи для конкретного дня.
    
    Args:
        year: Год
        month: Месяц
        day: День
    
    Returns:
        Список задач на этот день
    """
    try:
        # Проверяем валидность даты
        datetime(year, month, day)
    except ValueError:
        return []
    
    recurring = get_recurring_for_month(year, month)
    for item in recurring:
        if item["day"] == day:
            return item["tasks"]
    return []


def is_recurring_task(task_id: int) -> bool:
    """
    Проверить, является ли задача повторяющейся.
    
    Args:
        task_id: ID задачи
    
    Returns:
        True если задача повторяющаяся
    """
    return any(task["id"] == task_id for task in RECURRING_TASKS)


def get_task_by_id(task_id: int) -> Dict[str, Any]:
    """
    Получить задачу по ID.
    
    Args:
        task_id: ID задачи
    
    Returns:
        Словарь с задачей или None
    """
    for task in RECURRING_TASKS:
        if task["id"] == task_id:
            return task.copy()
    return None


def add_recurring_task(name: str, color: str, schedule_type: str, 
                       weekday: int = None, days: List[int] = None,
                       description: str = "") -> Dict[str, Any]:
    """
    Добавить новую повторяющуюся задачу.
    
    Args:
        name: Название задачи
        color: Цвет в формате #RRGGBB
        schedule_type: 'weekly' или 'monthly_days'
        weekday: День недели (0-6) для weekly
        days: Список дней месяца для monthly_days
        description: Описание задачи
    
    Returns:
        Созданная задача
    """
    new_id = max(task["id"] for task in RECURRING_TASKS) + 1 if RECURRING_TASKS else 1001
    
    new_task = {
        "id": new_id,
        "name": name,
        "color": color,
        "schedule_type": schedule_type,
        "description": description
    }
    
    if schedule_type == "weekly" and weekday is not None:
        new_task["weekday"] = weekday
    elif schedule_type == "monthly_days" and days:
        new_task["days"] = days
    
    RECURRING_TASKS.append(new_task)
    return new_task


def remove_recurring_task(task_id: int) -> bool:
    """
    Удалить повторяющуюся задачу.
    
    Args:
        task_id: ID задачи для удаления
    
    Returns:
        True если задача удалена
    """
    global RECURRING_TASKS
    original_len = len(RECURRING_TASKS)
    RECURRING_TASKS = [t for t in RECURRING_TASKS if t["id"] != task_id]
    return len(RECURRING_TASKS) < original_len


def get_upcoming_reminders(days_ahead: int = 3) -> list:
    """
    Получить предстоящие повторяющиеся задачи на ближайшие N дней.
    
    Args:
        days_ahead: Количество дней вперёд (по умолчанию 3)
    
    Returns:
        Список напоминаний вида:
        [
            {
                "date": "22.03.2026",
                "tasks": ["Протирка полок", "Ревизия"],
                "message": "22.03: Протирка полок, Ревизия"
            },
            ...
        ]
    """
    from datetime import date, timedelta
    
    reminders = []
    today = date.today()
    
    for i in range(days_ahead + 1):
        check_date = today + timedelta(days=i)
        tasks = get_recurring_for_day(check_date.year, check_date.month, check_date.day)
        
        if tasks:
            task_names = [t["name"] for t in tasks]
            reminders.append({
                "date": check_date.strftime("%d.%m.%Y"),
                "tasks": tasks,
                "task_names": task_names,
                "message": f"{check_date.strftime('%d.%m')}: {', '.join(task_names)}"
            })
    
    return reminders


# Для совместимости с旧 кодом
def get_recurring_schedule(year: int, month: int) -> List[Dict[str, Any]]:
    """Устаревшее имя функции, используйте get_recurring_for_month."""
    return get_recurring_for_month(year, month)


if __name__ == "__main__":
    # Тестовый запуск
    print("📅 Повторяющиеся задачи для графика работы")
    print("=" * 50)
    
    now = datetime.now()
    print(f"\nЗадачи на {now.strftime('%B %Y')}:\n")
    
    recurring = get_recurring_for_month(now.year, now.month)
    for item in recurring:
        day = item["day"]
        tasks = item["tasks"]
        print(f"  {day:2d} число: {', '.join(t['name'] for t in tasks)}")
    
    print("\n" + "=" * 50)
    print(f"Всего повторяющихся задач: {len(RECURRING_TASKS)}")
    for task in RECURRING_TASKS:
        print(f"  • {task['name']} ({task['schedule_type']})")
