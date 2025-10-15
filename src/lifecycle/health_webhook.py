"""
Platform Health Webhook Module
Posts compact health summaries to external webhooks (Slack, Teams, Webex, etc.)
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
import urllib.request
import urllib.error


def load_config() -> Dict[str, Any]:
    """Load lifecycle configuration."""
    config_path = Path(__file__).parent.parent.parent / "configs" / "lifecycle.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def load_latest_weekly_report() -> Optional[Dict[str, Any]]:
    """Load the most recent weekly report JSON summary."""
    reports_dir = Path(__file__).parent.parent.parent / "reports" / "lifecycle" / "weekly"

    if not reports_dir.exists():
        return None

    # Find most recent week directory
    week_dirs = sorted([d for d in reports_dir.iterdir() if d.is_dir()], reverse=True)
    if not week_dirs:
        return None

    report_path = week_dirs[0] / "report.json"
    if not report_path.exists():
        return None

    with open(report_path) as f:
        return json.load(f)


def get_webhook_url(config: Dict[str, Any]) -> Optional[str]:
    """Get webhook URL from config or environment."""
    webhook_config = config.get("webhook", {})

    if not webhook_config.get("enabled", False):
        return None

    url_secret = webhook_config.get("url_secret", "LIFECYCLE_WEBHOOK_URL")

    # Try environment variable
    webhook_url = os.environ.get(url_secret)

    # Try secrets file
    if not webhook_url:
        secrets_file = Path(__file__).parent.parent.parent / "configs" / "secrets.yaml"
        if secrets_file.exists():
            with open(secrets_file) as f:
                secrets = yaml.safe_load(f)
                webhook_url = secrets.get(url_secret)

    return webhook_url


def format_slack_payload(report_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format health data as Slack message payload.
    Uses block kit for rich formatting.
    """
    scores = report_data.get("scores", {})
    status = report_data.get("status", "unknown")
    recommendations = report_data.get("recommendations", [])

    # Determine status color
    avg_score = sum(scores.values()) / len(scores) if scores else 0
    if avg_score >= 95:
        color = "good"  # green
        status_text = "Excellent"
    elif avg_score >= 85:
        color = "warning"  # yellow
        status_text = "Good"
    elif avg_score >= 70:
        color = "warning"
        status_text = "Fair"
    else:
        color = "danger"  # red
        status_text = "Needs Attention"

    # Build Slack message
    payload = {
        "text": f"Weekly Platform Health Report - {status_text}",
        "attachments": [
            {
                "color": color,
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"Platform Health: {status_text}"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Security:*\n{scores.get('security', 0):.0f}/100"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Operations:*\n{scores.get('ops', 0):.0f}/100"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Governance:*\n{scores.get('governance', 0):.0f}/100"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Reliability:*\n{scores.get('reliability', 0):.0f}/100"
                            }
                        ]
                    }
                ]
            }
        ]
    }

    # Add recommendations if any
    if recommendations:
        rec_text = "\\n".join(f"- {rec}" for rec in recommendations[:3])
        payload["attachments"][0]["blocks"].append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Key Recommendations:*\\n{rec_text}"
            }
        })

    return payload


def format_teams_payload(report_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format health data as Microsoft Teams message payload.
    Uses Adaptive Cards format.
    """
    scores = report_data.get("scores", {})
    status = report_data.get("status", "unknown")

    avg_score = sum(scores.values()) / len(scores) if scores else 0
    if avg_score >= 95:
        status_text = "Excellent"
        color = "good"
    elif avg_score >= 85:
        status_text = "Good"
        color = "attention"
    elif avg_score >= 70:
        status_text = "Fair"
        color = "attention"
    else:
        status_text = "Needs Attention"
        color = "warning"

    payload = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": "7823DC",  # Kearney purple
        "summary": f"Platform Health: {status_text}",
        "sections": [
            {
                "activityTitle": "Weekly Platform Health Report",
                "activitySubtitle": f"Status: {status_text}",
                "facts": [
                    {"name": "Security", "value": f"{scores.get('security', 0):.0f}/100"},
                    {"name": "Operations", "value": f"{scores.get('ops', 0):.0f}/100"},
                    {"name": "Governance", "value": f"{scores.get('governance', 0):.0f}/100"},
                    {"name": "Reliability", "value": f"{scores.get('reliability', 0):.0f}/100"}
                ]
            }
        ]
    }

    return payload


def format_generic_payload(report_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format health data as generic JSON payload.
    Compatible with most webhook receivers.
    """
    scores = report_data.get("scores", {})

    # Determine release version if available
    release = "v1.0.0"  # Placeholder
    try:
        version_file = Path(__file__).parent.parent.parent / "VERSION"
        if version_file.exists():
            release = version_file.read_text().strip()
    except Exception:
        pass

    payload = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "scores": {
            "security": int(scores.get("security", 0)),
            "ops": int(scores.get("ops", 0)),
            "governance": int(scores.get("governance", 0)),
            "reliability": int(scores.get("reliability", 0))
        },
        "release": release,
        "status": report_data.get("status", "unknown")
    }

    return payload


def post_webhook(url: str, payload: Dict[str, Any], config: Dict[str, Any]) -> bool:
    """
    Post payload to webhook URL with retry logic.
    Returns True if successful, False otherwise.
    """
    webhook_config = config.get("webhook", {})
    retry_count = webhook_config.get("retry_count", 3)
    retry_backoff = webhook_config.get("retry_backoff", 2)
    timeout = webhook_config.get("timeout", 10)

    for attempt in range(retry_count):
        try:
            # Convert payload to JSON
            data = json.dumps(payload).encode("utf-8")

            # Create request
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"}
            )

            # Send request
            with urllib.request.urlopen(req, timeout=timeout) as response:
                if response.status == 200:
                    print(f"Webhook posted successfully (status: {response.status})")
                    return True
                else:
                    print(f"Webhook post failed with status: {response.status}")

        except urllib.error.HTTPError as e:
            print(f"Webhook HTTP error (attempt {attempt + 1}/{retry_count}): {e.code} {e.reason}")
            if attempt < retry_count - 1:
                sleep_time = retry_backoff ** attempt
                print(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)

        except urllib.error.URLError as e:
            print(f"Webhook URL error (attempt {attempt + 1}/{retry_count}): {e.reason}")
            if attempt < retry_count - 1:
                sleep_time = retry_backoff ** attempt
                print(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)

        except Exception as e:
            print(f"Webhook error (attempt {attempt + 1}/{retry_count}): {str(e)}")
            if attempt < retry_count - 1:
                sleep_time = retry_backoff ** attempt
                print(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)

    print(f"Webhook posting failed after {retry_count} attempts")
    return False


def log_audit_event(success: bool, webhook_url: str):
    """Log webhook posting to audit trail."""
    audit_dir = Path(__file__).parent.parent.parent / "governance" / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)

    audit_file = audit_dir / "lifecycle.ndjson"

    # Redact webhook URL for security (keep only domain)
    try:
        from urllib.parse import urlparse
        parsed = urlparse(webhook_url)
        redacted_url = f"{parsed.scheme}://{parsed.netloc}/***"
    except Exception:
        redacted_url = "***"

    event = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event": "health_webhook_posted",
        "success": success,
        "webhook_url": redacted_url
    }

    with open(audit_file, "a") as f:
        f.write(json.dumps(event) + "\n")


def main():
    """Main entry point."""
    print("Posting platform health webhook...")

    # Load configuration
    config = load_config()

    # Check if webhook is enabled
    if not config.get("webhook", {}).get("enabled", False):
        print("Webhook posting disabled in configuration")
        return

    # Get webhook URL
    webhook_url = get_webhook_url(config)
    if not webhook_url:
        print("ERROR: No webhook URL configured")
        print("Set LIFECYCLE_WEBHOOK_URL environment variable or add to configs/secrets.yaml")
        return

    # Load latest report data
    report_data = load_latest_weekly_report()
    if not report_data:
        print("ERROR: No weekly report found")
        print("Run weekly_hygiene_report.py first to generate a report")
        return

    # Format payload based on webhook type
    webhook_format = config.get("webhook", {}).get("format", "generic")

    if webhook_format == "slack":
        payload = format_slack_payload(report_data)
    elif webhook_format == "teams":
        payload = format_teams_payload(report_data)
    else:
        payload = format_generic_payload(report_data)

    print(f"Webhook format: {webhook_format}")
    print(f"Payload preview: {json.dumps(payload, indent=2)[:200]}...")

    # Post webhook
    success = post_webhook(webhook_url, payload, config)

    # Log audit event
    log_audit_event(success, webhook_url)

    if success:
        print("Platform health webhook posted successfully")
    else:
        print("Failed to post platform health webhook")
        exit(1)


if __name__ == "__main__":
    main()
