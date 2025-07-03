# test_task_manager.py - Tests pour la logique métier
import sys
import os
import re
import uuid
from datetime import datetime, timedelta
import pytest
from unittest.mock import patch


sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.task_manager import *

@pytest.fixture(autouse=True)
def mock_save_tasks():
    with patch('src.task_manager._save_tasks') as mock_save:
        yield mock_save

@pytest.fixture(autouse=True)
def mock_save_users():
    with patch('src.task_manager._save_users') as mock_save:
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

class TestUserManager:
    
    def setup_method(self):
        """Initialise les données de test avant chaque test"""
        user_list.clear()
        user_list.extend([
            {"id": "user-1", "name": "Alice Martin", "email": "alice@example.com"},
            {"id": "user-2", "name": "Bob Dupont", "email": "bob@example.com"}
        ]
        )
    
    def test_get_users_returns_list(self):
        users = get_users()
        assert isinstance(users, list)
        assert len(users) == 2
    
    def test_get_user_by_id_existing(self):
        user = get_user_by_id("user-1")
        assert user is not None
        assert user["name"] == "Alice Martin"
        assert user["email"] == "alice@example.com"
    
    def test_get_user_by_id_nonexistent(self):
        user = get_user_by_id("nonexistent")
        assert user is None
    
    def test_user_exists_true(self):
        assert user_exists("user-1") is True
        assert user_exists("user-2") is True
    
    def test_user_exists_false(self):
        assert user_exists("nonexistent") is False

class TestTaskAssignment:

    def setup_method(self):
        task_list.clear()
        user_list.clear()
        user_list.extend([
            {"id": "user-1", "name": "Alice Martin", "email": "alice@example.com"},
            {"id": "user-2", "name": "Bob Dupont", "email": "bob@example.com"}
        ]
        )
        
        # Créer une tâche de test
        create_task("Tâche à assigner", "Description test")
        self.task = task_list[0]

    def test_assign_task_to_existing_user(self):
        """ÉTANT DONNÉ QUE j'ai une tâche existante et un utilisateur existant, 
        LORSQUE j'assigne la tâche à l'utilisateur, 
        ALORS l'assignation est enregistrée et visible dans les détails de la tâche"""
        assigned_task = assign_task(self.task["id"], "user-1")
        assert assigned_task["assigned_user"] == "user-1"
        
        # Vérifier que l'assignation est persistée
        consulted_task = consult_task(self.task["id"])
        assert consulted_task["assigned_user"] == "user-1"

    def test_reassign_task_to_different_user(self):
        """ÉTANT DONNÉ QUE j'ai une tâche déjà assignée, 
        LORSQUE je l'assigne à un autre utilisateur, 
        ALORS l'ancienne assignation est remplacée par la nouvelle"""
        # Première assignation
        assign_task(self.task["id"], "user-1")
        
        # Réassignation
        reassigned_task = assign_task(self.task["id"], "user-2")
        assert reassigned_task["assigned_user"] == "user-2"
        
        # Vérifier que l'ancienne assignation est remplacée
        consulted_task = consult_task(self.task["id"])
        assert consulted_task["assigned_user"] == "user-2"

    def test_unassign_task(self):
        """ÉTANT DONNÉ QUE j'ai une tâche assignée, 
        LORSQUE je la désassigne (assigner à null/vide), 
        ALORS la tâche n'est plus assignée à personne"""
        # Assigner d'abord
        assign_task(self.task["id"], "user-1")
        
        # Désassigner avec None
        unassigned_task = assign_task(self.task["id"], None)
        assert unassigned_task["assigned_user"] is None
        
        # Tester aussi avec chaîne vide
        assign_task(self.task["id"], "user-1")
        unassigned_task = assign_task(self.task["id"], "")
        assert unassigned_task["assigned_user"] is None

    def test_assign_task_to_nonexistent_user_raises_error(self):
        """ÉTANT DONNÉ QUE je tente d'assigner une tâche à un utilisateur inexistant, 
        LORSQUE j'utilise un ID utilisateur invalide, 
        ALORS j'obtiens une erreur "User not found" """
        with pytest.raises(ValueError, match="User not found"):
            assign_task(self.task["id"], "nonexistent-user")

    def test_assign_nonexistent_task_raises_error(self):
        """ÉTANT DONNÉ QUE je tente d'assigner une tâche inexistante, 
        LORSQUE j'utilise un ID de tâche invalide, 
        ALORS j'obtiens une erreur "Task not found" """
        fake_task_id = str(uuid.uuid4())
        with pytest.raises(ValueError, match="Task not found"):
            assign_task(fake_task_id, "user-1")

    def test_assign_task_with_whitespace_user_id(self):
        """Test que les espaces autour de l'ID utilisateur sont nettoyés"""
        assigned_task = assign_task(self.task["id"], "  user-1  ")
        assert assigned_task["assigned_user"] == "user-1"

    def test_get_tasks_assigned_to_user(self):
        """Test récupération des tâches assignées à un utilisateur"""
        # Créer plusieurs tâches
        create_task("Tâche 2", "Autre tâche")
        create_task("Tâche 3", "Troisième tâche")
        
        # Assigner différentes tâches
        assign_task(task_list[0]["id"], "user-1")
        assign_task(task_list[1]["id"], "user-1")
        assign_task(task_list[2]["id"], "user-2")
        
        # Vérifier les tâches de user-1
        user1_tasks = get_tasks_assigned_to_user("user-1")
        assert len(user1_tasks) == 2
        assert all(task["assigned_user"] == "user-1" for task in user1_tasks)
        
        # Vérifier les tâches de user-2
        user2_tasks = get_tasks_assigned_to_user("user-2")
        assert len(user2_tasks) == 1
        assert user2_tasks[0]["assigned_user"] == "user-2"

    def test_get_unassigned_tasks(self):
        """Test récupération des tâches non assignées"""
        # Créer plusieurs tâches
        create_task("Tâche 2", "Autre tâche")
        create_task("Tâche 3", "Troisième tâche")
        
        # Assigner seulement une tâche
        assign_task(task_list[0]["id"], "user-1")
        
        # Les 2 autres tâches doivent être non assignées
        unassigned = get_unassigned_tasks()
        assert len(unassigned) == 2
        assert all(task.get("assigned_user") is None for task in unassigned)

    def test_create_task_has_assigned_user_field(self):
        """Test que les nouvelles tâches ont le champ assigned_user"""
        task_list.clear()
        new_task = create_task("Nouvelle tâche")
        assert "assigned_user" in new_task
        assert new_task["assigned_user"] is None

class TestFilterTasksByUser:

    def setup_method(self):
        task_list.clear()
        user_list.clear()
        user_list.extend([
            {"id": "user-1", "name": "Alice Martin", "email": "alice@example.com"},
            {"id": "user-2", "name": "Bob Dupont", "email": "bob@example.com"},
            {"id": "user-3", "name": "Charlie Brown", "email": "charlie@example.com"}
        ])
        
        create_task("Tâche Alice 1", "Première tâche d'Alice")
        create_task("Tâche Alice 2", "Deuxième tâche d'Alice")
        create_task("Tâche Bob", "Tâche de Bob")
        create_task("Tâche non assignée 1", "Pas d'assignation")
        create_task("Tâche non assignée 2", "Autre sans assignation")
        
        assign_task(task_list[0]["id"], "user-1")
        assign_task(task_list[1]["id"], "user-1")
        assign_task(task_list[2]["id"], "user-2") 

    def test_filter_tasks_by_specific_user_returns_only_assigned_tasks(self):
        """ÉTANT DONNÉ QUE j'ai des tâches assignées à différents utilisateurs, 
        LORSQUE je filtre par un utilisateur spécifique, 
        ALORS seules les tâches assignées à cet utilisateur sont retournées"""
        result = filter_tasks_by_user("user-1")
        assert len(result["tasks"]) == 2
        assert all(task["assigned_user"] == "user-1" for task in result["tasks"])
        assert result["total_items"] == 2
        
        titles = [task["title"] for task in result["tasks"]]
        assert "Tâche Alice 1" in titles
        assert "Tâche Alice 2" in titles
        
        result = filter_tasks_by_user("user-2")
        assert len(result["tasks"]) == 1
        assert result["tasks"][0]["assigned_user"] == "user-2"
        assert result["tasks"][0]["title"] == "Tâche Bob"

    def test_filter_unassigned_tasks_returns_only_unassigned(self):
        """ÉTANT DONNÉ QUE j'ai des tâches non assignées, 
        LORSQUE je filtre par "tâches non assignées", 
        ALORS seules les tâches sans assignation sont retournées"""
        result = filter_tasks_by_user("unassigned")
        assert len(result["tasks"]) == 2
        assert all(task.get("assigned_user") is None for task in result["tasks"])
        
        # Vérifier les titres des tâches non assignées
        titles = [task["title"] for task in result["tasks"]]
        assert "Tâche non assignée 1" in titles
        assert "Tâche non assignée 2" in titles

    def test_filter_by_user_with_no_assigned_tasks_returns_empty_list(self):
        """ÉTANT DONNÉ QUE je filtre par un utilisateur qui n'a aucune tâche assignée, 
        LORSQUE j'applique le filtre, 
        ALORS j'obtiens une liste vide"""
        result = filter_tasks_by_user("user-3")
        assert result["tasks"] == []
        assert result["total_items"] == 0
        assert result["total_pages"] == 0

    def test_filter_by_nonexistent_user_raises_error(self):
        """ÉTANT DONNÉ QUE je filtre par un utilisateur inexistant, 
        LORSQUE j'applique le filtre, 
        ALORS j'obtiens une erreur "User not found" """
        with pytest.raises(ValueError, match="User not found"):
            filter_tasks_by_user("nonexistent-user")

    def test_filter_by_user_with_pagination(self):
        """Test que le filtrage par utilisateur supporte la pagination"""
        # Créer plus de tâches pour Alice
        for i in range(15):
            create_task(f"Tâche Alice {i+3}", f"Description {i+3}")
            assign_task(task_list[-1]["id"], "user-1")
        
        # Alice a maintenant 17 tâches (2 + 15)
        page1 = filter_tasks_by_user("user-1", page=1, size=10)
        page2 = filter_tasks_by_user("user-1", page=2, size=10)
        
        assert len(page1["tasks"]) == 10
        assert len(page2["tasks"]) == 7
        assert page1["total_items"] == 17
        assert page1["total_pages"] == 2

class TestCombinedFilters:

    def setup_method(self):
        task_list.clear()
        global user_list
        user_list = [
            {"id": "user-1", "name": "Alice Martin", "email": "alice@example.com"},
            {"id": "user-2", "name": "Bob Dupont", "email": "bob@example.com"}
        ]
        
        # Créer des tâches avec différents statuts et assignations
        create_task("Réparer ordinateur Alice", "Problème de démarrage")
        create_task("Acheter matériel", "Pour le projet")
        create_task("Réparer imprimante Bob", "Bourrage papier")
        create_task("Nettoyer bureau", "Tâche de maintenance")
        create_task("Réparer serveur", "Maintenance urgente")
        
        # Assigner et définir les statuts
        assign_task(task_list[0]["id"], "user-1")  # Alice
        update_status(task_list[0]["id"], "TODO")
        
        assign_task(task_list[1]["id"], "user-1")  # Alice
        update_status(task_list[1]["id"], "DONE")
        
        assign_task(task_list[2]["id"], "user-2")  # Bob
        update_status(task_list[2]["id"], "ONGOING")
        
        # task_list[3] reste non assignée avec statut TODO
        update_status(task_list[3]["id"], "TODO")
        
        # task_list[4] reste non assignée avec statut DONE
        update_status(task_list[4]["id"], "DONE")

    def test_combine_user_filter_with_status_filter(self):
        """ÉTANT DONNÉ QUE je combine le filtre utilisateur avec d'autres filtres (statut), 
        LORSQUE j'applique les filtres, 
        ALORS tous les critères sont respectés"""
        # Filtrer tâches TODO d'Alice
        result = filter_tasks_combined(status="TODO", user_id="user-1")
        assert len(result["tasks"]) == 1
        assert result["tasks"][0]["title"] == "Réparer ordinateur Alice"
        assert result["tasks"][0]["status"] == "TODO"
        assert result["tasks"][0]["assigned_user"] == "user-1"
        
        # Filtrer tâches DONE non assignées
        result = filter_tasks_combined(status="DONE", user_id="unassigned")
        assert len(result["tasks"]) == 1
        assert result["tasks"][0]["title"] == "Réparer serveur"
        assert result["tasks"][0]["status"] == "DONE"
        assert result["tasks"][0]["assigned_user"] is None

    def test_combine_user_filter_with_search(self):
        """Test combinaison filtre utilisateur + recherche"""
        # Rechercher "réparer" dans les tâches d'Alice
        result = filter_tasks_combined(user_id="user-1", query="réparer", search_in="title")
        assert len(result["tasks"]) == 1
        assert result["tasks"][0]["title"] == "Réparer ordinateur Alice"
        assert result["tasks"][0]["assigned_user"] == "user-1"
        
        # Rechercher "réparer" dans les tâches non assignées
        result = filter_tasks_combined(user_id="unassigned", query="réparer", search_in="title")
        assert len(result["tasks"]) == 1
        assert result["tasks"][0]["title"] == "Réparer serveur"
        assert result["tasks"][0]["assigned_user"] is None

    def test_combine_all_filters(self):
        """Test combinaison de tous les filtres"""
        # Status TODO + User Alice + Search "réparer"
        result = filter_tasks_combined(
            status="TODO", 
            user_id="user-1", 
            query="réparer", 
            search_in="title"
        )
        assert len(result["tasks"]) == 1
        assert result["tasks"][0]["title"] == "Réparer ordinateur Alice"
        assert result["tasks"][0]["status"] == "TODO"
        assert result["tasks"][0]["assigned_user"] == "user-1"
        
        # Recherche qui ne devrait rien retourner
        result = filter_tasks_combined(
            status="DONE", 
            user_id="user-1", 
            query="impossible", 
            search_in="title"
        )
        assert result["tasks"] == []

    def test_combined_filters_with_invalid_user_raises_error(self):
        """Test que les filtres combinés valident l'existence de l'utilisateur"""
        with pytest.raises(ValueError, match="User not found"):
            filter_tasks_combined(status="TODO", user_id="nonexistent")

    def test_combined_filters_with_invalid_status_raises_error(self):
        """Test que les filtres combinés valident le statut"""
        with pytest.raises(ValueError, match="Invalid filter status"):
            filter_tasks_combined(status="INVALID", user_id="user-1")

    def test_combined_filters_with_pagination(self):
        """Test que les filtres combinés supportent la pagination"""
        # Créer plus de tâches TODO pour Alice
        for i in range(15):
            create_task(f"Tâche TODO Alice {i}", f"Description {i}")
            assign_task(task_list[-1]["id"], "user-1")
            update_status(task_list[-1]["id"], "TODO")
        
        # Alice a maintenant 16 tâches TODO (1 + 15)
        result = filter_tasks_combined(status="TODO", user_id="user-1", page=1, size=10)
        assert len(result["tasks"]) == 10
        assert result["total_items"] == 16
        assert result["total_pages"] == 2

class TestTaskDueDate:
    def setup_method(self):
        task_list.clear()
        self.task = add_task("Rendre le rapport", "Important")

    def test_set_valid_due_date(self):
        future_date = (datetime.now() + timedelta(days=5)).isoformat()
        set_task_due_date(self.task["id"], future_date)
        updated_task = get_task_by_id(self.task["id"])
        assert updated_task["due_date"] == future_date

    def test_modify_due_date(self):
        initial_due = (datetime.now() + timedelta(days=2)).isoformat()
        new_due = (datetime.now() + timedelta(days=10)).isoformat()
        set_task_due_date(self.task["id"], initial_due)
        set_task_due_date(self.task["id"], new_due)
        assert get_task_by_id(self.task["id"])["due_date"] == new_due

    def test_remove_due_date(self):
        set_task_due_date(self.task["id"], None)
        assert get_task_by_id(self.task["id"]).get("due_date") is None

    def test_invalid_date_format(self):
        with pytest.raises(ValueError, match="Invalid date format"):
            set_task_due_date(self.task["id"], "32-13-2025")

    def test_past_due_date(self):
        past_date = (datetime.now() - timedelta(days=1)).isoformat()
        set_task_due_date(self.task["id"], past_date)
        assert get_task_by_id(self.task["id"])["due_date"] == past_date

    def test_task_id_not_found(self):
        random_id = str(uuid.uuid4())
        with pytest.raises(ValueError, match="Task not found"):
            set_task_due_date(random_id, datetime.now().isoformat())


class TestTaskOverdue:
    def setup_method(self):
        task_list.clear()  
        self.task = add_task("Tâche test", "Description test")

    def test_todo_or_ongoing_with_past_due_is_overdue(self):
        past = (datetime.now() - timedelta(days=1)).isoformat()
        for status in ["TODO", "ONGOING"]:
            update_status(self.task["id"], status)
            set_task_due_date(self.task["id"], past)
            task = get_task_by_id(self.task["id"])
            assert is_task_overdue(task) is True

    def test_done_with_past_due_not_overdue(self):
        past = (datetime.now() - timedelta(days=1)).isoformat()
        update_status(self.task["id"], "DONE")
        set_task_due_date(self.task["id"], past)
        task = get_task_by_id(self.task["id"])
        assert is_task_overdue(task) is False

    def test_future_due_date_not_overdue(self):
        future = (datetime.now() + timedelta(days=5)).isoformat()
        for status in ["TODO", "ONGOING", "DONE"]:
            update_status(self.task["id"], status)
            set_task_due_date(self.task["id"], future)
            task = get_task_by_id(self.task["id"])
            assert is_task_overdue(task) is False

    def test_no_due_date_not_overdue(self):
        update_status(self.task["id"], "TODO")
        set_task_due_date(self.task["id"], None)
        task = get_task_by_id(self.task["id"])
        assert is_task_overdue(task) is False

    def test_due_today_not_overdue(self):
        today = datetime.now().date().isoformat()
        update_status(self.task["id"], "TODO")
        set_task_due_date(self.task["id"], today)
        task = get_task_by_id(self.task["id"])
        assert is_task_overdue(task) is False

    def test_filter_tasks_combined_returns_only_overdue(self):
        past = (datetime.now() - timedelta(days=1)).isoformat()
        future = (datetime.now() + timedelta(days=1)).isoformat()
        today = datetime.now().date().isoformat()

        task1 = add_task("Tâche 1", "Overdue TODO")
        update_status(task1["id"], "TODO")
        set_task_due_date(task1["id"], past)

        task2 = add_task("Tâche 2", "Overdue ONGOING")
        update_status(task2["id"], "ONGOING")
        set_task_due_date(task2["id"], past)

        task3 = add_task("Tâche 3", "Done passé")
        update_status(task3["id"], "DONE")
        set_task_due_date(task3["id"], past)

        task4 = add_task("Tâche 4", "Future due")
        update_status(task4["id"], "TODO")
        set_task_due_date(task4["id"], future)

        task5 = add_task("Tâche 5", "Due today")
        update_status(task5["id"], "TODO")
        set_task_due_date(task5["id"], today)

        # Appel à filter_tasks_combined avec overdue=True au lieu de filter_tasks_overdue
        result = filter_tasks_combined(overdue=True)
        overdue_tasks = result["tasks"]

        overdue_ids = {t["id"] for t in overdue_tasks}
        assert task1["id"] in overdue_ids
        assert task2["id"] in overdue_ids
        assert task3["id"] not in overdue_ids
        assert task4["id"] not in overdue_ids
        assert task5["id"] not in overdue_ids
