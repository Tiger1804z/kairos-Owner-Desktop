# db/engagement_repo.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from db.connection import get_connection


@dataclass(frozen=True)
class EngagementRow:
    id_engagement: int
    business_id: int
    client_id: Optional[int]
    title: str
    description: Optional[str]
    status: str
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    total_amount: Optional[Decimal]


def list_engagements(business_id: int, client_id: int | None = None) -> List[EngagementRow]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id_engagement,
                    business_id,
                    client_id,
                    title,
                    description,
                    status,
                    start_date,
                    end_date,
                    total_amount
                FROM engagements
                WHERE business_id = %s
                  AND (%s IS NULL OR client_id = %s)
                ORDER BY id_engagement DESC
                """,
                (business_id, client_id, client_id),
            )
            rows = cur.fetchall()

        out: List[EngagementRow] = []
        for r in rows:
            out.append(
                EngagementRow(
                    id_engagement=int(r[0]),
                    business_id=int(r[1]),
                    client_id=int(r[2]) if r[2] is not None else None,
                    title=r[3] or "",
                    description=r[4],
                    status=r[5] or "draft",
                    start_date=r[6],
                    end_date=r[7],
                    total_amount=r[8],
                )
            )
        return out
    finally:
        conn.close()


def create_engagement(
    business_id: int,
    title: str,
    status: str = "draft",
    description: Optional[str] = None,
    client_id: Optional[int] = None,
    start_date=None,
    end_date=None,
    total_amount: Optional[Decimal] = None,
) -> int:
    title = (title or "").strip()
    if not title:
        raise ValueError("ENGAGEMENT_TITLE_REQUIRED")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO engagements (
                    business_id,
                    client_id,
                    title,
                    description,
                    status,
                    start_date,
                    end_date,
                    total_amount,
                    created_at,
                    updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                RETURNING id_engagement
                """,
                (
                    business_id,
                    client_id,
                    title,
                    description,
                    status or "draft",
                    start_date,
                    end_date,
                    total_amount,
                ),
            )
            new_id = cur.fetchone()[0]
        conn.commit()
        return int(new_id)
    finally:
        conn.close()


def update_engagement(business_id: int, id_engagement: int, data: Dict[str, Any]) -> bool:
    """
    data peut contenir : title, description, status, client_id, start_date, end_date, total_amount
    """
    allowed = {"title", "description", "status", "client_id", "start_date", "end_date", "total_amount"}
    sets = []
    params = []

    for k in allowed:
        if k in data:
            sets.append(f"{k} = %s")
            params.append(data[k])

    if not sets:
        return False

    sets.append("updated_at = NOW()")

    params.extend([id_engagement, business_id])

    sql = f"""
        UPDATE engagements
        SET {", ".join(sets)}
        WHERE id_engagement = %s AND business_id = %s
    """

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            ok = cur.rowcount > 0
        conn.commit()
        return ok
    finally:
        conn.close()


def delete_engagement(business_id: int, id_engagement: int) -> bool:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM engagements
                WHERE id_engagement = %s AND business_id = %s
                """,
                (id_engagement, business_id),
            )
            ok = cur.rowcount > 0
        conn.commit()
        return ok
    finally:
        conn.close()


def recompute_engagement_total(business_id: int, id_engagement: int) -> Decimal:
    """
    Recalcule total_amount = SUM(line_total) des items liés à l'engagement.
    - Toujours conforme au schema: engagements.total_amount
    - Met aussi updated_at = NOW()
    - Retourne le total (Decimal)
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Somme sécurisée (on force le business via la table engagements)
            cur.execute(
                """
                SELECT COALESCE(SUM(ei.line_total), 0)
                FROM engagement_items ei
                JOIN engagements e ON e.id_engagement = ei.engagement_id
                WHERE e.id_engagement = %s
                  AND e.business_id = %s
                """,
                (id_engagement, business_id),
            )
            total = cur.fetchone()[0]
            if total is None:
                total = Decimal("0.00")

            # Update engagement total + updated_at
            cur.execute(
                """
                UPDATE engagements
                SET total_amount = %s,
                    updated_at = NOW()
                WHERE id_engagement = %s
                  AND business_id = %s
                """,
                (total, id_engagement, business_id),
            )

        conn.commit()
        return total if isinstance(total, Decimal) else Decimal(str(total))
    finally:
        conn.close()



