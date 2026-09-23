#!/usr/bin/env python3
import sys, os, gzip, json, struct

def decode_prbm(data):
    version = data[0]
    num_attributes = data[1] & 31
    num_vertices = data[2] + (data[3] << 8) + (data[4] << 16)
    num_indices = data[5] + (data[6] << 8) + (data[7] << 16)

    offset = 8
    attributes = {}
    for _ in range(num_attributes):
        name = ""
        while offset < len(data) and data[offset] != 0:
            name += chr(data[offset])
            offset += 1
        offset += 1 # skip null terminator
        attr_flags = data[offset]
        offset += 1
        cardinality = (attr_flags >> 4 & 3) + 1
        encoding = attr_flags & 15
        offset = (offset + 3) & ~3
        # bpe 对应: 1: Float32 (4), 2: Int16 (2), 3: Int8/SignedByte (1), 4: Int32 (4), 5: Uint16 (2), 6: Uint16 (2), 7: Uint8/UnsignedByte (1)
        bpe_map = {1: 4, 2: 2, 3: 1, 4: 4, 5: 2, 6: 2, 7: 1}
        bpe = bpe_map.get(encoding, 1)
        total_bytes = bpe * cardinality * num_vertices
        attributes[name] = {
            'cardinality': cardinality,
            'encoding': encoding,
            'offset': offset,
            'bpe': bpe,
            'bytes': total_bytes
        }
        offset += total_bytes

    # Material groups
    offset = (offset + 3) & ~3
    groups = []
    while offset + 12 <= len(data):
        mat_idx = int.from_bytes(data[offset:offset+4], 'little', signed=True)
        if mat_idx == -1:
            offset += 4
            break
        start = int.from_bytes(data[offset+4:offset+8], 'little')
        count = int.from_bytes(data[offset+8:offset+12], 'little')
        groups.append({'materialIndex': mat_idx, 'start': start, 'count': count})
        offset += 12

    return {
        'num_vertices': num_vertices,
        'attributes': attributes,
        'groups': groups,
        'raw_data': data
    }

def inspect(map_name, tile_path):
    textures_path = f"/home/mio/mc_portal/web/map/maps/{map_name}/textures.json.gz"
    with gzip.open(textures_path, "rt") as f:
        textures = json.load(f)

    with gzip.open(tile_path, "rb") as f:
        data = f.read()

    prbm = decode_prbm(data)
    print(f"=== Inspecting Tile: {tile_path} ===")
    print(f"Total Vertices: {prbm['num_vertices']} ({prbm['num_vertices']//3} triangles)")
    print(f"Attributes: {list(prbm['attributes'].keys())}")
    print(f"Material Groups: {len(prbm['groups'])}")
    
    mat_summary = {}
    for g in prbm['groups']:
        mid = g['materialIndex']
        mat_summary[mid] = mat_summary.get(mid, 0) + g['count']

    sorted_mats = sorted(mat_summary.items(), key=lambda x: x[1], reverse=True)
    print(f"\nTop Materials in tile:")
    for mid, count in sorted_mats[:30]:
        if 0 <= mid < len(textures):
            res = textures[mid].get('resourcePath', 'unknown')
        else:
            res = f"OUT_OF_BOUNDS({mid})"
        print(f"  [Mat {mid:4d}] {res:<50}: {count:6d} vertices ({count//3:5d} triangles)")

    # 光照分析
    if 'sunlight' in prbm['attributes']:
        sl_attr = prbm['attributes']['sunlight']
        raw = prbm['raw_data']
        off = sl_attr['offset']
        zeros = 0
        fulls = 0
        for i in range(prbm['num_vertices']):
            val = raw[off + i]
            if val == 0: zeros += 1
            elif val == 15: fulls += 1
        zero_pct = (zeros / prbm['num_vertices']) * 100 if prbm['num_vertices'] > 0 else 0
        full_pct = (fulls / prbm['num_vertices']) * 100 if prbm['num_vertices'] > 0 else 0
        print(f"\nSunlight Analysis: Zero-Light={zeros} ({zero_pct:.1f}%), Full-Light={fulls} ({full_pct:.1f}%)")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python3 inspect_tile.py <map_name> <tile_prbm_gz>")
        sys.exit(1)
    inspect(sys.argv[1], sys.argv[2])
