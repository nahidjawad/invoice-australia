def test_login_redirect(client):
    response = client.get('/login/google')
    assert response.status_code == 302
    assert "accounts.google.com" in response.location
