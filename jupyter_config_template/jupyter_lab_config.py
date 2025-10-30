# Jupyter Lab Configuration for AI Integration
# This file is copied to ~/.config/jupyter-lab/ during deployment

# Configure jupyter-ai to use Anthropic-compatible endpoint
# The API key and base URL are set via environment variables in the systemd service
c.AiExtension.model_provider_id = "anthropic-chat"

# Default model - change this to match your AI provider's model name
# For z.ai's Anthropic endpoint with GLM models
c.AiExtension.default_model = "glm-4.6"

# Configure default model for magic commands (%%ai)
c.AiMagics.default_language_model = "anthropic-chat:glm-4.6"

# Server configuration
c.ServerApp.allow_remote_access = True
c.ServerApp.open_browser = False

# Disable authentication (local sandbox environment)
c.ServerApp.token = ""
c.ServerApp.password = ""

# Allow all origins (local development)
c.ServerApp.allow_origin = "*"
c.ServerApp.disable_check_xsrf = True

# Optional: Customize notebook directory
# This is overridden by the systemd service mount
# c.ServerApp.root_dir = "/workspace/notebooks"
