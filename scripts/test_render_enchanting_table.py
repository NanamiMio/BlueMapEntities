import json
from pathlib import Path
from PIL import Image
import sys

sys.path.append("/Users/mio/project/BlueMapEntities/scripts")
from verify_model import ModelVerifier, ModelViewRenderer

verifier = ModelVerifier()
renderer = ModelViewRenderer(canvas_size=(1000, 800))

model_path = Path("/Users/mio/project/BlueMapEntities/src/main/resources/assets/minecraft/models/block/enchanting_table.json")
with open(model_path) as f:
    data = json.load(f)

tex_dir = Path("/Users/mio/project/BlueMapEntities/scripts/test_textures")
tex_map = {
    "bottom": Image.open(tex_dir / "enchanting_table_bottom.png").convert("RGBA"),
    "top": Image.open(tex_dir / "enchanting_table_top.png").convert("RGBA"),
    "side": Image.open(tex_dir / "enchanting_table_side.png").convert("RGBA"),
    "book": Image.open(tex_dir / "enchanting_table_book.png").convert("RGBA")
}

uv_issues = verifier.check_uv_range(data, "enchanting_table")
print(f"UV issues: {len(uv_issues)}")
for issue in uv_issues:
    print(issue)

preview = renderer.render_views([(data, tex_map)], title="Enchanting Table with Floating Book 4-View Preview")
out_img = Path("/Users/mio/project/BlueMapEntities/scripts/previews/preview_enchanting_table.png")
preview.save(out_img)
print("Saved preview to", out_img)
