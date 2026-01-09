# db/auth_repo.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import bcrypt

from db.connection import get_connection


@dataclass(frozen=True)
class AuthUser:
    id_user: int
    email: str
    role: str
    is_active: bool
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class AuthError(Exception):
    """Raised when authentication fails."""


def authenticate(email: str, password: str) -> AuthUser:
    """
    Authentifie un utilisateur avec son email et son mot de passe (bcrypt).

    Règles:
    - L'utilisateur doit exister
    - Le compte doit être actif (is_active = true)
    - Le mot de passe doit matcher password_hash (bcrypt)
    """
    email = (email or "").strip().lower()
    password = password or ""

    if not email or not password:
        raise AuthError("EMAIL_AND_PASSWORD_REQUIRED")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id_user, email, password_hash, role, is_active, first_name, last_name
                FROM users
                WHERE email = %s
                LIMIT 1
                """,
                (email,),
            )
            row = cur.fetchone()

        if not row:
            # Message volontairement vague pour éviter d’indiquer si l’email existe
            raise AuthError("INVALID_CREDENTIALS")

        (
            id_user,
            db_email,
            password_hash,
            role,
            is_active,
            first_name,
            last_name,
        ) = row

        if not is_active:
            raise AuthError("USER_INACTIVE")

        # password_hash de la DB peut être str ou bytes
        if isinstance(password_hash, str):
            password_hash_bytes = password_hash.encode("utf-8")
        else:
            password_hash_bytes = password_hash

        ok = bcrypt.checkpw(password.encode("utf-8"), password_hash_bytes)
        if not ok:
            raise AuthError("INVALID_CREDENTIALS")

        return AuthUser(
            id_user=int(id_user),
            email=str(db_email),
            role=str(role),
            is_active=bool(is_active),
            first_name=first_name,
            last_name=last_name,
        )
    finally:
        conn.close()


def _test_auth() -> None:
    """
    Test manuel:
    - demande email/password
    - affiche le résultat
    """
    import getpass

    print("== Owner Desktop Auth Test ==")
    email = input("Email: ").strip()
    password = getpass.getpass("Password: ")

    try:
        user = authenticate(email, password)
        full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        print("✅ Auth OK:", user)
        if full_name:
            print("👤 Full name:", full_name)
    except AuthError as e:
        print("❌ Auth FAILED:", str(e))
    except Exception as e:
        print("❌ Unexpected error:", e)


if __name__ == "__main__":
    _test_auth()
