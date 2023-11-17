import os

from dotenv import load_dotenv

from database import Account, build_session
from security.encryption import hash_password

if __name__ == '__main__':
    load_dotenv()
    email = os.getenv('ADMIN_EMAIL')
    password = os.getenv('ADMIN_PASSWORD')
    if not email or not password:
        raise ValueError("ADMIN_EMAIL and ADMIN_PASSWORD are required for seeding")
    hashed_pw = hash_password(password)
    admin = Account()
    admin.email = email
    admin.password = hashed_pw

    with build_session() as sess:
        sess.add(admin)
        sess.commit()
