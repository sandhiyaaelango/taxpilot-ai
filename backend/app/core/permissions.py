from enum import Enum
from typing import Optional

class UserRole(str, Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    ACCOUNTANT = "ACCOUNTANT"
    REVIEWER = "REVIEWER"

ROLE_HIERARCHY = {
    UserRole.OWNER: 4,
    UserRole.ADMIN: 3,
    UserRole.ACCOUNTANT: 2,
    UserRole.REVIEWER: 1,
}

def can_manage_clients(role: str) -> bool:
    return role in [UserRole.OWNER, UserRole.ADMIN, UserRole.ACCOUNTANT]

def can_start_investigation(role: str) -> bool:
    return role in [UserRole.OWNER, UserRole.ADMIN, UserRole.ACCOUNTANT]

def can_approve_response(role: str) -> bool:
    return role in [UserRole.OWNER, UserRole.ADMIN, UserRole.ACCOUNTANT]

def can_view_audit_logs(role: str) -> bool:
    return role in [UserRole.OWNER, UserRole.ADMIN]

def can_manage_users(role: str) -> bool:
    return role in [UserRole.OWNER, UserRole.ADMIN]
