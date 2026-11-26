import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.database.models.user import User
from app.database.models.organization import Organization, OrganizationMember
from app.database.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.schemas.common import SuccessResponse
from app.config.security import verify_password, hash_password, create_access_token
from app.core.dependencies import get_current_user, normalize_role

router = APIRouter()

@router.post("/register", response_model=SuccessResponse[TokenResponse])
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user_repo = UserRepository(db)
    existing = await user_repo.get_by_email(request.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )

    # Create new Organization
    org_id = uuid.uuid4()
    slug = request.organization_name.lower().replace(" ", "-")[:50] + f"-{str(org_id)[:4]}"
    org = Organization(
        id=org_id,
        name=request.organization_name,
        slug=slug,
        plan="PRO",
        is_active=True
    )
    db.add(org)

    # Create User (strict two-role standard: AUDITOR or ADMIN)
    user_id = uuid.uuid4()
    normalized_role = normalize_role(request.role)
    user = User(
        id=user_id,
        email=request.email.lower().strip(),
        hashed_password=hash_password(request.password),
        full_name=request.full_name,
        role=normalized_role,
        organization_id=org_id,
        is_active=True,
        is_verified=True
    )
    db.add(user)

    # Add Org Membership
    db.add(OrganizationMember(organization_id=org_id, user_id=user_id, role=normalized_role))
    await db.commit()

    token = create_access_token({"sub": str(user_id), "org_id": str(org_id), "role": normalized_role})
    user_res = UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=normalized_role,
        organization_id=str(user.organization_id),
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at
    )
    return SuccessResponse(
        data=TokenResponse(access_token=token, user=user_res),
        message="Registration successful"
    )

@router.post("/login", response_model=SuccessResponse[TokenResponse])
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    user_repo = UserRepository(db)
    user = await user_repo.get_by_email(request.email)
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account is disabled")

    # Map role to two-role standard: AUDITOR or ADMIN
    display_role = normalize_role(user.role)
    token = create_access_token({
        "sub": str(user.id),
        "org_id": str(user.organization_id) if user.organization_id else None,
        "role": display_role
    })
    user_res = UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=display_role,
        organization_id=str(user.organization_id) if user.organization_id else None,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at
    )
    return SuccessResponse(
        data=TokenResponse(access_token=token, user=user_res),
        message="Login successful"
    )

@router.get("/me", response_model=SuccessResponse[UserResponse])
async def get_me(current_user: User = Depends(get_current_user)):
    user_res = UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        role=normalize_role(current_user.role),
        organization_id=str(current_user.organization_id) if current_user.organization_id else None,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at
    )
    return SuccessResponse(data=user_res)

@router.post("/logout", response_model=SuccessResponse[bool])
async def logout(current_user: User = Depends(get_current_user)):
    return SuccessResponse(data=True, message="Successfully logged out")
