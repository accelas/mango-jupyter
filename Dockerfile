FROM ghcr.io/astral-sh/uv:python3.13-trixie-slim

# Set working directory
WORKDIR /workspace

# Install Jupyter Lab and jupyter-ai using uv
# Installing to system Python since this is a container
RUN uv pip install --system \
    jupyterlab \
    jupyter-ai \
    jupyter-ai-magics \
    ipykernel \
    openai \
    "langchain-openai<1.0" \
    "langchain-anthropic<1.0"

# Expose Jupyter Lab port
EXPOSE 8888

# Set environment variables
# UV_CACHE_DIR will be overridden by bind mount
ENV UV_CACHE_DIR=/workspace/.uv-cache
ENV JUPYTER_CONFIG_DIR=/workspace/.jupyter
ENV IPYTHONDIR=/workspace/.jupyter/ipython

# Start Jupyter Lab with no authentication
# This is a local sandbox environment
CMD ["jupyter", "lab", \
     "--ip=0.0.0.0", \
     "--port=8888", \
     "--no-browser", \
     "--allow-root", \
     "--ServerApp.token=", \
     "--ServerApp.password=", \
     "--ServerApp.allow_origin=*", \
     "--ServerApp.disable_check_xsrf=True", \
     "--ServerApp.root_dir=/workspace/notebooks"]
