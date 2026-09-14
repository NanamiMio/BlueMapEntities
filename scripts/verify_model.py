#!/usr/bin/env python3
"""
BlueMapEntities - Local Offline Model & Texture Verifier and Multi-View Renderer
快速离线验证模型几何尺寸、UV坐标合法性、贴图采样对齐，并秒级生成3D多视角贴图合成预览图。
"""

import os
import sys
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw

REPO_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = REPO_ROOT / "src/main/resources/assets/minecraft/models/entity"
TEXTURES_DIR = REPO_ROOT / "scripts/test_textures"
OUTPUT_DIR = REPO_ROOT / "scripts/previews"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class ModelVerifier:
    def check_uv_range(self, model_json, model_name):
        """检查模型所有面的 UV 坐标是否在合法区间 [0.0, 16.0] 内"""
        issues = []
        elements = model_json.get("elements", [])
        for elem in elements:
            elem_name = elem.get("name", "unknown")
            faces = elem.get("faces", {})
            for face_name, face_data in faces.items():
                uv = face_data.get("uv")
                if not uv:
                    continue
                if len(uv) != 4:
                    issues.append(f"[{elem_name}][{face_name}] UV 维度不为 4: {uv}")
                    continue
                u1, v1, u2, v2 = uv
                for val in (u1, v1, u2, v2):
                    if val < -0.01 or val > 16.01:
                        issues.append(
                            f"[{elem_name}][{face_name}] UV 越界: {uv} (超出 0.0~16.0 范围)"
                        )
                        break
        return issues

    def check_texture_sampling(self, model_json, texture_map):
        """检查 UV 映射在贴图上的采样像素是否越界或异常全透明"""
        issues = []
        elements = model_json.get("elements", [])
        for elem in elements:
            elem_name = elem.get("name", "unknown")
            faces = elem.get("faces", {})
            for face_name, face_data in faces.items():
                uv = face_data.get("uv")
                tex_key = face_data.get("texture", "#0").lstrip("#")
                tex_img = texture_map.get(tex_key)
                if not uv or not tex_img:
                    continue
                
                # 转换 UV [0..16] 到贴图像素坐标
                u1 = uv[0] / 16.0 * tex_img.width
                v1 = uv[1] / 16.0 * tex_img.height
                u2 = uv[2] / 16.0 * tex_img.width
                v2 = uv[3] / 16.0 * tex_img.height
                
                px_min_x = max(0, min(int(min(u1, u2)), tex_img.width - 1))
                px_max_x = min(tex_img.width, max(int(max(u1, u2)), 1))
                px_min_y = max(0, min(int(min(v1, v2)), tex_img.height - 1))
                px_max_y = min(tex_img.height, max(int(max(v1, v2)), 1))
                
                if px_min_x >= px_max_x or px_min_y >= px_max_y:
                    issues.append(f"[{elem_name}][{face_name}] 像素采样区域宽度或高度为 0: uv={uv}")
                    continue
                
                # 检查是否采样区全透明
                crop = tex_img.crop((px_min_x, px_min_y, px_max_x, px_max_y))
                if crop.mode == "RGBA":
                    extrema = crop.getextrema()
                    alpha_extrema = extrema[3]
                    if alpha_extrema[1] == 0:  # 最大 alpha 为 0，说明全透明
                        issues.append(f"[{elem_name}][{face_name}] 采样区域 100% 全透明! uv={uv}, rect=({px_min_x},{px_min_y},{px_max_x},{px_max_y})")
        return issues



def rotate_point(p, origin, axis, angle_deg):
    ox, oy, oz = origin
    rad = math.radians(angle_deg)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)
    x, y, z = p[0] - ox, p[1] - oy, p[2] - oz
    if axis == 'x':
        rx = x
        ry = y * cos_a - z * sin_a
        rz = y * sin_a + z * cos_a
    elif axis == 'y':
        rx = x * cos_a + z * sin_a
        ry = y
        rz = -x * sin_a + z * cos_a
    elif axis == 'z':
        rx = x * cos_a - y * sin_a
        ry = x * sin_a + y * cos_a
        rz = z
    else:
        rx, ry, rz = x, y, z
    return [rx + ox, ry + oy, rz + oz]

def rotate_normal(normal, axis, angle_deg):
    rad = math.radians(angle_deg)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)
    x, y, z = normal
    if axis == 'x':
        return [x, y * cos_a - z * sin_a, y * sin_a + z * cos_a]
    elif axis == 'y':
        return [x * cos_a + z * sin_a, y, -x * sin_a + z * cos_a]
    elif axis == 'z':
        return [x * cos_a - y * sin_a, x * sin_a + y * cos_a, z]
    return normal

class MultiViewRenderer:
    """轻量级 3D 贴图正交与透视多视角光栅化渲染器"""
    def __init__(self, canvas_size=(1000, 800), bg_color=(30, 32, 36, 255)):
        self.canvas_size = canvas_size
        self.bg_color = bg_color

    def render_views(self, models_with_textures, title="Model Multi-View Preview"):
        canvas = Image.new("RGBA", self.canvas_size, self.bg_color)
        draw = ImageDraw.Draw(canvas)
        draw.text((20, 15), title, fill=(220, 220, 220, 255))
        
        view_w = self.canvas_size[0] // 2
        view_h = (self.canvas_size[1] - 40) // 2
        
        views = [
            ("Front (North)", (0, 40), "front"),
            ("Side (West)", (view_w, 40), "side"),
            ("Back (South)", (0, 40 + view_h), "back"),
            ("Isometric 3D", (view_w, 40 + view_h), "iso"),
        ]
        
        for view_name, pos, mode in views:
            vp = Image.new("RGBA", (view_w, view_h), (24, 25, 28, 255))
            vp_draw = ImageDraw.Draw(vp)
            vp_draw.rectangle([0, 0, view_w - 1, view_h - 1], outline=(50, 52, 58, 255))
            vp_draw.text((10, 8), view_name, fill=(180, 180, 180, 255))
            
            self._render_single_view(vp, models_with_textures, mode)
            canvas.paste(vp, pos)
            
        return canvas

    def _render_single_view(self, viewport, models_with_textures, mode):
        vp_w, vp_h = viewport.size
        scale = min(vp_w / 28.0, vp_h / 38.0) * 0.82
        center_x = vp_w / 2.0
        ground_y = vp_h * 0.88
        
        quads = []
        
        # 相机视线方向定义（指向物体观察的方向）
        # Front: 相机在 -Z 朝 +Z 看
        # Back: 相机在 +Z 朝 -Z 看
        # Side: 相机在 -X 朝 +X 看 (看西侧面)
        # Iso: 相机在 (-1, 1, -1) 朝 (+1, -0.6, +1) 斜看
        view_dirs = {
            "front": (0, 0, 1),
            "back": (0, 0, -1),
            "side": (1, 0, 0),
            "iso": (0.7071, -0.4, 0.7071)
        }
        v_dir = view_dirs[mode]
        
        for model_json, tex_map in models_with_textures:
            elements = model_json.get("elements", [])
            for elem in elements:
                elem_name = elem.get("name", "")
                p_from = elem["from"]
                p_to = elem["to"]
                x1, y1, z1 = p_from
                x2, y2, z2 = p_to
                rot = elem.get("rotation")
                faces = elem.get("faces", {})
                
                # 面定义：(顶点列表, 法向量, 光照强度)
                face_defs = {
                    "north": (
                        [(x1, y2, z1), (x2, y2, z1), (x2, y1, z1), (x1, y1, z1)],
                        (0, 0, -1),
                        0.9
                    ),
                    "south": (
                        [(x2, y2, z2), (x1, y2, z2), (x1, y1, z2), (x2, y1, z2)],
                        (0, 0, 1),
                        0.8
                    ),
                    "west": (
                        [(x1, y2, z2), (x1, y2, z1), (x1, y1, z1), (x1, y1, z2)],
                        (-1, 0, 0),
                        0.7
                    ),
                    "east": (
                        [(x2, y2, z1), (x2, y2, z2), (x2, y1, z2), (x2, y1, z1)],
                        (1, 0, 0),
                        0.7
                    ),
                    "up": (
                        [(x1, y2, z2), (x2, y2, z2), (x2, y2, z1), (x1, y2, z1)],
                        (0, 1, 0),
                        1.0
                    ),
                    "down": (
                        [(x1, y1, z1), (x2, y1, z1), (x2, y1, z2), (x1, y1, z2)],
                        (0, -1, 0),
                        0.5
                    ),
                }
                
                for face_name, (vertices, normal, light) in face_defs.items():
                    if face_name not in faces:
                        continue
                    face_info = faces[face_name]
                    uv = face_info.get("uv")
                    tex_key = face_info.get("texture", "#0").lstrip("#")
                    tex_img = tex_map.get(tex_key)
                    if not uv or not tex_img:
                        continue
                    
                    cur_verts = vertices
                    cur_normal = normal
                    if rot:
                        origin = rot.get("origin", [0, 0, 0])
                        axis = rot.get("axis", "x")
                        angle = rot.get("angle", 0)
                        cur_verts = [rotate_point(v, origin, axis, angle) for v in vertices]
                        cur_normal = rotate_normal(normal, axis, angle)

                    # 3D 面法向背面剔除 (Back-face Culling)
                    dot = cur_normal[0] * v_dir[0] + cur_normal[1] * v_dir[1] + cur_normal[2] * v_dir[2]
                    if dot >= 0:
                        continue
                    
                    projected = []
                    depth = 0
                    for vx, vy, vz in cur_verts:
                        if mode == "front":
                            # 相机在北朝南看：-X 在左，+X 在右，+Y 在上
                            sx = center_x + vx * scale
                            sy = ground_y - vy * scale
                            d = vz  # 从远(+Z)到近(-Z)绘制，大 d 远，先画
                        elif mode == "back":
                            # 相机在南朝北看：+X 在左，-X 在右，+Y 在上
                            sx = center_x - vx * scale
                            sy = ground_y - vy * scale
                            d = -vz
                        elif mode == "side":
                            # 相机在西朝东看：北(-Z)在左，南(+Z)在右
                            sx = center_x + vz * scale
                            sy = ground_y - vy * scale
                            d = vx
                        elif mode == "iso":
                            # 斜视角
                            iso_x = (vx - vz) * 0.7071
                            iso_z = (vx + vz) * 0.7071
                            sx = center_x + iso_x * scale
                            sy = ground_y - (vy * 0.82 - iso_z * 0.42) * scale
                            d = iso_z
                        
                        projected.append((sx, sy))
                        depth += d
                    
                    depth /= len(cur_verts)
                    
                    quads.append({
                        "depth": depth,
                        "projected": projected,
                        "uv": uv,
                        "rotation": face_info.get("rotation", 0),
                        "tex_img": tex_img,
                        "light": light,
                        "face_name": face_name,
                        "elem_name": elem_name
                    })
        
        # Painter's Algorithm: 深度越大（离相机越远）先画，深度越小（离相机越近）后画
        quads.sort(key=lambda q: q["depth"], reverse=True)
        
        for q in quads:
            self._draw_textured_quad(viewport, q)

    def _draw_textured_quad(self, viewport, quad):
        pts = quad["projected"]
        uv = quad["uv"]
        tex_img = quad["tex_img"]
        light = quad["light"]
        rot_deg = quad.get("rotation", 0) % 360
        
        tw, th = tex_img.size
        u1 = uv[0] / 16.0 * tw
        v1 = uv[1] / 16.0 * th
        u2 = uv[2] / 16.0 * tw
        v2 = uv[3] / 16.0 * th
        
        left = int(min(u1, u2))
        top = int(min(v1, v2))
        right = int(max(u1, u2))
        bottom = int(max(v1, v2))
        
        w = max(1, right - left)
        h = max(1, bottom - top)
        
        crop = tex_img.crop((left, top, left + w, top + h))
        if u1 > u2:
            crop = crop.transpose(Image.FLIP_LEFT_RIGHT)
        if v1 > v2:
            crop = crop.transpose(Image.FLIP_TOP_BOTTOM)
            
        if rot_deg == 90:
            crop = crop.transpose(Image.ROTATE_270)
        elif rot_deg == 180:
            crop = crop.transpose(Image.ROTATE_180)
        elif rot_deg == 270:
            crop = crop.transpose(Image.ROTATE_90)
            
        if light < 0.99:
            enhancer = Image.new("RGBA", crop.size, (0, 0, 0, int(255 * (1.0 - light))))
            crop = Image.alpha_composite(crop.convert("RGBA"), enhancer)
            
        min_x = min(p[0] for p in pts)
        max_x = max(p[0] for p in pts)
        min_y = min(p[1] for p in pts)
        max_y = max(p[1] for p in pts)
        
        dw = int(math.ceil(max_x - min_x))
        dh = int(math.ceil(max_y - min_y))
        
        if dw <= 0 or dh <= 0:
            return
            
        resized = crop.resize((dw, dh), Image.NEAREST)
        viewport.alpha_composite(resized, (int(min_x), int(min_y)))


def verify_and_render_villager():
    verifier = ModelVerifier()
    villager_json_path = MODELS_DIR / "villager/villager.json"
    with open(villager_json_path, "r", encoding="utf-8") as f:
        villager_data = json.load(f)
        
    print(f"\n================ 检验村民模型: {villager_json_path.name} ================")
    uv_issues = verifier.check_uv_range(villager_data, "villager")
    if uv_issues:
        print(f"❌ 发现 {len(uv_issues)} 处 UV 越界:")
        for issue in uv_issues:
            print("  ", issue)
    else:
        print("✅ UV 范围检查 PASS: 所有 UV 均在 [0.0, 16.0] 内")
        
    tex_base = Image.open(TEXTURES_DIR / "entity/villager/villager.png").convert("RGBA")
    tex_plains = Image.open(TEXTURES_DIR / "entity/villager/type/plains.png").convert("RGBA")
    tex_map = {"0": tex_base, "1": tex_plains}
    
    sample_issues = verifier.check_texture_sampling(villager_data, tex_map)
    if sample_issues:
        print(f"⚠️ 贴图采样提示 ({len(sample_issues)}):")
        for issue in sample_issues:
            print("  ", issue)
    else:
        print("✅ 贴图采样检查 PASS")
        
    elem_map = {e["name"]: e for e in villager_data.get("elements", [])}
    if "head" in elem_map and "coat" in elem_map and "body" in elem_map:
        head_from_y = elem_map["head"]["from"][1]
        coat_to_y = elem_map["coat"]["to"][1]
        body_to_y = elem_map["body"]["to"][1]
        body_z_depth = elem_map["body"]["to"][2] - elem_map["body"]["from"][2]
        
        print(f"\n[几何颈部接缝诊断]")
        print(f"  Head From Y: {head_from_y}")
        print(f"  Coat To Y:   {coat_to_y} (缝隙: {head_from_y - coat_to_y})")
        print(f"  Body To Y:   {body_to_y} (缝隙: {head_from_y - body_to_y})")
        print(f"  Body Z Depth: {body_z_depth} (原版标准应为 6.0)")
        if head_from_y - coat_to_y > 0.01:
            print(f"  ❌ 颈部严重断层: Coat 顶部与 Head 底部相距 {head_from_y - coat_to_y} 单位未接合，导致悬空！")
        if body_z_depth < 5.9:
            print(f"  ❌ Body 厚度严重过薄: 当前 Z 厚度 {body_z_depth} < 6.0，导致身体无法填满头底！")

    renderer = MultiViewRenderer()
    preview_img = renderer.render_views([(villager_data, tex_map)], title="Villager (Plains) Offline 4-View Preview")
    out_file = OUTPUT_DIR / "preview_villager.png"
    preview_img.save(out_file)
    print(f"✅ 生成离线四重视角预览图: {out_file}")


def verify_and_render_armor_stand():
    verifier = ModelVerifier()
    stand_json_path = MODELS_DIR / "armor_stand/armor_stand.json"
    with open(stand_json_path, "r", encoding="utf-8") as f:
        stand_data = json.load(f)
        
    print(f"\n================ 检验盔甲架模型: {stand_json_path.name} ================")
    uv_issues = verifier.check_uv_range(stand_data, "armor_stand")
    if uv_issues:
        print(f"❌ 发现 {len(uv_issues)} 处 UV 越界:")
        for issue in uv_issues:
            print("  ", issue)
    else:
        print("✅ UV 范围检查 PASS: 所有 UV 均在 [0.0, 16.0] 内")
        
    tex_wood = Image.open(TEXTURES_DIR / "entity/armorstand/wood.png").convert("RGBA")
    tex_map = {"0": tex_wood}
    
    renderer = MultiViewRenderer()
    preview_img = renderer.render_views([(stand_data, tex_map)], title="Armor Stand Offline 4-View Preview")
    out_file = OUTPUT_DIR / "preview_armor_stand.png"
    preview_img.save(out_file)
    print(f"✅ 生成离线四重视角预览图: {out_file}")


def verify_and_render_armor_set():
    verifier = ModelVerifier()
    armor_files = [
        ("iron_helmet.json", "models/armor/iron_layer_1.png"),
        ("iron_chestplate.json", "models/armor/iron_layer_1.png"),
        ("iron_leggings.json", "models/armor/iron_layer_2.png"),
        ("iron_boots.json", "models/armor/iron_layer_1.png"),
    ]
    
    models_to_render = []
    
    # 基础盔甲架
    stand_json_path = MODELS_DIR / "armor_stand/armor_stand.json"
    with open(stand_json_path, "r", encoding="utf-8") as f:
        stand_data = json.load(f)
    tex_wood = Image.open(TEXTURES_DIR / "entity/armorstand/wood.png").convert("RGBA")
    models_to_render.append((stand_data, {"0": tex_wood}))
    
    print("\n================ 检验铁盔甲部件 ================")
    for fname, tex_rel in armor_files:
        p = MODELS_DIR / "armor" / fname
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        tex_img = Image.open(TEXTURES_DIR / tex_rel).convert("RGBA")
        issues = verifier.check_uv_range(data, fname)
        if issues:
            print(f"❌ {fname} UV 越界 ({len(issues)}):")
            for i in issues:
                print("  ", i)
        else:
            print(f"✅ {fname} UV 范围检查 PASS")
        models_to_render.append((data, {"0": tex_img}))
        
    renderer = MultiViewRenderer()
    preview_img = renderer.render_views(models_to_render, title="Armor Stand with Full Iron Armor Set (Offline Preview)")
    out_file = OUTPUT_DIR / "preview_armor_stand_equipped.png"
    preview_img.save(out_file)
    print(f"✅ 生成穿戴铁盔甲全套离线四重视角预览图: {out_file}")


def verify_and_render_farmer_villager():
    villager_json_path = MODELS_DIR / "villager/villager.json"
    farmer_json_path = MODELS_DIR / "villager/profession_farmer.json"
    
    with open(villager_json_path, "r", encoding="utf-8") as f:
        villager_data = json.load(f)
    with open(farmer_json_path, "r", encoding="utf-8") as f:
        farmer_data = json.load(f)
        
    tex_base = Image.open(TEXTURES_DIR / "entity/villager/villager.png").convert("RGBA")
    tex_plains = Image.open(TEXTURES_DIR / "entity/villager/type/plains.png").convert("RGBA")
    tex_farmer = Image.open(TEXTURES_DIR / "entity/villager/profession/farmer.png").convert("RGBA")
    
    models_to_render = [
        (villager_data, {"0": tex_base, "1": tex_plains}),
        (farmer_data, {"0": tex_farmer})
    ]
    
    renderer = MultiViewRenderer()
    preview_img = renderer.render_views(models_to_render, title="Farmer Villager (Plains) Offline Preview")
    out_file = OUTPUT_DIR / "preview_farmer_villager.png"
    preview_img.save(out_file)
    print(f"✅ 生成农夫村民离线四重视角预览图: {out_file}")


def verify_and_render_wolf():
    verifier = ModelVerifier()
    wolf_sitting_path = MODELS_DIR / "wolf/wolf_sitting.json"
    with open(wolf_sitting_path, "r", encoding="utf-8") as f:
        wolf_data = json.load(f)
        
    print(f"\n================ 检验坐姿狼模型: {wolf_sitting_path.name} ================")
    uv_issues = verifier.check_uv_range(wolf_data, "wolf_sitting")
    if uv_issues:
        print(f"❌ 发现 {len(uv_issues)} 处 UV 越界:")
        for issue in uv_issues:
            print("  ", issue)
    else:
        print("✅ UV 范围检查 PASS: 所有 UV 均在 [0.0, 16.0] 内")
        
    tex_wolf = Image.open(TEXTURES_DIR / "entity/wolf/wolf_tame.png").convert("RGBA")
    tex_map = {"0": tex_wolf}
    
    sample_issues = verifier.check_texture_sampling(wolf_data, tex_map)
    if sample_issues:
        print(f"⚠️ 贴图采样提示 ({len(sample_issues)}):")
        for issue in sample_issues:
            print("  ", issue)
    else:
        print("✅ 贴图采样检查 PASS")
        
    renderer = MultiViewRenderer()
    preview_img = renderer.render_views([(wolf_data, tex_map)], title="Wolf Sitting (Tame) 4-View Preview")
    out_file = OUTPUT_DIR / "preview_wolf_sitting.png"
    preview_img.save(out_file)
    print(f"✅ 生成坐姿狼离线四重视角预览图: {out_file}")

if __name__ == "__main__":
    verify_and_render_villager()
    verify_and_render_wolf()
    verify_and_render_farmer_villager()
    verify_and_render_armor_stand()
    verify_and_render_armor_set()

