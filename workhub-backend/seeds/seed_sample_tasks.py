"""
Seed 20 realistic sample tasks divided equally across 4 projects (5 per project).
If there are fewer than 4 projects, this script will create the missing ones.
Assignments prefer members of each project when available; otherwise leaves unassigned.

Run (from project root):
  docker exec workhub-backend python -u seeds/seed_sample_tasks.py
"""
import random
from datetime import datetime, timedelta

import os
import sys

# Ensure parent directory is on PYTHONPATH when running inside container
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from app import create_app
from models import db, User, Project, Task, ProjectMember


PROJECT_NAMES = [
    "Platform Core",
    "Mobile App",
    "Payments",
    "Analytics"
]


TASK_BANK = [
    ("Implement authentication with JWT",
     "Add login/logout, refresh tokens, and role-based route guards. Ensure tokens rotate and are stored securely.",
     "in_progress", "high", 3),
    ("Migrate database to Unicode",
     "Update chat message column to NVARCHAR and audit tables to ensure emoji support across the product.",
     "todo", "medium", 5),
    ("Add message reactions",
     "Implement emoji reactions with counters, per-user toggling, and tooltips for who reacted.",
     "todo", "medium", 7),
    ("Optimize task list queries",
     "Add proper indexes on status/priority and paginate queries to reduce load time by 40%.",
     "in_progress", "high", 10),
    ("Create CI pipeline",
     "Add GitHub Actions that run tests, lint, build Docker images, and push to registry on main branch.",
     "todo", "medium", 14),
    ("Introduce feature flags",
     "Add a simple feature-flag system for gradually rolling out new chat features to 10% of users.",
     "todo", "low", 12),
    ("Implement audit logs",
     "Record CRUD actions for admin-visible entities and expose a basic search/filter view.",
     "in_progress", "medium", 9),
    ("Add rate limiting to APIs",
     "Protect public endpoints from abuse with user/IP-based throttling and appropriate error messaging.",
     "todo", "high", 6),
    ("Refactor notification service",
     "Consolidate email/toast generation and introduce templates for system messages.",
     "todo", "medium", 8),
    ("Hardening settings page",
     "Validate inputs, add optimistic UI, and ensure personal settings persist across sessions.",
     "todo", "low", 11),
]


def ensure_projects():
    projects = Project.query.all()
    by_name = {p.name: p for p in projects}
    created = []
    for name in PROJECT_NAMES:
        if name not in by_name:
            p = Project(name=name, description=f"{name} initiative")
            db.session.add(p)
            created.append(p)
    if created:
        db.session.commit()
    return Project.query.order_by(Project.id.asc()).limit(4).all()


def get_project_members(project_id):
    members = ProjectMember.query.filter_by(project_id=project_id).all()
    users = []
    for m in members:
        u = User.query.get(m.user_id)
        if u:
            users.append(u)
    return users


def pick_status_priority(status, priority):
    return status, priority


def create_tasks_for_project(project: Project, num_tasks: int):
    members = get_project_members(project.id)
    all_users = User.query.all()
    creators = [u for u in all_users if (u.role or '').lower() in ['super_admin', 'admin', 'manager', 'team_lead']]
    creator = creators[0] if creators else (all_users[0] if all_users else None)

    tasks_created = 0
    i = 0
    while tasks_created < num_tasks and i < len(TASK_BANK):
        title, description, status, priority, days = TASK_BANK[i]
        i += 1
        # Vary titles slightly per project to avoid duplicates
        task_title = f"{title} ({project.name})"

        due_date = datetime.utcnow() + timedelta(days=days)

        assignee = random.choice(members) if members else None

        t = Task(
            title=task_title[:200],
            description=description,
            priority=priority,
            status=status,
            assigned_to=assignee.id if assignee else None,
            due_date=due_date,
            project_id=project.id,
            created_by=creator.id if creator else None,
        )
        db.session.add(t)
        tasks_created += 1

    db.session.commit()
    return tasks_created


def main():
    app = create_app()
    with app.app_context():
        projects = ensure_projects()
        if not projects:
            print("No projects found or created; aborting.")
            return

        total_needed = 20
        per_project = 5
        created_total = 0
        for p in projects[:4]:
            created = create_tasks_for_project(p, per_project)
            created_total += created
            print(f"✓ Created {created} tasks for project '{p.name}' (id={p.id})")

        print(f"\nDone. Total tasks created: {created_total}")


if __name__ == '__main__':
    main()


