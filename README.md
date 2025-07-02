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

CHECK LE TASK_LIST pour vérifier que l'ajout se soit bien effectué
