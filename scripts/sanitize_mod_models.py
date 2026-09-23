#!/usr/bin/env python3
import os, sys, zipfile, json, time, re

ZIP_PATH = '/home/mio/mc_portal/bluemap/packs/mod_assets.zip'
TEMP_PATH = ZIP_PATH + '.sanitized.tmp'

print("Starting Enhanced Mod Asset Sanitizer & Normalizer...")
t0 = time.time()

stats = {
    'total_models': 0,
    'parent_fixed': 0,
    'json_repaired': 0,
    'textures_fixed': 0,
    'forge_flattened': 0,
    'tintindex_cleared': 0,
    'snowrealmagic_fixed': 0
}

def try_repair_json(raw_str):
    s = raw_str.strip()
    s = re.sub(r'[^}\]]+$', '', s).strip()
    try:
        return json.loads(s)
    except Exception:
        pass
    
    if s.endswith('}}'):
        try:
            return json.loads(s[:-1])
        except Exception:
            pass

    m = re.search(r'(\{[\s\S]*\})', s)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    return None

def process_model(filename, data_bytes):
    stats['total_models'] += 1
    raw_str = None
    try:
        raw_str = data_bytes.decode('utf-8')
        model = json.loads(raw_str)
    except Exception:
        if raw_str is None:
            try:
                raw_str = data_bytes.decode('latin1')
            except Exception:
                return data_bytes
        model = try_repair_json(raw_str)
        if model is not None:
            stats['json_repaired'] += 1
        else:
            return data_bytes

    if not isinstance(model, dict):
        return data_bytes

    modified = False

    # 1. 修复 parent 缺少 minecraft: 前缀
    parent = model.get('parent')
    if isinstance(parent, str) and ':' not in parent:
        if parent.startswith(('block/', 'item/', 'builtin/')):
            model['parent'] = 'minecraft:' + parent
            stats['parent_fixed'] += 1
            modified = True

    # 2. 展平 Forge multi-layer
    if 'layers' in model and isinstance(model['layers'], dict):
        top_textures = dict(model.get('textures', {}))
        top_elements = list(model.get('elements', []))
        for layer_data in model['layers'].values():
            if isinstance(layer_data, dict):
                if 'textures' in layer_data and isinstance(layer_data['textures'], dict):
                    top_textures.update(layer_data['textures'])
                if 'elements' in layer_data and isinstance(layer_data['elements'], list):
                    top_elements.extend(layer_data['elements'])
        if top_elements:
            model['elements'] = top_elements
            model['textures'] = top_textures
            model.pop('layers', None)
            model.pop('loader', None)
            stats['forge_flattened'] += 1
            modified = True

    # 3. 修复 CFM 栅栏等非标准 tintindex: 1 导致被染脏色
    if 'cfm/' in filename or 'fence' in filename:
        for elem in model.get('elements', []):
            if isinstance(elem, dict) and 'faces' in elem:
                for f in elem['faces'].values():
                    if isinstance(f, dict) and f.get('tintindex') == 1:
                        f.pop('tintindex', None)
                        stats['tintindex_cleared'] += 1
                        modified = True

    # 4. 修复未定义的贴图变量
    if 'elements' in model and 'textures' in model and isinstance(model['textures'], dict):
        textures = model['textures']
        if len(textures) > 0:
            ref_vars = set()
            for elem in model.get('elements', []):
                if isinstance(elem, dict):
                    for f in elem.get('faces', {}).values():
                        if isinstance(f, dict):
                            tex = f.get('texture', '')
                            if isinstance(tex, str) and tex.startswith('#'):
                                ref_vars.add(tex[1:])
            missing_vars = ref_vars - set(textures.keys())
            if missing_vars:
                fallback = textures.get('particle')
                if not fallback or fallback.startswith('#'):
                    for v in textures.values():
                        if isinstance(v, str) and not v.startswith('#'):
                            fallback = v
                            break
                if not fallback:
                    fallback = 'minecraft:block/stone'
                for mv in missing_vars:
                    textures[mv] = fallback
                stats['textures_fixed'] += 1
                modified = True

    if modified:
        return json.dumps(model).encode('utf-8')
    return data_bytes

def process_blockstate(filename, data_bytes):
    if 'snowrealmagic/blockstates/snow.json' in filename:
        try:
            bs = json.loads(data_bytes.decode('utf-8'))
            changed = False
            def fix_model_path(obj):
                nonlocal changed
                if isinstance(obj, dict):
                    if 'model' in obj and isinstance(obj['model'], str) and ':' not in obj['model']:
                        obj['model'] = 'minecraft:' + obj['model']
                        changed = True
                    for v in obj.values():
                        fix_model_path(v)
                elif isinstance(obj, list):
                    for item in obj:
                        fix_model_path(item)
            fix_model_path(bs)
            if changed:
                stats['snowrealmagic_fixed'] += 1
                return json.dumps(bs).encode('utf-8')
        except Exception:
            pass
    return data_bytes

if not os.path.exists(ZIP_PATH):
    print(f"Error: {ZIP_PATH} not found!")
    sys.exit(1)

with zipfile.ZipFile(ZIP_PATH, 'r') as in_zf, zipfile.ZipFile(TEMP_PATH, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as out_zf:
    for item in in_zf.infolist():
        data = in_zf.read(item.filename)
        if '/models/' in item.filename and item.filename.endswith('.json'):
            data = process_model(item.filename, data)
        elif '/blockstates/' in item.filename and item.filename.endswith('.json'):
            data = process_blockstate(item.filename, data)
        out_zf.writestr(item, data)

os.replace(TEMP_PATH, ZIP_PATH)

print(f"\n=== Mod Asset Sanitization Complete in {time.time() - t0:.2f}s ===")
print(f"  Total Models Checked       : {stats['total_models']}")
print(f"  Parent Namespace Fixed     : {stats['parent_fixed']}")
print(f"  Corrupted JSON Repaired    : {stats['json_repaired']}")
print(f"  Missing Texture Fallbacks  : {stats['textures_fixed']}")
print(f"  Forge Composite Flattened  : {stats['forge_flattened']}")
print(f"  Invalid TintIndexes Cleared: {stats['tintindex_cleared']}")
print(f"  SnowRealMagic Blockstates  : {stats['snowrealmagic_fixed']}")
