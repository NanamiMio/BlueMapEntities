#!/usr/bin/env python3
import glob, gzip, json, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import inspect_tile

BLANK_PNG = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAA'

def prune_map(map_name, base_dir='/home/mio/mc_portal/web/map/maps'):
    map_dir = os.path.join(base_dir, map_name)
    tex_path = os.path.join(map_dir, 'textures.json.gz')
    tiles_pattern = os.path.join(map_dir, 'tiles/0/**/*.prbm.gz')

    if not os.path.exists(tex_path):
        print(f'[{map_name}] Skipped: {tex_path} does not exist')
        return

    # 1. 扫描瓦片中实际用到的 materialIndex
    used_indices = {0} # 保留第0号（missing材质）
    tile_files = glob.glob(tiles_pattern, recursive=True)
    for f in tile_files:
        try:
            with gzip.open(f, 'rb') as gz:
                res = inspect_tile.decode_prbm(gz.read())
            for g in res['groups']:
                used_indices.add(g['materialIndex'])
        except Exception:
            pass

    orig_size = os.path.getsize(tex_path)

    # 2. 读取 textures
    with gzip.open(tex_path, 'rt', encoding='utf-8') as f:
        textures = json.load(f)

    total_count = len(textures)
    used_count = len(used_indices)

    # 3. 瘦身：未使用的保留结构与索引，但将其巨型 base64 替换为 1x1 透明图
    pruned = []
    for idx, item in enumerate(textures):
        if idx in used_indices:
            c = item.get('color', [1, 1, 1, 1])
            if c[0] == 0 and c[1] == 0 and c[2] == 0 and not item.get('halfTransparent', False):
                item = dict(item)
                item['halfTransparent'] = True
                item['color'] = [0.0, 0.0, 0.0, 0.0]
            pruned.append(item)
        else:
            pruned.append({
                'color': [0, 0, 0, 0],
                'halfTransparent': True,
                'texture': BLANK_PNG
            })

    # 4. 备份原文件
    bak_path = tex_path + '.bak'
    if not os.path.exists(bak_path):
        os.rename(tex_path, bak_path)

    # 5. 写入压缩瘦身文件
    raw_data = json.dumps(pruned).encode('utf-8')
    with gzip.open(tex_path, 'wb', compresslevel=9) as f:
        f.write(raw_data)

    new_size = os.path.getsize(tex_path)
    print(f'[{map_name}] Processed: {len(tile_files)} tiles, {used_count}/{total_count} materials kept. Size: {orig_size/1024/1024:.2f}MB -> {new_size/1024/1024:.2f}MB (-{(1 - new_size/orig_size)*100:.1f}%)')

if __name__ == '__main__':
    maps = ['v0', 'v1', 'v2', 'v3', 'v4', 'v5', 'v6', 'v7', 'v8', 'v9', 'v10']
    base_dir = '/home/mio/mc_portal/web/map/maps'
    if len(sys.argv) > 1:
        if os.path.isdir(sys.argv[1]):
            base_dir = sys.argv[1]
            maps = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
        else:
            maps = sys.argv[1:]
    for m in maps:
        t0 = time.time()
        prune_map(m, base_dir)
