from nicegui import ui
from sqlmodel import Session, select
from app.database import ENGINE
from app.models import Counter
from typing import Optional


def get_or_create_counter(session: Session, name: str = "default") -> Counter:
    """Get existing counter or create a new one."""
    statement = select(Counter).where(Counter.name == name)
    counter = session.exec(statement).first()

    if counter is None:
        counter = Counter(name=name, value=0)
        session.add(counter)
        session.commit()
        session.refresh(counter)

    return counter


def update_counter_value(session: Session, counter_id: int, new_value: int) -> Optional[Counter]:
    """Update counter value in database."""
    counter = session.get(Counter, counter_id)
    if counter is None:
        return None

    counter.value = new_value
    session.commit()
    session.refresh(counter)
    return counter


def create() -> None:
    """Create the counter page."""

    @ui.page("/counter")
    def counter_page():
        with Session(ENGINE) as session:
            counter = get_or_create_counter(session, "main_counter")

        # Create reactive value for the counter
        counter_value = ui.number(value=counter.value, format="%.0f").props("readonly")
        counter_value.classes("text-center text-6xl font-bold")

        def increment():
            new_value = int(counter_value.value) + 1
            counter_value.set_value(new_value)

            # Update in database
            with Session(ENGINE) as session:
                if counter.id is not None:
                    update_counter_value(session, counter.id, new_value)

        def decrement():
            new_value = int(counter_value.value) - 1
            counter_value.set_value(new_value)

            # Update in database
            with Session(ENGINE) as session:
                if counter.id is not None:
                    update_counter_value(session, counter.id, new_value)

        # Layout
        with ui.column().classes("w-full max-w-md mx-auto mt-8 items-center gap-4"):
            ui.label("Counter App").classes("text-2xl font-bold mb-4")

            # Counter display
            with ui.card().classes("p-6 text-center min-w-[200px]"):
                counter_value

            # Buttons
            with ui.row().classes("gap-4"):
                ui.button("Decrement", on_click=decrement).props("color=red icon=remove")
                ui.button("Increment", on_click=increment).props("color=green icon=add")

            # Navigation
            ui.link("Back to Home", "/").classes("mt-4")

    @ui.page("/")
    def index():
        with ui.column().classes("w-full max-w-md mx-auto mt-8 items-center gap-4"):
            ui.label("Welcome to Counter App").classes("text-3xl font-bold mb-4")
            ui.link("Go to Counter", "/counter").classes("text-xl")
