"""
Ticket Routes - Now with advanced caching!
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from backend.database import get_db, CacheManager
from backend.models.tickets import TicketModel, TicketStatus, TicketPriority
from pydantic import BaseModel

router = APIRouter()


class TicketCreate(BaseModel):
    title: str
    description: str
    priority: TicketPriority


class TicketUpdate(BaseModel):
    title: str = None
    description: str = None
    status: TicketStatus = None
    priority: TicketPriority = None


class Ticket(BaseModel):
    id: str
    title: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- Service Layer --- 
# By moving the logic to a separate function, we can apply the decorator easily.

@CacheManager.cached(prefix="tickets_list", ttl=60)
async def get_tickets_service(skip: int, limit: int, db: Session) -> List[Ticket]:
    """Service function to get a list of tickets."""
    db_items = db.query(TicketModel).offset(skip).limit(limit).all()
    return [Ticket.from_orm(item) for item in db_items]

@CacheManager.cached(prefix="ticket_details", ttl=300)
async def get_ticket_by_id_service(ticket_id: str, db: Session) -> Ticket:
    """Service function to get a single ticket by its ID."""
    db_item = db.query(TicketModel).filter(TicketModel.id == ticket_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return Ticket.from_orm(db_item)


# --- API Routes --- 

@router.post("/tickets/", response_model=Ticket)
async def create_ticket(ticket: TicketCreate, db: Session = Depends(get_db)):
    db_ticket = TicketModel(**ticket.dict(), status=TicketStatus.OPEN)
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    # Invalidate caches that are now stale
    await CacheManager.clear_pattern("tickets_list:*")
    return Ticket.from_orm(db_ticket)


@router.get("/tickets/", response_model=List[Ticket])
async def read_tickets(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return await get_tickets_service(skip=skip, limit=limit, db=db)


@router.get("/tickets/{ticket_id}", response_model=Ticket)
async def read_ticket(ticket_id: str, db: Session = Depends(get_db)):
    return await get_ticket_by_id_service(ticket_id=ticket_id, db=db)


@router.put("/tickets/{ticket_id}", response_model=Ticket)
async def update_ticket(ticket_id: str, ticket: TicketUpdate, db: Session = Depends(get_db)):
    db_ticket = db.query(TicketModel).filter(TicketModel.id == ticket_id).first()
    if db_ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    update_data = ticket.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_ticket, key, value)

    db.commit()
    db.refresh(db_ticket)
    # Invalidate caches for both the list and the specific item
    await CacheManager.clear_pattern("tickets_list:*")
    await CacheManager.clear_pattern(f"ticket_details:get_ticket_by_id_service:{hash(json.dumps([ticket_id], sort_keys=True))}")
    return Ticket.from_orm(db_ticket)


@router.delete("/tickets/{ticket_id}", response_model=Ticket)
async def delete_ticket(ticket_id: str, db: Session = Depends(get_db)):
    db_ticket = db.query(TicketModel).filter(TicketModel.id == ticket_id).first()
    if db_ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    db.delete(db_ticket)
    db.commit()
    # Invalidate caches
    await CacheManager.clear_pattern("tickets_list:*")
    await CacheManager.clear_pattern(f"ticket_details:get_ticket_by_id_service:{hash(json.dumps([ticket_id], sort_keys=True))}")
    
    return Ticket.from_orm(db_ticket)
