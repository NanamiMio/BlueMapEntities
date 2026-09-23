#!/usr/bin/env python3
"""
MCA 1.7.10 -> 1.16.5 High-Fidelity Converter (Multi-Core Optimized)
完整提取 1.7.10 Blocks + Add 12-bit 方块 ID、解析 level.dat FML ItemData 注册表、
支持原版 Metadata（树种/石材/羊毛/玻璃等）及以太、魔法金属、群峦传说 (TFC) 模组树木与地形复原，
杜绝树木退化为石头，并将 PascalCase 实体映射为现代标准小写命名空间。
"""

import os, sys, glob, zlib, struct, io, math, time
from concurrent.futures import ProcessPoolExecutor

# NBT Tag Types
TAG_END = 0
TAG_BYTE = 1
TAG_SHORT = 2
TAG_INT = 3
TAG_LONG = 4
TAG_FLOAT = 5
TAG_DOUBLE = 6
TAG_BYTE_ARRAY = 7
TAG_STRING = 8
TAG_LIST = 9
TAG_COMPOUND = 10
TAG_INT_ARRAY = 11
TAG_LONG_ARRAY = 12

class NBTReader:
    def __init__(self, data):
        self.stream = io.BytesIO(data)

    def read_byte(self): return struct.unpack('>b', self.stream.read(1))[0]
    def read_ubyte(self): return self.stream.read(1)[0]
    def read_short(self): return struct.unpack('>h', self.stream.read(2))[0]
    def read_int(self): return struct.unpack('>i', self.stream.read(4))[0]
    def read_long(self): return struct.unpack('>q', self.stream.read(8))[0]
    def read_float(self): return struct.unpack('>f', self.stream.read(4))[0]
    def read_double(self): return struct.unpack('>d', self.stream.read(8))[0]

    def read_string(self):
        length = struct.unpack('>H', self.stream.read(2))[0]
        return self.stream.read(length).decode('utf-8', errors='replace')

    def read_payload(self, tag_type):
        if tag_type == TAG_BYTE: return self.read_byte()
        elif tag_type == TAG_SHORT: return self.read_short()
        elif tag_type == TAG_INT: return self.read_int()
        elif tag_type == TAG_LONG: return self.read_long()
        elif tag_type == TAG_FLOAT: return self.read_float()
        elif tag_type == TAG_DOUBLE: return self.read_double()
        elif tag_type == TAG_BYTE_ARRAY:
            length = self.read_int()
            return bytearray(self.stream.read(length))
        elif tag_type == TAG_STRING: return self.read_string()
        elif tag_type == TAG_LIST:
            item_type = self.read_ubyte()
            length = self.read_int()
            return {'type': item_type, 'items': [self.read_payload(item_type) for _ in range(length)]}
        elif tag_type == TAG_COMPOUND:
            res = {}
            while True:
                item_tag = self.read_ubyte()
                if item_tag == TAG_END: break
                name = self.read_string()
                res[name] = (item_tag, self.read_payload(item_tag))
            return res
        elif tag_type == TAG_INT_ARRAY:
            length = self.read_int()
            return [self.read_int() for _ in range(length)]
        elif tag_type == TAG_LONG_ARRAY:
            length = self.read_int()
            return [self.read_long() for _ in range(length)]
        else:
            raise ValueError(f"Unknown tag type {tag_type}")

    def read_root(self):
        tag_type = self.read_ubyte()
        if tag_type == TAG_END: return None
        return self.read_string(), self.read_payload(tag_type)

class NBTWriter:
    def __init__(self):
        self.stream = io.BytesIO()

    def write_byte(self, val): self.stream.write(struct.pack('>b', val))
    def write_ubyte(self, val): self.stream.write(bytes([val]))
    def write_short(self, val): self.stream.write(struct.pack('>h', val))
    def write_int(self, val): self.stream.write(struct.pack('>i', val))
    def write_long(self, val): self.stream.write(struct.pack('>q', val))
    def write_float(self, val): self.stream.write(struct.pack('>f', val))
    def write_double(self, val): self.stream.write(struct.pack('>d', val))

    def write_string(self, val):
        data = val.encode('utf-8')
        self.stream.write(struct.pack('>H', len(data)))
        self.stream.write(data)

    def write_payload(self, tag_type, val):
        if tag_type == TAG_BYTE: self.write_byte(val)
        elif tag_type == TAG_SHORT: self.write_short(val)
        elif tag_type == TAG_INT: self.write_int(val)
        elif tag_type == TAG_LONG: self.write_long(val)
        elif tag_type == TAG_FLOAT: self.write_float(val)
        elif tag_type == TAG_DOUBLE: self.write_double(val)
        elif tag_type == TAG_BYTE_ARRAY:
            self.write_int(len(val))
            self.stream.write(val)
        elif tag_type == TAG_STRING: self.write_string(val)
        elif tag_type == TAG_LIST:
            self.write_ubyte(val['type'])
            self.write_int(len(val['items']))
            for it in val['items']: self.write_payload(val['type'], it)
        elif tag_type == TAG_COMPOUND:
            for k, (t, v) in val.items():
                self.write_ubyte(t)
                self.write_string(k)
                self.write_payload(t, v)
            self.write_ubyte(TAG_END)
        elif tag_type == TAG_INT_ARRAY:
            self.write_int(len(val))
            for v in val: self.write_int(v)
        elif tag_type == TAG_LONG_ARRAY:
            self.write_int(len(val))
            for v in val: self.write_long(v)

    def write_root(self, name, compound):
        self.write_ubyte(TAG_COMPOUND)
        self.write_string(name)
        self.write_payload(TAG_COMPOUND, compound)
        return self.stream.getvalue()

# 颜色与木种列表
COLORS = ["white", "orange", "magenta", "light_blue", "yellow", "lime", "pink", "gray",
          "light_gray", "cyan", "purple", "blue", "brown", "green", "red", "black"]
WOOD_TYPES = ["oak", "spruce", "birch", "jungle", "acacia", "dark_oak"]

def resolve_vanilla_1710(bid, meta):
    if bid == 0: return "minecraft:air"
    if bid == 1:
        sub = meta & 7
        if sub == 1: return "minecraft:granite"
        if sub == 2: return "minecraft:polished_granite"
        if sub == 3: return "minecraft:diorite"
        if sub == 4: return "minecraft:polished_diorite"
        if sub == 5: return "minecraft:andesite"
        if sub == 6: return "minecraft:polished_andesite"
        return "minecraft:stone"
    if bid == 2: return "minecraft:grass_block"
    if bid == 3: return "minecraft:podzol" if (meta & 7) == 2 else "minecraft:dirt"
    if bid == 4: return "minecraft:cobblestone"
    if bid == 5:
        w_idx = min(meta & 7, len(WOOD_TYPES) - 1)
        return f"minecraft:{WOOD_TYPES[w_idx]}_planks"
    if bid == 6:
        w_idx = min(meta & 7, len(WOOD_TYPES) - 1)
        return f"minecraft:{WOOD_TYPES[w_idx]}_sapling"
    if bid == 7: return "minecraft:bedrock"
    if bid in (8, 9): return "minecraft:water"
    if bid in (10, 11): return "minecraft:lava"
    if bid == 12: return "minecraft:sand"
    if bid == 13: return "minecraft:gravel"
    if bid == 14: return "minecraft:gold_ore"
    if bid == 15: return "minecraft:iron_ore"
    if bid == 16: return "minecraft:coal_ore"
    if bid == 17:
        w_idx = min(meta & 3, 3)
        return f"minecraft:{WOOD_TYPES[w_idx]}_log"
    if bid == 18:
        w_idx = min(meta & 3, 3)
        return f"minecraft:{WOOD_TYPES[w_idx]}_leaves"
    if bid == 19: return "minecraft:sponge"
    if bid == 20: return "minecraft:glass"
    if bid == 21: return "minecraft:lapis_ore"
    if bid == 22: return "minecraft:lapis_block"
    if bid == 23: return "minecraft:dispenser"
    if bid == 24: return "minecraft:sandstone"
    if bid == 25: return "minecraft:note_block"
    if bid == 26: return "minecraft:red_bed"
    if bid == 27: return "minecraft:powered_rail"
    if bid == 28: return "minecraft:detector_rail"
    if bid == 29: return "minecraft:sticky_piston"
    if bid == 30: return "minecraft:cobweb"
    if bid == 31: return "minecraft:tall_grass" if (meta & 3) == 2 else "minecraft:short_grass"
    if bid == 32: return "minecraft:dead_bush"
    if bid == 35:
        c_idx = min(meta & 15, 15)
        return f"minecraft:{COLORS[c_idx]}_wool"
    if bid == 37: return "minecraft:dandelion"
    if bid == 38: return "minecraft:poppy"
    if bid == 39: return "minecraft:brown_mushroom"
    if bid == 40: return "minecraft:red_mushroom"
    if bid == 41: return "minecraft:gold_block"
    if bid == 42: return "minecraft:iron_block"
    if bid == 44: return "minecraft:smooth_stone_slab"
    if bid == 45: return "minecraft:bricks"
    if bid == 46: return "minecraft:tnt"
    if bid == 47: return "minecraft:bookshelf"
    if bid == 48: return "minecraft:mossy_cobblestone"
    if bid == 49: return "minecraft:obsidian"
    if bid == 50: return "minecraft:torch"
    if bid == 51: return "minecraft:fire"
    if bid == 53: return "minecraft:oak_stairs"
    if bid == 54: return "minecraft:chest"
    if bid == 56: return "minecraft:diamond_ore"
    if bid == 57: return "minecraft:diamond_block"
    if bid == 58: return "minecraft:crafting_table"
    if bid in (61, 62): return "minecraft:furnace"
    if bid == 64: return "minecraft:oak_door"
    if bid == 65: return "minecraft:ladder"
    if bid == 66: return "minecraft:rail"
    if bid == 67: return "minecraft:cobblestone_stairs"
    if bid in (73, 74): return "minecraft:redstone_ore"
    if bid == 78: return "minecraft:snow"
    if bid == 79: return "minecraft:ice"
    if bid == 80: return "minecraft:snow_block"
    if bid == 81: return "minecraft:cactus"
    if bid == 82: return "minecraft:clay"
    if bid == 83: return "minecraft:sugar_cane"
    if bid == 85: return "minecraft:oak_fence"
    if bid == 86: return "minecraft:pumpkin"
    if bid == 87: return "minecraft:netherrack"
    if bid == 88: return "minecraft:soul_sand"
    if bid == 89: return "minecraft:glowstone"
    if bid == 95:
        c_idx = min(meta & 15, 15)
        return f"minecraft:{COLORS[c_idx]}_stained_glass"
    if bid == 98: return "minecraft:stone_bricks"
    if bid == 102: return "minecraft:glass_pane"
    if bid == 103: return "minecraft:melon"
    if bid == 106: return "minecraft:vine"
    if bid == 111: return "minecraft:lily_pad"
    if bid == 121: return "minecraft:end_stone"
    if bid == 123: return "minecraft:redstone_lamp"
    if bid == 126: return "minecraft:oak_slab"
    if bid == 134: return "minecraft:spruce_stairs"
    if bid == 135: return "minecraft:birch_stairs"
    if bid == 136: return "minecraft:jungle_stairs"
    if bid == 160:
        c_idx = min(meta & 15, 15)
        return f"minecraft:{COLORS[c_idx]}_stained_glass_pane"
    if bid == 161:
        return "minecraft:dark_oak_leaves" if (meta & 1) == 1 else "minecraft:acacia_leaves"
    if bid == 162:
        return "minecraft:dark_oak_log" if (meta & 1) == 1 else "minecraft:acacia_log"
    if bid == 163: return "minecraft:acacia_stairs"
    if bid == 164: return "minecraft:dark_oak_stairs"
    if bid == 170: return "minecraft:hay_block"
    if bid == 172: return "minecraft:terracotta"
    if bid == 173: return "minecraft:coal_block"
    if bid == 174: return "minecraft:packed_ice"
    if bid == 175: return "minecraft:sunflower"
    return "minecraft:stone"

AETHER_EXPLICIT = {
    "aether_legacy:skyroot_log": "minecraft:birch_log",
    "aether_legacy:skyroot_leaves": "minecraft:birch_leaves",
    "aether_legacy:golden_oak_leaves": "minecraft:oak_leaves",
    "aether_legacy:crystal_leaves": "minecraft:flowering_azalea_leaves",
    "aether_legacy:crystal_fruit_leaves": "minecraft:flowering_azalea_leaves",
    "aether_legacy:holiday_leaves": "minecraft:spruce_leaves",
    "aether_legacy:aether_grass": "minecraft:grass_block",
    "aether_legacy:enchanted_aether_grass": "minecraft:moss_block",
    "aether_legacy:aether_dirt": "minecraft:dirt",
    "aether_legacy:holystone": "minecraft:end_stone",
    "aether_legacy:mossy_holystone": "minecraft:mossy_cobblestone",
    "aether_legacy:holystone_brick": "minecraft:end_stone_bricks",
    "aether_legacy:aercloud": "minecraft:white_stained_glass",
    "aether_legacy:aerogel": "minecraft:light_blue_stained_glass",
    "aether_legacy:quicksoil": "minecraft:sand",
    "aether_legacy:quicksoil_glass": "minecraft:glass",
    "aether_legacy:ambrosium_ore": "minecraft:coal_ore",
    "aether_legacy:zanite_ore": "minecraft:iron_ore",
    "aether_legacy:gravitite_ore": "minecraft:gold_ore",
    "aether_legacy:pillar": "minecraft:quartz_pillar",
    "aether_legacy:carved_stone": "minecraft:chiseled_quartz_block",
    "aether_legacy:angelic_stone": "minecraft:quartz_block",
    "aether_legacy:hellfire_stone": "minecraft:nether_bricks",
    "aether_legacy:skyroot_planks": "minecraft:birch_planks",
    "aether_legacy:skyroot_stairs": "minecraft:birch_stairs",
    "aether_legacy:skyroot_slab": "minecraft:birch_slab",
    "aether_legacy:skyroot_fence": "minecraft:birch_fence",
    "aether_legacy:skyroot_fence_gate": "minecraft:birch_fence_gate",
    "aether_legacy:ambrosium_torch": "minecraft:torch",
}

LEGACY_ENTITY_MAP = {
    "Cow": "minecraft:cow",
    "Sheep": "minecraft:sheep",
    "Pig": "minecraft:pig",
    "Chicken": "minecraft:chicken",
    "Wolf": "minecraft:wolf",
    "Villager": "minecraft:villager",
    "Zombie": "minecraft:zombie",
    "Skeleton": "minecraft:skeleton",
    "Spider": "minecraft:spider",
    "Creeper": "minecraft:creeper",
    "Enderman": "minecraft:enderman",
    "Bat": "minecraft:bat",
    "Squid": "minecraft:squid",
    "Ozelot": "minecraft:ocelot",
    "EntityHorse": "minecraft:horse",
    "MushroomCow": "minecraft:mooshroom",
    "Slime": "minecraft:slime",
    "LavaSlime": "minecraft:magma_cube",
    "ArmorStand": "minecraft:armor_stand",
    "Boat": "minecraft:boat",
    "MinecartRideable": "minecraft:minecart",
    "MinecartChest": "minecraft:chest_minecart",
}

def resolve_mod_block(raw_name):
    low = raw_name.lower()
    if raw_name in AETHER_EXPLICIT:
        return AETHER_EXPLICIT[raw_name]

    # TerraFirmaCraft 专属映射
    if 'terrafirmacraft' in low:
        if 'stoneigin' in low or 'stoneigex' in low or 'stonesed' in low or 'stonemm' in low:
            if 'cobble' in low: return "minecraft:cobblestone"
            if 'smooth' in low: return "minecraft:smooth_stone"
            if 'brick' in low: return "minecraft:stone_bricks"
            return "minecraft:stone"
        if 'dirt' in low: return "minecraft:dirt"
        if 'grass' in low: return "minecraft:grass_block"
        if 'clay' in low: return "minecraft:clay"
        if 'sand' in low: return "minecraft:sand"
        if 'gravel' in low: return "minecraft:gravel"
        if 'lognatural' in low: return "minecraft:oak_log"
        if 'leaves' in low: return "minecraft:oak_leaves"
        if 'ore' in low: return "minecraft:iron_ore"
        if 'planks' in low: return "minecraft:oak_planks"

    # 通用语义分类（树木绝不退化为石头）
    if 'log' in low or ('wood' in low and not any(k in low for k in ['plank', 'slab', 'stair', 'button', 'door', 'fence', 'salb'])):
        if 'cherry' in low or 'violet' in low: return "minecraft:cherry_log"
        if 'spruce' in low or 'pine' in low: return "minecraft:spruce_log"
        if 'birch' in low or 'skyroot' in low: return "minecraft:birch_log"
        if 'jungle' in low or 'palm' in low: return "minecraft:jungle_log"
        if 'acacia' in low or 'orange' in low: return "minecraft:acacia_log"
        if 'netherblue' in low: return "minecraft:warped_stem"
        if 'netherred' in low: return "minecraft:crimson_stem"
        return "minecraft:oak_log"

    if 'leave' in low or 'leaves' in low:
        if 'cherry' in low or 'violet' in low: return "minecraft:cherry_leaves"
        if 'spruce' in low or 'pine' in low: return "minecraft:spruce_leaves"
        if 'birch' in low or 'skyroot' in low: return "minecraft:birch_leaves"
        if 'jungle' in low or 'palm' in low: return "minecraft:jungle_leaves"
        if 'acacia' in low or 'orange' in low: return "minecraft:acacia_leaves"
        if 'flower' in low or 'fruit' in low: return "minecraft:flowering_azalea_leaves"
        return "minecraft:oak_leaves"

    if 'plank' in low:
        if 'spruce' in low: return "minecraft:spruce_planks"
        if 'birch' in low: return "minecraft:birch_planks"
        if 'jungle' in low: return "minecraft:jungle_planks"
        if 'acacia' in low: return "minecraft:acacia_planks"
        if 'cherry' in low: return "minecraft:cherry_planks"
        return "minecraft:oak_planks"

    if 'grass' in low:
        if 'path' in low: return "minecraft:dirt_path"
        if 'tall' in low or 'plant' in low: return "minecraft:tall_grass"
        return "minecraft:grass_block"

    if 'dirt' in low or 'soil' in low or 'farmland' in low:
        return "minecraft:farmland" if 'farm' in low else "minecraft:dirt"

    if 'ore' in low:
        if 'gold' in low: return "minecraft:gold_ore"
        if 'diamond' in low: return "minecraft:diamond_ore"
        if 'coal' in low: return "minecraft:coal_ore"
        if 'redstone' in low: return "minecraft:redstone_ore"
        if 'lapis' in low: return "minecraft:lapis_ore"
        if 'emerald' in low: return "minecraft:emerald_ore"
        return "minecraft:iron_ore"

    if 'deepslate' in low or 'deepstone' in low:
        if 'brick' in low: return "minecraft:deepslate_bricks"
        if 'stair' in low: return "minecraft:deepslate_brick_stairs"
        return "minecraft:deepslate"

    if 'glass' in low: return "minecraft:glass"
    if 'torch' in low: return "minecraft:torch"
    if 'stair' in low: return "minecraft:stone_brick_stairs"
    if 'slab' in low or 'salb' in low: return "minecraft:stone_brick_slab"
    if 'wall' in low: return "minecraft:cobblestone_wall"
    if 'chest' in low: return "minecraft:chest"
    if 'flower' in low or 'sapling' in low or 'crop' in low: return "minecraft:poppy"
    if 'sand' in low: return "minecraft:sand"

    return "minecraft:stone"

def load_mod_block_map(world_dir):
    level_dat = os.path.join(world_dir, 'level.dat')
    if not os.path.exists(level_dat): return {}
    try:
        with open(level_dat, 'rb') as f:
            decomp = zlib.decompress(f.read(), 16 + zlib.MAX_WBITS)
        
        idx = decomp.find(b'ItemData')
        if idx == -1: return {}
        pos = idx + 8
        count = struct.unpack('>i', decomp[pos+1:pos+5])[0]
        cur = pos + 5
        mod_map = {}
        for _ in range(count):
            comp = {}
            while True:
                tag_t = decomp[cur]
                cur += 1
                if tag_t == 0: break
                nl = struct.unpack('>H', decomp[cur:cur+2])[0]
                cur += 2
                name = decomp[cur:cur+nl].decode('utf-8', 'ignore')
                cur += nl
                if tag_t == 1: val = struct.unpack('>b', decomp[cur:cur+1])[0]; cur += 1
                elif tag_t == 2: val = struct.unpack('>h', decomp[cur:cur+2])[0]; cur += 2
                elif tag_t == 3: val = struct.unpack('>i', decomp[cur:cur+4])[0]; cur += 4
                elif tag_t == 8:
                    slen = struct.unpack('>H', decomp[cur:cur+2])[0]; cur += 2
                    val = decomp[cur:cur+slen]; cur += slen
                else: break
                comp[name] = val
            k = comp.get('K', b'')
            v = comp.get('V', -1)
            if k.startswith(b'\x01'): # Block
                mod_map[v] = k[1:].decode('utf-8', 'ignore')
        return mod_map
    except Exception as e:
        print(f"Notice: Failed to parse level.dat ItemData: {e}")
        return {}

def pack_block_states(indices, bpe):
    vals_per_long = 64 // bpe
    mask = (1 << bpe) - 1
    long_count = math.ceil(len(indices) / vals_per_long)
    longs = []
    idx = 0
    for _ in range(long_count):
        val = 0
        for i in range(vals_per_long):
            if idx < len(indices):
                val |= (indices[idx] & mask) << (i * bpe)
                idx += 1
        if val >= (1 << 63): val -= (1 << 64)
        longs.append(val)
    return longs

def convert_section_1710_to_116(sec_compound, mod_block_map):
    if 'Blocks' not in sec_compound: return sec_compound
    blocks = sec_compound['Blocks'][1]
    data = sec_compound['Data'][1] if 'Data' in sec_compound else bytearray(2048)
    add_data = sec_compound['Add'][1] if 'Add' in sec_compound else None
    y_val = sec_compound['Y'][1]

    unique_ids = []
    palette_map = {}
    indices = []

    for i in range(4096):
        b_low = blocks[i] & 0xFF
        if add_data is not None:
            add_byte = add_data[i >> 1]
            add_nibble = (add_byte >> (4 * (i & 1))) & 0x0F
            full_id = b_low | (add_nibble << 8)
        else:
            full_id = b_low

        data_byte = data[i >> 1]
        meta = (data_byte >> (4 * (i & 1))) & 0x0F

        if full_id == 0:
            bname = "minecraft:air"
        elif full_id in mod_block_map:
            bname = resolve_mod_block(mod_block_map[full_id])
        else:
            bname = resolve_vanilla_1710(full_id, meta)

        if bname not in palette_map:
            palette_map[bname] = len(unique_ids)
            unique_ids.append(bname)
        indices.append(palette_map[bname])

    palette_items = [{'Name': (TAG_STRING, name)} for name in unique_ids]
    bpe = max(4, math.ceil(math.log2(len(unique_ids)))) if len(unique_ids) > 1 else 4
    block_states = pack_block_states(indices, bpe)

    new_sec = {
        'Y': (TAG_BYTE, y_val),
        'Palette': (TAG_LIST, {'type': TAG_COMPOUND, 'items': palette_items}),
        'BlockStates': (TAG_LONG_ARRAY, block_states)
    }
    if 'BlockLight' in sec_compound: new_sec['BlockLight'] = sec_compound['BlockLight']
    if 'SkyLight' in sec_compound: new_sec['SkyLight'] = sec_compound['SkyLight']
    return new_sec

def convert_chunk_1710_to_116(decompressed_data, mod_block_map):
    reader = NBTReader(decompressed_data)
    root = reader.read_root()
    if not root: return None
    root_name, root_data = root
    if 'Level' not in root_data: return decompressed_data

    level_compound = root_data['Level'][1]
    root_data['DataVersion'] = (TAG_INT, 2586)
    level_compound['Status'] = (TAG_STRING, 'full')

    if 'Sections' in level_compound:
        sec_list = level_compound['Sections'][1]['items']
        new_sec_list = [convert_section_1710_to_116(sec, mod_block_map) for sec in sec_list]
        level_compound['Sections'] = (TAG_LIST, {'type': TAG_COMPOUND, 'items': new_sec_list})

    # 规范化 1.7.10 PascalCase 实体 ID
    if 'Entities' in level_compound:
        entities_list = level_compound['Entities'][1]['items']
        for ent in entities_list:
            if 'id' in ent:
                tag_t, ent_id = ent['id']
                if ent_id in LEGACY_ENTITY_MAP:
                    ent['id'] = (tag_t, LEGACY_ENTITY_MAP[ent_id])

    writer = NBTWriter()
    return writer.write_root(root_name, root_data)

def convert_single_mca(args):
    src_path, dst_path, mod_block_map = args
    try:
        with open(src_path, 'rb') as f: data = f.read()
        if len(data) < 8192: return 0

        header_locations = data[:4096]
        header_timestamps = data[4096:8192]
        new_sectors = bytearray(8192)
        new_locations = bytearray(4096)
        converted_chunks = 0

        for i in range(1024):
            offset = int.from_bytes(header_locations[i*4:i*4+3], 'big') * 4096
            if 0 < offset < len(data):
                length = int.from_bytes(data[offset:offset+4], 'big')
                comp_type = data[offset+4]
                chunk_bytes = data[offset+5:offset+4+length]
                try:
                    if comp_type == 2: decomp = zlib.decompress(chunk_bytes)
                    elif comp_type == 1: decomp = zlib.decompress(chunk_bytes, 16 + zlib.MAX_WBITS)
                    else: decomp = chunk_bytes

                    converted = convert_chunk_1710_to_116(decomp, mod_block_map)
                    if converted:
                        recomp = zlib.compress(converted)
                        total_len = len(recomp) + 1
                        sec_offset = len(new_sectors) // 4096
                        sec_data = struct.pack('>I', total_len) + bytes([2]) + recomp
                        pad_len = 4096 - (len(sec_data) % 4096)
                        if pad_len != 4096: sec_data += bytearray(pad_len)
                        sec_count = len(sec_data) // 4096
                        new_sectors.extend(sec_data)
                        new_locations[i*4:i*4+3] = sec_offset.to_bytes(3, 'big')
                        new_locations[i*4+3] = sec_count
                        converted_chunks += 1
                except: pass

        new_sectors[0:4096] = new_locations
        new_sectors[4096:8192] = header_timestamps
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
        with open(dst_path, 'wb') as f: f.write(new_sectors)
        return converted_chunks
    except Exception as e:
        return 0

def convert_world_1710(src_world_dir, dst_world_dir):
    print(f"=== 开始 1.7.10 -> 1.16.5 高精度世界转换 ===")
    print(f"源世界目录: {src_world_dir}")
    print(f"目标镜像目录: {dst_world_dir}")
    t0 = time.time()

    mod_map = load_mod_block_map(src_world_dir)
    print(f"成功解析 level.dat Mod 方块映射表: {len(mod_map)} 个方块注册")

    src_region = os.path.join(src_world_dir, 'region')
    dst_region = os.path.join(dst_world_dir, 'region')
    os.makedirs(dst_region, exist_ok=True)

    # 复制 level.dat 并修改 DataVersion
    level_dat = os.path.join(src_world_dir, 'level.dat')
    if os.path.exists(level_dat):
        with open(level_dat, 'rb') as f: ld = f.read()
        try:
            decomp = zlib.decompress(ld, 16 + zlib.MAX_WBITS)
            reader = NBTReader(decomp)
            rname, rdata = reader.read_root()
            rdata['DataVersion'] = (TAG_INT, 2586)
            writer = NBTWriter()
            new_ld = writer.write_root(rname, rdata)
            with open(os.path.join(dst_world_dir, 'level.dat'), 'wb') as f:
                f.write(zlib.compress(new_ld, 16 + zlib.MAX_WBITS))
        except:
            with open(os.path.join(dst_world_dir, 'level.dat'), 'wb') as f: f.write(ld)

    mca_files = sorted([f for f in os.listdir(src_region) if f.endswith('.mca')])
    print(f"检测到 {len(mca_files)} 个 MCA 区块文件，启动多核并发转换...")

    tasks = []
    for f in mca_files:
        tasks.append((os.path.join(src_region, f), os.path.join(dst_region, f), mod_map))

    total_chunks = 0
    with ProcessPoolExecutor(max_workers=8) as executor:
        for idx, chunks in enumerate(executor.map(convert_single_mca, tasks)):
            total_chunks += chunks
            if (idx + 1) % 10 == 0 or (idx + 1) == len(mca_files):
                print(f"[{idx+1}/{len(mca_files)}] MCA 文件转换完毕 (累计区块: {total_chunks})")

    print(f"=== 转换完成! 耗时 {time.time()-t0:.2f}s, 共处理 {len(mca_files)} 个 MCA 文件, {total_chunks} 个有效区块 ===")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("用法: python3 mca_convert.py <src_world_dir> <dst_world_dir>")
        sys.exit(1)
    convert_world_1710(sys.argv[1], sys.argv[2])
