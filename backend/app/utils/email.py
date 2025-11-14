"""
Email alarm system for critical errors.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from datetime import datetime

from app.config import get_config
from app.utils.logger import get_logger
from app.utils.retry import retry_on_failure

logger = get_logger(__name__)


class EmailService:
    """Email service for sending alarm notifications."""
    
    def __init__(self):
        """Initialize email service."""
        self.config = get_config()
        self.enabled = self.config.smtp.enabled
    
    def _create_message(
        self,
        subject: str,
        body: str,
        is_html: bool = False
    ) -> MIMEMultipart:
        """
        Create email message.
        
        Args:
            subject: Email subject.
            body: Email body.
            is_html: Whether body is HTML.
            
        Returns:
            MIME message.
        """
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.config.smtp.from_name} <{self.config.smtp.from_email}>"
        msg["To"] = ", ".join(self.config.smtp.to_emails)
        
        if is_html:
            msg.attach(MIMEText(body, "html"))
        else:
            msg.attach(MIMEText(body, "plain"))
        
        return msg
    
    @retry_on_failure(exceptions=(smtplib.SMTPException, OSError))
    def send_email(
        self,
        subject: str,
        body: str,
        recipients: Optional[List[str]] = None,
        is_html: bool = False
    ) -> bool:
        """
        Send email.
        
        Args:
            subject: Email subject.
            body: Email body.
            recipients: List of recipient emails. If None, uses config.
            is_html: Whether body is HTML.
            
        Returns:
            True if sent successfully, False otherwise.
        """
        if not self.enabled:
            logger.debug("Email service is disabled")
            return False
        
        if not self.config.smtp.username or not self.config.smtp.password:
            logger.warning("SMTP credentials not configured")
            return False
        
        recipients = recipients or self.config.smtp.to_emails
        if not recipients:
            logger.warning("No email recipients configured")
            return False
        
        try:
            msg = self._create_message(subject, body, is_html)
            msg["To"] = ", ".join(recipients)
            
            # Connect to SMTP server
            with smtplib.SMTP(
                self.config.smtp.host,
                self.config.smtp.port,
                timeout=30
            ) as server:
                if self.config.smtp.use_tls:
                    server.starttls()
                
                server.login(self.config.smtp.username, self.config.smtp.password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {recipients}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}", exc_info=True)
            return False
    
    def send_error_alert(
        self,
        error_type: str,
        error_message: str,
        error_details: Optional[str] = None,
        context: Optional[dict] = None
    ) -> bool:
        """
        Send critical error alert email.
        
        Args:
            error_type: Type of error.
            error_message: Error message.
            error_details: Detailed error information.
            context: Additional context dictionary.
            
        Returns:
            True if sent successfully, False otherwise.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        subject = f"[Santrac Alarm] {error_type} - {timestamp}"
        
        body = f"""
Santrac Platform - Critical Error Alert

Error Type: {error_type}
Timestamp: {timestamp}
Error Message: {error_message}

"""
        
        if error_details:
            body += f"Error Details:\n{error_details}\n\n"
        
        if context:
            body += "Additional Context:\n"
            for key, value in context.items():
                body += f"  {key}: {value}\n"
            body += "\n"
        
        body += """
This is an automated alert from the Santrac Platform monitoring system.
Please investigate this issue immediately.
"""
        
        return self.send_email(subject, body)
    
    def send_system_alert(
        self,
        alert_type: str,
        message: str,
        severity: str = "WARNING"
    ) -> bool:
        """
        Send system alert email.
        
        Args:
            alert_type: Type of alert.
            message: Alert message.
            severity: Alert severity (INFO, WARNING, ERROR, CRITICAL).
            
        Returns:
            True if sent successfully, False otherwise.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        subject = f"[Santrac Alert] {severity} - {alert_type}"
        
        body = f"""
Santrac Platform - System Alert

Alert Type: {alert_type}
Severity: {severity}
Timestamp: {timestamp}
Message: {message}

This is an automated alert from the Santrac Platform monitoring system.
"""
        
        return self.send_email(subject, body)


# Global email service instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """
    Get global email service instance.
    
    Returns:
        EmailService instance.
    """
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service

