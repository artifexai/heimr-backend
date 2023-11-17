from http.cookies import SimpleCookie, Morsel
from typing import List

from httpx import Headers

from security import decode_jwt


def test_login(admin_account, testing_client):
    response = testing_client.post('/auth/login', json={
        'email': admin_account.email,
        'password': 'test_password'
    })

    assert response.status_code == 200
    data = response.json()
    headers: Headers = response.headers
    cookies: List[str] = headers.get_list('set-cookie')
    at_cookie_str = [c for c in cookies if 'at=' in c][0]
    at_cookie: Morsel = SimpleCookie(at_cookie_str).get('at')
    at = at_cookie.value
    decoded = decode_jwt(at)

    # Assert that csrf is returned in the response and does not exist in the cookies
    assert 'csrf' in data
    assert 'csrf' not in cookies
    assert data['csrf'] and data['csrf'] == decoded['csrf']
    assert list(data.keys()) == ['message', 'csrf']
    assert at_cookie['httponly']

    response = testing_client.post('/auth/login', json={
        'email': admin_account.email,
        'password': 'bad_password'
    })

    assert response.status_code == 401
    assert not response.headers.get('set-cookie')
    assert not response.json().get('csrf')


def test_auth_flow(admin_account, testing_client):
    # Make sure the user is not logged in
    testing_client.cookies.clear()

    response = testing_client.post('/auth/login', json={
        'email': admin_account.email,
        'password': 'test_password'
    })
    assert response.status_code == 200
    assert testing_client.cookies.get('at')
    csrf = response.json().get('csrf')

    response = testing_client.get('/auth', headers={'X-CSRF-Token': csrf})
    assert response.status_code == 200
    assert response.json().get('logged_in') is True

    response = testing_client.get('/auth/logout')
    assert response.status_code == 200
    assert response.json().get('message') == 'success'
    assert testing_client.cookies.get('at') is None

    response = testing_client.get('/auth', headers={'X-CSRF-Token': csrf})
    assert response.status_code == 200
    assert response.json().get('logged_in') is False
