# Task Manager - Version Python CLI

Gestionnaire de tâches minimal développé avec approche TDD en utilisant pytest.

## Installation

```bash
pip install -r requirements.txt
```

## Utilisation

### Démarrer l'application CLI
```bash
python src/main.py --help
```

### Commandes disponibles
- `list` : Lister toutes les tâches avec assignations
- `create` : Créer une nouvelle tâche
- `consult <task_id>` : Consulter une tâche par ID avec assignation
- `update <task_id>` : Mettre à jour une tâche
- `delete <task_id>` : Supprimer une tâche
- `assign <task_id> [user_id]` : Assigner/désassigner une tâche
- `users` : Lister les utilisateurs
- `user-tasks <user_id>` : Voir les tâches d'un utilisateur
- `unassigned` : Voir les tâches non assignées
- `filter` : Filtrer avec plusieurs critères (statut, utilisateur, recherche)
- `user-filter <user_id>` : Filtrer par utilisateur spécifique

### Exemples de filtrage avancé
```bash
# Filtrer par statut et utilisateur
python src/main.py filter --status TODO --user user-1

# Filtrer les tâches non assignées avec recherche
python src/main.py filter --user unassigned --search "réparer"

# Combinaison de tous les filtres
python src/main.py filter --status ONGOING --user user-2 --search "urgent"

# Filtrer uniquement par utilisateur
python src/main.py user-filter user-1
python src/main.py user-filter unassigned
```

### Lancer les tests
```bash
# Tests simples
pytest

# Tests avec couverture
pytest --cov=src --cov-report=html

# Tests en mode verbose
pytest -v

# Tests avec monitoring des modifications
pytest-watch
```

## Couverture de tests

Objectif : maintenir une couverture > 90% sur la logique métier.

```bash
pytest --cov=src --cov-report=term-missing
```

## Fonctionnalités

- ✅ Création de tâches
- ✅ Consultation de tâches  
- ✅ Mise à jour de tâches
- ✅ Suppression de tâches
- ✅ Pagination des tâches
- ✅ Recherche dans les tâches
- ✅ Filtrage par statut
- ✅ Tri des tâches
- ✅ Assignation d'utilisateurs
- ✅ Gestion des utilisateurs
- ✅ Filtrage par utilisateur assigné
- ✅ Filtres combinés (statut + utilisateur + recherche)

CHECK LE TASK_LIST pour vérifier que l'ajout se soit bien effectué
