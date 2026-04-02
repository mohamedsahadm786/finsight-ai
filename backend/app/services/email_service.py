"""
Email service for FinSight AI.

Handles sending transactional emails using fastapi-mail:
- Password reset emails with secure token links
- (Future) User invitation emails
- (Future) Processing completion notifications

Uses Gmail SMTP with App Password authentication.
"""

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from backend.app.config import get_settings


def _get_mail_config() -> ConnectionConfig:
    """
    Build the fastapi-mail connection configuration from environment variables.

    This reads from .env via our Settings class:
    - MAIL_USERNAME: Gmail address
    - MAIL_PASSWORD: Gmail App Password (NOT your regular password)
    - MAIL_FROM: The "From" address shown to recipients
    - MAIL_SERVER: smtp.gmail.com
    - MAIL_PORT: 587 (TLS)
    - MAIL_TLS: True (encrypt the connection)
    - MAIL_SSL: False (we use TLS, not SSL — they're different)
    """
    settings = get_settings()

    return ConnectionConfig(
        MAIL_USERNAME=settings.MAIL_USERNAME,
        MAIL_PASSWORD=settings.MAIL_PASSWORD,
        MAIL_FROM=settings.MAIL_FROM,
        MAIL_PORT=settings.MAIL_PORT,
        MAIL_SERVER=settings.MAIL_SERVER,
        MAIL_STARTTLS=settings.MAIL_TLS,
        MAIL_SSL_TLS=settings.MAIL_SSL,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
    )


async def send_password_reset_email(to_email: str, reset_token: str) -> bool:
    """
    Send a password reset email to the user.

    Args:
        to_email: The user's email address
        reset_token: The raw reset token (will be included in the link)

    Returns:
        True if email sent successfully, False if it failed

    The email contains a link like:
        https://app.finsight.ai/reset-password?token=ABC123...

    During local development, the reset URL points to localhost.
    In production, it would point to the real domain.
    """
    settings = get_settings()

    # Build the reset link
    # In production, this would be: https://app.finsight.ai/reset-password?token=...
    # In development, we use localhost
    base_url = settings.FRONTEND_URL

    reset_link = f"{base_url}/reset-password?token={reset_token}"

    # Build the email content
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #0A0A0B; color: #F5F5F5; padding: 40px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #141416; border-radius: 12px; padding: 40px;">
            <h1 style="color: #C62828; margin-bottom: 20px;">FinSight AI</h1>
            <h2 style="color: #F5F5F5; margin-bottom: 16px;">Password Reset Request</h2>
            <p style="color: #9E9E9E; line-height: 1.6;">
                We received a request to reset your password. Click the button below
                to set a new password. This link expires in <strong>15 minutes</strong>.
            </p>
            <div style="text-align: center; margin: 32px 0;">
                <a href="{reset_link}"
                   style="background-color: #C62828; color: #FFFFFF; padding: 14px 32px;
                          border-radius: 8px; text-decoration: none; font-weight: bold;
                          display: inline-block;">
                    Reset Password
                </a>
            </div>
            <p style="color: #9E9E9E; font-size: 14px; line-height: 1.6;">
                If you didn't request this, you can safely ignore this email.
                Your password will not be changed.
            </p>
            <hr style="border: 1px solid #2A2A2A; margin: 24px 0;">
            <p style="color: #666666; font-size: 12px;">
                If the button doesn't work, copy and paste this link into your browser:<br>
                <span style="color: #9E9E9E;">{reset_link}</span>
            </p>
        </div>
    </body>
    </html>
    """

    # Create the message
    message = MessageSchema(
        subject="FinSight AI — Password Reset Request",
        recipients=[to_email],
        body=html_body,
        subtype=MessageType.html,
    )

    # Send the email
    try:
        conf = _get_mail_config()
        fm = FastMail(conf)
        await fm.send_message(message)
        return True
    except Exception as e:
        print(f"Failed to send password reset email to {to_email}: {e}")
        return False


async def send_user_invitation_email(
    to_email: str, full_name: str, tenant_name: str, temporary_password: str
) -> bool:
    """
    Send an invitation email to a newly created user.

    Called when an admin invites a new user via POST /admin/users/invite.
    The email contains the user's temporary credentials.
    """
    settings = get_settings()

    login_url = f"{settings.FRONTEND_URL}/login"

    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #0A0A0B; color: #F5F5F5; padding: 40px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #141416; border-radius: 12px; padding: 40px;">
            <h1 style="color: #C62828; margin-bottom: 20px;">FinSight AI</h1>
            <h2 style="color: #F5F5F5; margin-bottom: 16px;">Welcome to {tenant_name}!</h2>
            <p style="color: #9E9E9E; line-height: 1.6;">
                Hi {full_name},<br><br>
                You've been invited to join <strong>{tenant_name}</strong> on FinSight AI —
                the AI-powered credit risk analysis platform.
            </p>
            <div style="background-color: #1A1A1C; border-radius: 8px; padding: 20px; margin: 24px 0;">
                <p style="color: #F5F5F5; margin: 4px 0;"><strong>Email:</strong> {to_email}</p>
                <p style="color: #F5F5F5; margin: 4px 0;"><strong>Temporary Password:</strong> {temporary_password}</p>
            </div>
            <p style="color: #C62828; font-size: 14px; font-weight: bold;">
                Please change your password after your first login.
            </p>
            <div style="text-align: center; margin: 32px 0;">
                <a href="{login_url}"
                   style="background-color: #C62828; color: #FFFFFF; padding: 14px 32px;
                          border-radius: 8px; text-decoration: none; font-weight: bold;
                          display: inline-block;">
                    Log In Now
                </a>
            </div>
            <hr style="border: 1px solid #2A2A2A; margin: 24px 0;">
            <p style="color: #666666; font-size: 12px;">
                This is an automated message from FinSight AI. Do not reply to this email.
            </p>
        </div>
    </body>
    </html>
    """

    message = MessageSchema(
        subject=f"You've been invited to {tenant_name} on FinSight AI",
        recipients=[to_email],
        body=html_body,
        subtype=MessageType.html,
    )

    try:
        conf = _get_mail_config()
        fm = FastMail(conf)
        await fm.send_message(message)
        return True
    except Exception as e:
        print(f"Failed to send invitation email to {to_email}: {e}")
        return False