# db/engagement_item_repo.py
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List

from db.connection import get_connection
from db.engagement_repo import recompute_engagement_total


@dataclass(frozen=True)
class EngagementItemRow:
    id_item: int
    engagement_id: int
    business_id: int
    item_name: str
    item_type: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal


def list_items(engagement_id: int) -> List[EngagementItemRow]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id_item,
                    engagement_id,
                    business_id,
                    item_name,
                    item_type,
                    quantity,
                    unit_price,
                    line_total
                FROM engagement_items
                WHERE engagement_id = %s
                ORDER BY id_item ASC
                """,
                (engagement_id,),
            )
            rows = cur.fetchall()

        out: List[EngagementItemRow] = []
        for r in rows:
            out.append(
                EngagementItemRow(
                    id_item=int(r[0]),
                    engagement_id=int(r[1]),
                    business_id=int(r[2]),
                    item_name=r[3] or "",
                    item_type=r[4] or "service",
                    quantity=int(r[5]) if r[5] is not None else 1,
                    unit_price=r[6] if r[6] is not None else Decimal("0.00"),
                    line_total=r[7] if r[7] is not None else Decimal("0.00"),
                )
            )
        return out
    finally:
        conn.close()


def create_item(
    engagement_id: int,
    business_id: int,
    item_name: str,
    item_type: str,
    quantity: int,
    unit_price: Decimal,
) -> int:
    item_name = (item_name or "").strip()
    if not item_name:
        raise ValueError("ITEM_NAME_REQUIRED")

    qty = int(quantity or 0)
    if qty <= 0:
        raise ValueError("ITEM_QUANTITY_INVALID")

    up = unit_price if isinstance(unit_price, Decimal) else Decimal(str(unit_price))
    line_total = (Decimal(qty) * up).quantize(Decimal("0.01"))

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO engagement_items (
                    engagement_id,
                    business_id,
                    item_name,
                    item_type,
                    quantity,
                    unit_price,
                    line_total,
                    created_at,
                    updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                RETURNING id_item
                """,
                (engagement_id, business_id, item_name, item_type, qty, up, line_total),
            )
            new_id = cur.fetchone()[0]

        #  commit avant recompute (sinon l'item n'est pas visible)
        conn.commit()

        # recompute total engagement (dans une autre connexion, OK maintenant)
        recompute_engagement_total(business_id, engagement_id)

        return int(new_id)
    finally:
        conn.close()


def update_item(engagement_id: int, id_item: int, data: Dict[str, Any]) -> bool:
    """
    data peut contenir : item_name, item_type, quantity, unit_price
    line_total est recalculé automatiquement.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT item_name, item_type, quantity, unit_price, business_id
                FROM engagement_items
                WHERE id_item = %s AND engagement_id = %s
                """,
                (id_item, engagement_id),
            )
            row = cur.fetchone()
            if not row:
                return False

            cur_name, cur_type, cur_qty, cur_up, business_id = row

            new_name = (data.get("item_name", cur_name) or "").strip()
            new_type = data.get("item_type", cur_type)
            new_qty = int(data.get("quantity", cur_qty) or 0)
            new_up = data.get("unit_price", cur_up)

            if not new_name:
                raise ValueError("ITEM_NAME_REQUIRED")
            if new_qty <= 0:
                raise ValueError("ITEM_QUANTITY_INVALID")

            new_up = new_up if isinstance(new_up, Decimal) else Decimal(str(new_up))
            new_line_total = (Decimal(new_qty) * new_up).quantize(Decimal("0.01"))

            cur.execute(
                """
                UPDATE engagement_items
                SET item_name = %s,
                    item_type = %s,
                    quantity = %s,
                    unit_price = %s,
                    line_total = %s,
                    updated_at = NOW()
                WHERE id_item = %s AND engagement_id = %s
                """,
                (new_name, new_type, new_qty, new_up, new_line_total, id_item, engagement_id),
            )
            ok = cur.rowcount > 0

        #  commit avant recompute
        conn.commit()

        if ok:
            recompute_engagement_total(int(business_id), engagement_id)

        return ok
    finally:
        conn.close()


def delete_item(engagement_id: int, id_item: int) -> bool:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT business_id
                FROM engagement_items
                WHERE id_item = %s AND engagement_id = %s
                """,
                (id_item, engagement_id),
            )
            row = cur.fetchone()
            if not row:
                return False
            business_id = int(row[0])

            cur.execute(
                """
                DELETE FROM engagement_items
                WHERE id_item = %s AND engagement_id = %s
                """,
                (id_item, engagement_id),
            )
            ok = cur.rowcount > 0

        #  commit avant recompute
        conn.commit()

        if ok:
            recompute_engagement_total(business_id, engagement_id)

        return ok
    finally:
        conn.close()
