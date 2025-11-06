"""
Ticket Routes
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.database import get_db
from backend.models.tickets import TicketModel, TicketStatus, TicketPriority
from pydantic import BaseModel, Field
from datetime import datetime

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


@router.post("/tickets/", response_model=Ticket)
def create_ticket(ticket: TicketCreate, db: Session = Depends(get_db)):
    db_ticket = TicketModel(**ticket.dict(), status=TicketStatus.OPEN)
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


@router.get("/tickets/", response_model=List[Ticket])
def read_tickets(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(TicketModel).offset(skip).limit(limit).all()


@router.get("/tickets/{ticket_id}", response_model=Ticket)
def read_ticket(ticket_id: str, db: Session = Depends(get_db)):
    db_ticket = db.query(TicketModel).filter(TicketModel.id == ticket_id).first()
    if db_ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return db_ticket


@router.put("/tickets/{ticket_id}", response_model=Ticket)
def update_ticket(ticket_id: str, ticket: TicketUpdate, db: Session = Depends(get_db)):
    db_ticket = db.query(TicketModel).filter(TicketModel.id == ticket_id).first()
    if db_ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    for var, value in vars(ticket).items():
        if value is not None:
            setattr(db_ticket, var, value)

    db.commit()
    db.refresh(db_ticket)
    return db_ticket


@router.delete("/tickets/{ticket_id}", response_model=Ticket)
def delete_ticket(ticket_id: str, db: Session = Depends(get_db)):
    db_ticket = db.query(TicketModel).filter(TicketModel.id == ticket_id).first()
    if db_ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    db.delete(db_ticket)
    db.commit()
    return db_ticket
