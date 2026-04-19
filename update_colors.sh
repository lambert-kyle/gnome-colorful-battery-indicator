#!/bin/bash

# Define the directory
ICONS_DIR="/home/kyle/Projects/gnome-colorful-battery-indicator/colorful-battery-indicator@aneruam/icons"

# Define mappings
declare -A mappings
# Round 1 migration
# mappings["#ef555c"]="#5f10f5"
# mappings["#ff8000"]="#4540fb"
# mappings["#e09c00"]="#2366f1"
# mappings["#e0b700"]="#3b82f6"
# mappings["#c1e500"]="#0ea5e9"
# mappings["#7bcb00"]="#06b6d4"
# mappings["#59e900"]="#14b8a6"
# mappings["#31e900"]="#10b981"
# mappings["#22e900"]="#10c55e"
# mappings["#00cb00"]="#10c020"
# mappings["#00ec00"]="#00cc10"

# Round 2 migrationmappings
["#00cc10"]="#00cc10"
mappings["#10c020"]="#22d43a"
mappings["#10c55e"]="#6ee89a"
mappings["#10b981"]="#b4f2d0"
mappings["#14b8a6"]="#dffaf0"
mappings["#06b6d4"]="#ffffff"
mappings["#0ea5e9"]="#c8d8fc"
mappings["#3b82f6"]="#8aaaf8"
mappings["#2366f1"]="#6080f4"
mappings["#4540fb"]="#3040e4"
mappings["#5f10f5"]="#2a10f8"

for file in "$ICONS_DIR"/*.svg; do
    echo "Processing $file..."
    for old_color in "${!mappings[@]}"; do
        new_color=${mappings[$old_color]}
        # Replace both fill="#hex" and style="fill:#hex"
        sed -i "s/$old_color/$new_color/gI" "$file"
    done
done
