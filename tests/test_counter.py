import pytest
from sqlmodel import Session
from nicegui.testing import User
from nicegui import ui
from app.database import ENGINE, reset_db
from app.models import Counter
from app.counter import get_or_create_counter, update_counter_value


@pytest.fixture()
def new_db():
    reset_db()
    yield
    reset_db()


class TestCounterLogic:
    """Test counter business logic without UI."""

    def test_get_or_create_counter_creates_new(self, new_db):
        """Test creating a new counter when none exists."""
        with Session(ENGINE) as session:
            counter = get_or_create_counter(session, "test_counter")

            assert counter.name == "test_counter"
            assert counter.value == 0
            assert counter.id is not None

    def test_get_or_create_counter_gets_existing(self, new_db):
        """Test retrieving existing counter."""
        with Session(ENGINE) as session:
            # Create first counter
            counter1 = get_or_create_counter(session, "test_counter")
            original_id = counter1.id

            # Try to get same counter again
            counter2 = get_or_create_counter(session, "test_counter")

            assert counter2.id == original_id
            assert counter2.name == "test_counter"
            assert counter2.value == 0

    def test_update_counter_value_success(self, new_db):
        """Test updating counter value successfully."""
        with Session(ENGINE) as session:
            counter = get_or_create_counter(session, "test_counter")
            counter_id = counter.id

            assert counter_id is not None
            updated_counter = update_counter_value(session, counter_id, 42)

            assert updated_counter is not None
            assert updated_counter.value == 42
            assert updated_counter.id == counter_id

    def test_update_counter_value_nonexistent(self, new_db):
        """Test updating counter that doesn't exist."""
        with Session(ENGINE) as session:
            result = update_counter_value(session, 999, 42)
            assert result is None

    def test_counter_persistence(self, new_db):
        """Test that counter values persist across sessions."""
        counter_id = None

        # Create and update counter in first session
        with Session(ENGINE) as session:
            counter = get_or_create_counter(session, "persistent_counter")
            counter_id = counter.id
            assert counter_id is not None
            update_counter_value(session, counter_id, 100)

        # Verify persistence in second session
        with Session(ENGINE) as session:
            counter = session.get(Counter, counter_id)
            assert counter is not None
            assert counter.value == 100
            assert counter.name == "persistent_counter"

    def test_multiple_counters(self, new_db):
        """Test handling multiple different counters."""
        with Session(ENGINE) as session:
            counter1 = get_or_create_counter(session, "counter_1")
            counter2 = get_or_create_counter(session, "counter_2")

            assert counter1.id != counter2.id
            assert counter1.name == "counter_1"
            assert counter2.name == "counter_2"

            # Update different values
            if counter1.id is not None:
                update_counter_value(session, counter1.id, 10)
            if counter2.id is not None:
                update_counter_value(session, counter2.id, 20)

            # Verify both counters have correct values
            session.refresh(counter1)
            session.refresh(counter2)
            assert counter1.value == 10
            assert counter2.value == 20


class TestCounterUI:
    """Test counter UI interactions."""

    async def test_counter_page_loads(self, new_db, user: User):
        """Test that counter page loads successfully."""
        await user.open("/counter")
        await user.should_see("Counter App")
        await user.should_see("Increment")
        await user.should_see("Decrement")

    async def test_counter_increment(self, new_db, user: User):
        """Test increment button functionality."""
        await user.open("/counter")

        # Find initial value (should be 0)
        number_elements = list(user.find(ui.number).elements)
        assert len(number_elements) == 1
        counter_element = number_elements[0]
        assert counter_element.value == 0

        # Click increment button
        user.find("Increment").click()

        # Check value updated
        assert counter_element.value == 1

    async def test_counter_decrement(self, new_db, user: User):
        """Test decrement button functionality."""
        await user.open("/counter")

        # Find counter element
        number_elements = list(user.find(ui.number).elements)
        assert len(number_elements) == 1
        counter_element = number_elements[0]

        # Click decrement button
        user.find("Decrement").click()

        # Check value updated
        assert counter_element.value == -1

    async def test_counter_multiple_operations(self, new_db, user: User):
        """Test multiple increment and decrement operations."""
        await user.open("/counter")

        # Find counter element
        number_elements = list(user.find(ui.number).elements)
        counter_element = number_elements[0]

        # Perform multiple operations
        user.find("Increment").click()  # 1
        user.find("Increment").click()  # 2
        user.find("Increment").click()  # 3
        user.find("Decrement").click()  # 2

        assert counter_element.value == 2

    async def test_counter_negative_values(self, new_db, user: User):
        """Test counter can handle negative values."""
        await user.open("/counter")

        # Find counter element
        number_elements = list(user.find(ui.number).elements)
        counter_element = number_elements[0]

        # Go negative
        user.find("Decrement").click()  # -1
        user.find("Decrement").click()  # -2
        user.find("Decrement").click()  # -3

        assert counter_element.value == -3

    async def test_home_page_navigation(self, new_db, user: User):
        """Test navigation between pages."""
        await user.open("/")
        await user.should_see("Welcome to Counter App")
        await user.should_see("Go to Counter")

        # Navigate to counter page
        user.find("Go to Counter").click()
        await user.should_see("Counter App")
        await user.should_see("Back to Home")

        # Navigate back
        user.find("Back to Home").click()
        await user.should_see("Welcome to Counter App")
