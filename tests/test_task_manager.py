# test_task_manager.py - Tests pour la logique métier
import sys
import os
import re
import uuid
from datetime import datetime, timedelta
import pytest
from unittest.mock import patch


sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.task_manager import get_tasks, task_list, create_task, consult_task, delete_task, update_status, update_task, \
    get_tasks_paginated, search_tasks, filter_tasks_by_status, sort_tasks, create_user, list_users, user_list

@pytest.fixture(autouse=True)
def mock_save_tasks():
    with patch('src.task_manager._save_tasks') as mock_save:
        yield mock_save

class TestTaskManager:
    
    def setup_method(self):
        """Initialise les données de test avant chaque test"""
        task_list.clear()
        task_list.extend([
            {
                "id": str(uuid.uuid4()),
                "title": "Première tâche",
                "description": "Description de la première tâche",
                "status": "TODO"
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Deuxième tâche",
                "description": "Description de la deuxième tâche",
                "status": "DONE"
            }
        ])
    
    def test_get_tasks_returns_list(self):
        tasks = get_tasks()
        assert isinstance(tasks, list)
    
    def test_get_tasks_returns_two_tasks(self):
        tasks = get_tasks()
        assert len(tasks) == 2
    
    def test_get_tasks_returns_correct_structure(self):
        tasks = get_tasks()
        for task in tasks:
            assert "id" in task
            assert "title" in task
            assert "description" in task
            assert "status" in task

class TestCreateTask:

    def setup_method(self):
        task_list.clear()

    def test_create_task_with_valid_title(self):
        create_task("Ma tâche")
        assert len(task_list) == 1
        task = task_list[0]
        assert task["title"] == "Ma tâche"
        assert task["description"] == ""
        assert task["status"] == "TODO"
        assert isinstance(task["id"], str)

    def test_create_task_with_valid_title_and_description(self):
        create_task("Tâche complète", "Description test")
        task = task_list[0]
        assert task["title"] == "Tâche complète"
        assert task["description"] == "Description test"

    def test_create_task_title_strips_spaces(self):
        create_task("   Nettoyer les espaces   ")
        task = task_list[0]
        assert task["title"] == "Nettoyer les espaces"

    def test_create_task_with_empty_title_raises(self):
        with pytest.raises(ValueError, match="Title is required"):
            create_task("   ")
        assert len(task_list) == 0

    def test_create_task_title_too_long_raises(self):
        long_title = "T" * 101
        with pytest.raises(ValueError, match="Title cannot exceed 100 characters"):
            create_task(long_title)
        assert len(task_list) == 0

    def test_create_task_description_too_long_raises(self):
        long_desc = "D" * 501
        with pytest.raises(ValueError, match="Description cannot exceed 500 characters"):
            create_task("Valide", long_desc)
        assert len(task_list) == 0

    def test_create_task_created_at_is_precise(self):
        now = datetime.now()
        create_task("Horodatée")
        created = datetime.fromisoformat(task_list[0]["created_at"])
        assert abs((created - now).total_seconds()) < 1.0

class TestConsultTask:

    def setup_method(self):
        task_list.clear()

    def test_get_task_by_id_valid(self):
        create_task("Tâche à consulter", "Détails ici")
        task = task_list[0]
        retrieved = consult_task(task["id"])
        assert retrieved["id"] == task["id"]
        assert retrieved["title"] == "Tâche à consulter"
        assert retrieved["description"] == "Détails ici"
        assert "created_at" in retrieved
        assert retrieved["status"] == "TODO"

    def test_get_task_by_id_not_found(self):
        random_id = str(uuid.uuid4())
        with pytest.raises(ValueError, match="Task not found"):
            consult_task(random_id)

    def test_get_task_by_id_invalid_format(self):
        with pytest.raises(ValueError, match="Invalid ID format"):
            consult_task("invalid-format")

class TestDeleteTask:

    def setup_method(self):
        task_list.clear()
        self.task1 = {
            "id": str(uuid.uuid4()),
            "title": "Tâche à supprimer",
            "description": "Test",
            "status": "TODO"
        }
        self.task2 = {
            "id": str(uuid.uuid4()),
            "title": "Tâche restante",
            "description": "Doit rester",
            "status": "TODO"
        }
        task_list.extend([self.task1, self.task2])

    def test_delete_existing_task(self):
        delete_task(self.task1["id"])
        assert len(task_list) == 1
        assert task_list[0]["id"] == self.task2["id"]
    
    def test_delete_then_access_task(self):
        delete_task(self.task1["id"])
        with pytest.raises(ValueError, match="Task not found"):
            consult_task(self.task1["id"])
    
    def test_delete_non_existing_task(self):
        with pytest.raises(ValueError, match="Task not found"):
            delete_task(str(uuid.uuid4()))

class TestPagination:

    def setup_method(self):
        task_list.clear()
        for i in range(1, 26):
            task_list.append({
                "id": str(uuid.uuid4()),
                "title": f"Tâche {i}",
                "description": f"Description {i}",
                "status": "TODO",
                "created_at": datetime.now().isoformat()
            })

    def test_first_page_10_items(self):
        result = get_tasks_paginated(page=1, size=10)
        assert len(result["tasks"]) == 10
        assert result["page"] == 1
        assert result["total_items"] == 25
        assert result["total_pages"] == 3

    def test_second_page_items(self):
        result = get_tasks_paginated(page=2, size=10)
        assert len(result["tasks"]) == 10
        expected_titles = [f"Tâche {i}" for i in range(11, 21)]
        actual_titles = [task["title"] for task in result["tasks"]]
        assert actual_titles == expected_titles

    def test_page_beyond_total(self):
        result = get_tasks_paginated(page=5, size=10)
        assert result["tasks"] == []
        assert result["total_pages"] == 3

    def test_default_pagination(self):
        result = get_tasks_paginated()
        assert result["page"] == 1
        assert result.get("page_size", 20) == 20
        assert len(result["tasks"]) == 20

    def test_invalid_page_size(self):
        with pytest.raises(ValueError, match="Invalid page size"):
            get_tasks_paginated(size=0)

    def test_invalid_page_number(self):
        with pytest.raises(ValueError, match="Invalid page number"):
            get_tasks_paginated(page=0)

    def test_empty_task_list(self):
        task_list.clear()
        result = get_tasks_paginated(page=1, size=10)
        assert result["tasks"] == []
        assert result["total_items"] == 0
        assert result["total_pages"] == 0

class TestChangeStatus:

    def setup_method(self):
        task_list.clear()
        create_task("Tâche à modifier")
        self.task = task_list[-1]

    def test_valid_status_todo(self):
        update_status(self.task["id"], "TODO")
        updated = next(t for t in task_list if t["id"] == self.task["id"])
        assert updated["status"] == "TODO"

    def test_valid_status_ongoing(self):
        update_status(self.task["id"], "ONGOING")
        updated = next(t for t in task_list if t["id"] == self.task["id"])
        assert updated["status"] == "ONGOING"

    def test_valid_status_done(self):
        update_status(self.task["id"], "DONE")
        updated = next(t for t in task_list if t["id"] == self.task["id"])
        assert updated["status"] == "DONE"

    def test_invalid_status(self):
        with pytest.raises(ValueError, match="Invalid status. Allowed values: TODO, ONGOING, DONE"):
            update_status(self.task["id"], "FINISHED")

    def test_non_existing_task(self):
        with pytest.raises(ValueError, match="Task not found"):
            update_status("invalid-id", "DONE")

class TestUpdateTask:

    def setup_method(self):
        task_list.clear()
        create_task("Tâche à modifier")
        self.task = task_list[-1]

    def test_update_title_only(self):
        updated = update_task(self.task["id"], title="Titre modifié")
        assert updated["title"] == "Titre modifié"
        assert updated["description"] == self.task["description"]

    def test_update_description_only(self):
        updated = update_task(self.task["id"], description="Nouvelle description")
        assert updated["description"] == "Nouvelle description"
        assert updated["title"] == self.task["title"]

    def test_update_title_and_description(self):
        updated = update_task(self.task["id"], title="Nouveau titre", description="Nouvelle desc")
        assert updated["title"] == "Nouveau titre"
        assert updated["description"] == "Nouvelle desc"

    def test_update_with_empty_title(self):
        with pytest.raises(ValueError, match="Title is required"):
            update_task(self.task["id"], title=" ")

    def test_update_with_long_title(self):
        long_title = "T" * 101
        with pytest.raises(ValueError, match="Title cannot exceed 100 characters"):
            update_task(self.task["id"], title=long_title)

    def test_update_with_long_description(self):
        long_desc = "D" * 501
        with pytest.raises(ValueError, match="Description cannot exceed 500 characters"):
            update_task(self.task["id"], description=long_desc)

    def test_update_non_existing_task(self):
        with pytest.raises(ValueError, match="Task not found"):
            update_task("invalid-id", title="Test")

    def test_immutable_fields_ignored(self):
        updated = update_task(self.task["id"], title="Nouveau", description="desc")
        assert updated["id"] == self.task["id"]
        assert updated["created_at"] == self.task["created_at"]
        assert updated["status"] == self.task["status"]

class TestSearchTasks:

    def setup_method(self):
        task_list.clear()
        task_list.extend([
            {
                "id": str(uuid.uuid4()),
                "title": "Réparer la voiture",
                "description": "Trouver un garage pour réparer la voiture",
                "status": "TODO",
                "created_at": datetime.now().isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Appeler le plombier",
                "description": "Réparer la fuite d'eau",
                "status": "ONGOING",
                "created_at": datetime.now().isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Acheter du pain",
                "description": "Pain frais à la boulangerie",
                "status": "DONE",
                "created_at": datetime.now().isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Réparer le vélo",
                "description": "Vérifier les freins",
                "status": "TODO",
                "created_at": datetime.now().isoformat()
            }
        ])

    def test_search_in_title_returns_only_matching_tasks(self):
        result = search_tasks("réparer", search_in="title")
        titles = [t["title"] for t in result["tasks"]]
        assert all("réparer" in t.lower() for t in titles)
        assert len(titles) == 2

    def test_search_in_description_returns_only_matching_tasks(self):
        result = search_tasks("garage", search_in="description")
        descriptions = [t["description"] for t in result["tasks"]]
        assert all("garage" in d.lower() for d in descriptions)
        assert len(descriptions) == 1

    def test_search_in_title_and_description_returns_all_unique_tasks(self):
        result = search_tasks("réparer")
        assert len(result["tasks"]) == 1
        result2 = search_tasks("fuite")
        assert len(result2["tasks"]) == 0

    def test_search_non_existing_term_returns_empty_list(self):
        result = search_tasks("inexistant")
        assert result["tasks"] == []

    def test_search_empty_string_returns_all_tasks(self):
        result = search_tasks("")
        assert len(result["tasks"]) == len(task_list)

    def test_search_case_insensitive(self):
        result_lower = search_tasks("réparer")
        result_upper = search_tasks("RÉPARER")
        assert result_lower["tasks"] == result_upper["tasks"]

    def test_search_results_are_paginated(self):
        for i in range(30):
            task_list.append({
                "id": str(uuid.uuid4()),
                "title": f"Tâche test {i}",
                "description": "",
                "status": "TODO",
                "created_at": datetime.now().isoformat()
            })
        page1 = search_tasks("test", page=1, size=10, search_in="both")
        page2 = search_tasks("test", page=2, size=10, search_in="both")
        assert len(page1["tasks"]) == 10
        assert len(page2["tasks"]) == 10
        assert page1["total_items"] == 30

class TestFilterTasksByStatus:

    def setup_method(self):
        task_list.clear()
        statuses = ["TODO", "ONGOING", "DONE"]
        for i, status in enumerate(statuses):
            task_list.append({
                "id": str(uuid.uuid4()),
                "title": f"Tâche {status}",
                "description": "",
                "status": status,
                "created_at": datetime.now().isoformat()
            })

    def test_filter_todo_returns_only_todo_tasks(self):
        result = filter_tasks_by_status("TODO")
        assert all(t["status"] == "TODO" for t in result["tasks"])
        assert len(result["tasks"]) == 1

    def test_filter_ongoing_returns_only_ongoing_tasks(self):
        result = filter_tasks_by_status("ONGOING")
        assert all(t["status"] == "ONGOING" for t in result["tasks"])
        assert len(result["tasks"]) == 1

    def test_filter_done_returns_only_done_tasks(self):
        result = filter_tasks_by_status("DONE")
        assert all(t["status"] == "DONE" for t in result["tasks"])
        assert len(result["tasks"]) == 1

    def test_filter_status_with_no_match_returns_empty_list(self):
        result = filter_tasks_by_status("TODO")
        task_list[:] = [t for t in task_list if t["status"] != "TODO"]
        result = filter_tasks_by_status("TODO")
        assert result["tasks"] == []

    def test_filter_with_invalid_status_raises(self):
        with pytest.raises(ValueError, match="Invalid filter status"):
            filter_tasks_by_status("INVALID")

    def test_filter_results_are_paginated(self):
        task_list.clear()
        for i in range(25):
            task_list.append({
                "id": str(uuid.uuid4()),
                "title": f"Tâche {i}",
                "description": "",
                "status": "TODO",
                "created_at": datetime.now().isoformat()
            })
        result = filter_tasks_by_status("TODO", page=2, size=10)
        assert len(result["tasks"]) == 10
        assert result["page"] == 2
        assert result["total_items"] == 25

class TestSortTasks:

    def setup_method(self):
        task_list.clear()
        now = datetime.now()
        task_list.extend([
            {"id": "1", "title": "Banana", "status": "TODO", "created_at": now.isoformat()},
            {"id": "2", "title": "Apple", "status": "DONE", "created_at": (now - timedelta(days=1)).isoformat()},
            {"id": "3", "title": "Cherry", "status": "ONGOING", "created_at": (now - timedelta(days=2)).isoformat()},
        ])

    def test_sort_by_creation_date_asc(self):
        sorted_tasks = sort_tasks(by="created_at", ascending=True, tasks=task_list)
        dates = [t["created_at"] for t in sorted_tasks]
        assert dates == sorted(dates)

    def test_sort_by_creation_date_desc(self):
        sorted_tasks = sort_tasks(by="created_at", ascending=False, tasks=task_list)
        dates = [t["created_at"] for t in sorted_tasks]
        assert dates == sorted(dates, reverse=True)

    def test_sort_by_title_asc(self):
        sorted_tasks = sort_tasks(by="title", ascending=True, tasks=task_list)
        titles = [t["title"] for t in sorted_tasks]
        assert titles == sorted(titles)

    def test_sort_by_title_desc(self):
        sorted_tasks = sort_tasks(by="title", ascending=False, tasks=task_list)
        titles = [t["title"] for t in sorted_tasks]
        assert titles == sorted(titles, reverse=True)

    def test_sort_by_status_groups_in_order(self):
        # TODO < ONGOING < DONE
        sorted_tasks = sort_tasks(by="status", ascending=True, tasks=task_list)
        order_map = {"TODO": 0, "ONGOING": 1, "DONE": 2}
        status_order = [order_map[t["status"]] for t in sorted_tasks]
        assert status_order == sorted(status_order)

    def test_default_sort_is_creation_date_desc(self):
        sorted_tasks = sort_tasks(by="created_at", ascending=False, tasks=task_list)
        dates = [t["created_at"] for t in sorted_tasks]
        assert dates == sorted(dates, reverse=True)

    def test_invalid_sort_criteria_raises(self):
        with pytest.raises(ValueError, match="Invalid sort criteria"):
            sort_tasks(by="invalid", ascending=True, tasks=task_list)

    def test_sort_combined_with_filter(self):
        filtered = [t for t in task_list if t["status"] == "TODO"]
        sorted_tasks = sort_tasks(by="title", ascending=True, tasks=filtered)
        titles = [t["title"] for t in sorted_tasks]
        assert titles == sorted(titles)

class TestCreateUser:

    def setup_method(self):
        user_list.clear()

    def test_create_user_with_valid_data(self):
        user = create_user("Alice", "alice@example.com")
        assert user["name"] == "Alice"
        assert user["email"] == "alice@example.com"
        assert "id" in user
        assert "created_at" in user
        datetime.fromisoformat(user["created_at"])  # valid ISO date

    def test_create_user_with_duplicate_email_raises_error(self):
        create_user("Alice", "alice@example.com")
        with pytest.raises(ValueError, match="Email already in use"):
            create_user("Bob", "alice@example.com")

    def test_create_user_with_invalid_email_format_raises_error(self):
        with pytest.raises(ValueError, match="Invalid email format"):
            create_user("Charlie", "invalid-email")

    def test_create_user_with_empty_name_raises_error(self):
        with pytest.raises(ValueError, match="Name is required"):
            create_user("   ", "charlie@example.com")

    def test_create_user_with_name_too_long_raises_error(self):
        long_name = "A" * 51
        with pytest.raises(ValueError, match="Name cannot exceed 50 characters"):
            create_user(long_name, "david@example.com")


class TestListUsers:

    def setup_method(self):
        user_list.clear()
        self.users = [
            create_user("Zoe", "zoe@example.com"),
            create_user("Alice", "alice@example.com"),
            create_user("Bob", "bob@example.com"),
        ]

    def test_list_users_returns_all_users_sorted_by_name(self):
        result = list_users()
        names = [u["name"] for u in result["users"]]
        assert names == sorted(names)

    def test_list_users_returns_paginated_results(self):
        user_list.clear()
        for i in range(30):
            create_user(f"User{i}", f"user{i}@example.com")

        page1 = list_users(page=1, size=10)
        page2 = list_users(page=2, size=10)

        assert len(page1["users"]) == 10
        assert len(page2["users"]) == 10
        assert page1["total_items"] == 30
        assert page1["total_pages"] == 3

    def test_list_users_returns_empty_list_when_none_exist(self):
        user_list.clear()
        result = list_users()
        assert result["users"] == []