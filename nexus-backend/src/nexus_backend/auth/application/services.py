from nexus_backend.auth.domain.entities import User
from nexus_backend.auth.domain.ports import PasswordHasherPort, TokenIssuerPort, UserRepository
from nexus_backend.shared.domain.exceptions import BusinessRuleViolationException, UnauthorizedException


class AuthService:
    def __init__(
        self,
        user_repo: UserRepository,
        password_hasher: PasswordHasherPort,
        token_issuer: TokenIssuerPort,
    ) -> None:
        self._user_repo = user_repo
        self._password_hasher = password_hasher
        self._token_issuer = token_issuer

    async def register(self, email: str, password: str, full_name: str) -> User:
        existing = await self._user_repo.get_by_email(email)
        if existing:
            raise BusinessRuleViolationException("Email already registered")

        user = User(
            email=email,
            hashed_password=self._password_hasher.hash(password),
            full_name=full_name,
        )
        return await self._user_repo.create(user)

    async def authenticate(self, email: str, password: str) -> str:
        user = await self._user_repo.get_by_email(email)
        if not user or not self._password_hasher.verify(password, user.hashed_password):
            raise UnauthorizedException("Invalid credentials")
        if not user.is_active:
            raise UnauthorizedException("Account deactivated")
        return self._token_issuer.issue(str(user.id))
