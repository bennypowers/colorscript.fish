#!/usr/bin/env python3

import os
import sys
import tempfile
import shutil
import stat
from PIL import Image
import requests
import readline # Enables history and editing for input()

# --- Sprite Slicing Logic ---
def find_sprites(image_path, output_dir):
    try:
        img = Image.open(image_path).convert("RGBA")
    except IOError:
        print(f"Error: Cannot open image at {image_path}", file=sys.stderr)
        return []

    width, height = img.size
    pixels = img.load()
    bg_color = pixels[0, 0]
    print(f"Detected background color: {bg_color}", file=sys.stderr)

    visited = set()
    components = []

    for y in range(height):
        for x in range(width):
            if (x, y) in visited or pixels[x, y] == bg_color:
                continue

            q = [(x, y)]
            visited.add((x, y))
            min_x, max_x, min_y, max_y = x, x, y, y
            head = 0
            while head < len(q):
                px, py = q[head]
                head += 1
                min_x, max_x = min(min_x, px), max(max_x, px)
                min_y, max_y = min(min_y, py), max(max_y, py)
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nx, ny = px + dx, py + dy
                    if 0 <= nx < width and 0 <= ny < height and \
                       (nx, ny) not in visited and pixels[nx, ny] != bg_color:
                        visited.add((nx, ny))
                        q.append((nx, ny))
            
            components.append([min_x, min_y, max_x + 1, max_y + 1])

    if not components:
        return []

    # --- Intelligent Component Grouping ---
    
    # Calculate areas and identify the largest component
    areas = [(c[2]-c[0]) * (c[3]-c[1]) for c in components]
    max_area = max(areas) if areas else 0
    
    # Define bodies and fragments
    bodies = [c for c, a in zip(components, areas) if a >= 0.1 * max_area]
    fragments = [c for c, a in zip(components, areas) if a < 0.1 * max_area]

    # Merge fragments into the nearest body
    for frag in fragments:
        frag_center_x = (frag[0] + frag[2]) / 2
        frag_center_y = (frag[1] + frag[3]) / 2
        
        closest_body = None
        min_dist = float('inf')

        for i, body in enumerate(bodies):
            body_center_x = (body[0] + body[2]) / 2
            body_center_y = (body[1] + body[3]) / 2
            dist = ((frag_center_x - body_center_x)**2 + (frag_center_y - body_center_y)**2)**0.5
            if dist < min_dist:
                min_dist = dist
                closest_body = i
        
        if closest_body is not None:
            bodies[closest_body][0] = min(bodies[closest_body][0], frag[0])
            bodies[closest_body][1] = min(bodies[closest_body][1], frag[1])
            bodies[closest_body][2] = max(bodies[closest_body][2], frag[2])
            bodies[closest_body][3] = max(bodies[closest_body][3], frag[3])

    # Save the final merged sprites
    sprite_files = []
    for i, sprite_box in enumerate(bodies):
        sprite_img = img.crop(tuple(sprite_box))
        sprite_filename = os.path.join(output_dir, f"sprite_{i}.png")
        sprite_img.save(sprite_filename)
        sprite_files.append(sprite_filename)
        
    print(f"Found and saved {len(bodies)} sprites after merging.", file=sys.stderr)
    return sprite_files

# --- Colorscript Creation Logic ---
def convert_to_colorscript(image_path):
    try:
        img = Image.open(image_path).convert("RGBA")
    except IOError:
        return ""

    width, height = img.size
    pixels = img.load()
    bg_color = pixels[0, 0]

    min_x, max_x, min_y, max_y = width, -1, height, -1
    for y in range(height):
        for x in range(width):
            if pixels[x, y] != bg_color:
                min_x, max_x = min(min_x, x), max(max_x, x)
                min_y, max_y = min(min_y, y), max(max_y, y)

    if max_x == -1: return ""

    script_body = 'printf "\\n'
    for y in range(min_y, max_y + 1, 2):
        line_output = ""
        for x in range(min_x, max_x + 1):
            r1, g1, b1, a1 = pixels[x, y]
            is_upper_transparent = a1 == 0 or (r1, g1, b1, a1) == bg_color
            if y + 1 <= max_y:
                r2, g2, b2, a2 = pixels[x, y + 1]
                is_lower_transparent = a2 == 0 or (r2, g2, b2, a2) == bg_color
            else:
                is_lower_transparent = True

            if is_upper_transparent and is_lower_transparent:
                line_output += f'\\e[49m '
            elif not is_upper_transparent and is_lower_transparent:
                line_output += f'\\e[38;2;{r1};{g1};{b1}m\\e[49m▀'
            elif is_upper_transparent and not is_lower_transparent:
                line_output += f'\\e[38;2;{r2};{g2};{b2}m\\e[49m▄'
            else:
                if (r1, g1, b1) == (r2, g2, b2):
                    line_output += f'\\e[48;2;{r1};{g1};{b1}m '
                else:
                    line_output += f'\\e[38;2;{r1};{g1};{b1}m\\e[48;2;{r2};{g2};{b2}m▀'
        script_body += line_output + '\\e[0m\\n'
    script_body += '"\n'
    
    return f"#!/usr/bin/env fish\n\n# Generated by gen-colorscripts\n{script_body}"

# --- Main Application Logic ---
def main():
    if len(sys.argv) != 2:
        print("Usage: gen-colorscripts <path_or_url_to_sprite_sheet>", file=sys.stderr)
        sys.exit(1)

    source = sys.argv[1]
    temp_dir = tempfile.mkdtemp()
    
    try:
        if source.startswith(('http://', 'https://')):
            print(f"Downloading from {source}...", file=sys.stderr)
            response = requests.get(source, stream=True)
            response.raise_for_status()
            sheet_path = os.path.join(temp_dir, "sheet.png")
            with open(sheet_path, 'wb') as f:
                shutil.copyfileobj(response.raw, f)
            print("Download complete.", file=sys.stderr)
        else:
            sheet_path = source

        sprite_files = find_sprites(sheet_path, temp_dir)
        if not sprite_files:
            print("No sprites found.", file=sys.stderr)
            return

        target_dir = os.path.join(
            os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share")),
            "colorscripts"
        )
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
            print(f"Created directory: {target_dir}", file=sys.stderr)
        
        existing = {f.replace('.fish', '') for f in os.listdir(target_dir)}

        for sprite_path in sprite_files:
            script_content = convert_to_colorscript(sprite_path)
            if not script_content:
                print(f"Skipping empty sprite: {os.path.basename(sprite_path)}", file=sys.stderr)
                continue
            
            os.system(f'fish -c \'{script_content}\'')
            
            while True:
                try:
                    name = input(f"Enter a name for this script (or press Enter to skip): ")
                    if not name:
                        print("Skipping...", file=sys.stderr)
                        break
                    
                    save_path = os.path.join(target_dir, f"{name}.fish")
                    if name in existing:
                        overwrite = input(f"Warning: '{name}.fish' already exists. Overwrite? (y/N): ").lower()
                        if overwrite != 'y':
                            print("Save cancelled.", file=sys.stderr)
                            continue
                    
                    with open(save_path, "w") as f:
                        f.write(script_content)
                    
                    st = os.stat(save_path)
                    os.chmod(save_path, st.st_mode | stat.S_IEXEC)

                    print(f"Saved to {save_path} and made executable.", file=sys.stderr)
                    existing.add(name)
                    break
                except (EOFError, KeyboardInterrupt):
                    print("\nExiting.", file=sys.stderr)
                    return
    
    finally:
        print("Cleaning up temporary files...", file=sys.stderr)
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    main()
