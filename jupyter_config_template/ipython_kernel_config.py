# IPython Kernel Configuration
# This file is for kernel-level settings like auto-loading extensions

# Auto-load jupyter_ai_magics extension on kernel start
c.InteractiveShellApp.exec_lines = [
    '%load_ext jupyter_ai_magics'
]
