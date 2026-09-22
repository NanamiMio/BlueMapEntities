#!/usr/bin/env node
/**
 * BlueMapEntities - Automated Pre-Render Visual Verification Suite
 * 四层核验体系之第四道防线：端到端微距多机位自动化巡检与阻断门禁
 *
 * 核心流程：
 * 1. 调起本地 Headless Chrome 并连接 CDP；
 * 2. 依次移动至各个关键生物/设施的预设微距机位；
 * 3. 截取高分辨率实景切片；
 * 4. 自动调用 assert_no_missing_textures.py 进行像素级缺失贴图扫描；
 * 5. 若通过则允许全量发布，若不通过则阻断。
 */

import { spawn } from "child_process";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ARTIFACT_DIR = process.env.ARTIFACT_DIR || "/Users/mio/.gemini/antigravity/brain/a7f70ece-8d8a-48f5-a028-2f2eb0bfad43";

// 预设关键实体的巡检机位矩阵
const TARGET_INSPECTIONS = [
  {
    name: "map_overview",
    desc: "全图全局宏观视野",
    evalScript: null,
  },
  {
    name: "sitting_wolf_macro",
    desc: "坐姿狼背部与地面咬合微距特写",
    evalScript: `
      (() => {
        const cm = window.bluemap.mapViewer.controlsManager;
        cm.position.x = 902.5;
        cm.position.y = 71.4;
        cm.position.z = 161.5;
        cm.distance = 0;
        
        const dx = 900.5 - 902.5;
        const dy = 70.8 - 71.4;
        const dz = 161.5 - 161.5;
        const horiz = Math.hypot(dx, dz);
        
        const pitch = -Math.atan2(dy, horiz) * 180 / Math.PI;
        const yaw = Math.atan2(-dx, dz) * 180 / Math.PI;
        
        cm.rotation = (yaw - 180) * Math.PI / 180;
        cm.angle = -(pitch - 90) * Math.PI / 180;
        window.bluemap.mapViewer.updateLoadedMapArea();
      })()
    `
  },
  {
    name: "enchanting_table_macro",
    desc: "附魔台悬浮展开魔法书微距特写",
    evalScript: `
      (() => {
        const cm = window.bluemap.mapViewer.controlsManager;
        cm.position.x = 902.5;
        cm.position.y = 71.4;
        cm.position.z = 161.5;
        cm.distance = 0;
        
        const dx = 899.5 - 902.5;
        const dy = 70.8 - 71.4;
        const dz = 162.8 - 161.5;
        const horiz = Math.hypot(dx, dz);
        
        const pitch = -Math.atan2(dy, horiz) * 180 / Math.PI;
        const yaw = Math.atan2(-dx, dz) * 180 / Math.PI;
        
        cm.rotation = (yaw - 180) * Math.PI / 180;
        cm.angle = -(pitch - 90) * Math.PI / 180;
        window.bluemap.mapViewer.updateLoadedMapArea();
      })()
    `
  }
];

async function run() {
  console.log("========================================================================");
  console.log("          BlueMapEntities 预渲染自动化巡检与截帧门禁");
  console.log("========================================================================\n");

  const port = 9295;
  const profileDir = `/tmp/chrome-prerender-${Date.now()}`;
  const chrome = spawn("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", [
    "--headless=new",
    `--remote-debugging-port=${port}`,
    `--user-data-dir=${profileDir}`,
    "--window-size=1600,1000",
    "--enable-webgl",
    "--ignore-gpu-blocklist",
    "--use-gl=angle",
    "--use-angle=metal",
    "http://10.0.0.104:8100/"
  ]);

  try {
    await new Promise(r => setTimeout(r, 4000));
    const res = await fetch(`http://127.0.0.1:${port}/json/list`);
    const targets = await res.json();
    const pageTarget = targets.find(t => t.type === "page") || targets[0];
    if (!pageTarget) throw new Error("无法找到 Chrome 页面目标");

    const ws = new WebSocket(pageTarget.webSocketDebuggerUrl);
    await new Promise(r => ws.onopen = r);

    let id = 1;
    function send(method, params = {}) {
      return new Promise((resolve, reject) => {
        const msgId = id++;
        const handler = (e) => {
          const d = JSON.parse(e.data);
          if (d.id === msgId) {
            ws.removeEventListener("message", handler);
            if (d.error) reject(d.error);
            else resolve(d.result);
          }
        };
        ws.addEventListener("message", handler);
        ws.send(JSON.stringify({ id: msgId, method, params }));
      });
    }

    await send("Runtime.enable");
    await send("Page.enable");

    // 等待地图初次加载完毕
    console.log("正在等待 BlueMap 3D 场景与资源加载就绪...");
    for (let i = 0; i < 30; i++) {
      const chk = await send("Runtime.evaluate", {
        expression: "Boolean(window.bluemap?.mapViewer?.map && window.bluemap?.mapViewer?.controlsManager)",
        returnByValue: true
      });
      if (chk?.result?.value === true) break;
      await new Promise(r => setTimeout(r, 500));
    }
    await new Promise(r => setTimeout(r, 3000));

    const capturedFiles = [];

    for (const insp of TARGET_INSPECTIONS) {
      console.log(`\n[机位巡检] 正在对准机位: ${insp.name} (${insp.desc})...`);
      if (insp.evalScript) {
        await send("Runtime.evaluate", { expression: insp.evalScript });
        await new Promise(r => setTimeout(r, 2500));
      }

      const shot = await send("Page.captureScreenshot", { format: "png" });
      const outPath = path.join(ARTIFACT_DIR, `verify_${insp.name}.png`);
      fs.writeFileSync(outPath, Buffer.from(shot.data, "base64"));
      console.log(`  📸 截帧完成: ${outPath}`);
      capturedFiles.push(outPath);
    }

    ws.close();
    chrome.kill();

    // 调用 Python 像素阻断检测
    console.log("\n------------------------------------------------------------------------");
    console.log("正在启动第三道防线：像素级 Missing Texture 自动化扫描...");
    console.log("------------------------------------------------------------------------");

    const assertScript = path.join(__dirname, "assert_no_missing_textures.py");
    const py = spawn("python3", [assertScript, ...capturedFiles], { stdio: "inherit" });
    py.on("close", (code) => {
      if (code === 0) {
        console.log("\n🎉 自动化多机位视觉核验 100% 通过！准许全量渲染发布。");
        process.exit(0);
      } else {
        console.error("\n🚨 发现材质异常或严重阻断错误！已阻断全量发布。");
        process.exit(code);
      }
    });

  } catch (err) {
    console.error("巡检执行异常:", err);
    chrome.kill();
    process.exit(1);
  }
}

run();
