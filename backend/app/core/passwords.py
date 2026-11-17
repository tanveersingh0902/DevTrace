"""Password hashing policy; callers must never log passwords or encoded hashes."""

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from argon2.profiles import RFC_9106_LOW_MEMORY

# Explicit Argon2id profile: 64 MiB, three iterations, four lanes, random salt.
_hasher = PasswordHasher.from_parameters(RFC_9106_LOW_MEMORY)


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, encoded_hash: str) -> bool:
    try:
        return _hasher.verify(encoded_hash, password)
    except (VerificationError, InvalidHashError):
        return False
