"""Adaptador de infraestructura para envío de correos electrónicos vía Gmail / SMTP.

Utiliza la librería estándar de Python (smtplib, email) con soporte para
Contraseñas de Aplicación de Google (App Passwords) y ejecución asíncrona segura.
"""

from __future__ import annotations

import asyncio
import logging
import re
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
        user = smtp_user if smtp_user is not None else (
            getattr(settings, "SMTP_USER", "")
            or getattr(settings, "GMAIL_USER", "")
        )
        self.smtp_user = user.strip()

        pwd = smtp_password if smtp_password is not None else (
            getattr(settings, "SMTP_PASSWORD", "")
            or getattr(settings, "GMAIL_APP_PASSWORD", "")
        )
        self.smtp_password = pwd.strip().replace(" ", "")  # Eliminar espacios si la clave de Google fue pegada en bloques de 4
        self.smtp_host = smtp_host or getattr(settings, "SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = smtp_port or getattr(settings, "SMTP_PORT", 587)
        self.from_name = from_name or getattr(settings, "SMTP_FROM_NAME", "Nexus Digital Store 🎮")

    @property
    def is_configured(self) -> bool:
        """Indica si el adaptador tiene las credenciales mínimas configuradas."""
        return bool(self.smtp_user and self.smtp_password)

    def _markdown_to_email_html(self, text: str) -> str:
        """Convierte markdown estructurado (tablas, títulos, listas, citas, negritas) a HTML estilizado para correo."""
        lines = text.strip().split("\n")
        output: list[str] = []
        in_table = False
        table_rows: list[str] = []

        def flush_table() -> str:
            nonlocal in_table, table_rows
            if not table_rows:
                return ""
            html = (
                '<div style="overflow-x: auto; margin: 18px 0;">'
                '<table style="width: 100%; border-collapse: collapse; border: 1px solid #1e293b; border-radius: 8px; overflow: hidden; background: #0c1220;">'
            )
            for idx, row in enumerate(table_rows):
                if re.match(r"^[\|\s\-:]+$", row):
                    continue
                cols = [c.strip() for c in row.split("|")[1:-1]]
                if idx == 0:
                    html += '<thead><tr style="background: linear-gradient(90deg, #1e3a8a 0%, #1e293b 100%);">'
                    for col in cols:
                        html += f'<th style="padding: 10px 14px; text-align: left; font-size: 12px; font-weight: 700; color: #38bdf8; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 2px solid #2563eb;">{col}</th>'
                    html += "</tr></thead><tbody>"
                else:
                    bg = "rgba(15, 23, 42, 0.7)" if idx % 2 == 0 else "rgba(30, 41, 59, 0.4)"
                    html += f'<tr style="background: {bg}; border-bottom: 1px solid #1e293b;">'
                    for col in cols:
                        c_styled = col
                        if "MÁS BARATO" in col or "ahorras" in col.lower():
                            c_styled = f'<span style="color: #34d399; font-weight: 700;">{col}</span>'
                        elif "MÁS CARO" in col:
                            c_styled = f'<span style="color: #f87171; font-weight: 700;">{col}</span>'
                        elif "Nexus" in col:
                            c_styled = f'<span style="color: #38bdf8; font-weight: 700;">{col}</span>'
                        html += f'<td style="padding: 10px 14px; font-size: 13px; color: #e2e8f0;">{c_styled}</td>'
                    html += "</tr>"
            html += "</tbody></table></div>"
            in_table = False
            table_rows = []
            return html

        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Detección de tablas markdown
            if stripped.startswith("|") and stripped.endswith("|"):
                in_table = True
                table_rows.append(stripped)
                i += 1
                continue
            elif in_table:
                output.append(flush_table())

            # Separadores horizontales
            if stripped in ("---", "***", "___"):
                output.append(
                    '<hr style="border: 0; height: 1px; background: linear-gradient(90deg, #2563eb 0%, #ef4444 100%); margin: 22px 0;" />'
                )
                i += 1
                continue

            # Encabezados markdown
            if stripped.startswith("### "):
                h_text = stripped[4:]
                output.append(
                    f'<h3 style="color: #60a5fa; font-size: 17px; margin: 24px 0 10px 0; border-left: 4px solid #ef4444; padding-left: 10px; font-weight: 700; letter-spacing: -0.3px;">{h_text}</h3>'
                )
                i += 1
                continue
            elif stripped.startswith("## "):
                h_text = stripped[3:]
                output.append(
                    f'<h2 style="color: #ffffff; font-size: 19px; margin: 26px 0 12px 0; border-bottom: 1px solid #2563eb; padding-bottom: 6px; font-weight: 800;">{h_text}</h2>'
                )
                i += 1
                continue

            # Citas y notas destacadas (Trivia / Lore)
            if stripped.startswith("> "):
                q_text = stripped[2:]
                output.append(
                    f'<div style="background: rgba(239, 68, 68, 0.08); border-left: 4px solid #ef4444; border-radius: 0 8px 8px 0; padding: 12px 16px; margin: 16px 0; color: #fca5a5; font-size: 13.5px; font-style: italic;">{q_text}</div>'
                )
                i += 1
                continue

            # Elementos de lista
            if stripped.startswith(("- ", "* ")):
                li_text = stripped[2:]
                li_text = re.sub(r"\*\*(.*?)\*\*", r'<strong style="color: #ffffff;">\1</strong>', li_text)
                output.append(
                    f'<div style="margin: 6px 0; color: #cbd5e1; font-size: 14px; line-height: 1.6;"><span style="color: #ef4444; font-weight: bold; margin-right: 8px;">▸</span>{li_text}</div>'
                )
                i += 1
                continue

            if not stripped:
                i += 1
                continue

            # Párrafos normales
            p_text = re.sub(r"\*\*(.*?)\*\*", r'<strong style="color: #ffffff;">\1</strong>', line)
            p_text = re.sub(r"\*(.*?)\*", r'<em style="color: #cbd5e1;">\1</em>', p_text)
            output.append(
                f'<p style="margin: 0 0 14px 0; line-height: 1.65; color: #cbd5e1; font-size: 14.5px;">{p_text}</p>'
            )
            i += 1

        if in_table:
            output.append(flush_table())

        return "\n".join(output)

    def _build_html_template(self, recipient: str, subject: str, message_body: str) -> str:
        """Genera un correo HTML profesional de alta fidelidad con identidad visual Nexus (Azul + Rojo Gamer)."""
        formatted_content = self._markdown_to_email_html(message_body)

        return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{subject}</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      background-color: #070a12;
      color: #e2e8f0;
      margin: 0;
      padding: 24px 12px;
      -webkit-font-smoothing: antialiased;
    }}
    .wrapper {{
      width: 100%;
      max-width: 640px;
      margin: 0 auto;
      background: linear-gradient(180deg, #0e1526 0%, #080d19 100%);
      border: 1px solid #1e293b;
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.75);
    }}
    .top-neon-bar {{
      height: 4px;
      background: linear-gradient(90deg, #2563eb 0%, #38bdf8 35%, #ef4444 70%, #dc2626 100%);
    }}
    .header {{
      padding: 32px 28px 24px 28px;
      text-align: center;
      background: radial-gradient(circle at top, rgba(37, 99, 235, 0.12) 0%, transparent 70%);
      border-bottom: 1px solid #1e293b;
    }}
    .brand-title {{
      font-size: 24px;
      font-weight: 900;
      letter-spacing: 2px;
      text-transform: uppercase;
      margin-top: 10px;
    }}
    .brand-blue {{
      color: #38bdf8;
      text-shadow: 0 0 20px rgba(56, 189, 248, 0.5);
    }}
    .brand-red {{
      color: #ef4444;
      text-shadow: 0 0 20px rgba(239, 68, 68, 0.5);
    }}
    .brand-white {{
      color: #ffffff;
    }}
    .brand-tagline {{
      font-size: 11px;
      letter-spacing: 2px;
      color: #94a3b8;
      text-transform: uppercase;
      margin-top: 6px;
      font-weight: 600;
    }}
    .status-badge {{
      display: inline-block;
      background: rgba(37, 99, 235, 0.12);
      border: 1px solid rgba(56, 189, 248, 0.35);
      padding: 5px 14px;
      border-radius: 20px;
      font-size: 11px;
      color: #38bdf8;
      font-weight: 700;
      margin-top: 14px;
      letter-spacing: 0.5px;
    }}
    .content-body {{
      padding: 32px 28px;
    }}
    .welcome-card {{
      background: rgba(14, 165, 233, 0.05);
      border-left: 4px solid #38bdf8;
      border-right: 4px solid #ef4444;
      border-radius: 8px;
      padding: 16px 20px;
      margin-bottom: 24px;
    }}
    .welcome-card strong {{
      color: #38bdf8;
      font-size: 14.5px;
    }}
    .welcome-card p {{
      margin: 4px 0 0 0;
      font-size: 13.5px;
      color: #94a3b8;
      line-height: 1.5;
    }}
    .trust-table {{
      width: 100%;
      margin: 28px 0 20px 0;
      border-collapse: collapse;
    }}
    .trust-box {{
      width: 32%;
      background: rgba(30, 41, 59, 0.45);
      border: 1px solid #1e293b;
      border-radius: 8px;
      padding: 14px 8px;
      text-align: center;
    }}
    .cta-container {{
      text-align: center;
      margin: 32px 0 16px 0;
    }}
    .cta-button {{
      background: linear-gradient(135deg, #2563eb 0%, #dc2626 100%);
      color: #ffffff !important;
      padding: 14px 32px;
      border-radius: 8px;
      font-weight: 800;
      font-size: 13.5px;
      text-decoration: none;
      display: inline-block;
      box-shadow: 0 4px 20px rgba(220, 38, 38, 0.4);
      text-transform: uppercase;
      letter-spacing: 1px;
    }}
    .footer {{
      border-top: 1px solid #1e293b;
      padding: 24px 28px;
      text-align: center;
      font-size: 12px;
      color: #64748b;
      background: #060911;
      line-height: 1.6;
    }}
    .footer a {{
      color: #38bdf8;
      text-decoration: none;
    }}
  </style>
</head>
<body>
  <div class="wrapper">
    <!-- Barra superior Neón Azul/Rojo -->
    <div class="top-neon-bar"></div>

    <!-- Header con Logo SVG Gamer Nexus -->
    <div class="header">
      <div style="text-align: center;">
        <svg width="60" height="60" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
          <polygon points="50,5 92,25 92,75 50,95 8,75 8,25" stroke="url(#nexusBorder)" stroke-width="3" fill="#0d1527"/>
          <path d="M30 68V32L50 56V32" stroke="#38bdf8" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M50 68V44L70 68V32" stroke="#ef4444" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
          <circle cx="50" cy="50" r="4" fill="#ffffff"/>
          <defs>
            <linearGradient id="nexusBorder" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="#38bdf8"/>
              <stop offset="50%" stop-color="#2563eb"/>
              <stop offset="100%" stop-color="#ef4444"/>
            </linearGradient>
          </defs>
        </svg>
      </div>
      <div class="brand-title">
        <span class="brand-blue">NEXUS</span> <span class="brand-red">DIGITAL</span> <span class="brand-white">STORE</span>
      </div>
      <div class="brand-tagline">
        PLATAFORMA INTELIGENTE DE VIDEOJUEGOS • COTIZACIÓN & OFERTAS EN VIVO
      </div>
      <div>
        <span class="status-badge">⚡ ASESOR COGNITIVO NEXUSBOT • CHILE 🇨🇱</span>
      </div>
    </div>

    <!-- Contenido Principal -->
    <div class="content-body">
      <div class="welcome-card">
        <strong>¡Hola Gamer! 🎮</strong>
        <p>A continuación te presentamos la información oficial, comparativa internacional de tiendas y asesoramiento generado a tu solicitud.</p>
      </div>

      <!-- Texto y Tablas renderizados desde Markdown -->
      <div class="markdown-content">
        {formatted_content}
      </div>

      <!-- Grid de Confianza Gamer -->
      <table class="trust-table">
        <tr>
          <td class="trust-box">
            <div style="font-size: 18px; margin-bottom: 4px;">⚡</div>
            <div style="font-size: 12px; font-weight: 700; color: #38bdf8;">Entrega Inmediata</div>
            <div style="font-size: 11px; color: #64748b; margin-top: 2px;">Claves 24/7 en segundos</div>
          </td>
          <td style="width: 2%;"></td>
          <td class="trust-box">
            <div style="font-size: 18px; margin-bottom: 4px;">🛡️</div>
            <div style="font-size: 12px; font-weight: 700; color: #ef4444;">Garantía Oficial</div>
            <div style="font-size: 11px; color: #64748b; margin-top: 2px;">Activación 100% segura</div>
          </td>
          <td style="width: 2%;"></td>
          <td class="trust-box">
            <div style="font-size: 18px; margin-bottom: 4px;">🇨🇱</div>
            <div style="font-size: 12px; font-weight: 700; color: #38bdf8;">Precios en CLP</div>
            <div style="font-size: 11px; color: #64748b; margin-top: 2px;">Sin recargos bancarios</div>
          </td>
        </tr>
      </table>

      <!-- Botón Call To Action -->
      <div class="cta-container">
        <a href="https://nexusdigitalstore.cl" target="_blank" class="cta-button">
          🛒 Explorar Catálogo en Nexus Store
        </a>
      </div>
    </div>

    <!-- Footer Oficial -->
    <div class="footer">
      <p style="margin: 0 0 6px 0;">Este correo fue generado y enviado automáticamente por <strong>NexusBot</strong> mediante Inteligencia Artificial.</p>
      <p style="margin: 0 0 10px 0; color: #475569;">© 2026 Nexus Digital Store • Santiago, Chile • Todos los derechos reservados.</p>
      <p style="margin: 0; font-size: 11px;">
        <a href="https://nexusdigitalstore.cl">Visitar Tienda</a> • 
        <a href="mailto:soporte@nexusdigitalstore.cl">Soporte Gamer</a> • 
        <a href="https://nexusdigitalstore.cl/terminos">Términos y Condiciones</a>
      </p>
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

