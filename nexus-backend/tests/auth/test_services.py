import pytest
from unittest.mock import AsyncMock, MagicMock, call
import uuid
from typing import Any

from nexus_backend.auth.application.services import AuthService
from nexus_backend.auth.domain.entities import User
from nexus_backend.shared.domain.exceptions import BusinessRuleViolationException, UnauthorizedException


@pytest.fixture
def auth_service(
    mock_user_repo: AsyncMock,
    mock_password_hasher: MagicMock,
    mock_token_issuer: MagicMock,
) -> AuthService:
    return AuthService(
        user_repo=mock_user_repo,
        password_hasher=mock_password_hasher,
        token_issuer=mock_token_issuer,
    )


@pytest.mark.asyncio
async def test_register_success_validates_mutations_and_contract(
    auth_service: AuthService,
    mock_user_repo: AsyncMock,
    mock_password_hasher: MagicMock,
):
    # Arrange
    mock_user_repo.get_by_email.return_value = None
    # We want to capture the exact User object passed to the repository.
    mock_user_repo.create.side_effect = lambda u: u
    mock_password_hasher.hash.return_value = "strong_hashed_pwd"

    # Act
    result = await auth_service.register(
        email="sdet@nexus.com", password="P@ssw0rd123!", full_name="Principal SDET"
    )

    # Assert - Contract & State Mutations
    # 1. Spying: Exact parameters passed to dependencies
    mock_user_repo.get_by_email.assert_called_once_with("sdet@nexus.com")
    mock_password_hasher.hash.assert_called_once_with("P@ssw0rd123!")
    
    # 2. Spying: Capture the argument passed to repo.create
    assert mock_user_repo.create.call_count == 1
    call_args = mock_user_repo.create.call_args[0]
    user_passed_to_repo: User = call_args[0]
    
    # 3. State Mutation / Entity Integrity Verification
    assert isinstance(user_passed_to_repo.id, uuid.UUID), "Service must generate a valid UUID for new users"
    assert user_passed_to_repo.email == "sdet@nexus.com"
    assert user_passed_to_repo.hashed_password == "strong_hashed_pwd", "Service must store the hashed password, not the plain one"
    assert user_passed_to_repo.full_name == "Principal SDET"
    assert user_passed_to_repo.is_active is True, "New users must be active by default"
    
    # 4. Final Output Verification
    assert result == user_passed_to_repo


@pytest.mark.asyncio
async def test_register_duplicate_email_throws_domain_exception(
    auth_service: AuthService,
    mock_user_repo: AsyncMock,
    dummy_user: User,
):
    # Arrange
    # Simulating a user already exists in DB
    mock_user_repo.get_by_email.return_value = dummy_user

    # Act & Assert
    with pytest.raises(BusinessRuleViolationException, match="Email already registered") as exc_info:
        await auth_service.register(
            email=dummy_user.email, password="password", full_name="Copycat"
        )
    
    assert isinstance(exc_info.value, BusinessRuleViolationException)
    
    # Contract Verification: ensure repo.create is NEVER called if validation fails
    mock_user_repo.create.assert_not_called()


@pytest.mark.asyncio
async def test_authenticate_success_validates_contract(
    auth_service: AuthService,
    mock_user_repo: AsyncMock,
    mock_password_hasher: MagicMock,
    mock_token_issuer: MagicMock,
    dummy_user: User,
):
    # Arrange
    dummy_user.hashed_password = "db_hash_123"
    mock_user_repo.get_by_email.return_value = dummy_user
    mock_password_hasher.verify.return_value = True
    mock_token_issuer.issue.return_value = "jwt.token.sig"

    # Act
    token = await auth_service.authenticate(email=dummy_user.email, password="PlainPassword123")

    # Assert
    # 1. Spying: Exact lookup parameter
    mock_user_repo.get_by_email.assert_called_once_with(dummy_user.email)
    
    # 2. Spying: Ensure password verifier gets exactly the plain pass and the DB hash
    mock_password_hasher.verify.assert_called_once_with("PlainPassword123", "db_hash_123")
    
    # 3. Spying: Token is issued exactly for the User ID
    mock_token_issuer.issue.assert_called_once_with(str(dummy_user.id))
    
    assert token == "jwt.token.sig"


@pytest.mark.asyncio
async def test_authenticate_invalid_password_throws_unauthorized(
    auth_service: AuthService,
    mock_user_repo: AsyncMock,
    mock_password_hasher: MagicMock,
    mock_token_issuer: MagicMock,
    dummy_user: User,
):
    # Arrange
    mock_user_repo.get_by_email.return_value = dummy_user
    mock_password_hasher.verify.return_value = False  # Password mismatch

    # Act & Assert
    with pytest.raises(UnauthorizedException, match="Invalid credentials"):
        await auth_service.authenticate(email=dummy_user.email, password="wrong_password")
        
    # Verify exact parameters sent to hasher
    mock_password_hasher.verify.assert_called_once_with("wrong_password", dummy_user.hashed_password)
    # Ensure token is never issued
    mock_token_issuer.issue.assert_not_called()


@pytest.mark.asyncio
async def test_authenticate_user_not_found_throws_unauthorized(
    auth_service: AuthService,
    mock_user_repo: AsyncMock,
    mock_password_hasher: MagicMock,
):
    # Arrange
    mock_user_repo.get_by_email.return_value = None  # DB returns nothing

    # Act & Assert
    with pytest.raises(UnauthorizedException, match="Invalid credentials"):
        await auth_service.authenticate(email="ghost@nexus.com", password="password123")
        
    mock_password_hasher.verify.assert_not_called()


@pytest.mark.asyncio
async def test_authenticate_inactive_user_throws_unauthorized(
    auth_service: AuthService,
    mock_user_repo: AsyncMock,
    mock_token_issuer: MagicMock,
    dummy_user: User,
):
    # Arrange
    dummy_user.is_active = False
    mock_user_repo.get_by_email.return_value = dummy_user

    # Act & Assert
    with pytest.raises(UnauthorizedException, match="Account deactivated"):
        await auth_service.authenticate(email=dummy_user.email, password="password123")
        
    mock_token_issuer.issue.assert_not_called()
