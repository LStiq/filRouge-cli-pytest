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

ALLOWED_PRIORITIES = {"LOW", "NORMAL", "HIGH", "CRITICAL"}
PRIORITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "NORMAL": 2, "LOW": 3}
MAX_TAG_LENGTH = 20

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

def _validate_tag(tag: str) -> str:
    tag = tag.strip()
    if not tag or len(tag) > MAX_TAG_LENGTH:
        raise ValueError("Invalid tag validation")
    return tag

def consult_task(task_id: str) -> Dict:
    try:
        uuid.UUID(task_id)
    except ValueError:
        raise ValueError("Invalid ID format")
    for task in task_list:
        if str(task["id"]) == str(task_id):
            task["overdue"] = is_task_overdue(task)
            return task

    raise ValueError("Task not found")

def update_task(
    task_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    due_date: Optional[str] = None,
    add_tags: Optional[list[str]] = None,
    remove_tags: Optional[list[str]] = None
) -> dict:
    allowed_statuses = {"TODO", "ONGOING", "DONE"}
    allowed_priorities = {"LOW", "NORMAL", "HIGH", "CRITICAL"}

    task = consult_task(task_id)

    changed = False

    # Titre
    if title is not None:
        new_title = _validate_title(title)
        if task["title"] != new_title:
            old_title = task["title"]
            task["title"] = new_title
            add_history_event(task, "title_updated", {"old": old_title, "new": new_title})
            changed = True

    # Description
    if description is not None:
        new_desc = _validate_description(description)
        if task.get("description", "") != new_desc:
            old_desc = task.get("description", "")
            task["description"] = new_desc
            add_history_event(task, "description_updated", {"old": old_desc, "new": new_desc})
            changed = True

    # Statut
    if status is not None:
        if status not in allowed_statuses:
            raise ValueError("Invalid status. Allowed values: TODO, ONGOING, DONE")
        if task.get("status") != status:
            old_status = task.get("status")
            task["status"] = status
            add_history_event(task, "status_updated", {"old": old_status, "new": status})
            changed = True

    # Priorité
    if priority is not None:
        if priority not in allowed_priorities:
            raise ValueError(f"Invalid priority. Allowed values: {', '.join(allowed_priorities)}")
        if task.get("priority") != priority:
            old_priority = task.get("priority")
            task["priority"] = priority
            add_history_event(task, "priority_updated", {"old": old_priority, "new": priority})
            changed = True

    # Date d’échéance
    if due_date is not None:
        old_due_date = task.get("due_date")
        if due_date == "":
            task.pop("due_date", None)
            new_due_date = None
        else:
            try:
                parsed_date = datetime.fromisoformat(due_date)
                new_due_date = parsed_date.isoformat()
                task["due_date"] = new_due_date
            except ValueError:
                raise ValueError("Invalid date format")
        if old_due_date != new_due_date:
            add_history_event(task, "due_date_updated", {"old_due_date": old_due_date, "new_due_date": new_due_date})
            changed = True

    # Ajout de tags
    if add_tags:
        task.setdefault("tags", [])
        for tag in add_tags:
            tag = _validate_tag(tag)
            if tag not in task["tags"]:
                task["tags"].append(tag)
                add_history_event(task, "tag_added", {"tag": tag})
                changed = True

    # Suppression de tags
    if remove_tags:
        for tag in remove_tags:
            tag = _validate_tag(tag)
            if tag in task.get("tags", []):
                task["tags"].remove(tag)
                add_history_event(task, "tag_removed", {"tag": tag})
                changed = True

    if changed:
        _save_tasks(task_list)

    return task

def delete_task(task_id: str):
    """Supprime une tâche par son ID"""
    global task_list
    original_length = len(task_list)
    task_list[:] = [task for task in task_list if str(task["id"]) != str(task_id)]

    if len(task_list) == original_length:
        raise ValueError("Task not found")

    _save_tasks(task_list)

def validate_pagination_params(page: int, size: int) -> None:
    if page <= 0:
        raise ValueError("Invalid page number")
    if size <= 0:
        raise ValueError("Invalid page size")

def paginate(items: List[Dict], page: int, size: int) -> List[Dict]:
    start = (page - 1) * size
    end = start + size
    return items[start:end]


def search_filter_sort_tasks(
    query: Optional[str] = None,
    search_in: str = "both",
    status: Optional[str] = None,
    user_id: Optional[str] = None,
    priority: Optional[str] = None,
    tags: Optional[List[str]] = None,
    overdue: Optional[bool] = None,
    sort_by: str = "created_at",
    ascending: bool = True,
    page: int = 1,
    size: int = 20,
    tasks: Optional[List[Dict]] = None
) -> Dict:
    """Recherche, filtre, trie et retourne une liste paginée de tâches."""

    filtered = task_list
    validate_pagination_params(page, size)

    # -- Statut --
    if status is not None:
        allowed_statuses = {"TODO", "ONGOING", "DONE"}
        if status not in allowed_statuses:
            raise ValueError("Invalid filter status")
        filtered = [t for t in filtered if t.get("status") == status]

    # -- Utilisateur assigné --
    if user_id is not None and user_id != "unassigned":
        if not user_exists(user_id.strip()):
            raise ValueError("User not found")
        filtered = [t for t in filtered if t.get("assigned_user") == user_id]
    elif user_id == "unassigned":
        filtered = [t for t in filtered if not t.get("assigned_user")]

    # -- Priorité --
    if priority is not None:
        if priority not in ALLOWED_PRIORITIES:
            raise ValueError(f"Invalid priority. Allowed values: {', '.join(ALLOWED_PRIORITIES)}")
        filtered = [t for t in filtered if t.get("priority", "NORMAL") == priority]

    # -- Tags --
    if tags:
        tags = [_validate_tag(tag) for tag in tags]
        filtered = [t for t in filtered if set(t.get("tags", [])) & set(tags)]

    # -- Retard --
    if overdue is not None:
        filtered = [t for t in filtered if is_task_overdue(t) == overdue]

    # -- Recherche texte --
    if query and query.strip():
        query = query.lower()
        search_filtered = []
        seen_ids = set()
        for task in filtered:
            title = task.get("title", "").lower()
            description = (task.get("description") or "").lower()
            match = (
                (search_in == "title" and query in title) or
                (search_in == "description" and query in description) or
                (search_in == "both" and (query in title or query in description)) or
                (search_in not in {"title", "description", "both"} and (query in title and query in description))
            )
            if match and task["id"] not in seen_ids:
                search_filtered.append(task)
                seen_ids.add(task["id"])
        filtered = search_filtered

    # -- Tri --
    if tasks is None:
        tasks = task_list

    allowed_fields = {"id", "title", "status", "created_at", "priority","custom"}
    if sort_by not in allowed_fields:
        raise ValueError("Invalid sort criteria")

    def parse_date_safe(date_str):
        try:
            return datetime.fromisoformat(date_str)
        except Exception:
            return datetime.min

    def sort_key(task):
        if sort_by == "created_at":
            return parse_date_safe(task.get("created_at", ""))
        elif sort_by == "title":
            return task.get("title", "").lower()
        elif sort_by == "status":
            return {"TODO": 0, "ONGOING": 1, "DONE": 2}.get(task.get("status"), 99)
        elif sort_by == "priority":
            return {"CRITICAL": 0, "HIGH": 1, "NORMAL": 2, "LOW": 3}.get(task.get("priority", "NORMAL"), 99)
        else:
            return task.get(sort_by)

    filtered = sorted(filtered, key=sort_key, reverse=not ascending)

    # -- Pagination --
    items = paginate(filtered, page, size)
    total_items = len(filtered)
    total_pages = (total_items + size - 1) // size

    for task in items:
        task["overdue"] = is_task_overdue(task)

    return {
        "tasks": items,
        "page": page,
        "page_size": size,
        "total_items": total_items,
        "total_pages": total_pages
    }

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

def assign_user(task_id: str, user_id: str | None) -> None:
    task = consult_task(task_id)
    old_user = task.get("assigned_user")
    if old_user != user_id:
        task["assigned_user"] = user_id
        action = "assigned" if user_id else "unassigned"
        add_history_event(task, f"user_{action}", {"user_id": user_id})


def add_task(title: str, description: str = "", due_date: Optional[str] = None, priority: str = "NORMAL") -> Dict:
    """Crée une tâche avec titre, description, priorité et date d’échéance facultative."""

    validated_title = _validate_title(title)
    validated_description = _validate_description(description)

    ALLOWED_PRIORITIES = {"LOW", "NORMAL", "HIGH", "CRITICAL"}
    if priority not in ALLOWED_PRIORITIES:
        raise ValueError(f"Invalid priority. Allowed values: {', '.join(ALLOWED_PRIORITIES)}")

    task = {
        "id": str(uuid.uuid4()),
        "title": validated_title,
        "description": validated_description,
        "status": "TODO",
        "created_at": datetime.now().isoformat(),
        "priority": priority,
        "history": [],
        "assigned_user": None  # <- si tu veux garder la compatibilité avec l’ancienne `create_task`
    }

    if due_date:
        try:
            parsed_date = datetime.fromisoformat(due_date)
            task["due_date"] = parsed_date.isoformat()
        except ValueError:
            raise ValueError("Invalid date format")

    task["history"].append({
        "event": "creation",
        "timestamp": datetime.now().isoformat(),
        "details": {
            "title": validated_title,
            "description": validated_description,
            "priority": priority,
            "due_date": task.get("due_date")
        }
    })

    task_list.append(task)
    _save_tasks(task_list)
    return task

def is_task_overdue(task):
    if task.get("due_date") and task["status"] in {"TODO", "ONGOING"}:
        due = datetime.fromisoformat(task["due_date"])
        return due.date() < datetime.now(timezone.utc).date()
    return False

def get_all_tags() -> dict:
    """Retourne un dict {tag: count} de tous les tags utilisés dans toutes les tâches."""
    tag_counts = {}
    for task in task_list:
        for tag in task.get("tags", []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    return tag_counts

def add_history_event(task: dict, event_type: str, details: dict) -> None:
    if "history" not in task:
        task["history"] = []
    event = {
        "timestamp": datetime.now().isoformat(),
        "event": event_type,
        "details": details
    }
    task["history"].append(event)

def get_task_history(task_id: str, page: int = 1, size: int = 10) -> dict:
    task = consult_task(task_id)
    history = task.get("history", [])
    history_sorted = sorted(history, key=lambda e: e["timestamp"], reverse=True)
    total_items = len(history_sorted)
    total_pages = (total_items + size - 1) // size
    start = (page - 1) * size
    end = start + size
    page_items = history_sorted[start:end]
    return {
        "history": page_items,
        "page": page,
        "page_size": size,
        "total_items": total_items,
        "total_pages": total_pages
    }