# task_manager.py - Logique métier du gestionnaire de tâches

import json
import os
import re
from typing import List, Dict, Optional
from datetime import datetime, timezone
import uuid
DATA_FILE = "tasks.json"
USER_FILE = "users.json"

## Default data until task creation is ok
## TODO: remove
DEFAULT_TASKS = [
    {
        "id": 1,
        "title": "Première tâche",
        "description": "Description de la première tâche",
        "status": "TODO"
    },
    {
        "id": 2,
        "title": "Deuxième tâche",
        "description": "Description de la deuxième tâche",
        "status": "DONE"
    }
]

# Default users for development
DEFAULT_USERS = [
    {"id": "user-1", "name": "Alice Martin", "email": "alice@example.com"},
    {"id": "user-2", "name": "Bob Dupont", "email": "bob@example.com"},
    {"id": "user-3", "name": "Charlie Brown", "email": "charlie@example.com"}
]

EMAIL_REGEX = r"^[\w\.-]+@[\w\.-]+\.\w+$"

def _load_tasks():
    """Charge les tâches depuis le fichier JSON"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            _save_tasks(DEFAULT_TASKS)
            return DEFAULT_TASKS.copy()
    else:
        _save_tasks(DEFAULT_TASKS)
        return DEFAULT_TASKS.copy()

def _save_tasks(tasks_to_save):
    """Sauvegarde les tâches dans le fichier JSON"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(tasks_to_save, f, ensure_ascii=False, indent=2)
    except IOError:
        pass

task_list = _load_tasks()

def _load_users():
    """Charge les utilisateurs depuis le fichier JSON"""
    if os.path.exists(USER_FILE):
        try:
            with open(USER_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            _save_users(DEFAULT_USERS)
            return DEFAULT_USERS.copy()
    else:
        _save_users(DEFAULT_USERS)
        return DEFAULT_USERS.copy()

def _save_users(users_to_save):
    """Sauvegarde les utilisateurs dans le fichier JSON"""
    try:
        with open(USER_FILE, 'w', encoding='utf-8') as f:
            json.dump(users_to_save, f, ensure_ascii=False, indent=2)
    except IOError:
        pass

user_list = _load_users()

def _validate_title(title: str):
    if not title or not title.strip():
        raise ValueError("Title is required")
    if len(title.strip()) > 100:
        raise ValueError("Title cannot exceed 100 characters")
    return title.strip()

def _validate_description(description: str):
    if description is not None and len(description.strip()) > 500:
        raise ValueError("Description cannot exceed 500 characters")
    return description.strip() if description else ""


def create_task(title: str, description: str = "") -> Dict:
    """Crée une nouvelle tâche et l'ajoute à la liste"""
    validated_title = _validate_title(title)
    validated_description = _validate_description(description)
        
    task = {
        "id": str(uuid.uuid4()),
        "title": validated_title,
        "description": validated_description,
        "status": "TODO",
        "created_at": datetime.now().isoformat(timespec='seconds'),
        "assigned_user": None
    }
    task_list.append(task)
    _save_tasks(task_list)
    return task

def consult_task(task_id: str) -> Dict:
    """Consulte une tâche par son ID"""
    try:
        uuid.UUID(str(task_id))
    except ValueError:
        raise ValueError("Invalid ID format")

    for task in task_list:
        if str(task["id"]) == str(task_id):
            return task

    raise ValueError("Task not found")

def update_task(task_id, title=None, description=None):
    for task in task_list:
        if str(task["id"]) == str(task_id):
            if title is not None:
                task["title"] = _validate_title(title)

            if description is not None:
                task["description"] = _validate_description(description)

            _save_tasks(task_list)
            return task

    raise ValueError("Task not found")

def update_status(task_id: str, status: str) -> Dict:
    """Met à jour le statut d'une tâche"""
    allowed_statuses = {"TODO", "ONGOING", "DONE"}

    if status not in allowed_statuses:
        raise ValueError("Invalid status. Allowed values: TODO, ONGOING, DONE")

    for task in task_list:
        if task["id"] == task_id:
            task["status"] = status
            _save_tasks(task_list)
            return task

    raise ValueError("Task not found")

def delete_task(task_id: str):
    """Supprime une tâche par son ID"""
    global task_list
    original_length = len(task_list)
    task_list[:] = [task for task in task_list if str(task["id"]) != str(task_id)]

    if len(task_list) == original_length:
        raise ValueError("Task not found")

    _save_tasks(task_list)

def get_tasks_paginated(page: int = 1, size: int = 20) -> Dict:
    """Retourne une page de tâches avec infos de pagination"""
    if size <= 0:
        raise ValueError("Invalid page size")
    if page <= 0:
        raise ValueError("Invalid page number")

    total_items = len(task_list)
    total_pages = (total_items + size - 1) // size

    start = (page - 1) * size
    end = start + size
    items = task_list[start:end]

    return {
        "tasks": items,
        "page": page,
        "page_size": size,
        "total_items": total_items,
        "total_pages": total_pages
    }

def paginate(items: List[Dict], page: int, size: int) -> List[Dict]:
    if page <= 0 or size <= 0:
        raise ValueError("Invalid pagination parameters")
    start = (page - 1) * size
    end = start + size
    return items[start:end]

def search_tasks(query: str, page: int = 1, size: int = 20, search_in: str = "") -> Dict:
    """
    Recherche des tâches par titre, description ou les deux.
    search_in : "title", "description", "both" (par défaut)
    """
    if query == "":
        filtered = task_list
    else:
        query = query.lower()
        seen_ids = set()
        filtered = []

        for task in task_list:
            title = task.get("title", "").lower()
            description = (task.get("description") or "").lower()

            match = False
            if search_in == "title":
                match = query in title
            elif search_in == "description":
                match = query in description
            elif search_in == "both":
                match = query in title or query in description
            else:
                match = query in title and query in description

            if match and task["id"] not in seen_ids:
                filtered.append(task)
                seen_ids.add(task["id"])

    total_items = len(filtered)
    total_pages = (total_items + size - 1) // size
    items = paginate(filtered, page, size)

    return {
        "tasks": items,
        "page": page,
        "page_size": size,
        "total_items": total_items,
        "total_pages": total_pages
    }

def filter_tasks_by_status(status: str, page: int = 1, size: int = 20) -> Dict:
    allowed_statuses = {"TODO", "ONGOING", "DONE"}
    if status not in allowed_statuses:
        raise ValueError("Invalid filter status")

    filtered = [task for task in task_list if task.get("status") == status]

    total_items = len(filtered)
    total_pages = (total_items + size - 1) // size
    items = paginate(filtered, page, size)

    return {
        "tasks": items,
        "page": page,
        "page_size": size,
        "total_items": total_items,
        "total_pages": total_pages
    }

def sort_tasks(by: str = "created_at", ascending: bool = True, tasks: Optional[List[Dict]] = None) -> List[Dict]:
    if tasks is None:
        tasks = task_list

    allowed_fields = {"id", "title", "status", "created_at"}
    if by not in allowed_fields:
        raise ValueError("Invalid sort criteria")

    def parse_date_safe(date_str):
        try:
            return datetime.fromisoformat(date_str)
        except Exception:
            return datetime.min

    def sort_key(task):
        if by == "created_at":
            date_str = task.get("created_at", "")
            return parse_date_safe(date_str)
        elif by == "title":
            return task.get("title", "").lower()
        elif by == "status":
            order = {"TODO": 0, "ONGOING": 1, "DONE": 2}
            return order.get(task.get("status"), 99)
        else:
            return task.get(by)

    return sorted(tasks, key=sort_key, reverse=not ascending)

def create_user(name: str, email: str) -> dict:
    name = name.strip()
    email = email.strip().lower()

    if not name:
        raise ValueError("Name is required")
    if len(name) > 50:
        raise ValueError("Name cannot exceed 50 characters")
    if not re.match(EMAIL_REGEX, email):
        raise ValueError("Invalid email format")
    if any(u["email"] == email for u in user_list):
        raise ValueError("Email already in use")

    user = {
        "id": str(uuid.uuid4()),
        "name": name,
        "email": email,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    user_list.append(user)
    _save_users(user_list)
    return user

def list_users(page: int = 1, size: int = 20) -> dict:
    sorted_users = sorted(user_list, key=lambda u: u["name"].lower())
    total_items = len(sorted_users)
    total_pages = (total_items + size - 1) // size

    start = (page - 1) * size
    end = start + size
    paginated = sorted_users[start:end]

    return {
        "users": paginated,
        "total_items": total_items,
        "total_pages": total_pages,
        "current_page": page,
    }

def get_tasks() -> List[Dict]:
    """Récupère la liste des tâches"""
    return task_list

def get_users() -> List[Dict]:
    """Récupère la liste des utilisateurs"""
    return user_list

def get_user_by_id(user_id: str) -> Optional[Dict]:
    """Récupère un utilisateur par son ID"""
    users = _load_users()
    for user in users:
        if str(user["id"]) == str(user_id):
            return user
    return None

def user_exists(user_id: str) -> bool:
    """Vérifie si un utilisateur existe"""
    return get_user_by_id(user_id) is not None

def assign_task(task_id: str, user_id: Optional[str] = None) -> Dict:
    """Assigne une tâche à un utilisateur ou la désassigne"""
    task = None
    for t in task_list:
        if str(t["id"]) == str(task_id):
            task = t
            break
    
    if not task:
        raise ValueError("Task not found")
    
    if user_id is not None and user_id.strip():
        if not user_exists(user_id.strip()):
            raise ValueError("User not found")
        task["assigned_user"] = str(user_id).strip()
    else:
        task["assigned_user"] = None
    
    _save_tasks(task_list)
    return task

def get_tasks_assigned_to_user(user_id: str) -> List[Dict]:
    """Récupère toutes les tâches assignées à un utilisateur"""
    return [task for task in task_list if task.get("assigned_user") == user_id]

def get_unassigned_tasks() -> List[Dict]:
    """Récupère toutes les tâches non assignées"""
    return [task for task in task_list if not task.get("assigned_user")]

def set_task_due_date(task_id: str, due_date: Optional[str]) -> Dict:
    task = get_task_by_id(task_id)

    if due_date is None:
        task.pop("due_date", None)
    else:
        try:
            parsed_date = datetime.fromisoformat(due_date)
        except ValueError:
            raise ValueError("Invalid date format")
        task["due_date"] = parsed_date.isoformat()

    _save_tasks(task_list)
    return task


def add_task(title: str, description: str = "", due_date: Optional[str] = None) -> Dict:
    """Ajoute une tâche avec option de date d’échéance (alternative à create_task)"""
    validated_title = _validate_title(title)
    validated_description = _validate_description(description)

    task = {
        "id": str(uuid.uuid4()),
        "title": validated_title,
        "description": validated_description,
        "status": "TODO",
        "created_at": datetime.now().isoformat()
    }

    if due_date:
        try:
            parsed_date = datetime.fromisoformat(due_date)
        except ValueError:
            raise ValueError("Invalid date format")
        task["due_date"] = parsed_date.isoformat()

    task_list.append(task)
    _save_tasks(task_list)
    return task

def get_task_by_id(task_id: str) -> Dict:
    try:
        uuid.UUID(task_id)
    except ValueError:
        raise ValueError("Invalid ID format")

    for task in task_list:
        if str(task["id"]) == task_id:
            return task

    raise ValueError("Task not found")

def filter_tasks_by_user(user_id: Optional[str] = None, page: int = 1, size: int = 20) -> Dict:
    """Filtre les tâches par utilisateur assigné"""
    if user_id is not None and user_id != "unassigned":
        if not user_exists(user_id.strip()):
            raise ValueError("User not found")
        
        filtered = [task for task in task_list if task.get("assigned_user") == user_id]
    elif user_id == "unassigned":
        filtered = [task for task in task_list if not task.get("assigned_user")]
    else:
        filtered = task_list

    total_items = len(filtered)
    total_pages = (total_items + size - 1) // size
    items = paginate(filtered, page, size)

    return {
        "tasks": items,
        "page": page,
        "page_size": size,
        "total_items": total_items,
        "total_pages": total_pages
    }

def filter_tasks_combined(status: Optional[str] = None, user_id: Optional[str] = None, 
                         query: Optional[str] = None, search_in: str = "both",
                         page: int = 1, size: int = 20) -> Dict:
    """Filtre les tâches avec plusieurs critères combinés"""
    filtered = task_list

    # Filtre par statut
    if status is not None:
        allowed_statuses = {"TODO", "ONGOING", "DONE"}
        if status not in allowed_statuses:
            raise ValueError("Invalid filter status")
        filtered = [task for task in filtered if task.get("status") == status]

    # Filtre par utilisateur
    if user_id is not None and user_id != "unassigned":
        if not user_exists(user_id):
            raise ValueError("User not found")
        filtered = [task for task in filtered if task.get("assigned_user") == user_id]
    elif user_id == "unassigned":
        filtered = [task for task in filtered if not task.get("assigned_user")]

    # Filtre par recherche
    if query and query.strip():
        query = query.lower()
        search_filtered = []
        seen_ids = set()

        for task in filtered:
            title = task.get("title", "").lower()
            description = (task.get("description") or "").lower()

            match = False
            if search_in == "title":
                match = query in title
            elif search_in == "description":
                match = query in description
            elif search_in == "both":
                match = query in title or query in description
            else:
                match = query in title and query in description

            if match and task["id"] not in seen_ids:
                search_filtered.append(task)
                seen_ids.add(task["id"])

        filtered = search_filtered

    total_items = len(filtered)
    total_pages = (total_items + size - 1) // size
    items = paginate(filtered, page, size)

    return {
        "tasks": items,
        "page": page,
        "page_size": size,
        "total_items": total_items,
        "total_pages": total_pages
    }