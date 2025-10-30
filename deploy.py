#!/usr/bin/env python3
# /// script
# dependencies = [
#   "questionary>=2.0.0",
#   "rich>=13.0.0",
#   "tomli-w>=1.0.0",
#   "typer>=0.9.0",
# ]
# requires-python = ">=3.11"
# ///

"""
Jupyter Lab Podman Container - One-Command Deployer

Usage:
    uv run deploy.py              # Smart deployment
    uv run deploy.py --rebuild    # Force rebuild
    uv run deploy.py --status     # Show status only
    uv run deploy.py --stop       # Stop service
"""

import subprocess
import sys
from pathlib import Path
import tomllib
import tomli_w
import questionary
import typer
from rich.console import Console
from rich.panel import Panel
from typing import Optional

app = typer.Typer()
console = Console()

# Configuration paths
CONFIG_DIR = Path.home() / ".config" / "jupyter-lab"
CONFIG_FILE = CONFIG_DIR / "config.toml"
DATA_DIR = Path.home() / ".local" / "share" / "jupyter-lab"
CACHE_DIR = DATA_DIR / ".uv-cache"
SERVICE_FILE = Path.home() / ".config" / "systemd" / "user" / "jupyter-lab.service"

# Default values
DEFAULTS = {
    "ai": {
        "base_url": "https://api.z.ai/v1",
        "model": "glm-4-flash",
    },
    "paths": {
        "notebooks_dir": str(Path.home() / "Documents" / "jupyter"),
    },
    "container": {
        "image_name": "localhost/jupyter-lab:latest",
        "port": 8888,
    },
}


class DeploymentError(Exception):
    """Non-fatal deployment error - we can continue"""
    pass


def load_config() -> dict:
    """Load config from TOML file"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "rb") as f:
            return tomllib.load(f)
    return {}


def save_config(config: dict):
    """Save config to TOML file"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "wb") as f:
        tomli_w.dump(config, f)


def is_config_complete(config: dict) -> tuple[bool, list[str]]:
    """Check if all required fields are present"""
    missing = []
    if not config.get("ai", {}).get("api_key"):
        missing.append("AI API key")
    if not config.get("ai", {}).get("base_url"):
        missing.append("AI API base URL")
    if not config.get("paths", {}).get("notebooks_dir"):
        missing.append("Notebooks directory")
    return len(missing) == 0, missing


def prompt_config(existing_config: dict = None) -> dict:
    """Interactively prompt for configuration"""
    existing_config = existing_config or {}

    console.print("\n[bold]Configuration Setup[/bold]\n")

    # AI Configuration
    api_key = questionary.password(
        "Enter z.ai API key:",
        default=existing_config.get("ai", {}).get("api_key", "")
    ).ask()

    if not api_key:
        console.print("[red]Error:[/red] API key is required")
        sys.exit(1)

    base_url = questionary.text(
        "AI API base URL:",
        default=existing_config.get("ai", {}).get("base_url", DEFAULTS["ai"]["base_url"])
    ).ask().strip()

    model = questionary.select(
        "Select AI model:",
        choices=[
            "glm-4-flash",
            "glm-4",
            "glm-4-plus",
            questionary.Choice("(custom)", "custom")
        ],
        default=existing_config.get("ai", {}).get("model", DEFAULTS["ai"]["model"])
    ).ask()

    if model == "custom":
        model = questionary.text("Enter custom model name:").ask()

    # Paths Configuration
    notebooks_dir = questionary.path(
        "Notebooks directory:",
        default=existing_config.get("paths", {}).get("notebooks_dir", DEFAULTS["paths"]["notebooks_dir"]),
        only_directories=True
    ).ask()

    return {
        "ai": {
            "api_key": api_key,
            "base_url": base_url,
            "model": model,
        },
        "paths": {
            "notebooks_dir": notebooks_dir,
        },
        "container": existing_config.get("container", DEFAULTS["container"]),
    }


def run_command(cmd: list[str], error_msg: str, continue_on_error=True) -> bool:
    """Run a command and handle errors"""
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        return True
    except subprocess.CalledProcessError as e:
        if continue_on_error:
            console.print(f"[yellow]⚠[/yellow] {error_msg}")
            if e.stderr:
                console.print(f"[dim]{e.stderr.strip()}[/dim]")
            return False
        else:
            console.print(f"[red]✗[/red] {error_msg}")
            if e.stderr:
                console.print(f"[dim]{e.stderr.strip()}[/dim]")
            raise DeploymentError(error_msg)


def check_service_status() -> tuple[bool, str]:
    """Check if systemd service is running"""
    try:
        result = subprocess.run(
            ["systemctl", "--user", "is-active", "jupyter-lab.service"],
            capture_output=True,
            text=True
        )
        is_running = result.returncode == 0
        status = result.stdout.strip()
        return is_running, status
    except Exception:
        return False, "unknown"


def build_image(force=False):
    """Build container image"""
    console.print("\n[bold]Building container image...[/bold]")

    # Check if image exists
    if not force:
        result = subprocess.run(
            ["podman", "images", "-q", "localhost/jupyter-lab:latest"],
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            console.print("[green]✓[/green] Image already exists (use --rebuild to force)")
            return True

    with console.status("[bold green]Building..."):
        success = run_command(
            ["podman", "build", "-t", "localhost/jupyter-lab:latest", str(Path(__file__).parent)],
            "Failed to build image"
        )
        if success:
            console.print("[green]✓[/green] Image built successfully")
        return success


def create_directories(config: dict):
    """Create necessary directories"""
    console.print("\n[bold]Creating directories...[/bold]")

    dirs = [
        CONFIG_DIR,
        CACHE_DIR,
        Path(config["paths"]["notebooks_dir"]),
    ]

    for dir_path in dirs:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            console.print(f"[green]✓[/green] {dir_path}")
        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] Failed to create {dir_path}: {e}")


def copy_jupyter_config():
    """Copy Jupyter config templates if they don't exist"""
    import shutil

    configs = [
        ("jupyter_lab_config.py", "Jupyter Lab config"),
        ("ipython_kernel_config.py", "IPython kernel config"),
    ]

    for config_file, description in configs:
        dest = CONFIG_DIR / config_file
        src = Path(__file__).parent / "jupyter_config_template" / config_file

        if not dest.exists() and src.exists():
            try:
                shutil.copy2(src, dest)
                console.print(f"[green]✓[/green] Copied {description} to {dest}")
            except Exception as e:
                console.print(f"[yellow]⚠[/yellow] Failed to copy {description}: {e}")

    # Copy IPython directory structure
    ipython_src = Path(__file__).parent / "jupyter_config_template" / "ipython"
    ipython_dest = CONFIG_DIR / "ipython"

    if ipython_src.exists():
        try:
            shutil.copytree(ipython_src, ipython_dest, dirs_exist_ok=True)
            console.print(f"[green]✓[/green] Copied IPython startup scripts to {ipython_dest}")
        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] Failed to copy IPython config: {e}")


def install_systemd_service(config: dict):
    """Install systemd service file"""
    console.print("\n[bold]Installing systemd service...[/bold]")

    service_content = f"""[Unit]
Description=Jupyter Lab Container
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
Restart=always
RestartSec=5
Environment="JUPYTER_NOTEBOOKS_DIR={config['paths']['notebooks_dir']}"
Environment="OPENAI_API_KEY={config['ai']['api_key']}"
Environment="OPENAI_BASE_URL={config['ai']['base_url']}"
Environment="ANTHROPIC_API_KEY={config['ai']['api_key']}"
Environment="ANTHROPIC_BASE_URL={config['ai']['base_url']}"

ExecStartPre=-/usr/bin/podman stop jupyter-lab
ExecStart=/usr/bin/podman run --rm --name jupyter-lab \\
  --net=host \\
  -e OPENAI_API_KEY \\
  -e OPENAI_BASE_URL \\
  -e ANTHROPIC_API_KEY \\
  -e ANTHROPIC_BASE_URL \\
  -v ${{JUPYTER_NOTEBOOKS_DIR}}:/workspace/notebooks:Z \\
  -v %h/.local/share/jupyter-lab/.uv-cache:/workspace/.uv-cache:Z \\
  -v %h/.config/jupyter-lab:/workspace/.jupyter:Z \\
  {config['container']['image_name']}

ExecStop=/usr/bin/podman stop -t 10 jupyter-lab

[Install]
WantedBy=default.target
"""

    SERVICE_FILE.parent.mkdir(parents=True, exist_ok=True)
    SERVICE_FILE.write_text(service_content)
    console.print(f"[green]✓[/green] {SERVICE_FILE}")

    # Reload systemd
    if run_command(
        ["systemctl", "--user", "daemon-reload"],
        "Failed to reload systemd",
        continue_on_error=True
    ):
        console.print("[green]✓[/green] Systemd configuration reloaded")


def start_service():
    """Start systemd service"""
    console.print("\n[bold]Starting service...[/bold]")

    with console.status("[bold green]Starting..."):
        if run_command(
            ["systemctl", "--user", "start", "jupyter-lab.service"],
            "Failed to start service"
        ):
            run_command(
                ["systemctl", "--user", "enable", "jupyter-lab.service"],
                "Failed to enable service",
                continue_on_error=True
            )
            console.print("[green]✓[/green] Service started")
            return True
    return False


def stop_service():
    """Stop systemd service"""
    console.print("\n[bold]Stopping service...[/bold]")

    if run_command(
        ["systemctl", "--user", "stop", "jupyter-lab.service"],
        "Failed to stop service"
    ):
        console.print("[green]✓[/green] Service stopped")
        return True
    return False


def show_status(config: dict):
    """Show service status and information"""
    is_running, status = check_service_status()

    if is_running:
        panel_content = (
            "[green]✓[/green] Jupyter Lab is running\n\n"
            f"Access at: [blue]http://localhost:{config['container']['port']}[/blue]\n"
            f"Notebooks: [cyan]{config['paths']['notebooks_dir']}[/cyan]\n"
            f"Service: [dim]jupyter-lab.service[/dim]"
        )

        console.print(Panel.fit(panel_content, title="Jupyter Lab Status", border_style="green"))

        # Show recent logs
        console.print("\n[bold]Recent logs:[/bold]")
        subprocess.run(
            ["journalctl", "--user", "-u", "jupyter-lab.service", "-n", "10", "--no-pager"],
            check=False
        )

        console.print("\n[dim]Commands:[/dim]")
        console.print("  [cyan]systemctl --user restart jupyter-lab[/cyan]  # Restart")
        console.print("  [cyan]journalctl --user -u jupyter-lab -f[/cyan]   # View logs")
        console.print("  [cyan]uv run deploy.py --stop[/cyan]             # Stop service")
    else:
        console.print(Panel.fit(
            f"[yellow]⚠[/yellow] Service is not running (status: {status})",
            title="Jupyter Lab Status",
            border_style="yellow"
        ))


@app.command()
def main(
    rebuild: bool = typer.Option(False, "--rebuild", help="Force rebuild container image"),
    reconfigure: bool = typer.Option(False, "--reconfigure", help="Re-prompt for configuration"),
    status_only: bool = typer.Option(False, "--status", help="Only show status"),
    stop: bool = typer.Option(False, "--stop", help="Stop the service"),
):
    """
    Jupyter Lab Podman Container - One-Command Deployer
    """
    console.print(Panel.fit(
        "[bold]Jupyter Lab Deployment[/bold]",
        border_style="blue"
    ))

    # Handle --stop
    if stop:
        stop_service()
        return

    # Load existing config
    config = load_config()
    is_complete, missing = is_config_complete(config)

    # Handle --reconfigure or missing config
    if reconfigure or not is_complete:
        if not is_complete:
            console.print(f"\n[yellow]Missing configuration:[/yellow] {', '.join(missing)}")
        config = prompt_config(config if reconfigure else {})
        save_config(config)
        console.print("\n[green]✓[/green] Configuration saved")

    # Handle --status
    if status_only:
        show_status(config)
        return

    # Check if service is already running
    is_running, _ = check_service_status()

    if is_running and not rebuild:
        show_status(config)
        return

    # Full deployment
    if not build_image(force=rebuild):
        console.print("[yellow]⚠[/yellow] Continuing despite build issues...")

    create_directories(config)
    copy_jupyter_config()
    install_systemd_service(config)

    # Start or restart service
    if is_running:
        console.print("\n[bold]Restarting service...[/bold]")
        stop_service()

    if start_service():
        import time
        time.sleep(2)  # Give service time to start
        show_status(config)
    else:
        console.print("[red]✗[/red] Failed to start service. Check logs:")
        console.print("  [cyan]journalctl --user -u jupyter-lab -n 50[/cyan]")


if __name__ == "__main__":
    app()
