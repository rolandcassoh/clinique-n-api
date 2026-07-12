import hashlib
import bcrypt


def _prepare_password(plain: str) -> bytes:
    """
    Prépare le mot de passe pour bcrypt en utilisant SHA256.
    Cela permet d'accepter des mots de passe de n'importe quelle longueur.
    """
    return hashlib.sha256(plain.encode('utf-8')).digest()


def hash_password(plain: str) -> str:
    """Hash un mot de passe avec bcrypt via SHA256."""
    prepared = _prepare_password(plain)
    hashed = bcrypt.hashpw(prepared, bcrypt.gensalt())
    return hashed.decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    """Vérifie un mot de passe contre son hash bcrypt."""
    prepared = _prepare_password(plain)
    try:
        return bcrypt.checkpw(prepared, hashed.encode('utf-8'))
    except Exception:
        return False
