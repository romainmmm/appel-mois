import auth


def test_hash_verify_roundtrip():
    h = auth.hash_password("secret123")
    assert auth.verify_password("secret123", h)
    assert not auth.verify_password("wrong", h)


def test_hash_is_salted():
    assert auth.hash_password("x") != auth.hash_password("x")  # random salt


def test_authenticate():
    users = {"gerant": {"hash": auth.hash_password("pw"), "role": "gerant"}}
    res = auth.authenticate(users, "gerant", "pw")
    assert res == {"username": "gerant", "role": "gerant"}
    assert auth.authenticate(users, "gerant", "bad") is None
    assert auth.authenticate(users, "unknown", "pw") is None
