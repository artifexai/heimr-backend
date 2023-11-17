import json

import pytest
from fastapi import Response
from fastapi.testclient import TestClient
from sqlalchemy import text

from api.dependencies import app_db, set_cookie
from main import app
from models.property import PropertyStruct
from security.encryption import hash_password
from utils.paths import get_root_directory
from utils.testing_helpers import load_testing_environment


@pytest.fixture(scope='session')
def testing_db():
    from database import build_session, Base

    load_testing_environment()

    with build_session() as sess:
        sess.execute(text('CREATE SCHEMA IF NOT EXISTS prod;'))
        sess.commit()
        Base.metadata.drop_all(sess.bind.engine)
        Base.metadata.create_all(sess.bind.engine)
    yield build_session


@pytest.fixture
def testing_client(testing_db):
    # testing cookies are not set https secure
    def _set_cookie():
        def func(response: Response, key: str, value: str):
            response.set_cookie(key=key, value=value, httponly=True, samesite="none")

        yield func

    with TestClient(app) as client:
        app.dependency_overrides[app_db] = testing_db
        app.dependency_overrides[set_cookie] = _set_cookie
        yield client


@pytest.fixture
def properties(testing_db):
    # These listings are guaranteed to have listings and tax records
    with open(f'{get_root_directory()}/_test_data_/properties.json', 'r') as f:
        data = json.load(f)
    parsed = [PropertyStruct.parse_obj(prop) for prop in data]
    db_records = [prop.to_orm_obj() for prop in parsed]
    with testing_db() as sess:
        for p in db_records:
            sess.merge(p)
        sess.commit()
    return db_records


@pytest.fixture
def admin_account(testing_db):
    from database import Account
    with testing_db() as sess:
        admin = Account()
        admin.email = 'test@email.com'
        admin.password = hash_password('test_password')
        sess.add(admin)
        sess.commit()
        yield admin


@pytest.fixture
def authenticated_client(admin_account, testing_client):
    response = testing_client.post('/auth/login', json={
        'email': admin_account.email,
        'password': 'test_password'
    })
    csrf = response.json().get('csrf')
    testing_client.headers.update({'X-CSRF-TOKEN': csrf})
    return testing_client
