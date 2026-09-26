from password import get_password_hash, verify_password


def test_password_hash_is_not_plaintext():
    password = "WES350-test-password"
    hashed = get_password_hash(password)

    assert hashed != password


def test_correct_password_verifies():
    password = "WES350-test-password"
    hashed = get_password_hash(password)

    assert verify_password(password, hashed) is True


def test_wrong_password_does_not_verify():
    hashed = get_password_hash("correct-password")

    assert verify_password("wrong-password", hashed) is False
