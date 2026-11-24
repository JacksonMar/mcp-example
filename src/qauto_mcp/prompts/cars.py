"""Prompt: analyze_cars."""

from typing import Annotated

from mcp.server.mcpserver import MCPServer
from pydantic import Field

KM_PER_MILE = 1.609344


def register_car_prompts(mcp: MCPServer) -> None:
    @mcp.prompt(name="analyze_cars", title="Analyze cars")
    def analyze_cars(
        units: Annotated[str, Field(description='Одиниці пробігу в таблиці: "km" (за замовчуванням) або "miles".')] = "km",
        max_mileage: Annotated[
            str,
            Field(description='Показати тільки авто з пробігом до цього числа включно, у тих самих одиницях, що й units. Наприклад "50000". Порожнє — усі авто.'),
        ] = "",
    ) -> str:
        """Таблиця всіх авто користувача, від більшого пробігу до меншого, зі статусом.

        Статус за пробігом: зелений, жовтий або червоний. Prompt для всього
        гаража, а не для одного авто. Можна обмежити список за пробігом.
        """
        units = units.strip().lower()
        if units in ("mi", "mile", "miles", "милі", "миль", "мілі", "миля"):
            units = "miles"
        if units not in ("km", "miles"):
            raise ValueError('units must be "km" or "miles"')

        max_mileage = max_mileage.strip().replace(" ", "").replace("_", "")
        if max_mileage and (not max_mileage.isdigit()):
            raise ValueError("max_mileage must be a whole number, for example 50000")

        if units == "miles":
            units_rule = (
                f"   API повертає пробіг у km. Переведи mileage і initialMileage у милі: "
                f"km / {KM_PER_MILE}, округли до цілого.\n"
                "   Назви колонку \"Mileage (miles)\".\n"
            )
        else:
            units_rule = "   Пробіг показуй у km. Назви колонку \"Mileage (km)\".\n"

        if max_mileage:
            filter_rule = (
                f"3. Залиш тільки авто з mileage <= {int(max_mileage)} {units}. "
                "Порівнюй пробіг у тих самих одиницях. "
                "У введенні вкажи, скільки авто пройшло фільтр із загальної кількості.\n"
            )
        else:
            filter_rule = "3. Покажи всі авто, без фільтра за пробігом.\n"

        return (
            "Проаналізуй усі авто поточного користувача в qauto.\n\n"
            "1. Якщо сесії немає (get_cars повертає 401), спочатку виклич signin без аргументів.\n"
            "2. Виклич get_cars і візьми повний список авто.\n"
            f"{filter_rule}"
            "4. Для кожного авто використай усю доступну інформацію "
            "(id, brand, model, mileage, carBrandId, carModelId, "
            "initialMileage, updatedMileageAt, carCreatedAt, logo тощо).\n"
            "5. Відсортуй авто за mileage від більшого до меншого.\n"
            "6. Відповідь дай у вигляді markdown-таблиці з колонками:\n"
            "   | Brand | Model | Mileage | Status | Інші поля… |\n"
            f"{units_rule}"
            "7. Статус визнач за mileage у km з API, незалежно від одиниць у таблиці:\n"
            "   - mileage < 10000 → 🟢 зелений\n"
            "   - 10000 <= mileage <= 50000 → 🟡 жовтий\n"
            "   - mileage > 50000 → 🔴 червоний\n"
            "8. Якщо авто немає (або жодне не пройшло фільтр), так і напиши, без таблиці.\n"
            "9. Відповідай українською. Без зайвого тексту: лише коротке введення і таблиця."
        )
