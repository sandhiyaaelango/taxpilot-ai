import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.database.models.user import User
from app.database.models.client import Client, ClientGSTINProfile
from app.database.repositories.client_repository import ClientRepository
from app.schemas.client import ClientCreate, ClientUpdate, ClientResponse, GSTINProfileCreate, GSTINProfileResponse
from app.schemas.common import SuccessResponse, PaginatedResponse
from app.core.dependencies import get_current_user, require_accountant

router = APIRouter()

@router.get("", response_model=PaginatedResponse[ClientResponse])
async def list_clients(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo = ClientRepository(db)
    skip = (page - 1) * page_size
    clients = await repo.list_by_organization(
        str(current_user.organization_id),
        skip=skip,
        limit=page_size,
        search=search,
        status=status_filter
    )
    total = await repo.count_by_organization(
        str(current_user.organization_id),
        search=search,
        status=status_filter
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    client_responses = []
    for c in clients:
        client_responses.append(ClientResponse(
            id=str(c.id),
            organization_id=str(c.organization_id),
            business_name=c.business_name,
            primary_gstin=c.primary_gstin,
            contact_name=c.contact_name,
            contact_email=c.contact_email,
            contact_phone=c.contact_phone,
            state_code=c.state_code,
            industry=c.industry,
            address=c.address,
            status=c.status,
            is_demo=c.is_demo,
            created_at=c.created_at,
            updated_at=c.updated_at,
            gstin_profiles=[]
        ))

    return PaginatedResponse(
        success=True,
        data=client_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.post("", response_model=SuccessResponse[ClientResponse], status_code=status.HTTP_201_CREATED)
async def create_client(
    client_in: ClientCreate,
    current_user: User = Depends(require_accountant),
    db: AsyncSession = Depends(get_db)
):
    repo = ClientRepository(db)
    existing = await repo.get_by_gstin(str(current_user.organization_id), client_in.primary_gstin)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A client with GSTIN {client_in.primary_gstin} already exists in your organization"
        )

    client_id = uuid.uuid4()
    client = Client(
        id=client_id,
        organization_id=current_user.organization_id,
        business_name=client_in.business_name,
        primary_gstin=client_in.primary_gstin,
        contact_name=client_in.contact_name,
        contact_email=client_in.contact_email,
        contact_phone=client_in.contact_phone,
        state_code=client_in.state_code or client_in.primary_gstin[:2],
        industry=client_in.industry,
        address=client_in.address,
        status="ACTIVE",
        is_demo=False
    )
    db.add(client)

    # Automatically create primary GSTIN profile
    gstin_profile = ClientGSTINProfile(
        id=uuid.uuid4(),
        client_id=client_id,
        gstin=client_in.primary_gstin,
        trade_name=client_in.business_name,
        registration_type="Regular",
        state_code=client_in.state_code or client_in.primary_gstin[:2],
        is_primary=True,
        is_active=True
    )
    db.add(gstin_profile)
    await db.commit()

    return SuccessResponse(
        data=ClientResponse(
            id=str(client.id),
            organization_id=str(client.organization_id),
            business_name=client.business_name,
            primary_gstin=client.primary_gstin,
            contact_name=client.contact_name,
            contact_email=client.contact_email,
            contact_phone=client.contact_phone,
            state_code=client.state_code,
            industry=client.industry,
            address=client.address,
            status=client.status,
            is_demo=client.is_demo,
            created_at=client.created_at,
            updated_at=client.updated_at,
            gstin_profiles=[
                GSTINProfileResponse(
                    id=str(gstin_profile.id),
                    client_id=str(gstin_profile.client_id),
                    gstin=gstin_profile.gstin,
                    trade_name=gstin_profile.trade_name,
                    registration_type=gstin_profile.registration_type,
                    state_code=gstin_profile.state_code,
                    is_primary=gstin_profile.is_primary,
                    is_active=gstin_profile.is_active
                )
            ]
        ),
        message="Client created successfully"
    )

@router.get("/{client_id}", response_model=SuccessResponse[ClientResponse])
async def get_client(
    client_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo = ClientRepository(db)
    client = await repo.get_with_gstins(client_id)
    if not client or str(client.organization_id) != str(current_user.organization_id):
        raise HTTPException(status_code=404, detail="Client not found")

    gstins = [
        GSTINProfileResponse(
            id=str(g.id),
            client_id=str(g.client_id),
            gstin=g.gstin,
            trade_name=g.trade_name,
            registration_type=g.registration_type,
            state_code=g.state_code,
            is_primary=g.is_primary,
            is_active=g.is_active
        )
        for g in (client.gstin_profiles or [])
    ]

    return SuccessResponse(
        data=ClientResponse(
            id=str(client.id),
            organization_id=str(client.organization_id),
            business_name=client.business_name,
            primary_gstin=client.primary_gstin,
            contact_name=client.contact_name,
            contact_email=client.contact_email,
            contact_phone=client.contact_phone,
            state_code=client.state_code,
            industry=client.industry,
            address=client.address,
            status=client.status,
            is_demo=client.is_demo,
            created_at=client.created_at,
            updated_at=client.updated_at,
            gstin_profiles=gstins
        )
    )

@router.put("/{client_id}", response_model=SuccessResponse[ClientResponse])
async def update_client(
    client_id: str,
    client_update: ClientUpdate,
    current_user: User = Depends(require_accountant),
    db: AsyncSession = Depends(get_db)
):
    repo = ClientRepository(db)
    client = await repo.get_by_id(client_id)
    if not client or str(client.organization_id) != str(current_user.organization_id):
        raise HTTPException(status_code=404, detail="Client not found")

    update_data = client_update.model_dump(exclude_unset=True)
    updated = await repo.update(client_id, **update_data)
    await db.commit()

    return SuccessResponse(
        data=ClientResponse(
            id=str(updated.id),
            organization_id=str(updated.organization_id),
            business_name=updated.business_name,
            primary_gstin=updated.primary_gstin,
            contact_name=updated.contact_name,
            contact_email=updated.contact_email,
            contact_phone=updated.contact_phone,
            state_code=updated.state_code,
            industry=updated.industry,
            address=updated.address,
            status=updated.status,
            is_demo=updated.is_demo,
            created_at=updated.created_at,
            updated_at=updated.updated_at
        ),
        message="Client updated successfully"
    )

@router.delete("/{client_id}", response_model=SuccessResponse[bool])
async def delete_client(
    client_id: str,
    current_user: User = Depends(require_accountant),
    db: AsyncSession = Depends(get_db)
):
    repo = ClientRepository(db)
    client = await repo.get_by_id(client_id)
    if not client or str(client.organization_id) != str(current_user.organization_id):
        raise HTTPException(status_code=404, detail="Client not found")

    await repo.delete(client_id)
    await db.commit()
    return SuccessResponse(data=True, message="Client deleted successfully")
