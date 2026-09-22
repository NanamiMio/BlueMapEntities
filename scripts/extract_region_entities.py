#!/usr/bin/env python3
"""
Minecraft 1.16.5 / 1.12.2 Region 实体提取与 1.17+ 格式桥接转换器
用于将旧版 region/*.mca 中内置的 Level.Entities 提取并打包为标准的 entities/*.mca
使得 BlueMap 5.12 及 BlueMapEntities 能够无缝读取并以 3D 渲染旧周目的实体！
"""

import os, sys, glob, zlib, struct, io

class NBTStream:
    def __init__(self, data):
        self.stream = io.BytesIO(data)

    def read_tag(self, t):
        if t == 0: return None
        if t == 1: return struct.unpack('>b', self.stream.read(1))[0]
        if t == 2: return struct.unpack('>h', self.stream.read(2))[0]
        if t == 3: return struct.unpack('>i', self.stream.read(4))[0]
        if t == 4: return struct.unpack('>q', self.stream.read(8))[0]
        if t == 5: return struct.unpack('>f', self.stream.read(4))[0]
        if t == 6: return struct.unpack('>d', self.stream.read(8))[0]
        if t == 7:
            l = struct.unpack('>i', self.stream.read(4))[0]
            return self.stream.read(l)
        if t == 8:
            l = struct.unpack('>H', self.stream.read(2))[0]
            return self.stream.read(l).decode('utf-8', 'ignore')
        if t == 9: # list
            sub_t = struct.unpack('>b', self.stream.read(1))[0]
            count = struct.unpack('>i', self.stream.read(4))[0]
            return (sub_t, [self.read_tag(sub_t) for _ in range(count)])
        if t == 10: # compound
            res = {}
            while True:
                sub_t = struct.unpack('>b', self.stream.read(1))[0]
                if sub_t == 0: break
                nl = struct.unpack('>H', self.stream.read(2))[0]
                name = self.stream.read(nl).decode('utf-8', 'ignore')
                res[name] = (sub_t, self.read_tag(sub_t))
            return res
        if t == 11:
            l = struct.unpack('>i', self.stream.read(4))[0]
            return [struct.unpack('>i', self.stream.read(4))[0] for _ in range(l)]
        if t == 12:
            l = struct.unpack('>i', self.stream.read(4))[0]
            return [struct.unpack('>q', self.stream.read(8))[0] for _ in range(l)]
        return None

def write_tag(stream, t, val, name=None):
    if name is not None:
        stream.write(struct.pack('>b', t))
        name_bytes = name.encode('utf-8')
        stream.write(struct.pack('>H', len(name_bytes)))
        stream.write(name_bytes)
    
    if t == 1: stream.write(struct.pack('>b', val))
    elif t == 2: stream.write(struct.pack('>h', val))
    elif t == 3: stream.write(struct.pack('>i', val))
    elif t == 4: stream.write(struct.pack('>q', val))
    elif t == 5: stream.write(struct.pack('>f', val))
    elif t == 6: stream.write(struct.pack('>d', val))
    elif t == 7:
        stream.write(struct.pack('>i', len(val)))
        stream.write(val)
    elif t == 8:
        val_bytes = val.encode('utf-8')
        stream.write(struct.pack('>H', len(val_bytes)))
        stream.write(val_bytes)
    elif t == 9: # list
        sub_t, items = val
        stream.write(struct.pack('>b', sub_t))
        stream.write(struct.pack('>i', len(items)))
        for item in items:
            write_tag(stream, sub_t, item)
    elif t == 10: # compound
        for k, (sub_t, sub_v) in val.items():
            write_tag(stream, sub_t, sub_v, k)
        stream.write(b'\x00') # end tag
    elif t == 11: # int array
        stream.write(struct.pack('>i', len(val)))
        for x in val:
            stream.write(struct.pack('>i', x))
    elif t == 12: # long array
        stream.write(struct.pack('>i', len(val)))
        for x in val:
            stream.write(struct.pack('>q', x))

def serialize_entity_chunk(data_version, x_pos, z_pos, entities_sub_t, entities_list):
    """序列化为 1.17+ 格式的 Entity Chunk Compound"""
    root = {
        'DataVersion': (3, data_version),
        'Position': (11, [x_pos, z_pos]),
        'Entities': (9, (entities_sub_t, entities_list))
    }
    buf = io.BytesIO()
    # root tag 10, name ''
    buf.write(b'\x0a\x00\x00')
    for k, (t, v) in root.items():
        write_tag(buf, t, v, k)
    buf.write(b'\x00')
    return buf.getvalue()

def process_world(world_path):
    region_dir = os.path.join(world_path, 'region')
    if not os.path.isdir(region_dir):
        print(f"[SKIP] {world_path}: No region directory")
        return

    entities_dir = os.path.join(world_path, 'entities')
    os.makedirs(entities_dir, exist_ok=True)

    mca_files = glob.glob(os.path.join(region_dir, '*.mca'))
    print(f"[PROCESS] {world_path}: {len(mca_files)} mca files found in region/")

    converted_regions = 0
    total_entities = 0

    for mca_path in mca_files:
        base_name = os.path.basename(mca_path)
        out_mca_path = os.path.join(entities_dir, base_name)
        
        # 读取 region mca
        with open(mca_path, 'rb') as f:
            header = f.read(8192)
            if len(header) < 8192: continue
            locations = [struct.unpack('>I', header[i*4:i*4+4])[0] for i in range(1024)]
            timestamps = [struct.unpack('>I', header[4096+i*4:4096+i*4+4])[0] for i in range(1024)]

            new_chunks_data = {} # chunk_index -> compressed_bytes
            
            for i, loc in enumerate(locations):
                if loc == 0: continue
                offset = (loc >> 8) * 4096
                length = (loc & 0xFF) * 4096
                f.seek(offset)
                chunk_hdr = f.read(5)
                if len(chunk_hdr) < 5: continue
                chunk_len = struct.unpack('>I', chunk_hdr[:4])[0]
                comp_type = chunk_hdr[4]
                raw = f.read(chunk_len - 1)
                if comp_type != 2: continue # 只处理 zlib

                try:
                    decomp = zlib.decompress(raw)
                    if b'Entities' not in decomp: continue

                    # 解析 NBT
                    nl = struct.unpack('>H', decomp[1:3])[0]
                    payload = decomp[3+nl:]
                    parsed = NBTStream(payload).read_tag(10)
                    if not parsed: continue

                    data_version = parsed.get('DataVersion', (3, 2586))[1]
                    level = parsed.get('Level', (10, {}))[1]
                    entities_entry = level.get('Entities')
                    
                    if entities_entry and entities_entry[1] and len(entities_entry[1][1]) > 0:
                        ents_list = entities_entry[1][1]
                        ents_sub_t = entities_entry[1][0]
                        x_pos = level.get('xPos', (3, 0))[1]
                        z_pos = level.get('zPos', (3, 0))[1]

                        # 序列化为新格式
                        new_nbt = serialize_entity_chunk(data_version, x_pos, z_pos, ents_sub_t, ents_list)
                        comp = zlib.compress(new_nbt)
                        new_chunks_data[i] = (comp, timestamps[i])
                        total_entities += len(ents_list)
                except Exception as e:
                    pass

        # 如果这个 region 里有实体，打包生成 entities/*.mca
        if new_chunks_data:
            out_locations = [0] * 1024
            out_timestamps = [0] * 1024
            
            sectors = [bytearray(4096), bytearray(4096)] # 0: loc table, 1: time table
            curr_sector = 2

            for i in range(1024):
                if i in new_chunks_data:
                    comp_data, ts = new_chunks_data[i]
                    full_payload = struct.pack('>IB', len(comp_data) + 1, 2) + comp_data
                    sector_count = (len(full_payload) + 4095) // 4096
                    pad_len = sector_count * 4096 - len(full_payload)
                    padded_payload = full_payload + (b'\x00' * pad_len)
                    
                    sectors.append(padded_payload)
                    out_locations[i] = (curr_sector << 8) | sector_count
                    out_timestamps[i] = ts
                    curr_sector += sector_count

            # 写回 header
            loc_buf = io.BytesIO()
            for loc in out_locations:
                loc_buf.write(struct.pack('>I', loc))
            sectors[0] = loc_buf.getvalue()

            ts_buf = io.BytesIO()
            for ts in out_timestamps:
                ts_buf.write(struct.pack('>I', ts))
            sectors[1] = ts_buf.getvalue()

            with open(out_mca_path, 'wb') as out_f:
                for sec in sectors:
                    out_f.write(sec)
            
            converted_regions += 1

    print(f"[DONE] {world_path}: Converted {converted_regions} region files into entities/ (Total {total_entities} entities extracted!)")

if __name__ == '__main__':
    targets = sys.argv[1:] if len(sys.argv) > 1 else ['/home/mio/mc/v1/world']
    for t in targets:
        process_world(t)
