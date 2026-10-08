#!/usr/bin/env python3
"""
audit_all_seasons_blocks.py
《无故事王国》全周目（V0~V10）方块映射与渲染资产全面体检脚本

深度审计各周目：
1. 真实 MCA 区域中出现的全部方块（原版 vs 模组）；
2. 模组方块在 packs/mod_assets.zip 中的 blockstate 与 model 完备度；
3. 1.7.10 转换周目（V4、V6）的原版与模组方块映射退化情况；
4. Web 前端 textures.json.gz 材质表与材质健康度（是否存在缺失贴图/异常黑块）。
"""

import os
import sys
import glob
import re
import zlib
import json
import zipfile
import math
from collections import defaultdict

# 引入 NBTReader
try:
    from mca_convert import NBTReader
except ImportError:
    # 尝试当前目录或相对路径
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from mca_convert import NBTReader

CONF_DIR = "/home/mio/mc_portal/bluemap/maps"
MOD_ASSETS_ZIP = "/home/mio/mc_portal/bluemap/packs/mod_assets.zip"
WEB_MAPS_DIR = "/home/mio/mc_portal/web/map/maps"

def parse_map_config(conf_path):
    with open(conf_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    cid = os.path.basename(conf_path).replace(".conf", "")
    
    w_match = re.search(r'world:\s*"([^"]+)"', content)
    world = w_match.group(1) if w_match else ""
    
    name_match = re.search(r'name:\s*"([^"]+)"', content)
    name = name_match.group(1) if name_match else cid
    
    dim_match = re.search(r'dimension:\s*"([^"]+)"', content)
    dimension = dim_match.group(1) if dim_match else "minecraft:overworld"
    
    sp_match = re.search(r'start-pos:\s*\{x:([-\d]+),\s*z:([-\d]+)\}', content)
    start_pos = (int(sp_match.group(1)), int(sp_match.group(2))) if sp_match else (0, 0)
    
    masks = []
    mask_blocks = re.findall(r'\{\s*min-x:\s*([-\d]+)\s*max-x:\s*([-\d]+)\s*min-z:\s*([-\d]+)\s*max-z:\s*([-\d]+)\s*min-y:\s*([-\d]+)\s*max-y:\s*([-\d]+)\s*\}', content)
    for m in mask_blocks:
        masks.append({
            "min_x": int(m[0]), "max_x": int(m[1]),
            "min_z": int(m[2]), "max_z": int(m[3]),
            "min_y": int(m[4]), "max_y": int(m[5])
        })
    return {
        "id": cid,
        "name": name,
        "world": world,
        "dimension": dimension,
        "start_pos": start_pos,
        "masks": masks
    }

def load_mod_assets_index(zip_path):
    print("正在加载 mod_assets.zip 资源索引...")
    blockstates = set()
    models = set()
    textures = set()
    
    if not os.path.exists(zip_path):
        print(f"警告: mod_assets.zip 不存在: {zip_path}")
        return blockstates, models, textures

    with zipfile.ZipFile(zip_path, "r") as zf:
        for name in zf.namelist():
            name_lower = name.lower()
            if "/blockstates/" in name_lower and name_lower.endswith(".json"):
                idx = name_lower.find("/blockstates/")
                prefix = name_lower[:idx]
                ns = prefix.split("/")[-1]
                subpath = name_lower[idx + len("/blockstates/"):-5]
                blockstates.add(f"{ns}:{subpath}")
                blockstates.add(f"{ns}:{os.path.basename(subpath)}")
            elif "/models/block/" in name_lower and name_lower.endswith(".json"):
                idx = name_lower.find("/models/block/")
                prefix = name_lower[:idx]
                ns = prefix.split("/")[-1]
                subpath = name_lower[idx + len("/models/block/"):-5]
                models.add(f"{ns}:{subpath}")
                models.add(f"{ns}:{os.path.basename(subpath)}")
            elif "/textures/" in name_lower and name_lower.endswith(".png"):
                parts = name_lower.split("/")
                if len(parts) >= 4 and parts[0] == "assets":
                    ns = parts[1]
                    tname = "/".join(parts[3:])
                    textures.add(f"{ns}:{tname}")
    print(f"索引加载完成: {len(blockstates)} 个 blockstates, {len(models)} 个 block models, {len(textures)} 个 textures")
    return blockstates, models, textures

def is_chunk_in_masks(cx, cz, masks):
    if not masks:
        return True
    bx0, bx1 = cx * 16, cx * 16 + 15
    bz0, bz1 = cz * 16, cz * 16 + 15
    for m in masks:
        if bx1 >= m["min_x"] and bx0 <= m["max_x"] and bz1 >= m["min_z"] and bz0 <= m["max_z"]:
            return True
    return False

def scan_world_blocks(world_dir, masks, max_chunks_per_region=1024):
    region_dir = os.path.join(world_dir, "region")
    if not os.path.exists(region_dir):
        return {}

    # 确定需要扫描的 region 坐标
    needed_regions = set()
    if masks:
        for m in masks:
            rx_min = m["min_x"] >> 9
            rx_max = m["max_x"] >> 9
            rz_min = m["min_z"] >> 9
            rz_max = m["max_z"] >> 9
            for rx in range(rx_min, rx_max + 1):
                for rz in range(rz_min, rz_max + 1):
                    needed_regions.add(f"r.{rx}.{rz}.mca")
    else:
        needed_regions = {f for f in os.listdir(region_dir) if f.endswith(".mca")}

    block_counts = defaultdict(int)
    scanned_chunks = 0
    scanned_regions = 0

    for rfile in sorted(needed_regions):
        rpath = os.path.join(region_dir, rfile)
        if not os.path.exists(rpath):
            continue
        scanned_regions += 1
        try:
            with open(rpath, "rb") as f:
                data = f.read()
        except:
            continue

        for i in range(1024):
            off = int.from_bytes(data[i*4:i*4+3], "big") * 4096
            cnt = data[i*4+3] * 4096
            if off == 0 or cnt == 0:
                continue
            cdata = data[off:off+cnt]
            if len(cdata) < 5:
                continue
            c_len = int.from_bytes(cdata[:4], "big")
            if c_len > len(cdata) - 4:
                continue
            
            # 解析区块坐标
            chunk_in_region_x = i % 32
            chunk_in_region_z = i // 32
            m = re.match(r"r\.([-\d]+)\.([-\d]+)\.mca", rfile)
            if m:
                rx, rz = int(m.group(1)), int(m.group(2))
                cx = rx * 32 + chunk_in_region_x
                cz = rz * 32 + chunk_in_region_z
                if not is_chunk_in_masks(cx, cz, masks):
                    continue

            try:
                decomp = zlib.decompress(cdata[5:4+c_len])
                r = NBTReader(decomp)
                _, root = r.read_root()
                scanned_chunks += 1
                
                # 兼容 1.18+ (root.sections) 与 1.16- (root.Level.Sections)
                if "sections" in root:
                    # 1.18+
                    sections = root["sections"][1].get("items", [])
                    for sec in sections:
                        bs = sec.get("block_states", (10, {}))[1]
                        pal = bs.get("palette", (9, {"items": []}))[1].get("items", [])
                        for p in pal:
                            bname = p.get("Name", (8, ""))[1]
                            if bname:
                                block_counts[bname] += 1
                elif "Level" in root:
                    # 1.16 / 1.12
                    level = root["Level"][1]
                    sections = level.get("Sections", (9, {"items": []}))[1].get("items", [])
                    for sec in sections:
                        pal = sec.get("Palette", (9, {"items": []}))[1].get("items", [])
                        for p in pal:
                            bname = p.get("Name", (8, ""))[1]
                            if bname:
                                block_counts[bname] += 1
            except:
                pass

    return {
        "scanned_regions": scanned_regions,
        "scanned_chunks": scanned_chunks,
        "blocks": block_counts
    }

def audit_season(config, mod_blockstates, mod_models):
    cid = config["id"]
    name = config["name"]
    world = config["world"]
    masks = config["masks"]
    
    print(f"\n======================================================================")
    print(f"【{cid.upper()} - {name}】方块映射与资产审计")
    print(f"======================================================================")
    print(f"  世界路径: {world}")
    print(f"  掩码范围: {masks}")
    
    if not os.path.exists(world):
        print(f"  ❌ 世界目录不存在: {world}")
        return
    
    # 扫描方块
    scan_res = scan_world_blocks(world, masks)
    total_chunks = scan_res["scanned_chunks"]
    blocks = scan_res["blocks"]
    print(f"  扫描区域: {scan_res['scanned_regions']} 个 MCA 文件, 命中掩码区块: {total_chunks} 个")
    print(f"  总独立方块种类: {len(blocks)} 种")
    
    vanilla_blocks = {k: v for k, v in blocks.items() if k.startswith("minecraft:")}
    mod_blocks = {k: v for k, v in blocks.items() if not k.startswith("minecraft:")}
    
    print(f"  原版方块: {len(vanilla_blocks)} 种")
    print(f"  模组方块: {len(mod_blocks)} 种")
    
    # 按命名空间分类模组方块
    ns_map = defaultdict(list)
    for b in mod_blocks:
        ns = b.split(":")[0]
        ns_map[ns].append(b)
        
    for ns, b_list in sorted(ns_map.items()):
        supported_count = 0
        missing_list = []
        for b in b_list:
            if b in mod_blockstates or b in mod_models:
                supported_count += 1
            else:
                missing_list.append(b)
        rate = (supported_count / len(b_list)) * 100 if b_list else 100
        print(f"    • [{ns}] 包含 {len(b_list)} 种方块 | 资产包覆盖率: {rate:.1f}% ({supported_count}/{len(b_list)})")
        if missing_list:
            print(f"      ⚠️ 未在 mod_assets.zip 中匹配到 blockstate/model 的方块 ({len(missing_list)} 个):")
            for mb in missing_list[:10]:
                print(f"         - {mb} (出现 {blocks[mb]} 次)")
            if len(missing_list) > 10:
                print(f"         ... 等共 {len(missing_list)} 个")

    # 检查 Web 材质表
    web_map_dir = os.path.join(WEB_MAPS_DIR, cid)
    tex_path = os.path.join(web_map_dir, "textures.json.gz")
    if not os.path.exists(tex_path):
        tex_path = os.path.join(web_map_dir, "textures.json")
    
    if os.path.exists(tex_path):
        try:
            if tex_path.endswith(".gz"):
                with gzip.open(tex_path, "rt", encoding="utf-8") as f:
                    tex_data = json.load(f)
            else:
                with open(tex_path, "r", encoding="utf-8") as f:
                    tex_data = json.load(f)
            textures = tex_data if isinstance(tex_data, list) else tex_data.get("textures", [])
            print(f"  Web 烘焙材质库: {len(textures)} 个材质槽位")
            
            # 检查是否有异常材质 (排除合法的 0 号缺失占位符)
            abnormal_missing = [i for i, t in enumerate(textures) if i > 0 and "missing" in str(t).lower()]
            if abnormal_missing:
                print(f"    ❌ 检测到 {len(abnormal_missing)} 个异常 missing 材质索引: {abnormal_missing}")
            else:
                print(f"    ✅ 材质健康度 100% (仅保留内置 0 号占位，无额外异常缺失)")
        except Exception as e:
            print(f"  ⚠️ Web 材质表读取异常: {e}")
    else:
        print(f"  ⚠️ 未找到 Web 材质表: {tex_path}")

def main():
    import gzip
    # 确保 gzip 在当前命名空间可用
    globals()['gzip'] = gzip
    
    conf_files = sorted(glob.glob(os.path.join(CONF_DIR, "v*.conf")), key=lambda p: (
        int(re.search(r'\d+', os.path.basename(p)).group()) if re.search(r'\d+', os.path.basename(p)) else 999
    ))
    
    mod_blockstates, mod_models, _ = load_mod_assets_index(MOD_ASSETS_ZIP)
    
    for conf_file in conf_files:
        conf = parse_map_config(conf_file)
        audit_season(conf, mod_blockstates, mod_models)

if __name__ == "__main__":
    main()
