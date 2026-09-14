import json
import math
from pathlib import Path
from PIL import Image, ImageDraw

def create_enchanting_table_model():
    return {
        "parent": "block/block",
        "textures": {
            "particle": "block/enchanting_table_bottom",
            "bottom": "block/enchanting_table_bottom",
            "top": "block/enchanting_table_top",
            "side": "block/enchanting_table_side",
            "book": "entity/enchanting_table_book"
        },
        "elements": [
            # 1. Base pedestal
            {
                "name": "base",
                "from": [0, 0, 0],
                "to": [16, 12, 16],
                "faces": {
                    "down":  { "uv": [0, 0, 16, 16], "texture": "#bottom", "cullface": "down" },
                    "up":    { "uv": [0, 0, 16, 16], "texture": "#top" },
                    "north": { "uv": [0, 4, 16, 16], "texture": "#side", "cullface": "north" },
                    "south": { "uv": [0, 4, 16, 16], "texture": "#side", "cullface": "south" },
                    "west":  { "uv": [0, 4, 16, 16], "texture": "#side", "cullface": "west" },
                    "east":  { "uv": [0, 4, 16, 16], "texture": "#side", "cullface": "east" }
                }
            },
            # 2. Book spine (seam)
            {
                "name": "book_spine",
                "from": [7.3, 13.2, 3.0],
                "to": [8.7, 13.6, 13.0],
                "faces": {
                    "down":  { "uv": [3.0, 0.0, 3.5, 5.0], "texture": "#book" },
                    "up":    { "uv": [3.0, 0.0, 3.5, 5.0], "texture": "#book" },
                    "north": { "uv": [3.0, 0.0, 3.5, 0.5], "texture": "#book" },
                    "south": { "uv": [3.0, 4.5, 3.5, 5.0], "texture": "#book" }
                }
            },
            # 3. Left cover
            {
                "name": "book_left_lid",
                "from": [1.5, 13.2, 3.0],
                "to": [7.5, 13.5, 13.0],
                "rotation": {
                    "origin": [7.5, 13.5, 8.0],
                    "axis": "z",
                    "angle": -22.5
                },
                "faces": {
                    "down":  { "uv": [0.0, 0.0, 1.5, 5.0], "texture": "#book" },
                    "up":    { "uv": [1.5, 0.0, 3.0, 5.0], "texture": "#book" },
                    "west":  { "uv": [0.0, 0.0, 0.25, 5.0], "texture": "#book" },
                    "north": { "uv": [0.0, 0.0, 1.5, 0.25], "texture": "#book" },
                    "south": { "uv": [0.0, 4.75, 1.5, 5.0], "texture": "#book" }
                }
            },
            # 4. Right cover
            {
                "name": "book_right_lid",
                "from": [8.5, 13.2, 3.0],
                "to": [14.5, 13.5, 13.0],
                "rotation": {
                    "origin": [8.5, 13.5, 8.0],
                    "axis": "z",
                    "angle": 22.5
                },
                "faces": {
                    "down":  { "uv": [5.5, 0.0, 7.0, 5.0], "texture": "#book" },
                    "up":    { "uv": [4.0, 0.0, 5.5, 5.0], "texture": "#book" },
                    "east":  { "uv": [6.75, 0.0, 7.0, 5.0], "texture": "#book" },
                    "north": { "uv": [5.5, 0.0, 7.0, 0.25], "texture": "#book" },
                    "south": { "uv": [5.5, 4.75, 7.0, 5.0], "texture": "#book" }
                }
            },
            # 5. Left pages
            {
                "name": "book_left_pages",
                "from": [2.3, 13.5, 4.0],
                "to": [7.3, 14.3, 12.0],
                "rotation": {
                    "origin": [7.5, 13.5, 8.0],
                    "axis": "z",
                    "angle": -22.5
                },
                "faces": {
                    "up":    { "uv": [0.25, 5.5, 1.5, 9.5], "texture": "#book" },
                    "down":  { "uv": [1.5, 5.0, 2.75, 5.5], "texture": "#book" },
                    "west":  { "uv": [0.0, 5.5, 0.25, 9.5], "texture": "#book" },
                    "north": { "uv": [0.25, 5.0, 1.5, 5.5], "texture": "#book" },
                    "south": { "uv": [1.75, 5.5, 3.0, 6.0], "texture": "#book" }
                }
            },
            # 6. Right pages
            {
                "name": "book_right_pages",
                "from": [8.7, 13.5, 4.0],
                "to": [13.7, 14.3, 12.0],
                "rotation": {
                    "origin": [8.5, 13.5, 8.0],
                    "axis": "z",
                    "angle": 22.5
                },
                "faces": {
                    "up":    { "uv": [3.25, 5.5, 4.5, 9.5], "texture": "#book" },
                    "down":  { "uv": [4.5, 5.0, 5.75, 5.5], "texture": "#book" },
                    "east":  { "uv": [4.5, 5.5, 4.75, 9.5], "texture": "#book" },
                    "north": { "uv": [3.25, 5.0, 4.5, 5.5], "texture": "#book" },
                    "south": { "uv": [4.75, 5.5, 6.0, 6.0], "texture": "#book" }
                }
            }
        ]
    }

if __name__ == "__main__":
    model = create_enchanting_table_model()
    out_json = Path("/Users/mio/project/BlueMapEntities/src/main/resources/assets/minecraft/models/block/enchanting_table.json")
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(model, f, indent=2)
    print("Written to", out_json)
