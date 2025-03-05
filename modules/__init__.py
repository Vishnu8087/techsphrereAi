import os

# Create __init__.py if it doesn't exist
modules_dir = "modules"
if not os.path.exists(os.path.join(modules_dir, "__init__.py")):
    with open(os.path.join(modules_dir, "__init__.py"), "w") as f:
        pass  # Creates an empty file