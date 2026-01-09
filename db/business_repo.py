"""
KAIROS Owner Desktop - Repository pour la gestion des entreprises
"""

from __future__ import annotations
from    dataclasses import dataclass
from typing      import List, Optional

from db.connection import get_connection

@dataclass(frozen=True)
class BusinessRow:
    id_business: int
    owner_id: int
    name: str
    business_type: Optional[str]
    city: Optional[str]
    country: Optional[str]
    currency: str
    timezone: str
    is_active: bool


def list_businesses(owner_id: int) -> List[BusinessRow]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                 """
                SELECT id_business, owner_id, name, business_type, city, country,
                       currency, timezone, is_active
                FROM businesses
                WHERE owner_id = %s
                ORDER BY id_business DESC
                """,
                (owner_id,),
            )
            rows = cur.fetchall()
        return [
            BusinessRow(
                id_business=row[0],
                owner_id=row[1],
                name=row[2],
                business_type=row[3],
                city=row[4],
                country=row[5],
                currency=row[6],
                timezone=row[7],
                is_active=row[8],
            )
            for row in rows
        ]
    finally:
        conn.close()
        
def update_business(owner_id: int, id_business: int, data: dict) -> None:
    """
    Met à jour les informations d'une entreprise.
    
    Args:
        owner_id (int): L'ID du propriétaire de l'entreprise.
        id_business (int): L'ID de l'entreprise à mettre à jour.
        data (dict): Un dictionnaire contenant les champs à mettre à jour.
    """
    allowed = {"name", "business_type", "city", "country", "currency", "timezone", "is_active"}
    fields = {k: v for k, v in data.items() if k in allowed}
    
    if not fields:
        return  # Rien à mettre à jour
    set_sql = ", ".join(f"{k} = %s" for k in fields.keys())
    values = list(fields.values()) 
    
    
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                 f"""
                UPDATE businesses
                SET {set_sql}
                WHERE id_business = %s AND owner_id = %s
                """,
                (*values, id_business, owner_id),
            )
        conn.commit()
    finally:
        conn.close()
        
def create_business(
    owner_id: int,
    name: str,
    business_type: Optional[str] = None,
    city: Optional[str] = None,
    country: Optional[str] = None,
    currency: str = "CAD",
    timezone: str = "America/Montreal",
    is_active: bool = True,
) -> int:
    """
    Create a business for this owner and return the new id_business.
    """
    name = (name or "").strip()
    if not name:
        raise ValueError("NAME_REQUIRED")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO businesses
                    (owner_id, name, business_type, city, country, currency, timezone, is_active, created_at, updated_at)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                RETURNING id_business
                """,
                (owner_id, name, business_type, city, country, currency, timezone, is_active),
            )
            new_id = cur.fetchone()[0]
        conn.commit()
        return int(new_id)
    finally:
        conn.close()


def delete_business(owner_id: int, id_business: int) -> bool:
    """
    Delete a business only if it belongs to owner_id.
    Returns True if deleted, False if not found/not owned.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM businesses
                WHERE id_business = %s AND owner_id = %s
                """,
                (id_business, owner_id),
            )
            deleted = cur.rowcount > 0
        conn.commit()
        return deleted
    finally:
        conn.close()