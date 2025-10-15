"""
Security CLI commands for orchestrator.

Commands:
- orchestrator security apikey create
- orchestrator security apikey list
- orchestrator security apikey revoke
- orchestrator security tenant add
- orchestrator security tenant remove
- orchestrator security tenant list
"""

import click
from rich.console import Console
from rich.table import Table
from datetime import datetime, timedelta
from typing import Optional, List

from .keys import get_key_manager
from .schemas import RoleEnum, ScopeEnum
from .audit import get_audit_logger


console = Console()


@click.group(name="security")
def security_group():
    """Security management commands."""
    pass


@security_group.group(name="apikey")
def apikey_group():
    """API key management."""
    pass


@apikey_group.command(name="create")
@click.option("--tenant", required=True, help="Tenant slug or '*' for all")
@click.option("--roles", required=True, help="Comma-separated roles (admin,editor,viewer,service)")
@click.option("--scopes", help="Comma-separated scopes (overrides role defaults)")
@click.option("--ttl", type=int, help="TTL in days (default: 90)")
@click.option("--name", help="Human-readable key name")
@click.option("--description", help="Key description")
@click.option("--owner-id", default="cli-user", help="Owner identity ID")
def apikey_create(
    tenant: str,
    roles: str,
    scopes: Optional[str],
    ttl: Optional[int],
    name: Optional[str],
    description: Optional[str],
    owner_id: str
):
    """
    Create new API key.

    Examples:
        orchestrator security apikey create --tenant acme-corp --roles editor --ttl 30d
        orchestrator security apikey create --tenant '*' --roles admin --name "Admin Key"
    """
    try:
        # Parse roles
        role_list = []
        for role_str in roles.split(","):
            role_str = role_str.strip()
            try:
                role_list.append(RoleEnum(role_str))
            except ValueError:
                console.print(f"[red]Invalid role: {role_str}[/red]")
                console.print(f"Valid roles: {', '.join([r.value for r in RoleEnum])}")
                raise click.Abort()

        # Parse scopes if provided
        scope_list = None
        if scopes:
            scope_list = []
            for scope_str in scopes.split(","):
                scope_str = scope_str.strip()
                try:
                    scope_list.append(ScopeEnum(scope_str))
                except ValueError:
                    console.print(f"[red]Invalid scope: {scope_str}[/red]")
                    console.print(f"Valid scopes: {', '.join([s.value for s in ScopeEnum])}")
                    raise click.Abort()

        # Parse tenants
        tenant_list = [t.strip() for t in tenant.split(",")]

        # Create API key
        key_manager = get_key_manager()
        api_key, plain_key = key_manager.create(
            owner_id=owner_id,
            roles=role_list,
            tenants=tenant_list,
            scopes=scope_list,
            ttl_days=ttl or 90,
            name=name,
            description=description
        )

        # Log audit event
        from .schemas import Identity
        admin_identity = Identity(
            id="cli-admin",
            type="admin",
            roles=[RoleEnum.ADMIN],
            scopes={ScopeEnum.SECURITY_MANAGE},
            tenants=["*"],
            source="cli"
        )

        audit_logger = get_audit_logger()
        audit_logger.log_api_key_create(
            identity=admin_identity,
            key_id=api_key.id,
            key_owner=owner_id,
            key_roles=role_list,
            key_tenants=tenant_list,
            trace_id=None
        )

        # Display success
        console.print("\n[green]API Key Created Successfully[/green]\n")

        # Create table
        table = Table(show_header=False, box=None)
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Key ID", api_key.id)
        table.add_row("Key", f"[yellow]{plain_key}[/yellow]")
        table.add_row("Prefix", api_key.prefix)
        table.add_row("Owner", owner_id)
        table.add_row("Roles", ", ".join([r.value for r in role_list]))
        table.add_row("Tenants", ", ".join(tenant_list))
        if scope_list:
            table.add_row("Scopes", ", ".join([s.value for s in scope_list]))
        if ttl:
            expires_at = datetime.utcnow() + timedelta(days=ttl)
            table.add_row("Expires", expires_at.strftime("%Y-%m-%d %H:%M UTC"))
        else:
            table.add_row("Expires", "Never")
        if name:
            table.add_row("Name", name)

        console.print(table)

        console.print("\n[yellow]Save this key securely - it cannot be retrieved later![/yellow]\n")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()


@apikey_group.command(name="list")
@click.option("--tenant", help="Filter by tenant")
@click.option("--owner", help="Filter by owner ID")
@click.option("--all", "show_all", is_flag=True, help="Show revoked/expired keys")
def apikey_list(tenant: Optional[str], owner: Optional[str], show_all: bool):
    """
    List API keys.

    Examples:
        orchestrator security apikey list
        orchestrator security apikey list --tenant acme-corp
        orchestrator security apikey list --all
    """
    try:
        key_manager = get_key_manager()
        keys = key_manager.list(
            tenant=tenant,
            owner_id=owner,
            active_only=not show_all
        )

        if not keys:
            console.print("[yellow]No API keys found[/yellow]")
            return

        # Create table
        table = Table(title=f"API Keys ({len(keys)} found)")
        table.add_column("ID", style="cyan")
        table.add_column("Prefix", style="white")
        table.add_column("Owner", style="white")
        table.add_column("Roles", style="green")
        table.add_column("Tenants", style="blue")
        table.add_column("Created", style="white")
        table.add_column("Expires", style="white")
        table.add_column("Status", style="white")

        for key in keys:
            # Status
            if key.revoked_at:
                status = "[red]Revoked[/red]"
            elif key.expires_at and datetime.utcnow() > key.expires_at:
                status = "[yellow]Expired[/yellow]"
            else:
                status = "[green]Active[/green]"

            # Expires
            if key.expires_at:
                expires_str = key.expires_at.strftime("%Y-%m-%d")
            else:
                expires_str = "Never"

            table.add_row(
                key.id,
                key.prefix,
                key.owner_id,
                ", ".join([r.value for r in key.roles]),
                ", ".join(key.tenants),
                key.created_at.strftime("%Y-%m-%d"),
                expires_str,
                status
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()


@apikey_group.command(name="revoke")
@click.option("--id", "key_id", required=True, help="API key ID to revoke")
def apikey_revoke(key_id: str):
    """
    Revoke API key.

    Examples:
        orchestrator security apikey revoke --id abc123def456
    """
    try:
        key_manager = get_key_manager()

        # Check if key exists
        api_key = key_manager.get_by_id(key_id)
        if not api_key:
            console.print(f"[red]API key not found: {key_id}[/red]")
            raise click.Abort()

        # Confirm revocation
        console.print(f"\n[yellow]Revoking API key:[/yellow]")
        console.print(f"  ID: {api_key.id}")
        console.print(f"  Owner: {api_key.owner_id}")
        console.print(f"  Roles: {', '.join([r.value for r in api_key.roles])}")

        if not click.confirm("\nAre you sure?"):
            console.print("[yellow]Cancelled[/yellow]")
            return

        # Revoke
        success = key_manager.revoke(key_id)
        if not success:
            console.print(f"[red]Failed to revoke key: {key_id}[/red]")
            raise click.Abort()

        # Log audit event
        from .schemas import Identity
        admin_identity = Identity(
            id="cli-admin",
            type="admin",
            roles=[RoleEnum.ADMIN],
            scopes={ScopeEnum.SECURITY_MANAGE},
            tenants=["*"],
            source="cli"
        )

        audit_logger = get_audit_logger()
        audit_logger.log_api_key_revoke(
            identity=admin_identity,
            key_id=key_id,
            trace_id=None
        )

        console.print(f"\n[green]API key revoked: {key_id}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()


@security_group.group(name="tenant")
def tenant_group():
    """Tenant management."""
    pass


@tenant_group.command(name="list")
def tenant_list():
    """
    List configured tenants.

    Examples:
        orchestrator security tenant list
    """
    try:
        import yaml
        from pathlib import Path

        config_path = Path("configs/security.yaml")
        if not config_path.exists():
            console.print("[red]Security config not found: configs/security.yaml[/red]")
            raise click.Abort()

        with open(config_path) as f:
            config = yaml.safe_load(f)

        tenants = config.get("tenants", [])

        if not tenants:
            console.print("[yellow]No tenants configured[/yellow]")
            return

        # Create table
        table = Table(title=f"Configured Tenants ({len(tenants)})")
        table.add_column("Slug", style="cyan")
        table.add_column("Name", style="white")
        table.add_column("Status", style="white")

        for tenant in tenants:
            enabled = tenant.get("enabled", True)
            status = "[green]Enabled[/green]" if enabled else "[red]Disabled[/red]"

            table.add_row(
                tenant.get("slug", ""),
                tenant.get("name", ""),
                status
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()


@tenant_group.command(name="add")
@click.option("--slug", required=True, help="Tenant slug (lowercase, hyphens)")
@click.option("--name", required=True, help="Tenant display name")
def tenant_add(slug: str, name: str):
    """
    Add new tenant to security config.

    Examples:
        orchestrator security tenant add --slug acme-corp --name "Acme Corporation"
    """
    try:
        import yaml
        from pathlib import Path

        config_path = Path("configs/security.yaml")
        if not config_path.exists():
            console.print("[red]Security config not found: configs/security.yaml[/red]")
            raise click.Abort()

        # Load config
        with open(config_path) as f:
            config = yaml.safe_load(f)

        tenants = config.get("tenants", [])

        # Check if tenant already exists
        if any(t.get("slug") == slug for t in tenants):
            console.print(f"[red]Tenant already exists: {slug}[/red]")
            raise click.Abort()

        # Add tenant
        tenants.append({
            "slug": slug,
            "name": name,
            "enabled": True
        })

        config["tenants"] = tenants

        # Write config
        with open(config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        console.print(f"\n[green]Tenant added: {slug}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()


@tenant_group.command(name="remove")
@click.option("--slug", required=True, help="Tenant slug to remove")
def tenant_remove(slug: str):
    """
    Remove tenant from security config.

    Examples:
        orchestrator security tenant remove --slug acme-corp
    """
    try:
        import yaml
        from pathlib import Path

        config_path = Path("configs/security.yaml")
        if not config_path.exists():
            console.print("[red]Security config not found: configs/security.yaml[/red]")
            raise click.Abort()

        # Load config
        with open(config_path) as f:
            config = yaml.safe_load(f)

        tenants = config.get("tenants", [])

        # Find tenant
        tenant = next((t for t in tenants if t.get("slug") == slug), None)
        if not tenant:
            console.print(f"[red]Tenant not found: {slug}[/red]")
            raise click.Abort()

        # Confirm removal
        console.print(f"\n[yellow]Removing tenant:[/yellow]")
        console.print(f"  Slug: {slug}")
        console.print(f"  Name: {tenant.get('name')}")

        if not click.confirm("\nAre you sure?"):
            console.print("[yellow]Cancelled[/yellow]")
            return

        # Remove tenant
        tenants = [t for t in tenants if t.get("slug") != slug]
        config["tenants"] = tenants

        # Write config
        with open(config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        console.print(f"\n[green]Tenant removed: {slug}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()


if __name__ == "__main__":
    security_group()
