"""Alerting system for proactive monitoring."""

from __future__ import annotations

import asyncio
import smtplib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

from harness.observability.logging import get_logger

logger = get_logger()


@dataclass
class Alert:
    """Alert data structure."""

    name: str
    severity: str  # "info", "warning", "error", "critical"
    message: str
    labels: Dict[str, str]
    timestamp: float


class AlertNotifier(ABC):
    """Base class for alert notifiers."""

    @abstractmethod
    async def notify(self, alert: Alert) -> None:
        """Send alert notification."""
        pass


class EmailNotifier(AlertNotifier):
    """Send alerts via email."""

    def __init__(self, smtp_server: str, smtp_port: int, from_email: str, to_emails: List[str]):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.from_email = from_email
        self.to_emails = to_emails

    async def notify(self, alert: Alert) -> None:
        try:
            msg = MIMEText(f"""
Alert: {alert.name}
Severity: {alert.severity}
Message: {alert.message}
Labels: {alert.labels}
Timestamp: {alert.timestamp}
            """.strip())

            msg['Subject'] = f"[{alert.severity.upper()}] {alert.name}"
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)

            # Run SMTP in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._send_email,
                msg.as_string()
            )

            logger.info("alert_sent", alert=alert.name, method="email")

        except Exception as e:
            logger.error("alert_send_failed", alert=alert.name, error=str(e))

    def _send_email(self, message: str) -> None:
        """Send email synchronously."""
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.sendmail(self.from_email, self.to_emails, message)


class SlackNotifier(AlertNotifier):
    """Send alerts to Slack."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    async def notify(self, alert: Alert) -> None:
        try:
            import aiohttp

            payload = {
                "text": f"🚨 *{alert.name}* ({alert.severity})\n{alert.message}",
                "attachments": [{
                    "fields": [
                        {"title": k, "value": str(v), "short": True}
                        for k, v in alert.labels.items()
                    ]
                }]
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as resp:
                    if resp.status != 200:
                        raise Exception(f"Slack API returned {resp.status}")

            logger.info("alert_sent", alert=alert.name, method="slack")

        except Exception as e:
            logger.error("alert_send_failed", alert=alert.name, error=str(e))


class AlertManager:
    """Manages alerts and notifications."""

    def __init__(self):
        self.notifiers: List[AlertNotifier] = []
        self.alert_history: List[Alert] = []
        self.max_history = 1000

    def add_notifier(self, notifier: AlertNotifier) -> None:
        """Add an alert notifier."""
        self.notifiers.append(notifier)

    async def send_alert(
        self,
        name: str,
        severity: str,
        message: str,
        labels: Optional[Dict[str, str]] = None,
        timestamp: Optional[float] = None
    ) -> None:
        """Send an alert to all notifiers."""
        import time

        alert = Alert(
            name=name,
            severity=severity,
            message=message,
            labels=labels or {},
            timestamp=timestamp or time.time()
        )

        # Store in history
        self.alert_history.append(alert)
        if len(self.alert_history) > self.max_history:
            self.alert_history.pop(0)

        # Send to all notifiers concurrently
        tasks = [notifier.notify(alert) for notifier in self.notifiers]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        logger.info("alert_processed", name=name, severity=severity)

    async def alert_on_metric_threshold(
        self,
        metric_name: str,
        current_value: float,
        threshold: float,
        comparison: str,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Send alert if metric crosses threshold."""
        triggered = False

        if comparison == ">" and current_value > threshold:
            triggered = True
        elif comparison == "<" and current_value < threshold:
            triggered = True
        elif comparison == ">=" and current_value >= threshold:
            triggered = True
        elif comparison == "<=" and current_value <= threshold:
            triggered = True

        if triggered:
            await self.send_alert(
                name=f"metric_threshold_{metric_name}",
                severity="warning",
                message=f"{metric_name} {comparison} {threshold} (current: {current_value})",
                labels=labels or {}
            )


# Global alert manager instance
alert_manager = AlertManager()