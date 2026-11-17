import pytest
from argon2 import Type, extract_parameters
from pydantic import ValidationError

from app.core.passwords import hash_password, verify_password
from app.schemas.auth import RegistrationRequest


def test_argon2id_uses_random_salts_and_verifies_without_trimming() -> None:
    password = "  a long passphrase  "
    first = hash_password(password)
    second = hash_password(password)
    parameters = extract_parameters(first)
    assert parameters.type is Type.ID
    assert parameters.memory_cost == 65536
    assert parameters.time_cost == 3
    assert first != second
    assert verify_password(password, first)
    assert not verify_password(password.strip(), first)
    assert not verify_password("wrong password", first)
    assert not verify_password(password, "not-a-hash")


def test_registration_contract_normalizes_email_and_hides_password() -> None:
    data = RegistrationRequest(
        email="  Person@EXAMPLE.com ", display_name=" Person ", password="a secure passphrase"
    )
    assert data.email == "person@example.com"
    assert data.display_name == "Person"
    assert "a secure passphrase" not in repr(data)


@pytest.mark.parametrize("password", ["short", "x" * 129])
def test_password_policy(password: str) -> None:
    with pytest.raises(ValidationError):
        RegistrationRequest(email="person@example.com", display_name="Person", password=password)
