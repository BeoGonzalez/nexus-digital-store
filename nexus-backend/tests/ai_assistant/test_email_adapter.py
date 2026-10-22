import pytest
from unittest.mock import MagicMock, patch

from nexus_backend.ai_assistant.infrastructure.email_adapter import GmailEmailAdapter


@pytest.mark.asyncio
async def test_email_adapter_unconfigured():
    adapter = GmailEmailAdapter(smtp_user="", smtp_password="")
    assert not adapter.is_configured
    res = await adapter.send_email(
        to_email="gamer@example.com",
        subject="Test",
        content_html="Hola",
    )
    assert not res["success"]
    assert "incompletas" in res["error"]


@pytest.mark.asyncio
async def test_email_adapter_send_success():
    adapter = GmailEmailAdapter(
        smtp_user="nexus.store@gmail.com",
        smtp_password="abcd efgh ijkl mnop",
    )
    assert adapter.is_configured
    assert adapter.smtp_password == "abcdefghijklmnop"  # Limpieza de espacios

    with patch("smtplib.SMTP") as mock_smtp_cls:
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_server

        res = await adapter.send_email(
            to_email="cliente@gamer.com",
            subject="Cotización Elden Ring",
            content_html="Detalles de Elden Ring a $39.990 CLP",
        )

        assert res["success"] is True
        assert res["to_email"] == "cliente@gamer.com"
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("nexus.store@gmail.com", "abcdefghijklmnop")
        mock_server.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_email_adapter_auth_error():
    import smtplib

    adapter = GmailEmailAdapter(
        smtp_user="nexus.store@gmail.com",
        smtp_password="badpassword",
    )

    with patch("smtplib.SMTP") as mock_smtp_cls:
        mock_server = MagicMock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Authentication Failed")
        mock_smtp_cls.return_value.__enter__.return_value = mock_server

        res = await adapter.send_email(
            to_email="cliente@gamer.com",
            subject="Test Error",
            content_html="Mensaje",
        )

        assert res["success"] is False
        assert "Contraseña de Aplicaciones" in res["error"]

