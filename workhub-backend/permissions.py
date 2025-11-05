"""Permissions and Role-Based Access Control (RBAC) System"""

# Define all available permissions
class Permission:
    # User management
    USERS_CREATE = "users.create"
    USERS_READ = "users.read"
    USERS_UPDATE = "users.update"
    USERS_DELETE = "users.delete"
    USERS_ASSIGN_ROLE = "users.assign_role"
    
    # Task management
    TASKS_CREATE = "tasks.create"
    TASKS_READ = "tasks.read"
    TASKS_UPDATE = "tasks.update"
    TASKS_DELETE = "tasks.delete"
    TASKS_ASSIGN = "tasks.assign"
    TASKS_ASSIGN_ANY = "tasks.assign_any"  # Assign to anyone, not just your team
    TASKS_DELETE_ANY = "tasks.delete_any"  # Delete any task, not just your own
    
    # Reports
    REPORTS_VIEW = "reports.view"
    REPORTS_VIEW_ALL = "reports.view_all"  # View all users' reports
    REPORTS_EXPORT = "reports.export"

    # Projects & Sprints
    PROJECTS_CREATE = "projects.create"
    PROJECTS_READ = "projects.read"
    PROJECTS_UPDATE = "projects.update"
    PROJECTS_DELETE = "projects.delete"
    SPRINTS_CREATE = "sprints.create"
    SPRINTS_READ = "sprints.read"
    SPRINTS_UPDATE = "sprints.update"
    SPRINTS_DELETE = "sprints.delete"
    
    # Settings
    SETTINGS_MANAGE = "settings.manage"
    SETTINGS_VIEW = "settings.view"
    
    # System administration
    SYSTEM_MANAGE = "system.manage"
    
    # Notifications
    NOTIFICATIONS_DELETE = "notifications.delete"
    
    # Comments
    COMMENTS_CREATE = "comments.create"
    COMMENTS_DELETE = "comments.delete"
    COMMENTS_DELETE_ANY = "comments.delete_any"


# Define roles and their permissions
ROLE_PERMISSIONS = {
    # Super Admin - Full access to everything
    "super_admin": {
        Permission.USERS_CREATE,
        Permission.USERS_READ,
        Permission.USERS_UPDATE,
        Permission.USERS_DELETE,
        Permission.USERS_ASSIGN_ROLE,
        Permission.TASKS_CREATE,
        Permission.TASKS_READ,
        Permission.TASKS_UPDATE,
        Permission.TASKS_DELETE,
        Permission.TASKS_ASSIGN,
        Permission.TASKS_ASSIGN_ANY,
        Permission.TASKS_DELETE_ANY,
        Permission.REPORTS_VIEW,
        Permission.REPORTS_VIEW_ALL,
        Permission.REPORTS_EXPORT,
        Permission.PROJECTS_CREATE, Permission.PROJECTS_READ, Permission.PROJECTS_UPDATE, Permission.PROJECTS_DELETE,
        Permission.SPRINTS_CREATE, Permission.SPRINTS_READ, Permission.SPRINTS_UPDATE, Permission.SPRINTS_DELETE,
        Permission.SETTINGS_MANAGE,
        Permission.SETTINGS_VIEW,
        Permission.SYSTEM_MANAGE,
        Permission.NOTIFICATIONS_DELETE,
        Permission.COMMENTS_CREATE,
        Permission.COMMENTS_DELETE,
        Permission.COMMENTS_DELETE_ANY,
    },
    
    # Admin - Most permissions except system management
    "admin": {
        Permission.USERS_CREATE,
        Permission.USERS_READ,
        Permission.USERS_UPDATE,
        Permission.USERS_DELETE,
        Permission.USERS_ASSIGN_ROLE,
        Permission.TASKS_CREATE,
        Permission.TASKS_READ,
        Permission.TASKS_UPDATE,
        Permission.TASKS_DELETE,
        Permission.TASKS_ASSIGN,
        Permission.TASKS_ASSIGN_ANY,
        Permission.TASKS_DELETE_ANY,
        Permission.REPORTS_VIEW,
        Permission.REPORTS_VIEW_ALL,
        Permission.REPORTS_EXPORT,
        Permission.PROJECTS_CREATE, Permission.PROJECTS_READ, Permission.PROJECTS_UPDATE, Permission.PROJECTS_DELETE,
        Permission.SPRINTS_CREATE, Permission.SPRINTS_READ, Permission.SPRINTS_UPDATE, Permission.SPRINTS_DELETE,
        Permission.SETTINGS_VIEW,
        Permission.NOTIFICATIONS_DELETE,
        Permission.COMMENTS_CREATE,
        Permission.COMMENTS_DELETE,
        Permission.COMMENTS_DELETE_ANY,
    },
    
    # Manager - Team and task management
    "manager": {
        Permission.USERS_READ,  # Can view team members
        Permission.TASKS_CREATE,
        Permission.TASKS_READ,
        Permission.TASKS_UPDATE,
        Permission.TASKS_ASSIGN,
        Permission.TASKS_DELETE,  # Can delete tasks they created
        Permission.REPORTS_VIEW,
        Permission.REPORTS_VIEW_ALL,  # Can see team reports
        Permission.REPORTS_EXPORT,
        Permission.PROJECTS_READ,
        Permission.SPRINTS_READ,
        Permission.SETTINGS_VIEW,
        Permission.NOTIFICATIONS_DELETE,
        Permission.COMMENTS_CREATE,
        Permission.COMMENTS_DELETE,
    },
    
    # Team Lead - Can manage team tasks
    "team_lead": {
        Permission.USERS_READ,
        Permission.TASKS_CREATE,
        Permission.TASKS_READ,
        Permission.TASKS_UPDATE,
        Permission.TASKS_ASSIGN,  # Can assign to team members
        Permission.TASKS_DELETE,  # Can delete tasks they created
        Permission.REPORTS_VIEW,
        Permission.REPORTS_VIEW_ALL,  # Can see team reports
        Permission.SETTINGS_VIEW,
        Permission.PROJECTS_READ, Permission.SPRINTS_READ,
        Permission.NOTIFICATIONS_DELETE,
        Permission.COMMENTS_CREATE,
        Permission.COMMENTS_DELETE,
    },
    
    # Developer - Can manage assigned tasks
    "developer": {
        Permission.TASKS_CREATE,
        Permission.TASKS_READ,
        Permission.TASKS_UPDATE,  # Can update assigned tasks
        Permission.REPORTS_VIEW,
        Permission.SETTINGS_VIEW,
        Permission.PROJECTS_READ, Permission.SPRINTS_READ,
        Permission.NOTIFICATIONS_DELETE,
        Permission.COMMENTS_CREATE,
    },
    
    # Viewer - Read-only access
    "viewer": {
        Permission.TASKS_READ,
        Permission.USERS_READ,
        Permission.REPORTS_VIEW,
        Permission.SETTINGS_VIEW,
        Permission.PROJECTS_READ, Permission.SPRINTS_READ,
    },
    
    # User - Basic user (alias for developer, for backwards compatibility)
    "user": {
        Permission.TASKS_CREATE,
        Permission.TASKS_READ,
        Permission.TASKS_UPDATE,
        Permission.REPORTS_VIEW,
        Permission.SETTINGS_VIEW,
        Permission.COMMENTS_CREATE,
    }
}


def has_permission(user_role: str, permission: str) -> bool:
    """
    Check if a role has a specific permission
    
    Args:
        user_role: The user's role (e.g., 'admin', 'developer')
        permission: The permission to check (e.g., 'tasks.create')
    
    Returns:
        bool: True if the role has the permission, False otherwise
    """
    role_lower = user_role.lower() if user_role else "viewer"
    permissions = ROLE_PERMISSIONS.get(role_lower, set())
    return permission in permissions


def has_any_permission(user_role: str, permissions: list) -> bool:
    """
    Check if a role has any of the specified permissions
    
    Args:
        user_role: The user's role
        permissions: List of permissions to check
    
    Returns:
        bool: True if the role has any of the permissions
    """
    role_lower = user_role.lower() if user_role else "viewer"
    role_perms = ROLE_PERMISSIONS.get(role_lower, set())
    return any(perm in role_perms for perm in permissions)


def has_all_permissions(user_role: str, permissions: list) -> bool:
    """
    Check if a role has all of the specified permissions
    
    Args:
        user_role: The user's role
        permissions: List of permissions to check
    
    Returns:
        bool: True if the role has all of the permissions
    """
    role_lower = user_role.lower() if user_role else "viewer"
    role_perms = ROLE_PERMISSIONS.get(role_lower, set())
    return all(perm in role_perms for perm in permissions)


def get_role_permissions(role: str) -> set:
    """
    Get all permissions for a specific role
    
    Args:
        role: The role name
    
    Returns:
        set: Set of permissions for the role
    """
    role_lower = role.lower() if role else "viewer"
    return ROLE_PERMISSIONS.get(role_lower, set())


def get_available_roles() -> list:
    """
    Get a list of all available roles
    
    Returns:
        list: List of role names
    """
    return list(ROLE_PERMISSIONS.keys())


def get_role_display_name(role: str) -> str:
    """
    Get a human-readable display name for a role
    
    Args:
        role: The role name
    
    Returns:
        str: Display name
    """
    display_names = {
        "super_admin": "Super Admin",
        "admin": "Admin",
        "manager": "Manager",
        "team_lead": "Team Lead",
        "developer": "Developer",
        "viewer": "Viewer"
    }
    return display_names.get(role.lower(), role.title())

