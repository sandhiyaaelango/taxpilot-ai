import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.session import get_db
from app.database.models.user import User
from app.database.models.organization import Organization, OrganizationMember
from app.database.repositories.user_repository import UserRepository
from app.schemas.auth import UserResponse, UserCreateRequest, UserUpdateRequest
from app.schemas.common import SuccessResponse
from app.core.dependencies import get_current_user, require_admin
from app.config.security import hash_password

router = APIRouter()

@router.get("", response_model=SuccessResponse[List[UserResponse]])
async def list_team_members(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo = UserRepository(db)
    users = await repo.get_by_organization(str(current_user.organization_id))
    return SuccessResponse(
        data=[
            UserResponse(
                id=str(u.id),
                email=u.email,
                full_name=u.full_name,
                role="AUDITOR" if u.role in ["ACCOUNTANT", "REVIEWER", "AUDITOR"] else "ADMIN",
                organization_id=str(u.organization_id) if u.organization_id else None,
                is_active=u.is_active,
                is_verified=u.is_verified,
                created_at=u.created_at
            )
            for u in users
        ]
    )

@router.post("", response_model=SuccessResponse[UserResponse], status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreateRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    repo = UserRepository(db)
    existing = await repo.get_by_email(user_in.email)
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    target_role = user_in.role.upper()
    if target_role not in ["AUDITOR", "ADMIN"]:
        raise HTTPException(status_code=400, detail="Role must be either AUDITOR or ADMIN")
    
    db_role = target_role

    new_user = User(
        id=uuid.uuid4(),
        email=user_in.email.lower().strip(),
        hashed_password=hash_password(user_in.password),
        full_name=user_in.full_name,
        role=db_role,
        organization_id=current_user.organization_id,
        is_active=True,
        is_verified=True
    )
    db.add(new_user)
    db.add(OrganizationMember(
        organization_id=current_user.organization_id,
        user_id=new_user.id,
        role=db_role
    ))
    await db.commit()
    await db.refresh(new_user)

    return SuccessResponse(
        data=UserResponse(
            id=str(new_user.id),
            email=new_user.email,
            full_name=new_user.full_name,
            role=target_role,
            organization_id=str(new_user.organization_id),
            is_active=new_user.is_active,
            is_verified=new_user.is_verified,
            created_at=new_user.created_at
        ),
        message=f"User {new_user.email} created successfully as {target_role}"
    )

@router.patch("/{user_id}", response_model=SuccessResponse[UserResponse])
async def update_user(
    user_id: str,
    user_in: UserUpdateRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user or str(user.organization_id) != str(current_user.organization_id):
        raise HTTPException(status_code=404, detail="User not found in your organization")

    if user_in.full_name is not None:
        user.full_name = user_in.full_name
    if user_in.is_active is not None:
        user.is_active = user_in.is_active
    if user_in.role is not None:
        target_role = user_in.role.upper()
        if target_role not in ["AUDITOR", "ADMIN"]:
            raise HTTPException(status_code=400, detail="Role must be either AUDITOR or ADMIN")
        user.role = target_role

    await db.commit()
    await db.refresh(user)

    return SuccessResponse(
        data=UserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            role="AUDITOR" if user.role in ["ACCOUNTANT", "REVIEWER", "AUDITOR"] else "ADMIN",
            organization_id=str(user.organization_id),
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at
        ),
        message="User updated successfully"
    )

@router.get("/organizations", response_model=SuccessResponse[List[dict]])
async def list_organizations(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Organization))
    orgs = result.scalars().all()
    return SuccessResponse(
        data=[
            {
                "id": str(o.id),
                "name": o.name,
                "slug": o.slug,
                "plan": o.plan,
                "is_active": o.is_active,
                "created_at": o.created_at.isoformat() if o.created_at else None
            }
            for o in orgs
        ]
    )
