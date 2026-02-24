from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from db.connection import get_connection

@dataclass(frozen=True)
class TransactionRow:
    id_transaction:   int
    business_id:      int
    client_id:        Optional[int]
    engagement_id:    Optional[int]
    transaction_type: str           # 'income' ou 'expense'
    category:         Optional[str]
    amount:           Decimal
    payment_method:   Optional[str] # 'cash' | 'card' | 'transfer' | 'check' | 'other'
    reference_number: Optional[str]
    description:      Optional[str]
    transaction_date: datetime
    
    
@dataclass(frozen=True)
class StatsResult:
    total_income:  Decimal
    total_expense: Decimal
    balance:       Decimal
    # [(year, month, total_income, total_expense), ...]
    monthly:       List[tuple]
    # [(category_label, transaction_type, total), ...]
    by_category:   List[tuple]



def list_transactions(
    business_id: int,
    type_filter: Optional[str] = None,
) -> List[TransactionRow]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id_transaction, business_id, client_id, engagement_id,
                    transaction_type, category, amount, payment_method,
                    reference_number, description, transaction_date
                FROM transactions
                WHERE business_id = %s
                  AND (%s IS NULL OR transaction_type = %s)
                ORDER BY transaction_date DESC, id_transaction DESC
                """,
                (business_id, type_filter, type_filter),
            )
            rows = cur.fetchall()

        out: List[TransactionRow] = []
        for r in rows:
            out.append(TransactionRow(
                id_transaction=int(r[0]),
                business_id=int(r[1]),
                client_id=int(r[2]) if r[2] is not None else None,
                engagement_id=int(r[3]) if r[3] is not None else None,
                transaction_type=r[4],
                category=r[5],
                amount=r[6] if isinstance(r[6], Decimal) else Decimal(str(r[6])), # protege contre les type innatendus venant de la base de données
                payment_method=r[7],
                reference_number=r[8],
                description=r[9],
                transaction_date=r[10],
            ))
        return out
    finally:
        conn.close()
       

def create_transaction(
    business_id: int,
    transaction_type: str,
    amount: Decimal,
    client_id: Optional[int] = None,
    engagement_id: Optional[int] = None,
    category: Optional[str] = None,
    payment_method: Optional[str] = None,
    reference_number: Optional[str] = None,
    description: Optional[str] = None,
    transaction_date: Optional[datetime] = None,
) -> int:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO transactions (
                    business_id, client_id, engagement_id, transaction_type, category, amount, payment_method, reference_number, description, transaction_date
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, COALESCE(%s, NOW()))
                RETURNING id_transaction
                """,
                (
                    business_id,
                    client_id,
                    engagement_id,
                    transaction_type,
                    category,
                    amount,
                    payment_method,
                    reference_number,
                    description,
                    transaction_date,
                ),
            )
            new_id = cur.fetchone()[0]
            conn.commit()
            return new_id
    finally:
        conn.close()


def update_transaction(
    business_id:    int,
    id_transaction: int,
    data:           Dict[str, Any],
) -> bool:
    allowed = {
        "transaction_type", "category", "amount", "payment_method",
        "reference_number", "description", "transaction_date",
        "client_id", "engagement_id",
    }
    sets = []
    params = []

    for k in allowed:
        if k in data:
            sets.append(f"{k} = %s")
            params.append(data[k])

    if not sets:
        return False

    sets.append("updated_at = NOW()")
    params.extend([id_transaction, business_id])

    sql = f"""
        UPDATE transactions
        SET {", ".join(sets)}
        WHERE id_transaction = %s AND business_id = %s
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


def delete_transaction(business_id: int, id_transaction: int) -> bool:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM transactions
                WHERE id_transaction = %s AND business_id = %s
                """,
                (id_transaction, business_id),
            )
            ok = cur.rowcount > 0
        conn.commit()
        return ok
    finally:
        conn.close()
        
def get_stats(business_id: int) -> StatsResult:
    """Retourne les stats agrégées pour l'onglet stats"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Totaux globaux
            cur.execute(
                """
                SELECT
                    COALESCE(SUM(CASE WHEN transaction_type = 'income'  THEN amount ELSE 0 END), 0),
                    COALESCE(SUM(CASE WHEN transaction_type = 'expense' THEN amount ELSE 0 END), 0)
                FROM transactions
                WHERE business_id = %s
                """, 
                (business_id,),
            )
            row = cur.fetchone()
            total_income  = row[0] if isinstance(row[0], Decimal) else Decimal(str(row[0]))
            total_expense = row[1] if isinstance(row[1], Decimal) else Decimal(str(row[1]))
            balance = total_income - total_expense
            
            # revenus et dépenses par mois (12 derniers)
            cur.execute(
                """
                SELECT
                    EXTRACT(YEAR FROM transaction_date)::INT AS yr,
                    EXTRACT(MONTH FROM transaction_date)::INT AS mo,
                    COALESCE(SUM(CASE WHEN transaction_type = 'income'  THEN amount ELSE 0 END), 0),
                    COALESCE(SUM(CASE WHEN transaction_type = 'expense' THEN amount ELSE 0 END), 0)
                FROM transactions
                WHERE business_id = %s
                  AND transaction_date >= NOW() - INTERVAL '12 months'
                GROUP BY yr, mo
                ORDER BY yr , mo
                """, 
                (business_id,),
            )
            monthly = []
            for r in cur.fetchall():
                monthly.append((int(r[0]), int(r[1]), 
                    r[2] if isinstance(r[2], Decimal) else Decimal(str(r[2])),
                    r[3] if isinstance(r[3], Decimal) else Decimal(str(r[3]))))
            
            # totaux par catégorie (top 20)
            cur.execute(
                """
                SELECT
                    COALESCE(category, 'Sans catégorie') AS cat,
                    transaction_type,
                    SUM(amount) AS total
                FROM transactions
                WHERE business_id = %s
                GROUP BY cat, transaction_type
                ORDER BY total DESC
                LIMIT 20
                """,
                (business_id,),
            )
            by_category = []
            for r in cur.fetchall():
                by_category.append((r[0], r[1], 
                    r[2] if isinstance(r[2], Decimal) else Decimal(str(r[2]))))
            
            return StatsResult(
                total_income=total_income,
                total_expense=total_expense,
                balance=balance,
                monthly=monthly,
                by_category=by_category,
            )
    finally:        
        conn.close()
            
                
            
 
def get_balance(business_id: int) -> Decimal:
    """Retourne revenus - dépenses pour la business. Toujours >= 0 n'est pas garanti."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    COALESCE(SUM(CASE WHEN transaction_type = 'income'  THEN amount ELSE 0 END), 0),
                    COALESCE(SUM(CASE WHEN transaction_type = 'expense' THEN amount ELSE 0 END), 0)
                FROM transactions
                WHERE business_id = %s
                """,
                (business_id,),
            )
            row = cur.fetchone()
        income  = row[0] if isinstance(row[0], Decimal) else Decimal(str(row[0]))
        expense = row[1] if isinstance(row[1], Decimal) else Decimal(str(row[1]))
        return income - expense
    finally:
        conn.close()


