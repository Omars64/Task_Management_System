#!/usr/bin/env python3
"""
Seed production database with sample projects and tasks.
This script creates realistic sample data for demonstration purposes.

Run from Cloud Shell or locally (with proper environment variables set):
  python seed_production_data.py
"""
import os
import sys
from datetime import datetime, timedelta
import random

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, User, Project, Task, ProjectMember

# Sample project data
PROJECTS_DATA = [
    {
        "name": "Platform Core",
        "description": "Core platform infrastructure and foundational services. Includes authentication, API gateway, and core microservices."
    },
    {
        "name": "Mobile App",
        "description": "Native mobile application for iOS and Android. Features include offline sync, push notifications, and biometric authentication."
    },
    {
        "name": "Payments Integration",
        "description": "Payment processing system with support for multiple payment gateways, subscription management, and invoicing."
    },
    {
        "name": "Analytics Dashboard",
        "description": "Real-time analytics and reporting dashboard with custom metrics, data visualization, and export capabilities."
    },
    {
        "name": "Customer Portal",
        "description": "Self-service customer portal with account management, support tickets, and knowledge base integration."
    }
]

# Sample task data - varied and realistic
TASKS_DATA = [
    # Platform Core tasks
    ("Implement OAuth2 authentication", "Add OAuth2 provider support with Google, GitHub, and Microsoft. Include refresh token rotation and secure token storage.", "in_progress", "high", 5),
    ("Set up API rate limiting", "Implement rate limiting middleware with Redis backend. Configure limits per endpoint and user tier.", "todo", "high", 7),
    ("Migrate to microservices architecture", "Break down monolithic services into microservices. Set up service mesh and inter-service communication.", "todo", "high", 30),
    ("Add comprehensive logging", "Implement structured logging with correlation IDs. Integrate with log aggregation service.", "in_progress", "medium", 10),
    ("Implement caching layer", "Add Redis caching for frequently accessed data. Configure cache invalidation strategies.", "todo", "medium", 12),
    
    # Mobile App tasks
    ("Design mobile UI/UX", "Create wireframes and design system for mobile app. Ensure consistency across iOS and Android.", "completed", "high", -5),
    ("Implement offline mode", "Add offline data synchronization. Handle conflict resolution and background sync.", "in_progress", "high", 8),
    ("Add push notifications", "Integrate Firebase Cloud Messaging. Implement notification preferences and scheduling.", "todo", "medium", 15),
    ("Optimize app performance", "Profile and optimize app startup time. Reduce memory footprint and improve battery usage.", "todo", "medium", 20),
    ("Implement biometric authentication", "Add fingerprint and face ID authentication. Secure keychain storage for credentials.", "todo", "low", 25),
    
    # Payments Integration tasks
    ("Integrate Stripe payment gateway", "Set up Stripe API integration. Implement payment processing, webhooks, and error handling.", "in_progress", "high", 6),
    ("Add subscription management", "Implement subscription lifecycle management. Handle upgrades, downgrades, and cancellations.", "todo", "high", 14),
    ("Create invoice generation system", "Build PDF invoice generator with company branding. Support multiple currencies and tax calculations.", "todo", "medium", 18),
    ("Implement payment retry logic", "Add automatic retry for failed payments. Configure retry schedule and notification system.", "todo", "medium", 22),
    ("Add payment analytics", "Track payment metrics and success rates. Create dashboard for financial reporting.", "todo", "low", 28),
    
    # Analytics Dashboard tasks
    ("Build real-time data pipeline", "Set up Kafka for real-time event streaming. Process and aggregate events for analytics.", "in_progress", "high", 9),
    ("Create custom metrics builder", "Allow users to define custom metrics. Support complex aggregations and time-based calculations.", "todo", "high", 16),
    ("Implement data visualization", "Add interactive charts and graphs. Support multiple chart types and export options.", "todo", "medium", 19),
    ("Add scheduled reports", "Implement email scheduling for reports. Support PDF and CSV export formats.", "todo", "medium", 24),
    ("Optimize query performance", "Add database indexes and query optimization. Implement materialized views for complex queries.", "todo", "low", 30),
    
    # Customer Portal tasks
    ("Design portal interface", "Create user-friendly interface for customer portal. Ensure responsive design and accessibility.", "completed", "high", -3),
    ("Implement account management", "Add profile editing, password change, and account deletion features.", "in_progress", "high", 11),
    ("Build support ticket system", "Create ticket creation, tracking, and resolution workflow. Add email notifications.", "todo", "high", 17),
    ("Integrate knowledge base", "Connect portal with knowledge base. Add search functionality and article recommendations.", "todo", "medium", 21),
    ("Add multi-language support", "Implement i18n for customer portal. Support 5+ languages with translation management.", "todo", "low", 35),
]


def get_or_create_owner():
    """Get the current user (super admin) as project owner"""
    owner = User.query.filter_by(email='omarsolanki35@gmail.com').first()
    if not owner:
        # Fallback to any super_admin or admin
        owner = User.query.filter_by(role='super_admin').first()
        if not owner:
            owner = User.query.filter_by(role='admin').first()
    return owner


def create_projects(owner):
    """Create sample projects if they don't exist"""
    created_projects = []
    existing_projects = {p.name: p for p in Project.query.all()}
    
    for project_data in PROJECTS_DATA:
        if project_data["name"] not in existing_projects:
            project = Project(
                name=project_data["name"],
                description=project_data["description"],
                owner_id=owner.id if owner else None
            )
            db.session.add(project)
            created_projects.append(project)
            print(f"✓ Created project: {project_data['name']}")
        else:
            created_projects.append(existing_projects[project_data["name"]])
            print(f"→ Project already exists: {project_data['name']}")
    
    if created_projects:
        db.session.commit()
    
    return created_projects


def add_project_members(project, owner):
    """Add owner as project member if not already a member"""
    existing_member = ProjectMember.query.filter_by(
        project_id=project.id,
        user_id=owner.id
    ).first()
    
    if not existing_member and owner:
        member = ProjectMember(
            project_id=project.id,
            user_id=owner.id,
            role='owner'
        )
        db.session.add(member)
        db.session.commit()
        print(f"  → Added {owner.name} as project member")


def create_tasks_for_project(project, owner, tasks_per_project=5):
    """Create sample tasks for a project"""
    # Get tasks for this project (distribute tasks across projects)
    project_index = PROJECTS_DATA.index(next(p for p in PROJECTS_DATA if p["name"] == project.name))
    start_idx = project_index * tasks_per_project
    end_idx = start_idx + tasks_per_project
    
    project_tasks = TASKS_DATA[start_idx:end_idx]
    
    created_count = 0
    for title, description, status, priority, days_offset in project_tasks:
        # Check if task already exists
        existing = Task.query.filter_by(
            title=title,
            project_id=project.id
        ).first()
        
        if existing:
            print(f"  → Task already exists: {title[:50]}...")
            continue
        
        due_date = datetime.utcnow() + timedelta(days=days_offset) if days_offset > 0 else datetime.utcnow() + timedelta(days=abs(days_offset))
        completed_at = datetime.utcnow() - timedelta(days=1) if status == 'completed' else None
        
        task = Task(
            title=title,
            description=description,
            priority=priority,
            status=status,
            project_id=project.id,
            assigned_to=owner.id if owner else None,
            created_by=owner.id if owner else None,
            due_date=due_date,
            completed_at=completed_at
        )
        db.session.add(task)
        created_count += 1
    
    if created_count > 0:
        db.session.commit()
        print(f"  ✓ Created {created_count} tasks for '{project.name}'")
    
    return created_count


def main():
    """Main function to seed production data"""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("Seeding Production Database with Sample Data")
        print("=" * 60)
        print()
        
        # Get owner
        owner = get_or_create_owner()
        if not owner:
            print("❌ Error: No owner found. Please ensure you have a super_admin or admin user.")
            return
        
        print(f"✓ Using owner: {owner.name} ({owner.email})")
        print()
        
        # Create projects
        print("Creating projects...")
        projects = create_projects(owner)
        print(f"✓ Total projects: {len(projects)}")
        print()
        
        # Add project members
        print("Adding project members...")
        for project in projects:
            add_project_members(project, owner)
        print()
        
        # Create tasks
        print("Creating tasks...")
        total_tasks = 0
        for project in projects:
            tasks_created = create_tasks_for_project(project, owner, tasks_per_project=5)
            total_tasks += tasks_created
        
        print()
        print("=" * 60)
        print(f"✅ Seeding Complete!")
        print(f"   Projects: {len(projects)}")
        print(f"   Tasks: {total_tasks}")
        print("=" * 60)


if __name__ == '__main__':
    main()

