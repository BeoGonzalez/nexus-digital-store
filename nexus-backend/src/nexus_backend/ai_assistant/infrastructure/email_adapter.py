"""Adaptador de infraestructura para envío de correos electrónicos vía Gmail / SMTP.

Utiliza la librería estándar de Python (smtplib, email) con soporte para
Contraseñas de Aplicación de Google (App Passwords) y ejecución asíncrona segura.
"""

from __future__ import annotations

import asyncio
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from nexus_backend.config import get_settings

logger = logging.getLogger(__name__)


class GmailEmailAdapter:
    """Adaptador de correo electrónico compatible con Google Gmail SMTP."""

    def __init__(
        self,
        smtp_user: str | None = None,
        smtp_password: str | None = None,
        smtp_host: str | None = None,
        smtp_port: int | None = None,
        from_name: str | None = None,
    ) -> None:
        settings = get_settings()
        self.smtp_user = (
            smtp_user
            or getattr(settings, "SMTP_USER", "")
            or getattr(settings, "GMAIL_USER", "")
        ).strip()
        self.smtp_password = (
            smtp_password
            or getattr(settings, "SMTP_PASSWORD", "")
            or getattr(settings, "GMAIL_APP_PASSWORD", "")
        ).strip().replace(" ", "")  # Eliminar espacios si la clave de Google fue pegada en bloques de 4
        self.smtp_host = smtp_host or getattr(settings, "SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = smtp_port or getattr(settings, "SMTP_PORT", 587)
        self.from_name = from_name or getattr(settings, "SMTP_FROM_NAME", "Nexus Digital Store 🎮")

    @property
    def is_configured(self) -> bool:
        """Indica si el adaptador tiene las credenciales mínimas configuradas."""
        return bool(self.smtp_user and self.smtp_password)

    def _build_html_template(self, recipient: str, subject: str, message_body: str) -> str:
        """Genera un correo HTML con diseño Gamer Dark moderno."""
        # Convertir saltos de línea a párrafos y listas HTML básicas
        formatted_content = message_body.replace("\n\n", "</p><p>").replace("\n", "<br/>")

        return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{subject}</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      background-color: #0b0f19;
      color: #e2e8f0;
      margin: 0;
      padding: 24px;
    }}
    .container {{
      max-width: 640px;
      margin: 0 auto;
      background: linear-gradient(180deg, #161e31 0%, #0f172a 100%);
      border: 1px solid #1e293b;
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 20px 40px rgba(0,0,0,0.6);
    }}
    .header {{
      background: linear-gradient(90deg, #0284c7 0%, #6366f1 50%, #a855f7 100%);
      padding: 24px 32px;
      text-align: center;
    }}
    .header h1 {{
      margin: 0;
      font-size: 24px;
      font-weight: 800;
      letter-spacing: -0.5px;
      color: #ffffff;
      text-transform: uppercase;
    }}
    .header p {{
      margin: 6px 0 0 0;
      color: rgba(255,255,255,0.85);
      font-size: 13px;
      letter-spacing: 1px;
    }}
    .badge {{
      display: inline-block;
      background: rgba(0,0,0,0.3);
      padding: 4px 12px;
      border-radius: 20px;
      font-size: 11px;
      color: #38bdf8;
      font-weight: bold;
      margin-top: 8px;
    }}
    .content {{
      padding: 32px;
      font-size: 15px;
      line-height: 1.7;
      color: #cbd5e1;
    }}
    .content p {{
      margin-bottom: 16px;
    }}
    .card-highlight {{
      background: rgba(14, 165, 233, 0.08);
      border-left: 4px solid #38bdf8;
      border-radius: 0 8px 8px 0;
      padding: 16px 20px;
      margin: 20px 0;
    }}
    .footer {{
      border-top: 1px solid #1e293b;
      padding: 24px 32px;
      text-align: center;
      font-size: 12px;
      color: #64748b;
      background: #090d16;
    }}
    .footer a {{
      color: #38bdf8;
      text-decoration: none;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>🎮 Nexus Digital Store</h1>
      <p>Asistente Gamer de Inteligencia Artificial (NexusBot)</p>
      <div class="badge">POWERED BY LAYA AI • GROQ • CHEAPSHARK • TAVILY</div>
    </div>
    <div class="content">
      <div class="card-highlight">
        <strong style="color: #38bdf8;">Hola Gamer:</strong>
        <p style="margin: 4px 0 0 0; font-size: 14px;">Aquí tienes la información y recomendaciones solicitadas desde nuestra plataforma.</p>
      </div>
      <div>
        <p>{formatted_content}</p>
      </div>
    </div>
    <div class="footer">
      <p>Este correo fue generado y enviado automáticamente por el asistente inteligente de <strong>Nexus Digital Store</strong>.</p>
      <p>© 2026 Nexus Digital Store • Santiago, Chile</p>
    </div>
  </div>
</body>
</html>"""

    def _send_sync(self, to_email: str, subject: str, content_html: str, content_text: str) -> dict[str, Any]:
        """Ejecuta el protocolo SMTP sincrónico en un hilo worker."""
        if not self.is_configured:
            error_msg = (
                "Credenciales de Gmail incompletas. Configura SMTP_USER y SMTP_PASSWORD "
                "(o GMAIL_USER y GMAIL_APP_PASSWORD) en tu archivo .env con tu Clave de Aplicación de Google."
            )
            logger.warning(error_msg)
            return {"success": False, "error": error_msg}

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.from_name} <{self.smtp_user}>"
        msg["To"] = to_email

        # Versión texto plano
        plain_part = MIMEText(content_text or content_html, "plain", "utf-8")
        msg.attach(plain_part)

        # Versión HTML enriquecida
        html_wrapper = self._build_html_template(to_email, subject, content_html)
        html_part = MIMEText(html_wrapper, "html", "utf-8")
        msg.attach(html_part)

        try:
            logger.info("Connecting to SMTP %s:%d via STARTTLS...", self.smtp_host, self.smtp_port)
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=15) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            success_msg = f"Correo enviado exitosamente a {to_email}"
            logger.info(success_msg)
            return {
                "success": True,
                "message": success_msg,
                "to_email": to_email,
                "subject": subject,
            }
        except smtplib.SMTPAuthenticationError as auth_err:
            error_detail = (
                f"Error de autenticación con Google SMTP ({auth_err.smtp_code}): "
                "Verifica que estés usando una 'Contraseña de Aplicaciones' de Google de 16 caracteres "
                "creada en https://myaccount.google.com/apppasswords (no tu contraseña habitual de Google)."
            )
            logger.error(error_detail)
            return {"success": False, "error": error_detail}
        except Exception as exc:
            error_detail = f"Fallo al enviar correo vía SMTP ({type(exc).__name__}): {exc}"
            logger.error(error_detail, exc_info=True)
            return {"success": False, "error": error_detail}

    async def send_email(
        self,
        to_email: str,
        subject: str,
        content_html: str,
        content_text: str = "",
    ) -> dict[str, Any]:
        """Envía un correo electrónico asincrónicamente delegando el bloqueo I/O a un thread."""
        return await asyncio.to_thread(
            self._send_sync,
            to_email=to_email,
            subject=subject,
            content_html=content_html,
            content_text=content_text,
        )

