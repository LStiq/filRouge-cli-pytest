#!/usr/bin/env python3

import click
from rich.console import Console
from rich.table import Table

from src.task_manager import get_tasks, create_task, consult_task, update_task, delete_task, assign_task, get_tasks_assigned_to_user, get_unassigned_tasks, get_users, get_user_by_id, filter_tasks_by_user, filter_tasks_combined

console = Console()

@click.group()
def cli():
    """Gestionnaire de Tâches - Version CLI Python"""
    pass

@cli.command()
def list():
    """Lister les tâches"""
    tasks = get_tasks()
    
    if not tasks:
        console.print("Aucune tâche trouvée.", style="yellow")
        return
    
    table = Table(title="Liste des tâches")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Statut", style="green")
    table.add_column("Titre", style="white")
    table.add_column("Description", style="dim")
    table.add_column("Assigné à", style="magenta")
    
    for task in tasks:
        assigned_user = ""
        if task.get("assigned_user"):
            user = get_user_by_id(task["assigned_user"])
            assigned_user = user["name"] if user else task["assigned_user"]
        
        table.add_row(
            str(task["id"]),
            task['status'],
            task["title"],
            task["description"],
            assigned_user or "(non assigné)"
        )
    
    console.print(table)

@cli.command()
def create():
    """Créer une nouvelle tâche"""
    title = click.prompt("Titre de la tâche", type=str)
    description = click.prompt("Description (optionnelle)", type=str, default="")
    
    try:
        task = create_task(title, description)
        console.print(f"Tâche créée avec ID: [bold]{task['id']}[/bold]", style="green")
    except ValueError as e:
        console.print(f"Erreur lors de la création de la tâche: {e}", style="red")
        return
    
    console.print(f"Tâche créée avec succès: [bold]{title}[/bold]", style="green")

@cli.command()
@click.argument('task_id')
def consult(task_id):
    """Consulter une tâche par ID"""
    try:
        task = consult_task(task_id)
    except ValueError as e:
        console.print(f"Erreur : {str(e)}", style="red")
        return
    except LookupError:
        console.print(f"Tâche avec ID {task_id} non trouvée.", style="red")
        return

    console.print(f"ID: {task['id']}", style="cyan")
    console.print(f"Titre: {task['title']}", style="bold")
    console.print(f"Description: {task['description'] or '(vide)'}", style="dim")
    console.print(f"Statut: {task['status']}", style="green")
    
    # Afficher l'assignation
    if task.get("assigned_user"):
        user = get_user_by_id(task["assigned_user"])
        user_name = user["name"] if user else task["assigned_user"]
        console.print(f"Assigné à: {user_name}", style="magenta")
    else:
        console.print("Assigné à: (non assigné)", style="dim")
    
    if "created_at" in task:
        console.print(f"Créée le: {task['created_at']}", style="blue")

@cli.command()
@click.argument('task_id')
def update(task_id):
    """Mettre à jour une tâche par ID"""
    title = click.prompt("Nouveau titre de la tâche (laisser vide pour ne pas changer)", type=str, default="")
    description = click.prompt("Nouvelle description (laisser vide pour ne pas changer)", type=str, default="")
    
    try:
        task = update_task(task_id, title=title or None, description=description or None)
        console.print(f"Tâche mise à jour avec succès: [bold]{task['title']}[/bold]", style="green")
    except ValueError as e:
        console.print(f"Erreur lors de la mise à jour de la tâche: {e}", style="red")
        return

@cli.command()
@click.argument('task_id')
def delete(task_id):
    """Supprimer une tâche par ID"""
    try:
        delete_task(task_id)
        console.print(f"Tâche avec ID {task_id} supprimée avec succès.", style="green")
    except ValueError as e:
        console.print(f"Erreur lors de la suppression de la tâche: {e}", style="red")
        return
    except LookupError:
        console.print(f"Tâche avec ID {task_id} non trouvée.", style="red")
        return

@cli.command()
@click.argument('task_id')
@click.argument('user_id', required=False)
def assign(task_id, user_id):
    """Assigner une tâche à un utilisateur (ou désassigner si user_id vide)"""
    try:
        task = assign_task(task_id, user_id)
        if task["assigned_user"]:
            user = get_user_by_id(task["assigned_user"])
            user_name = user["name"] if user else task["assigned_user"]
            console.print(f"Tâche assignée à [bold]{user_name}[/bold]", style="green")
        else:
            console.print("Tâche désassignée", style="yellow")
    except ValueError as e:
        console.print(f"Erreur : {str(e)}", style="red")

@cli.command()
def users():
    """Lister les utilisateurs"""
    users = get_users()
    
    if not users:
        console.print("Aucun utilisateur trouvé.", style="yellow")
        return
    
    table = Table(title="Liste des utilisateurs")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Nom", style="white")
    table.add_column("Email", style="blue")
    
    for user in users:
        table.add_row(user["id"], user["name"], user["email"])
    
    console.print(table)

@cli.command()
@click.argument('user_id')
def user_tasks(user_id):
    """Voir les tâches assignées à un utilisateur"""
    user = get_user_by_id(user_id)
    if not user:
        console.print(f"Utilisateur {user_id} non trouvé.", style="red")
        return
    
    tasks = get_tasks_assigned_to_user(user_id)
    
    console.print(f"Tâches assignées à [bold]{user['name']}[/bold]:")
    
    if not tasks:
        console.print("Aucune tâche assignée.", style="yellow")
        return
    
    for task in tasks:
        console.print(f"• [{task['status']}] {task['title']}")

@cli.command()
def unassigned():
    """Voir les tâches non assignées"""
    tasks = get_unassigned_tasks()
    
    console.print("Tâches non assignées:")
    
    if not tasks:
        console.print("Toutes les tâches sont assignées.", style="green")
        return
    
    for task in tasks:
        console.print(f"• [{task['status']}] {task['title']}")

@cli.command()
@click.option('--status', type=click.Choice(['TODO', 'ONGOING', 'DONE']), help='Filtrer par statut')
@click.option('--user', help='Filtrer par utilisateur assigné (ou "unassigned" pour non assignées)')
@click.option('--search', help='Rechercher dans titre/description')
@click.option('--page', default=1, help='Numéro de page (défaut: 1)')
@click.option('--size', default=20, help='Taille de page (défaut: 20)')
def filter(status, user, search, page, size):
    """Filtrer les tâches avec plusieurs critères"""
    try:
        result = filter_tasks_combined(
            status=status,
            user_id=user,
            query=search,
            page=page,
            size=size
        )
        
        if not result["tasks"]:
            console.print("Aucune tâche trouvée avec ces critères.", style="yellow")
            return
        
        # Construire le titre avec les filtres appliqués
        filters = []
        if status:
            filters.append(f"statut: {status}")
        if user:
            if user == "unassigned":
                filters.append("non assignées")
            else:
                user_obj = get_user_by_id(user)
                user_name = user_obj["name"] if user_obj else user
                filters.append(f"assigné à: {user_name}")
        if search:
            filters.append(f"recherche: '{search}'")
        
        title = "Tâches filtrées"
        if filters:
            title += f" ({', '.join(filters)})"
        
        table = Table(title=title)
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Statut", style="green")
        table.add_column("Titre", style="white")
        table.add_column("Description", style="dim")
        table.add_column("Assigné à", style="magenta")
        
        for task in result["tasks"]:
            assigned_user = ""
            if task.get("assigned_user"):
                user_obj = get_user_by_id(task["assigned_user"])
                assigned_user = user_obj["name"] if user_obj else task["assigned_user"]
            
            table.add_row(
                str(task["id"]),
                task['status'],
                task["title"],
                task["description"],
                assigned_user or "(non assigné)"
            )
        
        console.print(table)
        
        # Afficher les informations de pagination
        if result["total_pages"] > 1:
            console.print(f"\nPage {result['page']}/{result['total_pages']} - {result['total_items']} tâche(s) au total", style="dim")
            
    except ValueError as e:
        console.print(f"Erreur : {str(e)}", style="red")

@cli.command()
@click.argument('user_id')
@click.option('--page', default=1, help='Numéro de page (défaut: 1)')
@click.option('--size', default=20, help='Taille de page (défaut: 20)')
def user_filter(user_id, page, size):
    """Voir les tâches assignées à un utilisateur spécifique"""
    try:
        result = filter_tasks_by_user(user_id, page, size)
        
        if not result["tasks"]:
            if user_id == "unassigned":
                console.print("Aucune tâche non assignée.", style="yellow")
            else:
                user = get_user_by_id(user_id)
                user_name = user["name"] if user else user_id
                console.print(f"Aucune tâche assignée à {user_name}.", style="yellow")
            return
        
        # Construire le titre
        if user_id == "unassigned":
            title = "Tâches non assignées"
        else:
            user = get_user_by_id(user_id)
            user_name = user["name"] if user else user_id
            title = f"Tâches assignées à {user_name}"
        
        table = Table(title=title)
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Statut", style="green")
        table.add_column("Titre", style="white")
        table.add_column("Description", style="dim")
        
        for task in result["tasks"]:
            table.add_row(
                str(task["id"]),
                task['status'],
                task["title"],
                task["description"]
            )
        
        console.print(table)
        
        # Afficher les informations de pagination
        if result["total_pages"] > 1:
            console.print(f"\nPage {result['page']}/{result['total_pages']} - {result['total_items']} tâche(s) au total", style="dim")
            
    except ValueError as e:
        console.print(f"Erreur : {str(e)}", style="red")

if __name__ == '__main__':
    console.print("Gestionnaire de Tâches - Version CLI Python\n", style="bold blue")
    cli()
