import sys, os, gzip, math, struct
from pathlib import Path
from PIL import Image, ImageDraw

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(REPO_ROOT / "scripts"))
from inspect_tile import decode_prbm

# 1. 抓取瓦片
tile_local = REPO_ROOT / "scripts/previews/farm_tile.prbm.gz"
if not tile_local.exists():
    import subprocess
    cmd = "scp pve-mc:/home/mio/mc_portal/web/map/maps/v5/tiles/0/x7/0/z-1/0/0.prbm.gz " + str(tile_local)
    subprocess.run(cmd, shell=True, check=True)

with gzip.open(tile_local, "rb") as f:
    prbm = decode_prbm(f.read())

pos_attr = prbm['attributes']['position']
offset = pos_attr['offset']
raw = prbm['raw_data']

# 提取圈舍内所有的三角形
# 限制在农场圈舍范围: X 7~14, Y 64~67, Z -23~-15 (瓦片相对坐标)
triangles = []
for g in prbm['groups']:
    if g['materialIndex'] == 418:
        for i in range(g['start'], g['start'] + g['count'], 3):
            tri = []
            for vi in range(3):
                o = offset + (i + vi) * 12
                x, y, z = struct.unpack('<fff', raw[o:o+12])
                tri.append((x, y, z))
            # 过滤在圈舍的一段典型栅栏
            if all(7 <= v[0] <= 13.5 and 64 <= v[1] <= 67 and 10 <= v[2] <= 32 for v in tri):
                triangles.append(tri)

print(f"Extracted {len(triangles)} fence triangles for closeup rendering.")

# 加载新木纹贴图
wood_img = Image.open(REPO_ROOT / "scripts/previews/white_picket_wood.png").convert("RGBA")

# 简单光栅化 3D 渲染器 (等轴测俯视)
def render_view(tris, use_wood=True, img_size=(800, 800)):
    im = Image.new("RGBA", img_size, (26, 27, 30, 255))
    draw = ImageDraw.Draw(im)
    
    # 投影参数
    # 视角: yaw=45, pitch=30
    yaw = math.radians(45)
    pitch = math.radians(30)
    
    # 中心点
    cx_w = 10.5
    cy_w = 65.5
    cz_w = 20.0
    
    scale = 55.0
    
    # 三角形排序 (Painter's algorithm)
    sorted_tris = []
    for tri in tris:
        # 计算中心深度
        mid_x = sum(v[0] for v in tri) / 3.0 - cx_w
        mid_y = sum(v[1] for v in tri) / 3.0 - cy_w
        mid_z = sum(v[2] for v in tri) / 3.0 - cz_w
        
        # 旋转
        rx = mid_x * math.cos(yaw) - mid_z * math.sin(yaw)
        rz = mid_x * math.sin(yaw) + mid_z * math.cos(yaw)
        ry = mid_y * math.cos(pitch) - rz * math.sin(pitch)
        depth = mid_y * math.sin(pitch) + rz * math.cos(pitch)
        
        # 法线与光照计算
        v0, v1, v2 = tri
        e1 = (v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2])
        e2 = (v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2])
        norm = (
            e1[1]*e2[2] - e1[2]*e2[1],
            e1[2]*e2[0] - e1[0]*e2[2],
            e1[0]*e2[1] - e1[1]*e2[0]
        )
        l = math.sqrt(norm[0]**2 + norm[1]**2 + norm[2]**2)
        if l > 1e-6:
            norm = (norm[0]/l, norm[1]/l, norm[2]/l)
        else:
            norm = (0, 1, 0)
            
        # 主平行光方向 (从斜上方照下)
        light_dir = (-0.4, 0.8, -0.4)
        ll = math.sqrt(sum(k**2 for k in light_dir))
        light_dir = tuple(k/ll for k in light_dir)
        
        diff = max(0.0, norm[0]*light_dir[0] + norm[1]*light_dir[1] + norm[2]*light_dir[2])
        light = 0.45 + 0.55 * diff
        
        sorted_tris.append((depth, tri, norm, light))
        
    sorted_tris.sort(key=lambda x: x[0])
    
    # 投影到屏幕
    for depth, tri, norm, light in sorted_tris:
        pts = []
        for v in tri:
            vx = v[0] - cx_w
            vy = v[1] - cy_w
            vz = v[2] - cz_w
            
            rx = vx * math.cos(yaw) - vz * math.sin(yaw)
            rz = vx * math.sin(yaw) + vz * math.cos(yaw)
            ry = vy * math.cos(pitch) - rz * math.sin(pitch)
            
            sx = img_size[0] // 2 + rx * scale
            sy = img_size[1] // 2 - ry * scale
            pts.append((sx, sy))
            
        if use_wood:
            # 白色木纹色调
            base_col = (235, 238, 240)
            # 根据法线朝向加入板条阴影
            if abs(norm[1]) < 0.3: # 侧面/竖条面
                base_col = (220, 225, 230)
        else:
            # 原始纯白混凝土 (死白平坦)
            base_col = (255, 255, 255)
            
        fill_col = tuple(min(255, int(c * light)) for c in base_col)
        outline_col = (min(255, int(fill_col[0] * 0.85)), min(255, int(fill_col[1] * 0.85)), min(255, int(fill_col[2] * 0.85)) if use_wood else fill_col)
        
        draw.polygon(pts, fill=fill_col, outline=outline_col if use_wood else None)
        
    return im

comp = Image.new("RGBA", (1600, 800), (20, 20, 20, 255))
left = render_view(triangles, use_wood=False)
right = render_view(triangles, use_wood=True)

# 贴上标签
draw = ImageDraw.Draw(comp)
comp.paste(left, (0, 0))
comp.paste(right, (800, 0))

draw.text((30, 30), "BEFORE: Pure White Concrete (Dead Light / Plastic)", fill=(255, 100, 100, 255))
draw.text((830, 30), "AFTER: White Picket Wood (Natural Grain & Depth)", fill=(100, 255, 100, 255))

out_path = REPO_ROOT / "scripts/previews/v5_fence_comparison.png"
comp.save(out_path)
print(f"Comparison saved to {out_path}")
