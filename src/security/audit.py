"""
Audit logging for security events.

Appends events to NDJSON audit log with fields:
- timestamp
- actor (identity ID)
- tenant
- action
- resource type and ID
- result
- IP address, trace ID
"""

from pathlib import Path
from typing import Optional
from datetime import datetime
import json

from .schemas import AuditEvent, Identity


class AuditLogger:
    """
    Append-only audit logger.

    Writes to NDJSON file.
    """

    def __init__(self, log_path: str = ".claude/logs/audit.log"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        # Create file if not exists
        if not self.log_path.exists():
            self.log_path.touch()

    def log(
        self,
        actor: Identity,
        action: str,
        resource_type: str,
        result: str,
        tenant: Optional[str] = None,
        resource_id: Optional[str] = None,
        result_details: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        trace_id: Optional[str] = None,
        **metadata
    ):
        """
        Log audit event.

        Args:
            actor: Identity performing action
            action: Action name (create, update, delete, access, etc.)
            resource_type: Resource type (api_key, theme, model, etc.)
            result: Result (success, failure, denied)
            tenant: Tenant slug
            resource_id: Resource ID
            result_details: Additional result details
            ip_address: IP address
            user_agent: User agent string
            trace_id: Trace ID for correlation
            **metadata: Additional metadata
        """
        event = AuditEvent(
            actor_id=actor.id,
            actor_type=actor.type,
            tenant=tenant,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            result=result,
            result_details=result_details,
            ip_address=ip_address,
            user_agent=user_agent,
            trace_id=trace_id,
            metadata=metadata
        )

        self._append(event)

    def log_auth_success(
        self,
        identity: Identity,
        ip_address: Optional[str] = None,
        trace_id: Optional[str] = None
    ):
        """Log successful authentication."""
        self.log(
            actor=identity,
            action="login",
            resource_type="auth",
            result="success",
            ip_address=ip_address,
            trace_id=trace_id,
            source=identity.source
        )

    def log_auth_failure(
        self,
        actor_id: str,
        reason: str,
        ip_address: Optional[str] = None,
        trace_id: Optional[str] = None
    ):
        """Log failed authentication."""
        # Create temporary identity for logging
        from .schemas import Identity
        temp_identity = Identity(
            id=actor_id,
            type="unknown",
            roles=[],
            scopes=set(),
            tenants=[],
            source="unknown"
        )

        self.log(
            actor=temp_identity,
            action="login",
            resource_type="auth",
            result="failure",
            result_details=reason,
            ip_address=ip_address,
            trace_id=trace_id
        )

    def log_access_denied(
        self,
        identity: Identity,
        resource_type: str,
        resource_id: Optional[str] = None,
        tenant: Optional[str] = None,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        trace_id: Optional[str] = None
    ):
        """Log access denied event."""
        self.log(
            actor=identity,
            action="access",
            resource_type=resource_type,
            resource_id=resource_id,
            tenant=tenant,
            result="denied",
            result_details=reason,
            ip_address=ip_address,
            trace_id=trace_id
        )

    def log_api_key_create(
        self,
        identity: Identity,
        key_id: str,
        key_owner: str,
        key_roles: list,
        key_tenants: list,
        trace_id: Optional[str] = None
    ):
        """Log API key creation."""
        self.log(
            actor=identity,
            action="create",
            resource_type="api_key",
            resource_id=key_id,
            result="success",
            trace_id=trace_id,
            key_owner=key_owner,
            key_roles=[r.value if hasattr(r, 'value') else r for r in key_roles],
            key_tenants=key_tenants
        )

    def log_api_key_revoke(
        self,
        identity: Identity,
        key_id: str,
        trace_id: Optional[str] = None
    ):
        """Log API key revocation."""
        self.log(
            actor=identity,
            action="revoke",
            resource_type="api_key",
            resource_id=key_id,
            result="success",
            trace_id=trace_id
        )

    def log_signed_url_issue(
        self,
        identity: Identity,
        path: str,
        tenant: str,
        ttl_seconds: int,
        ip_address: Optional[str] = None,
        trace_id: Optional[str] = None
    ):
        """Log signed URL issuance."""
        self.log(
            actor=identity,
            action="issue",
            resource_type="signed_url",
            resource_id=path,
            tenant=tenant,
            result="success",
            ip_address=ip_address,
            trace_id=trace_id,
            ttl_seconds=ttl_seconds
        )

    def log_artifact_download(
        self,
        identity: Identity,
        artifact_path: str,
        tenant: str,
        signed: bool,
        ip_address: Optional[str] = None,
        trace_id: Optional[str] = None
    ):
        """Log artifact download."""
        self.log(
            actor=identity,
            action="download",
            resource_type="artifact",
            resource_id=artifact_path,
            tenant=tenant,
            result="success",
            ip_address=ip_address,
            trace_id=trace_id,
            signed=signed
        )

    def _append(self, event: AuditEvent):
        """Append event to audit log."""
        with open(self.log_path, "a") as f:
            f.write(event.to_ndjson_line() + "\n")

    def read_recent(self, limit: int = 100) -> list[AuditEvent]:
        """
        Read recent audit events.

        Args:
            limit: Maximum events to return

        Returns:
            List of recent events (newest first)
        """
        if not self.log_path.exists():
            return []

        events = []
        with open(self.log_path, "r") as f:
            lines = f.readlines()

        # Read last N lines
        for line in lines[-limit:]:
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
                # Reconstruct AuditEvent (simplified)
                events.append(data)
            except Exception:
                continue

        # Return newest first
        events.reverse()
        return events

    def export_csv(self, output_path: str, days: Optional[int] = None):
        """
        Export audit log to CSV.

        Args:
            output_path: Output CSV path
            days: Only export last N days (None = all)
        """
        import csv
        from datetime import timedelta

        if not self.log_path.exists():
            return

        cutoff = None
        if days:
            cutoff = datetime.utcnow() - timedelta(days=days)

        with open(self.log_path, "r") as infile:
            with open(output_path, "w", newline="") as outfile:
                writer = csv.writer(outfile)

                # Write header
                writer.writerow([
                    "timestamp", "actor", "actor_type", "tenant", "action",
                    "resource", "resource_id", "result", "result_details",
                    "ip", "trace_id"
                ])

                for line in infile:
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)

                        # Check cutoff
                        if cutoff:
                            ts_str = data.get("ts", "")
                            try:
                                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                                if ts < cutoff:
                                    continue
                            except Exception:
                                continue

                        # Write row
                        writer.writerow([
                            data.get("ts", ""),
                            data.get("actor", ""),
                            data.get("actor_type", ""),
                            data.get("tenant", ""),
                            data.get("action", ""),
                            data.get("resource", ""),
                            data.get("resource_id", ""),
                            data.get("result", ""),
                            data.get("result_details", ""),
                            data.get("ip", ""),
                            data.get("trace_id", ""),
                        ])
                    except Exception:
                        continue


# Global instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
