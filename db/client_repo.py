# db/client_repo.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from db.connection import get_connection


@dataclass(frozen=True)
class ClientRow:
    id_client: int
    business_id: int
    first_name: Optional[str]
    last_name: Optional[str]
    company_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    is_active: bool


def list_clients(business_id: int) -> List[ClientRow]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id_client, business_id, first_name, last_name, company_name, email, phone, is_active
                FROM clients
                WHERE business_id = %s
                ORDER BY id_client DESC
                """,
                (business_id,),
            )
            rows = cur.fetchall()

        return [
            ClientRow(
                id_client=r[0],
                business_id=r[1],
                first_name=r[2],
                last_name=r[3],
                company_name=r[4],
                email=r[5],
                phone=r[6],
                is_active=r[7],
            )
            for r in rows
        ]
    finally:
        conn.close()


def create_client(
    business_id: int,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    company_name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    is_active: bool = True,
) -> int:
    # Minimum: at least one of (company_name) or (first_name/last_name)
    if not (company_name or first_name or last_name):
        raise ValueError("CLIENT_NAME_REQUIRED")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO clients
                    (business_id, first_name, last_name, company_name, email, phone, is_active, created_at, updated_at)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                RETURNING id_client
                """,
                (business_id, first_name, last_name, company_name, email, phone, is_active),
            )
            new_id = cur.fetchone()[0]
        conn.commit()
        return int(new_id)
    finally:
        conn.close()


def update_client(business_id: int, id_client: int, data: dict) -> None:
    allowed = {"first_name", "last_name", "company_name", "email", "phone", "is_active"}
    fields = {k: v for k, v in data.items() if k in allowed}
    if not fields:
        return

    set_sql = ", ".join([f"{k} = %s" for k in fields.keys()])
    values = list(fields.values())

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE clients
                SET {set_sql}, updated_at = NOW()
                WHERE id_client = %s AND business_id = %s
                """,
                (*values, id_client, business_id),
            )
        conn.commit()
    finally:
        conn.close()


def delete_client(business_id: int, id_client: int) -> bool:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM clients
                WHERE id_client = %s AND business_id = %s
                """,
                (id_client, business_id),
            )
            ok = cur.rowcount > 0
        conn.commit()
        return ok
    finally:
        conn.close()
