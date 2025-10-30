# Auto-load jupyter_ai_magics extension and configure default model
# Note: Must use extension_manager for ZMQInteractiveShell (Jupyter kernels)
# The .magic() method doesn't exist in kernel shells

ip = get_ipython()

try:
    # Load extension using extension_manager (correct method for kernels)
    ip.extension_manager.load_extension('jupyter_ai_magics')

    # Configure default model for %%ai magic with higher token limit
    # This must be done after loading the extension
    from jupyter_ai_magics.magics import AiMagics
    ai_magics_instance = ip.magics_manager.registry.get('AiMagics')
    if ai_magics_instance:
        # Set default model
        ai_magics_instance.default_language_model = "anthropic-chat:glm-4.6"

        # Set default max_tokens to 16384 (GLM-4.6 supports up to 128k)
        # This applies to all %%ai calls unless overridden with -m parameter
        ai_magics_instance.default_model_parameters = {"max_tokens": 16384}

except Exception as e:
    print(f"Error configuring jupyter_ai_magics: {e}")
