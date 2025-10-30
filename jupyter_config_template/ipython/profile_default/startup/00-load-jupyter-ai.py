# Auto-load jupyter_ai_magics extension and configure default model
# Note: Must use extension_manager for ZMQInteractiveShell (Jupyter kernels)
# The .magic() method doesn't exist in kernel shells

ip = get_ipython()

try:
    # Load extension using extension_manager (correct method for kernels)
    ip.extension_manager.load_extension('jupyter_ai_magics')

    # Configure default model for %%ai magic
    # This must be done after loading the extension
    from jupyter_ai_magics.magics import AiMagics
    ai_magics_instance = ip.magics_manager.registry.get('AiMagics')
    if ai_magics_instance:
        ai_magics_instance.default_language_model = "anthropic-chat:glm-4.6"

except Exception as e:
    print(f"Error configuring jupyter_ai_magics: {e}")
