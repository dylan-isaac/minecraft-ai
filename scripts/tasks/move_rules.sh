#!/bin/bash

# Define directories
TEMP_DIR=".cursor/rules_staging"
RULES_DIR=".cursor/rules"

# Ensure the staging and target directories exist
mkdir -p "$TEMP_DIR"
mkdir -p "$RULES_DIR"

# Check if staging directory exists (should always pass due to mkdir -p)
if [ ! -d "$TEMP_DIR" ]; then
  echo "Error: Directory '$TEMP_DIR' could not be created or found."
  exit 1
fi

# Loop through all .md files in the staging directory
for file in "$TEMP_DIR"/*.md; do
  # Check if the file exists (to handle cases where no .md files are found)
  if [ -f "$file" ]; then
    # Get the base name (e.g., tdd-guidance)
    base_name=$(basename "$file" .md)

    # Define the new name with .mdc extension
    new_name="${base_name}.mdc"

    # Define the destination path
    dest_path="$RULES_DIR/$new_name"

    # Move and rename the file
    mv "$file" "$dest_path"
    echo "Moved and renamed '$file' to '$dest_path'"
  fi
done

# Remove the temporary directory if it's empty
if [ -d "$TEMP_DIR" ] && [ -z "$(ls -A "$TEMP_DIR")" ]; then
  rmdir "$TEMP_DIR"
  echo "Removed empty directory '$TEMP_DIR'"
elif [ -d "$TEMP_DIR" ]; then
 echo "Warning: '$TEMP_DIR' was not empty after processing. Manual cleanup might be needed."
fi

echo "Script finished."
