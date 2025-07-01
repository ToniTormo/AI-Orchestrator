"""
Email Notification Service

Handles sending notifications via email using specific templates.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.utils.logging import setup_logger
from src.config import settings
from src.utils.exceptions_control import create_error, EmailNotificationError
from src.domain.models import ViabilityAnalysisResult

logger = setup_logger(
    "notification.email_service",
    settings.logging.module_levels.get("notification", settings.logging.level)
)

class EmailNotificationService:
    """Service for sending notifications via email."""
    
    def __init__(self):
        """Initialize notification service."""
        self.smtp_server = settings.notification.smtp_server
        self.smtp_port = settings.notification.smtp_port
        self.smtp_username = settings.notification.smtp_username
        self.smtp_password = settings.notification.smtp_password
        self.sender_email = settings.notification.email
        
        if not all([self.smtp_server, self.smtp_username, self.smtp_password, self.sender_email]):
            raise create_error(
                EmailNotificationError,
                "Email service not properly configured. Missing SMTP credentials or sender email.",
                "EmailNotificationService"
            )
        
    async def send_viability_notification(self, email: str, project_url: str, viability_result: ViabilityAnalysisResult):
        """Send a project viability notification."""
        if not email or not project_url:
            raise create_error(
                EmailNotificationError,
                "Email and project URL are required for viability notification",
                "EmailNotificationService"
            )
            
        subject = f"AI Analysis Report for {project_url}"
        
        message = f"""
        <html>
        <body>
            <h2>AI Analysis Report</h2>
            <p><strong>Project:</strong> {project_url}</p>
            <p><strong>Viable for implementation:</strong> {'Yes' if viability_result.is_viable else 'No'}</p>
            <p><strong>Confidence Score:</strong> {viability_result.confidence_score}%</p>
            <h3>Recommended Tasks:</h3>
            <ul>
        """
        if viability_result.tasks_steps:
            for task in viability_result.tasks_steps:
                message += f"<li>{task}</li>"
        else:
            message += "<li>No specific tasks recommended.</li>"
            
        message += """
            </ul>
        </body>
        </html>
        """
        await self._send_email(email, subject, message)

    async def send_completion_notification(self, email: str, project_url: str, pr_url: str, summary: str):
        """Send a project completion notification."""
        if not email or not project_url or not pr_url:
            raise create_error(
                EmailNotificationError,
                "Email, project URL and PR URL are required for completion notification",
                "EmailNotificationService"
            )
            
        subject = f"Project Implementation Completed for {project_url}"
        
        message = f"""
        <html>
        <body>
            <h2>Project Implementation Complete</h2>
            <p>The AI-driven implementation for <strong>{project_url}</strong> is complete.</p>
            <p>A pull request has been created for your review: <a href="{pr_url}">{pr_url}</a></p>
            <h3>Summary of Changes:</h3>
            <p>{summary}</p>
        </body>
        </html>
        """
        await self._send_email(email, subject, message)
        
    async def _send_email(self, email: str, subject: str, message: str) -> None:
        """
        Send an email notification.
        
        Args:
            email: Recipient email address.
            subject: Email subject.
            message: Email message content.
            
        Raises:
            EmailNotificationError: If email sending fails.
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = email
            msg['Subject'] = subject
            msg.attach(MIMEText(message, 'html'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"[EmailNotificationService] Notification sent successfully to {email}")
            
        except Exception as e:
            raise create_error(
                EmailNotificationError,
                f"Failed to send notification to {email}: {str(e)}",
                "EmailNotificationService"
            ) 
            