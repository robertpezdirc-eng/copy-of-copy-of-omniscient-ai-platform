"""
Seed the database with sample tickets.
"""

import asyncio
from sqlalchemy.orm import sessionmaker
from backend.database import postgres_engine
from backend.models.tickets import TicketModel, TicketStatus, TicketPriority

async def seed_tickets():
    """Seed the database with sample tickets."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=postgres_engine)
    db = SessionLocal()

    try:
        tickets = [
            TicketModel(
                title="Fix login button",
                description="The login button on the main page is not working.",
                status=TicketStatus.OPEN,
                priority=TicketPriority.HIGH,
            ),
            TicketModel(
                title="Add a new feature",
                description="We need a new feature that does X, Y, and Z.",
                status=TicketStatus.IN_PROGRESS,
                priority=TicketPriority.MEDIUM,
            ),
            TicketModel(
                title="Change button color",
                description="The client wants to change the color of the button from blue to green.",
                status=TicketStatus.CLOSED,
                priority=TicketPriority.LOW,
            ),
        ]

        for ticket in tickets:
            db.add(ticket)
        
        db.commit()
        print("Successfully seeded tickets.")

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(seed_tickets())
