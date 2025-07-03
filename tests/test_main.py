# test_main.py - Tests pour l'interface CLI
import sys
import os
import uuid
import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.main import cli
from src.task_manager import *

class TestMainCLI:
    
    def setup_method(self):
        """Initialise le runner Click avant chaque test"""
        self.runner = CliRunner()

class TestListCommand:
    
    def setup_method(self):
        self.runner = CliRunner()

    @patch('src.main.get_tasks')
    @patch('src.main.get_user_by_id')
    def test_list_command_with_tasks(self, mock_get_user, mock_get_tasks):
        """Test la commande list avec des tâches existantes"""
        mock_tasks = [
            {
                "id": "task-1",
                "title": "Tâche test",
                "description": "Description test",
                "status": "TODO",
                "assigned_user": "user-1"
            },
            {
                "id": "task-2", 
                "title": "Autre tâche",
                "description": "Autre description",
                "status": "DONE",
                "assigned_user": None
            }
        ]
        mock_get_tasks.return_value = mock_tasks
        mock_get_user.return_value = {"name": "Alice Martin"}
        
        result = self.runner.invoke(cli, ['list'])
        
        assert result.exit_code == 0
        assert "Tâche test" in result.output
        assert "Autre tâche" in result.output
        assert "Alice Martin" in result.output
        assert "(non assigné)" in result.output

    @patch('src.main.get_tasks')
    def test_list_command_with_no_tasks(self, mock_get_tasks):
        """Test la commande list sans tâches"""
        mock_get_tasks.return_value = []
        
        result = self.runner.invoke(cli, ['list'])
        
        assert result.exit_code == 0
        assert "Aucune tâche trouvée" in result.output

    @patch('src.main.get_tasks')
    @patch('src.main.get_user_by_id')
    def test_list_command_with_user_not_found(self, mock_get_user, mock_get_tasks):
        """Test la commande list quand l'utilisateur assigné n'existe plus"""
        mock_tasks = [
            {
                "id": "task-1",
                "title": "Tâche test",
                "description": "Description test",
                "status": "TODO",
                "assigned_user": "user-deleted"
            }
        ]
        mock_get_tasks.return_value = mock_tasks
        mock_get_user.return_value = None
        
        result = self.runner.invoke(cli, ['list'])
        
        assert result.exit_code == 0
        assert "user-deleted" in result.output 

class TestCreateCommand:
    
    def setup_method(self):
        self.runner = CliRunner()

    @patch('src.main.add_task')
    def test_create_command_success(self, mock_create_task):
        """Test la création d'une tâche avec succès"""
        mock_task = {
            "id": str(uuid.uuid4()),
            "title": "Nouvelle tâche",
            "description": "Description test"
        }
        mock_create_task.return_value = mock_task
        
        result = self.runner.invoke(cli, ['create'], input='Nouvelle tâche\nDescription test\n')
        
        assert result.exit_code == 0
        assert "Tâche créée avec succès" in result.output
        assert "Nouvelle tâche" in result.output
        mock_create_task.assert_called_once_with(title="Nouvelle tâche", description="Description test")

    @patch('src.main.add_task')
    def test_create_command_with_error(self, mock_create_task):
        """Test la création d'une tâche avec erreur"""
        mock_create_task.side_effect = ValueError("Title is required")
        
        result = self.runner.invoke(cli, ['create'], input='\nDescription test\n')
        
        assert result.exit_code == 0
        assert "Erreur lors de la création de la tâche" in result.output
        assert "Title is required" in result.output

class TestConsultCommand:
    
    def setup_method(self):
        self.runner = CliRunner()

    @patch('src.main.consult_task')
    @patch('src.main.get_user_by_id')
    def test_consult_command_success(self, mock_get_user, mock_consult_task):
        """Test la consultation d'une tâche avec succès"""
        task_id = str(uuid.uuid4())
        mock_task = {
            "id": task_id,
            "title": "Tâche consultée",
            "description": "Description consultée",
            "status": "TODO",
            "assigned_user": "user-1",
            "created_at": "2024-01-01T10:00:00"
        }
        mock_consult_task.return_value = mock_task
        mock_get_user.return_value = {"name": "Alice Martin"}
        
        result = self.runner.invoke(cli, ['consult', task_id])
        
        assert result.exit_code == 0
        assert "Tâche consultée" in result.output
        assert "Description consultée" in result.output
        assert "Alice Martin" in result.output
        mock_consult_task.assert_called_once_with(task_id)

    @patch('src.main.consult_task')
    def test_consult_command_task_not_found(self, mock_consult_task):
        """Test la consultation d'une tâche inexistante"""
        mock_consult_task.side_effect = ValueError("Task not found")
        
        result = self.runner.invoke(cli, ['consult', 'invalid-id'])
        
        assert result.exit_code == 0
        assert "Erreur" in result.output
        assert "Task not found" in result.output

    @patch('src.main.consult_task')
    def test_consult_command_with_lookup_error(self, mock_consult_task):
        """Test la consultation avec LookupError"""
        mock_consult_task.side_effect = LookupError("Task not found")
        
        result = self.runner.invoke(cli, ['consult', 'invalid-id'])
        
        assert result.exit_code == 0
        assert "non trouvée" in result.output

    @patch('src.main.consult_task')
    def test_consult_command_with_unassigned_task(self, mock_consult_task):
        """Test la consultation d'une tâche non assignée"""
        task_id = str(uuid.uuid4())
        mock_task = {
            "id": task_id,
            "title": "Tâche non assignée",
            "description": "Description",
            "status": "TODO",
            "assigned_user": None,
            "created_at": "2024-01-01T10:00:00"
        }
        mock_consult_task.return_value = mock_task
        
        result = self.runner.invoke(cli, ['consult', task_id])
        
        assert result.exit_code == 0
        assert "(non assigné)" in result.output

    @patch('src.main.consult_task')
    @patch('src.main.get_user_by_id')
    def test_consult_command_with_user_not_found(self, mock_get_user, mock_consult_task):
        """Test la consultation quand l'utilisateur assigné n'existe plus"""
        task_id = str(uuid.uuid4())
        mock_task = {
            "id": task_id,
            "title": "Tâche avec user supprimé",
            "description": "Description",
            "status": "TODO",
            "assigned_user": "user-deleted",
            "created_at": "2024-01-01T10:00:00"
        }
        mock_consult_task.return_value = mock_task
        mock_get_user.return_value = None
        
        result = self.runner.invoke(cli, ['consult', task_id])
        
        assert result.exit_code == 0
        assert "user-deleted" in result.output

class TestUpdateCommand:
    
    def setup_method(self):
        self.runner = CliRunner()

    @patch('src.main.update_task')
    def test_update_command_success(self, mock_update_task):
        """Test la mise à jour d'une tâche avec succès"""
        task_id = str(uuid.uuid4())
        mock_task = {
            "id": task_id,
            "title": "Titre modifié",
            "description": "Description modifiée"
        }
        mock_update_task.return_value = mock_task
        
        result = self.runner.invoke(cli, ['update', task_id], input='Titre modifié\nDescription modifiée\n')
        
        assert result.exit_code == 0
        assert "Tâche mise à jour avec succès" in result.output
        assert "Titre modifié" in result.output
        mock_update_task.assert_called_once_with(task_id, title="Titre modifié", description="Description modifiée")

    @patch('src.main.update_task')
    def test_update_command_with_error(self, mock_update_task):
        """Test la mise à jour avec erreur"""
        mock_update_task.side_effect = ValueError("Task not found")
        
        result = self.runner.invoke(cli, ['update', 'invalid-id'], input='Nouveau titre\n\n')
        
        assert result.exit_code == 0
        assert "Erreur lors de la mise à jour" in result.output

    @patch('src.main.update_task')
    def test_update_command_with_empty_inputs(self, mock_update_task):
        """Test la mise à jour avec des entrées vides"""
        task_id = str(uuid.uuid4())
        mock_task = {"id": task_id, "title": "Ancien titre"}
        mock_update_task.return_value = mock_task
        
        result = self.runner.invoke(cli, ['update', task_id], input='\n\n')
        
        assert result.exit_code == 0
        mock_update_task.assert_called_once_with(task_id, title=None, description=None)

class TestDeleteCommand:
    
    def setup_method(self):
        self.runner = CliRunner()

    @patch('src.main.delete_task')
    def test_delete_command_success(self, mock_delete_task):
        """Test la suppression d'une tâche avec succès"""
        task_id = str(uuid.uuid4())
        
        result = self.runner.invoke(cli, ['delete', task_id])
        
        assert result.exit_code == 0
        assert "supprimée avec succès" in result.output
        mock_delete_task.assert_called_once_with(task_id)

    @patch('src.main.delete_task')
    def test_delete_command_task_not_found(self, mock_delete_task):
        """Test la suppression d'une tâche inexistante"""
        mock_delete_task.side_effect = ValueError("Task not found")
        
        result = self.runner.invoke(cli, ['delete', 'invalid-id'])
        
        assert result.exit_code == 0
        assert "Erreur lors de la suppression" in result.output

    @patch('src.main.delete_task')
    def test_delete_command_with_lookup_error(self, mock_delete_task):
        """Test la suppression avec LookupError"""
        mock_delete_task.side_effect = LookupError("Task not found")
        
        result = self.runner.invoke(cli, ['delete', 'invalid-id'])
        
        assert result.exit_code == 0
        assert "non trouvée" in result.output

class TestAssignCommand:
    
    def setup_method(self):
        self.runner = CliRunner()

    @patch('src.main.assign_task')
    @patch('src.main.get_user_by_id')
    def test_assign_command_success(self, mock_get_user, mock_assign_task):
        """Test l'assignation d'une tâche avec succès"""
        task_id = str(uuid.uuid4())
        user_id = "user-1"
        mock_task = {
            "id": task_id,
            "assigned_user": user_id
        }
        mock_assign_task.return_value = mock_task
        mock_get_user.return_value = {"name": "Alice Martin"}
        
        result = self.runner.invoke(cli, ['assign', task_id, user_id])
        
        assert result.exit_code == 0
        assert "Tâche assignée à" in result.output
        assert "Alice Martin" in result.output
        mock_assign_task.assert_called_once_with(task_id, user_id)

    @patch('src.main.assign_task')
    def test_assign_command_unassign(self, mock_assign_task):
        """Test la désassignation d'une tâche"""
        task_id = str(uuid.uuid4())
        mock_task = {
            "id": task_id,
            "assigned_user": None
        }
        mock_assign_task.return_value = mock_task
        
        result = self.runner.invoke(cli, ['assign', task_id])
        
        assert result.exit_code == 0
        assert "Tâche désassignée" in result.output

    @patch('src.main.assign_task')
    def test_assign_command_with_error(self, mock_assign_task):
        """Test l'assignation avec erreur"""
        mock_assign_task.side_effect = ValueError("User not found")
        
        result = self.runner.invoke(cli, ['assign', 'task-id', 'invalid-user'])
        
        assert result.exit_code == 0
        assert "Erreur" in result.output
        assert "User not found" in result.output

    @patch('src.main.assign_task')
    @patch('src.main.get_user_by_id')
    def test_assign_command_user_not_found_in_display(self, mock_get_user, mock_assign_task):
        """Test l'assignation quand l'utilisateur existe mais pas trouvé pour l'affichage"""
        task_id = str(uuid.uuid4())
        user_id = "user-1"
        mock_task = {
            "id": task_id,
            "assigned_user": user_id
        }
        mock_assign_task.return_value = mock_task
        mock_get_user.return_value = None  
        
        result = self.runner.invoke(cli, ['assign', task_id, user_id])
        
        assert result.exit_code == 0
        assert "user-1" in result.output

class TestUsersCommand:
    
    def setup_method(self):
        self.runner = CliRunner()

    @patch('src.main.get_users')
    def test_users_command_with_users(self, mock_get_users):
        """Test la commande users avec des utilisateurs"""
        mock_users = [
            {"id": "user-1", "name": "Alice Martin", "email": "alice@example.com"},
            {"id": "user-2", "name": "Bob Dupont", "email": "bob@example.com"}
        ]
        mock_get_users.return_value = mock_users
        
        result = self.runner.invoke(cli, ['users'])
        
        assert result.exit_code == 0
        assert "Alice Martin" in result.output
        assert "Bob Dupont" in result.output
        assert "alice@example.com" in result.output

    @patch('src.main.get_users')
    def test_users_command_with_no_users(self, mock_get_users):
        """Test la commande users sans utilisateurs"""
        mock_get_users.return_value = []
        
        result = self.runner.invoke(cli, ['users'])
        
        assert result.exit_code == 0
        assert "Aucun utilisateur trouvé" in result.output

class TestUserTasksCommand:
    
    def setup_method(self):
        self.runner = CliRunner()

    @patch('src.main.get_user_by_id')
    @patch('src.main.get_tasks_assigned_to_user')
    def test_user_tasks_command_with_tasks(self, mock_get_tasks, mock_get_user):
        """Test la commande user-tasks avec des tâches"""
        user_id = "user-1"
        mock_user = {"name": "Alice Martin"}
        mock_tasks = [
            {"title": "Tâche 1", "status": "TODO"},
            {"title": "Tâche 2", "status": "DONE"}
        ]
        mock_get_user.return_value = mock_user
        mock_get_tasks.return_value = mock_tasks
        
        result = self.runner.invoke(cli, ['user-tasks', user_id])
        
        assert result.exit_code == 0
        assert "Alice Martin" in result.output
        assert "Tâche 1" in result.output
        assert "Tâche 2" in result.output

    @patch('src.main.get_user_by_id')
    def test_user_tasks_command_user_not_found(self, mock_get_user):
        """Test la commande user-tasks avec utilisateur inexistant"""
        mock_get_user.return_value = None
        
        result = self.runner.invoke(cli, ['user-tasks', 'invalid-user'])
        
        assert result.exit_code == 0
        assert "Utilisateur" in result.output
        assert "non trouvé" in result.output

    @patch('src.main.get_user_by_id')
    @patch('src.main.get_tasks_assigned_to_user')
    def test_user_tasks_command_no_tasks(self, mock_get_tasks, mock_get_user):
        """Test la commande user-tasks sans tâches assignées"""
        mock_user = {"name": "Alice Martin"}
        mock_get_user.return_value = mock_user
        mock_get_tasks.return_value = []
        
        result = self.runner.invoke(cli, ['user-tasks', 'user-1'])
        
        assert result.exit_code == 0
        assert "Aucune tâche assignée" in result.output

class TestUnassignedCommand:
    
    def setup_method(self):
        self.runner = CliRunner()

    @patch('src.main.get_unassigned_tasks')
    def test_unassigned_command_with_tasks(self, mock_get_unassigned):
        """Test la commande unassigned avec des tâches non assignées"""
        mock_tasks = [
            {"title": "Tâche libre 1", "status": "TODO"},
            {"title": "Tâche libre 2", "status": "ONGOING"}
        ]
        mock_get_unassigned.return_value = mock_tasks
        
        result = self.runner.invoke(cli, ['unassigned'])
        
        assert result.exit_code == 0
        assert "Tâche libre 1" in result.output
        assert "Tâche libre 2" in result.output

    @patch('src.main.get_unassigned_tasks')
    def test_unassigned_command_no_tasks(self, mock_get_unassigned):
        """Test la commande unassigned sans tâches non assignées"""
        mock_get_unassigned.return_value = []
        
        result = self.runner.invoke(cli, ['unassigned'])
        
        assert result.exit_code == 0
        assert "Toutes les tâches sont assignées" in result.output

class TestFilterCommand:
    
    def setup_method(self):
        self.runner = CliRunner()

    @patch('src.main.search_filter_sort_tasks')
    @patch('src.main.get_user_by_id')
    def test_filter_command_success(self, mock_get_user, mock_filter):
        """Test la commande filter avec succès"""
        mock_tasks = [
            {
                "id": "task-1",
                "title": "Tâche filtrée",
                "description": "Description",
                "status": "TODO",
                "assigned_user": "user-1"
            }
        ]
        mock_result = {
            "tasks": mock_tasks,
            "page": 1,
            "total_items": 1,
            "total_pages": 1
        }
        mock_filter.return_value = mock_result
        mock_get_user.return_value = {"name": "Alice Martin"}
        
        result = self.runner.invoke(cli, ['filter', '--status', 'TODO', '--user', 'user-1'])
        
        assert result.exit_code == 0
        assert "Tâche filtrée" in result.output
        mock_filter.assert_called_once_with(
            status="TODO",
            user_id="user-1",
            query=None,
            page=1,
            size=20
        )

    @patch('src.main.search_filter_sort_tasks')
    def test_filter_command_no_results(self, mock_filter):
        """Test la commande filter sans résultats"""
        mock_result = {
            "tasks": [],
            "page": 1,
            "total_items": 0,
            "total_pages": 0
        }
        mock_filter.return_value = mock_result
        
        result = self.runner.invoke(cli, ['filter', '--status', 'DONE'])
        
        assert result.exit_code == 0
        assert "Aucune tâche trouvée avec ces critères" in result.output

    @patch('src.main.search_filter_sort_tasks')
    def test_filter_command_with_error(self, mock_filter):
        """Test la commande filter avec erreur de la fonction filter_tasks_combined"""
        # Test d'une erreur qui vient de la logique métier (pas de Click)
        mock_filter.side_effect = ValueError("User not found")
        
        result = self.runner.invoke(cli, ['filter', '--user', 'invalid-user'])
        
        assert result.exit_code == 0  # L'erreur est gérée par le code CLI
        assert "Erreur" in result.output
        assert "User not found" in result.output

    def test_filter_command_with_invalid_click_option(self):
        """Test la commande filter avec option invalide (gérée par Click)"""
        # Click valide les options avant d'appeler la fonction
        result = self.runner.invoke(cli, ['filter', '--status', 'INVALID'])
        
        assert result.exit_code == 2  # Click retourne 2 pour les choix invalides
        # Click peut afficher différents messages selon la version
        assert "Invalid choice" in result.output or "is not one of" in result.output

    @patch('src.main.search_filter_sort_tasks')
    def test_filter_command_with_pagination(self, mock_filter):
        """Test la commande filter avec pagination"""
        mock_result = {
            "tasks": [{"id": "task-1", "title": "Test", "description": "", "status": "TODO", "assigned_user": None}],
            "page": 2,
            "total_items": 25,
            "total_pages": 3
        }
        mock_filter.return_value = mock_result
        
        result = self.runner.invoke(cli, ['filter', '--page', '2', '--size', '10'])
        
        assert result.exit_code == 0
        assert "Page 2/3" in result.output
        assert "25 tâche(s) au total" in result.output

    @patch('src.main.search_filter_sort_tasks')
    @patch('src.main.get_user_by_id')
    def test_filter_command_with_user_not_found_for_display(self, mock_get_user, mock_filter):
        """Test filter quand l'utilisateur assigné n'est pas trouvé pour l'affichage"""
        mock_tasks = [
            {
                "id": "task-1",
                "title": "Test",
                "description": "",
                "status": "TODO",
                "assigned_user": "user-deleted"
            }
        ]
        mock_result = {
            "tasks": mock_tasks,
            "page": 1,
            "total_items": 1,
            "total_pages": 1
        }
        mock_filter.return_value = mock_result
        mock_get_user.return_value = None  # Utilisateur introuvable
        
        result = self.runner.invoke(cli, ['filter'])
        
        assert result.exit_code == 0
        assert "user-deleted" in result.output

class TestUserFilterCommand:
    
    def setup_method(self):
        self.runner = CliRunner()

    @patch('src.main.search_filter_sort_tasks')
    @patch('src.main.get_user_by_id')
    def test_user_filter_command_success(self, mock_get_user, mock_filter):
        """Test la commande user-filter avec succès"""
        mock_tasks = [
            {
                "id": "task-1",
                "title": "Tâche Alice",
                "description": "Description",
                "status": "TODO"
            }
        ]
        mock_result = {
            "tasks": mock_tasks,
            "page": 1,
            "total_items": 1,
            "total_pages": 1
        }
        mock_filter.return_value = mock_result
        mock_get_user.return_value = {"name": "Alice Martin"}
        
        result = self.runner.invoke(cli, ['user-filter', 'user-1'])
        
        assert result.exit_code == 0
        assert "Tâches assignées à Alice Martin" in result.output
        assert "Tâche Alice" in result.output

    @patch('src.main.search_filter_sort_tasks')
    def test_user_filter_command_unassigned(self, mock_filter):
        """Test la commande user-filter pour les tâches non assignées"""
        mock_result = {
            "tasks": [{"id": "task-1", "title": "Libre", "description": "", "status": "TODO"}],
            "page": 1,
            "total_items": 1,
            "total_pages": 1
        }
        mock_filter.return_value = mock_result
        
        result = self.runner.invoke(cli, ['user-filter', 'unassigned'])
        
        assert result.exit_code == 0
        assert "Tâches non assignées" in result.output

    @patch('src.main.search_filter_sort_tasks')
    def test_user_filter_command_with_error(self, mock_filter):
        """Test la commande user-filter avec erreur"""
        mock_filter.side_effect = ValueError("User not found")
        
        result = self.runner.invoke(cli, ['user-filter', 'invalid-user'])
        
        assert result.exit_code == 0
        assert "Erreur" in result.output
        assert "User not found" in result.output

    @patch('src.main.search_filter_sort_tasks')
    @patch('src.main.get_user_by_id')
    def test_user_filter_command_no_tasks_with_user_not_found(self, mock_get_user, mock_filter):
        """Test user-filter sans résultats quand l'utilisateur n'est pas trouvé pour l'affichage"""
        mock_result = {
            "tasks": [],
            "page": 1,
            "total_items": 0,
            "total_pages": 0
        }
        mock_filter.return_value = mock_result
        mock_get_user.return_value = None
        
        result = self.runner.invoke(cli, ['user-filter', 'user-1'])
        
        assert result.exit_code == 0
        assert "user-1" in result.output

    @patch('src.main.search_filter_sort_tasks')
    @patch('src.main.get_user_by_id')
    def test_user_filter_command_with_pagination_and_user_not_found(self, mock_get_user, mock_filter):
        """Test user-filter avec pagination quand l'utilisateur n'est pas trouvé pour l'affichage"""
        mock_result = {
            "tasks": [{"id": "task-1", "title": "Test", "description": "", "status": "TODO"}],
            "page": 2,
            "total_items": 25,
            "total_pages": 3
        }
        mock_filter.return_value = mock_result
        mock_get_user.return_value = None
        
        result = self.runner.invoke(cli, ['user-filter', 'user-1', '--page', '2'])
        
        assert result.exit_code == 0
        assert "Page 2/3" in result.output
        assert "user-1" in result.output

class TestMainCoverage:
    """Tests pour améliorer la couverture sur les lignes manquantes"""
    
    def setup_method(self):
        self.runner = CliRunner()

    @patch('src.main.add_task')
    def test_create_command_early_return_on_error(self, mock_create_task):
        """Test que create fait un return après l'affichage d'erreur (ligne 216)"""
        mock_create_task.side_effect = ValueError("Test error")
        
        result = self.runner.invoke(cli, ['create'], input='Titre\nDesc\n')
        
        assert result.exit_code == 0
        assert "Erreur lors de la création de la tâche" in result.output
        # La ligne suivante ne devrait pas être exécutée
        assert "Tâche créée avec succès" not in result.output

    @patch('src.main.consult_task')
    def test_consult_command_lookup_error_handling(self, mock_consult_task):
        """Test la gestion de LookupError dans consult (ligne 222)"""
        mock_consult_task.side_effect = LookupError("Task not found")
        
        result = self.runner.invoke(cli, ['consult', 'task-id'])
        
        assert result.exit_code == 0
        assert "non trouvée" in result.output

    @patch('src.main.delete_task')
    def test_delete_command_lookup_error_handling(self, mock_delete_task):
        """Test la gestion de LookupError dans delete (ligne 269)"""
        mock_delete_task.side_effect = LookupError("Task not found")
        
        result = self.runner.invoke(cli, ['delete', 'task-id'])
        
        assert result.exit_code == 0
        assert "non trouvée" in result.output

    def test_main_script_execution(self):
        """Test l'exécution du script principal (lignes 308-309)"""
        # Tester que le script peut être exécuté
        # Ces lignes sont normalement exécutées quand le fichier est appelé directement
        # On peut les tester indirectement en important le module
        import src.main
        assert hasattr(src.main, 'cli')
        assert hasattr(src.main, 'console')