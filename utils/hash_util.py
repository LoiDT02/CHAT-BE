from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
argon2_hasher = PasswordHasher()

def get_hash_scheme(hashed_password: str) -> str | None:
    return pwd_context.identify(hashed_password)


def hash_password(password: str):
    return argon2_hasher.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    scheme = get_hash_scheme(hashed_password=hashed_password)

    try:
        if scheme == "bcrypt":
            return pwd_context.verify(password, hashed_password)
        return argon2_hasher.verify(hashed_password, password)
    except (VerifyMismatchError, ValueError) as e:
        return False
    except Exception:
        return False
