import json
import os

import bcrypt
from cryptography.fernet import Fernet


def encrypt_str(string: str) -> bytes:
    sk = os.getenv("AUTH_KEY")
    aus = os.getenv("AUTH_SALT")
    if not sk or not aus:
        raise ValueError("KEY and SALT are required for encryption")

    data = {'string': string, 'salt': aus}
    as_bytes = json.dumps(data).encode('utf-8')
    f = Fernet(sk)
    return f.encrypt(as_bytes)


def decrypt_str(data: bytes) -> str:
    sk = os.getenv("AUTH_KEY")
    aus = os.getenv("AUTH_SALT")
    if not sk or not aus:
        raise ValueError("KEY and SALT are required for decryption")
    f = Fernet(sk)
    decrypted = f.decrypt(data)
    as_str = decrypted.decode('utf-8')
    data = json.loads(as_str)
    salt = data.pop('salt')
    string = data.pop('string')
    if salt or salt != aus:
        raise ValueError("Invalid salt")
    if not string:
        raise ValueError("Invalid string")
    return string


def hash_password(pw: str) -> str:
    hashed = bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')


def verify_password(stored_password: str, provided_password: str) -> bool:
    return bcrypt.checkpw(
        provided_password.encode('utf-8'),
        stored_password.encode('utf-8')
    )
