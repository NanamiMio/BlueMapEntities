#!/usr/bin/env python3
"""
BlueMapEntities - Pre-Render Automated Missing Texture Detector
四层核验体系之第三道防线：像素级 Missing Texture 自动化阻断门禁

检测给定的截帧图像中是否含有 Minecraft 标准丢失贴图特征：
品红色 (RGB ~ 248, 0, 248 / #F800F8) 与纯黑色 (RGB ~ 0, 0, 0) 相间的棋盘格像素聚集群。
若检出连续连通域，立即返回非零退出码 (Exit Code 1) 触发硬性阻断，禁止发布。
"""

import sys
import os
from pathlib import Path
from PIL import Image

def detect_missing_texture(image_path, threshold_pixels=16, dump_annotated=True):
    path = Path(image_path)
    if not path.exists():
        print(f"❌ 图像文件不存在: {image_path}")
        return False, 0, []

    img = Image.open(path).convert("RGBA")
    width, height = img.size
    pixels = img.load()

    # 寻找符合品红 (R >= 230, G <= 25, B >= 230) 的像素坐标
    magenta_pixels = []
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if a > 200: # 非透明
                if r >= 230 and g <= 25 and b >= 230:
                    magenta_pixels.append((x, y))

    if not magenta_pixels:
        print(f"  ✅ [PASS] 未检测到任何 Missing Texture 品红像素 (图像: {path.name}, 分辨率: {width}x{height})")
        return True, 0, []

    # 进行简单的空间聚集连通性判定 (排除孤立单个微小杂色噪点)
    pixel_set = set(magenta_pixels)
    clusters = []
    visited = set()

    for px in magenta_pixels:
        if px in visited:
            continue
        cluster = []
        queue = [px]
        visited.add(px)
        while queue:
            curr = queue.pop(0)
            cluster.append(curr)
            cx, cy = curr
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)]:
                neighbor = (cx + dx, cy + dy)
                if neighbor in pixel_set and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        if len(cluster) >= threshold_pixels:
            clusters.append(cluster)

    if not clusters:
        print(f"  ✅ [PASS] 检测到零星散乱噪点 ({len(magenta_pixels)} px)，无成块 Missing Texture 连通域")
        return True, len(magenta_pixels), []

    # 检出真正的 Missing Texture 异常！
    total_anomaly_pixels = sum(len(c) for c in clusters)
    print(f"  ❌ [FAIL - HARD BLOCK] 在图像 {path.name} 中检测到 {len(clusters)} 处 Missing Texture 黑紫块异常！")
    print(f"     总异常像素数: {total_anomaly_pixels} px (连通域阈值: {threshold_pixels} px)")

    for idx, c in enumerate(clusters[:5]):
        min_x = min(p[0] for p in c)
        max_x = max(p[0] for p in c)
        min_y = min(p[1] for p in c)
        max_y = max(p[1] for p in c)
        print(f"     • 异常区域 #{idx+1}: 范围 [{min_x}, {min_y}] -> [{max_x}, {max_y}] ({max_x-min_x+1}x{max_y-min_y+1} 区域, 包含 {len(c)} 像素)")

    # 标记出异常并保存
    if dump_annotated:
        annotated = img.copy()
        ann_pixels = annotated.load()
        for c in clusters:
            for x, y in c:
                ann_pixels[x, y] = (255, 255, 0, 255) # 亮黄色高亮标记
        out_path = path.parent / f"anomaly_detected_{path.name}"
        annotated.save(out_path)
        print(f"     ⚠️ 异常标注图已保存至: {out_path}")

    return False, total_anomaly_pixels, clusters

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 assert_no_missing_textures.py <image_path_1> [image_path_2 ...]")
        sys.exit(1)

    all_pass = True
    for img_path in sys.argv[1:]:
        print(f"\n正在扫描图像: {img_path}")
        passed, count, _ = detect_missing_texture(img_path)
        if not passed:
            all_pass = False

    if all_pass:
        print("\n🎉 所有图像像素级 Missing Texture 检查通过，无任何黑紫材质丢失！")
        sys.exit(0)
    else:
        print("\n🚨 发现材质丢失异常，自动化验证门禁触发阻断！")
        sys.exit(1)
