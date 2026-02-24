from __future__ import annotations
import csv
import os
import re
from datetime import date, datetime
from db.connection import get_connection


def _safe_name(name: str) -> str:
    # transforme le nom de la business en un nom de fichier valide
    name = name.strip().lower()
    namewithout_special = re.sub(r"[^\w\s-]", "", name)
    namewithout_spaces = re.sub(r"\s+", "_", namewithout_special) 
    return namewithout_spaces[:50]   or "business"  # limite à 50 chars


def _fmt_date(v) -> str:
    if v is None:
        return ""
    if isinstance(v, (date, datetime)):
        return v.strftime("%Y-%m-%d")
    return str(v)



def _fmt_decimal(v) -> str:
    # convertit un Decimal (ou None) en string avec 2 décimales
    if v is None:
        return ""
    try:
        return f"{float(v):.2f}"
    except Exception:
        return str(v)

def export_transactions_csv(business_id: int, business_name: str, folder_path: str) -> str:
    file_name = f"{_safe_name(business_name)}_transactions_{date.today()}.csv"
    file_path = os.path.join(folder_path, file_name)

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                 """
                SELECT
                    t.transaction_date,
                    t.transaction_type,
                    t.amount,
                    t.payment_method,
                    t.category,
                    NULLIF(TRIM(
                        COALESCE(c.first_name, '') || ' ' || COALESCE(c.last_name, '')
                    ), '')         AS full_name,
                    c.company_name,
                    t.description
                FROM transactions t
                LEFT JOIN clients c
                       ON c.id_client   = t.client_id
                      AND c.business_id = t.business_id
                WHERE t.business_id = %s
                ORDER BY t.transaction_date DESC, t.id_transaction DESC
                """,
                (business_id,),
            )
            rows = cur.fetchall()
    finally:
        conn.close()
        
    # utf-8-sig pour que les accents soient bien affichés
    with open(file_path,"w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "type", "amount", "payment_method", "category", "client_name", "client_company","description"])
        for r in rows:
            tx_date, tx_type, amount, payment_method, category, full_name, company, description = r
            client_name  = full_name or company or ""
            writer.writerow([
                _fmt_date(tx_date),
                tx_type or "",
                _fmt_decimal(amount),
                payment_method or "",
                category or "",
                client_name,
                company or "",
                description or ""
            ])
    return file_path

def export_clients_engagements_csv(business_id: int, business_name: str, folder_path: str) -> str:
    # un client sans engagement = 1 ligne avec colonnes engament vides (LEFT JOIN)
    file_name = f"{_safe_name(business_name)}_clients_engagements_{date.today()}.csv"
    file_path = os.path.join(folder_path, file_name)
    
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                 """
                SELECT
                    NULLIF(TRIM(
                        COALESCE(c.first_name, '') || ' ' || COALESCE(c.last_name, '')
                    ), '')         AS client_name,
                    c.company_name,
                    c.email,
                    c.phone,
                    e.title        AS engagement_title,
                    e.status,
                    e.total_amount,
                    e.start_date,
                    e.end_date
                FROM clients c
                LEFT JOIN engagements e
                       ON e.client_id   = c.id_client
                      AND e.business_id = c.business_id
                WHERE c.business_id = %s
                ORDER BY c.id_client DESC, e.id_engagement DESC
                """,
                (business_id,),
            )
            rows = cur.fetchall()
    finally:
        conn.close()
        
    with open(file_path,"w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "client_name", "company_name", "email", "phone",
            "engagement_title", "status", "total_amount", "start_date", "end_date",
        ])
        for r in rows:
            client_name, company_name, email, phone, engagement_title, status, total_amount, start_date, end_date = r
            writer.writerow([
                client_name or "",
                company_name or "",
                email or "",
                phone or "",
                engagement_title or "",
                status or "",
                _fmt_decimal(total_amount),
                _fmt_date(start_date),
                _fmt_date(end_date),
            ])
    return file_path