"""Pruebas unitarias para la entidad de dominio User (Reglas de negocio e invariantes)."""

from uuid import uuid4
import pytest

from nexus_backend.auth.domain.entities import User


class TestUserDomainEntity:
    """Suite de validación de invariantes de negocio de la entidad User."""

    @pytest.mark.parametrize(
        ("role_input", "expected_is_admin"),
        [
            ("admin", True),
            ("ADMIN", True),
            (" Admin ", True),
            ("administrator", False),
            ("user", False),
            ("customer", False),
            ("", False),
            (None, False),
        ],
    )
    def test_is_admin_property_evaluates_strictly(
        self, role_input: str | None, expected_is_admin: bool
    ) -> None:
        # Arrange
        user = User(id=uuid4(), name="Test Subject", email="test@nexus.cl", role=role_input)  # type: ignore[arg-type]

        # Act
        is_admin_result = user.is_admin

        # Assert
        # Regla de negocio: Solo los roles equivalentes a 'admin' (case-insensitive)
        # deben otorgar privilegios administrativos, protegiendo las mutaciones del catálogo.
        assert is_admin_result is expected_is_admin

    @pytest.mark.parametrize(
        ("banned_flag", "expected_is_active"),
        [
            (False, True),
            (True, False),
        ],
    )
    def test_is_active_inverts_banned_state_faithfully(
        self, banned_flag: bool, expected_is_active: bool
    ) -> None:
        # Arrange
        user = User(
            id=uuid4(),
            name="State Subject",
            email="state@nexus.cl",
            banned=banned_flag,
        )

        # Act
        is_active_result = user.is_active

        # Assert
        # Regla de negocio: Un usuario baneado por Neon Auth nunca debe considerarse activo
        # ni debe permitírsele interactuar con órdenes o catálogo.
        assert is_active_result is expected_is_active
