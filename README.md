# Jupyter Lab Podman Container

A containerized Jupyter Lab environment with AI assistant integration, managed by systemd.

## Features

- **Python 3.13** via uv base image
- **UV package manager** with persistent cache for fast dependency management
- **Jupyter Lab** with interactive notebooks
- **AI Assistant** integration via jupyter-ai-magics (Anthropic-compatible API)
  - Supports GLM 4.6 from z.ai
  - Auto-loads on kernel start with default model configured
  - Works with any Anthropic-compatible or OpenAI-compatible endpoint
- **No authentication** (local sandbox environment)
- **Systemd user service** for lifecycle management
- **One-command deployment** with interactive setup

## Quick Start

```bash
# Clone or navigate to this repository
cd /home/kai/work/jupyter

# Run the deployment script
uv run deploy.py
```

The script will:
1. Prompt for configuration (API key, model, notebooks directory)
2. Build the container image
3. Create necessary directories
4. Install and start the systemd service
5. Show the access URL

## Prerequisites

- Python 3.11+ (for running deploy.py)
- Podman
- systemd
- uvx (from uv)

Install uv if you haven't already:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Configuration

Configuration is stored in `~/.config/jupyter-lab/config.toml`:

```toml
[ai]
api_key = "your-api-key"
base_url = "https://api.z.ai/api/anthropic"
model = "glm-4.6"

[paths]
notebooks_dir = "/home/user/Documents/jupyter"

[container]
image_name = "localhost/jupyter-lab:latest"
port = 8888
```

### Reconfiguring

To change configuration values:

```bash
uv run deploy.py --reconfigure
```

Or edit `~/.config/jupyter-lab/config.toml` directly and restart:

```bash
systemctl --user restart jupyter-lab
```

## Usage

### Daily Usage

Simply run the deployment script - it will start the service if it's not running, or show the status if it is:

```bash
uv run deploy.py
```

Access Jupyter Lab at: http://localhost:8888

### Advanced Commands

```bash
# Force rebuild the container image
uv run deploy.py --rebuild

# Show status without starting
uv run deploy.py --status

# Stop the service
uv run deploy.py --stop

# Restart the service (after changing Jupyter config)
systemctl --user restart jupyter-lab

# View logs
journalctl --user -u jupyter-lab -f

# Check service status
systemctl --user status jupyter-lab
```

### Using AI Assistant in Jupyter

The jupyter-ai-magics extension provides AI capabilities in your notebooks:

1. **Magic commands** in code cells (auto-loaded on kernel start):
   ```python
   # Simple shorthand with default 16k token limit
   # (uses: anthropic-chat:glm-4.6, max_tokens: 16384)
   %%ai
   Explain how to use pandas DataFrames
   ```

   The default max_tokens is set to **16384**, which provides detailed responses without truncation. For even longer responses (GLM-4.6 supports up to 128k):
   ```python
   # For very long responses (32k tokens)
   %%ai -m '{"max_tokens": 32768}'
   Write a comprehensive tutorial on ANOVA with examples

   # For extremely long responses (64k tokens)
   %%ai -m '{"max_tokens": 65536}'
   Create a detailed data science textbook chapter
   ```

   Specify a different model explicitly:
   ```python
   %%ai anthropic-chat:glm-4.6
   Write a function to calculate fibonacci numbers
   ```

2. **Chat interface**: Click the AI chat icon in the sidebar

3. **Code generation**: Ask the AI to generate code directly in cells

## Directory Structure

### Development (this repository)
```
/home/kai/work/jupyter/
├── deploy.py                                      # One-command deployment script
├── Dockerfile                                     # Container definition
├── README.md                                      # This file
├── jupyter_config_template/                       # Configuration templates
│   ├── jupyter_lab_config.py                     # Jupyter Lab config
│   ├── ipython_kernel_config.py                  # IPython kernel config
│   └── ipython/profile_default/startup/
│       └── 00-load-jupyter-ai.py                 # Auto-load AI extension
└── .gitignore
```

### Deployment (on your system)
```
~/.config/jupyter-lab/
├── config.toml                                    # Deployment configuration
├── jupyter_lab_config.py                          # Jupyter Lab config
├── ipython_kernel_config.py                       # IPython kernel config
└── ipython/profile_default/startup/
    └── 00-load-jupyter-ai.py                      # Auto-loads jupyter_ai_magics

~/.local/share/jupyter-lab/
└── .uv-cache/                                     # Persistent UV cache

~/.config/systemd/user/
└── jupyter-lab.service                            # Systemd service unit

~/Documents/jupyter/                               # Your notebooks (configurable)
└── *.ipynb
```

## How It Works

1. **Container**: Runs Jupyter Lab in a Podman container with host networking
2. **UV Integration**: Uses uv for fast Python package installation, with cache persisted on host
3. **Bind Mounts**:
   - Notebooks directory → `/workspace/notebooks` in container
   - UV cache → `/workspace/.uv-cache` in container
   - Jupyter config → `/workspace/.jupyter` in container (includes IPython startup scripts)
4. **Systemd**: Manages container lifecycle (start on boot, restart on failure)
5. **AI Integration**:
   - Environment variables configure Anthropic-compatible API endpoint
   - IPython startup script auto-loads jupyter_ai_magics on every kernel start
   - Default model configured for shorthand `%%ai` usage

## Using UV in the Container

Access the container shell:
```bash
podman exec -it jupyter-lab bash
```

Install packages with uv:
```bash
# In container
uv pip install pandas numpy matplotlib

# Or use uvx to run tools without installing
uvx ruff check .
```

The UV cache is persisted, so packages install quickly on subsequent runs.

## Customization

### Change AI Model

Edit the startup script `~/.config/jupyter-lab/ipython/profile_default/startup/00-load-jupyter-ai.py`:

```python
# Change the default model
ai_magics_instance.default_language_model = "anthropic-chat:glm-4.6"  # or any other model
```

Or edit `~/.config/jupyter-lab/jupyter_lab_config.py` for the chat interface:
```python
c.AiExtension.default_model = "glm-4.6"
```

Restart the service to apply changes:
```bash
systemctl --user restart jupyter-lab
```

### Change Port

Edit `~/.config/jupyter-lab/config.toml`:

```toml
[container]
port = 9999
```

And update the Dockerfile's EXPOSE line, then rebuild:
```bash
uv run deploy.py --rebuild
```

### Add More Python Packages

Option 1: Install in the container (temporary):
```bash
podman exec jupyter-lab uv pip install --system package-name
```

Option 2: Add to Dockerfile (permanent):
```dockerfile
RUN uv pip install --system \
    jupyterlab \
    jupyter-ai \
    jupyter-ai-magics \
    ipykernel \
    openai \
    langchain-anthropic \
    langchain-openai \
    your-package-here
```

Then rebuild:
```bash
uv run deploy.py --rebuild
```

### Use a Different AI Provider

The setup works with any Anthropic-compatible or OpenAI-compatible API. Just update the configuration:

```toml
[ai]
api_key = "your-key"
base_url = "https://api.provider.com/v1"  # or /api/anthropic for Anthropic-compatible
model = "model-name"
```

Note: If using OpenAI-compatible endpoints, you may need to install `langchain-openai` in the container.

## Troubleshooting

### Service won't start

Check logs:
```bash
journalctl --user -u jupyter-lab -n 50
```

Common issues:
- Podman not installed: `sudo apt install podman`
- Port 8888 already in use: Change port in config
- API key invalid: Run `uv run deploy.py --reconfigure`

### Image build fails

Make sure you're in the correct directory:
```bash
cd /home/kai/work/jupyter
uv run deploy.py --rebuild
```

### Cannot access Jupyter Lab

1. Check service is running: `systemctl --user status jupyter-lab`
2. Check port: `ss -tlnp | grep 8888`
3. Try http://127.0.0.1:8888 instead of localhost

### AI assistant not working

1. Check API key is set: `cat ~/.config/jupyter-lab/config.toml`
2. Check API endpoint is accessible: `curl -I https://api.z.ai/api/anthropic`
3. Verify extension is loaded: In a notebook, run `'ai' in get_ipython().magics_manager.magics.get('cell', {})`
4. View container logs: `journalctl --user -u jupyter-lab -f`

## Development

### Building Locally

```bash
podman build -t localhost/jupyter-lab:latest .
```

### Testing Container Manually

```bash
podman run --rm -it \
  --net=host \
  -e ANTHROPIC_API_KEY="your-key" \
  -e ANTHROPIC_BASE_URL="https://api.z.ai/api/anthropic" \
  -v ~/Documents/jupyter:/workspace/notebooks:Z \
  -v ~/.local/share/jupyter-lab/.uv-cache:/workspace/.uv-cache:Z \
  -v ~/.config/jupyter-lab:/workspace/.jupyter:Z \
  localhost/jupyter-lab:latest
```

### Publishing to Registry

```bash
# Tag for registry
podman tag localhost/jupyter-lab:latest ghcr.io/username/jupyter-lab:latest

# Push to registry
podman push ghcr.io/username/jupyter-lab:latest

# Update config to use registry image
# Edit ~/.config/jupyter-lab/config.toml:
[container]
image_name = "ghcr.io/username/jupyter-lab:latest"
```

## Security Notes

- **No authentication**: This setup disables Jupyter authentication for local use
- **API keys in systemd**: API keys are stored in the systemd service file
- **Host networking**: Container uses host network (no isolation)
- **Local only**: Only suitable for local development, not production

For production use, consider:
- Enabling Jupyter authentication
- Using container networking with port mapping
- Storing secrets in a secret manager
- Using HTTPS with a reverse proxy

## License

This is a personal development environment setup. Modify as needed for your use case.
