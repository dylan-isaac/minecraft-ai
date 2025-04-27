#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status.

ENV_FILE=".env"
OVERRIDE_FILE="docker-compose.override.yml"
ENV_EXAMPLE=".env.example"
OVERRIDE_EXAMPLE="docker-compose.override.yml.example"

# --- Check if files exist ---
if [ -f "$ENV_FILE" ] || [ -f "$OVERRIDE_FILE" ]; then
    echo "WARNING: $ENV_FILE or $OVERRIDE_FILE already exists."
    read -p "Overwrite existing configuration? (y/N): " -n 1 -r
    echo # Move to a new line
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Initialization aborted. No changes made."
        exit 1
    fi
    echo "Proceeding with overwrite..."
fi

# --- Copy example files ---
echo "Creating initial configuration files..."
cp "$ENV_EXAMPLE" "$ENV_FILE"
cp "$OVERRIDE_EXAMPLE" "$OVERRIDE_FILE"

# --- Gather user input ---
echo "Please provide the following configuration values:"

# Prism Launcher Host Path
DEFAULT_PRISM_PATH="/Users/$USER/Library/Application Support/PrismLauncher" # Common macOS path
read -p "Enter the absolute path to your PrismLauncher folder on this host machine [default: $DEFAULT_PRISM_PATH]: " PRISM_HOST_PATH
PRISM_HOST_PATH="${PRISM_HOST_PATH:-$DEFAULT_PRISM_PATH}" # Use default if empty

# Mod Target Container Path
DEFAULT_TARGET_DIR="/prism-launcher/instances/YourInstanceName/.minecraft/mods" # Example
read -p "Enter the desired mod deployment path *inside the container* (e.g., /prism-launcher/instances/MyInstance/.minecraft/mods) [Leave blank to skip deployment]: " MOD_TARGET_DIR
# No default here, user must provide it or leave blank

# API Keys
read -p "Enter your OpenAI API Key (starts with sk-...): " OPENAI_KEY
read -p "Enter your Minecraft AI API Key (starts with mcai_...) [optional, can generate later]: " MINECRAFT_AI_KEY

# --- Replace placeholders ---
echo "Updating configuration files..."

# Use different delimiters for sed to handle paths with slashes
SED_DELIMITER='#'

# Update docker-compose.override.yml
sed -i.bak "s${SED_DELIMITER}__PRISM_LAUNCHER_HOST_PATH_PLACEHOLDER__${SED_DELIMITER}${PRISM_HOST_PATH}${SED_DELIMITER}g" "$OVERRIDE_FILE"

# Update .env
sed -i.bak "s${SED_DELIMITER}YOUR_OPENAI_API_KEY_HERE${SED_DELIMITER}${OPENAI_KEY}${SED_DELIMITER}g" "$ENV_FILE"
sed -i.bak "s${SED_DELIMITER}YOUR_MINECRAFT_AI_API_KEY_HERE${SED_DELIMITER}${MINECRAFT_AI_KEY}${SED_DELIMITER}g" "$ENV_FILE"
sed -i.bak "s${SED_DELIMITER}__MINECRAFT_MOD_TARGET_DIR_PLACEHOLDER__${SED_DELIMITER}${MOD_TARGET_DIR}${SED_DELIMITER}g" "$ENV_FILE"

# Remove backup files created by sed -i
rm -f "${OVERRIDE_FILE}.bak"
rm -f "${ENV_FILE}.bak"

echo "
✅ Initialization Complete!

Configuration saved to $ENV_FILE and $OVERRIDE_FILE.
These files are ignored by Git.

➡️ Next Step: If you are in VS Code or Cursor, run the 'Dev Containers: Reopen in Container' command.
   Otherwise, restart your Docker Compose setup.
"

exit 0
