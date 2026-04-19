#!/bin/bash

# Define the directory
ICONS_DIR="/home/kyle/Projects/gnome-colorful-battery-indicator/colorful-battery-indicator@aneruam/icons"

# Define mappings
declare -A mappings
mappings["#ef555c"]="#5f10f5"
mappings["#ff8000"]="#4540fb"
mappings["#e09c00"]="#2366f1"
mappings["#e0b700"]="#3b82f6"
mappings["#c1e500"]="#0ea5e9"
mappings["#7bcb00"]="#06b6d4"
mappings["#59e900"]="#14b8a6"
mappings["#31e900"]="#10b981"
mappings["#22e900"]="#10c55e"
mappings["#00cb00"]="#10c020"
mappings["#00ec00"]="#00cc10"

for file in "$ICONS_DIR"/*.svg; do
    echo "Processing $file..."
    for old_color in "${!mappings[@]}"; do
        new_color=${mappings[$old_color]}
        # Replace both fill="#hex" and style="fill:#hex"
        sed -i "s/$old_color/$new_color/gI" "$file"
    done
done
