#!/usr/bin/env python3
"""
生成全 11 周目的直达独立路由 (/v0/map/index.html ~ /v10/map/index.html)
"""
import os

views = {
    "v0": ("v0:896:72:150:85:0.35:0.55:0:0:perspective", "v0 纯净生电起点"),
    "v1": ("v1:-320:72:90:100:0.4:0.5:0:0:perspective", "v1 工业科技时代"),
    "v2": ("v2:8:64:8:60:0.3:0.4:0:0:perspective", "v2 原版机制空岛"),
    "v3": ("v3:260:75:650:120:0.35:0.5:0:0:perspective", "v3 宏大自然生态"),
    "v4": ("v4:-24:148:-5764:100:0.35:0.5:0:0:perspective", "v4 群峦救援硬核重工"),
    "v5": ("v5:2200:120:-3150:120:0.35:0.5:0:0:perspective", "v5 模拟殖民地探险"),
    "v6": ("v6:-40:70:248:100:0.35:0.5:0:0:perspective", "v6 魔法金属与以太"),
    "v7": ("v7:0:75:-64:85:0.35:0.5:0:0:perspective", "v7 休闲农夫乐事"),
    "v8": ("v8:-280:85:-1780:100:0.35:0.5:0:0:perspective", "v8 华夏古风与群系"),
    "v9": ("v9:-32:105:50:85:0.35:0.5:0:0:perspective", "v9 现代正版旗舰"),
    "v10": ("v10:-992:75:-1008:120:0.35:0.5:0:0:perspective", "v10 宝可梦重铸冒险")
}

web_root = "/home/mio/mc_portal/web"

template = """<!DOCTYPE html>
<html lang="zh-CN">
    <head>
        <meta charset="utf-8">
        <base href="/">
        <meta name="viewport" content="user-scalable=no, width=device-width, initial-scale=1, maximum-scale=1">
        <meta name="description"
              content="BlueMap is a tool that generates 3D maps of your Minecraft worlds and displays them in your browser">
        <meta name="version" content="5.3">
        <meta name="keywords" content="bluemap, map, minecraft, minecraft map">
        <meta name="theme-color" content="#181a20">
        <meta name="og:site_name" content="无故事王国 3D 纪元视界">
        <meta name="og:title" content="无故事王国 · {title} 3D 全景地图">
        <meta name="og:description"
              content="无故事王国 {title} 3D 实体全景地图">
        <meta name="og:type" content="website">
        <meta name="robots" content="index,nofollow">
        <link rel="icon" href="/assets/favicon-8768b872.png">
        <title>无故事王国 · {title} 3D 地图</title>
        <!-- BlueMap Hash 预加载解析与补齐控制器 -->
        <script>
        (function() {{
          const targetView = "{view}";
          const currentMap = "{vid}";
          function normalize() {{
            const raw = (window.location.hash || "").replace("#", "").trim();
            if (!raw) {{
              history.replaceState(null, "", "#" + targetView);
            }} else {{
              const parts = raw.split(":");
              if (parts.length !== 10 || parts[0] !== currentMap) {{
                history.replaceState(null, "", "#" + targetView);
              }}
            }}
          }}
          normalize();
        }})();
        </script>
        <script type="module" crossorigin src="/assets/index-58a9319d.js"></script>
        <link rel="stylesheet" href="/assets/index-fa43c574.css">
        <link rel="stylesheet" href="/custom/hud_nav.css">
    </head>
    <body>
        <noscript>
            <strong>Sorry but BlueMap doesn't work without JavaScript enabled.
                Please <a href="https://www.enable-javascript.com/">enable</a> it to continue.</strong>
        </noscript>
        <div id="map-container"></div>
        <div id="app"></div>

        <!-- Minecraft 地牢风格内嵌导航栏 -->
        <script src="/js/mc_sound.js"></script>
        <script src="/custom/hud_nav.js"></script>
    </body>
</html>
"""

def deploy():
    for vid, (view, title) in views.items():
        map_dir = os.path.join(web_root, vid, "map")
        os.makedirs(map_dir, exist_ok=True)
        html_content = template.format(vid=vid, view=view, title=title)
        html_path = os.path.join(map_dir, "index.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"Generated route for {vid}: {html_path}")

    # 同时更新根目录 map.html 中的 base 标签与初始配置
    print("All 11 direct routes successfully deployed!")

if __name__ == "__main__":
    deploy()
