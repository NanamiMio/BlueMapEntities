package de.bluecolored.bluemap.entities.renderer;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import de.bluecolored.bluemap.core.map.TextureGallery;
import de.bluecolored.bluemap.core.map.hires.TileModel;
import de.bluecolored.bluemap.core.map.hires.TileModelView;
import de.bluecolored.bluemap.core.resources.ResourcePath;
import de.bluecolored.bluemap.core.resources.pack.resourcepack.blockstate.Variant;
import de.bluecolored.bluemap.core.util.Key;
import de.bluecolored.bluemap.core.world.BlockEntity;
import de.bluecolored.bluemap.core.world.BlockState;
import de.bluecolored.bluemap.core.world.block.BlockNeighborhood;
import de.bluecolored.bluemap.core.world.mca.blockentity.SignBlockEntity;

import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.File;
import java.io.FileReader;
import java.util.*;
import java.util.List;
import java.util.concurrent.ConcurrentHashMap;
import java.util.logging.Level;
import java.util.logging.Logger;

public class SignTextRenderer {

    private static final Logger LOGGER = Logger.getLogger("SignTextRenderer");
    private static final int CANVAS_W = 96;
    private static final int CANVAS_H = 48;

    private static final Map<String, FallbackSign> FALLBACK_SIGNS = new ConcurrentHashMap<>();
    private static volatile boolean fallbackLoaded = false;
    private static final Font BASE_SIGN_FONT;
    private static final boolean IS_PIXEL_FONT;

    static {
        Font loaded = null;
        boolean isPixel = false;
        File[] fontCandidates = new File[]{
                new File(System.getProperty("user.home"), ".local/share/fonts/unifont.ttf"),
                new File(System.getProperty("user.home"), "Library/Fonts/unifont.ttf"),
                new File("/home/mio/.local/share/fonts/unifont.ttf"),
                new File("unifont.ttf"),
                new File("../unifont.ttf"),
                new File("/home/mio/bluemap-render/unifont.ttf"),
                new File("/usr/share/fonts/truetype/unifont/unifont.ttf"),
                new File(System.getProperty("user.home"), ".local/share/fonts/wqy-microhei.ttc"),
                new File("/home/mio/.local/share/fonts/wqy-microhei.ttc"),
                new File("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc")
        };
        for (File f : fontCandidates) {
            if (f.exists() && f.isFile()) {
                try {
                    loaded = Font.createFont(Font.TRUETYPE_FONT, f);
                    isPixel = f.getName().toLowerCase(Locale.ROOT).contains("unifont");
                    LOGGER.info("Loaded custom sign font from " + f.getAbsolutePath() + " (isPixel=" + isPixel + ")");
                    break;
                } catch (Exception e) {
                    LOGGER.log(Level.WARNING, "Failed to load font from " + f, e);
                }
            }
        }
        if (loaded == null) {
            String[] families = new String[]{"Unifont", "WenQuanYi Micro Hei", "Noto Sans CJK SC", "Microsoft YaHei", "PingFang SC", "SimHei", Font.SANS_SERIF};
            for (String family : families) {
                Font test = new Font(family, Font.PLAIN, 16);
                if (test.canDisplay('经') || family.equals(Font.SANS_SERIF)) {
                    loaded = test;
                    isPixel = family.toLowerCase(Locale.ROOT).contains("unifont");
                    break;
                }
            }
        }
        if (loaded == null) {
            loaded = new Font(Font.SANS_SERIF, Font.PLAIN, 16);
        }
        BASE_SIGN_FONT = loaded;
        IS_PIXEL_FONT = isPixel;
    }

    private final TextureGallery textureGallery;
    private int whiteMaterialIndex = -1;

    // Cache of rendered text quads by (lines + color)
    private final Map<String, List<Quad>> textQuadCache = new ConcurrentHashMap<>();

    private static final Map<String, float[]> DYE_COLORS = new HashMap<>();

    static {
        DYE_COLORS.put("black", new float[]{0.08f, 0.08f, 0.08f});
        DYE_COLORS.put("white", new float[]{0.95f, 0.95f, 0.95f});
        DYE_COLORS.put("orange", new float[]{0.95f, 0.55f, 0.15f});
        DYE_COLORS.put("magenta", new float[]{0.80f, 0.30f, 0.75f});
        DYE_COLORS.put("light_blue", new float[]{0.40f, 0.65f, 0.90f});
        DYE_COLORS.put("yellow", new float[]{0.95f, 0.85f, 0.20f});
        DYE_COLORS.put("lime", new float[]{0.50f, 0.80f, 0.15f});
        DYE_COLORS.put("pink", new float[]{0.95f, 0.60f, 0.70f});
        DYE_COLORS.put("gray", new float[]{0.35f, 0.35f, 0.35f});
        DYE_COLORS.put("light_gray", new float[]{0.65f, 0.65f, 0.65f});
        DYE_COLORS.put("cyan", new float[]{0.15f, 0.60f, 0.65f});
        DYE_COLORS.put("purple", new float[]{0.60f, 0.25f, 0.75f});
        DYE_COLORS.put("blue", new float[]{0.25f, 0.30f, 0.75f});
        DYE_COLORS.put("brown", new float[]{0.50f, 0.35f, 0.20f});
        DYE_COLORS.put("green", new float[]{0.40f, 0.55f, 0.15f});
        DYE_COLORS.put("red", new float[]{0.80f, 0.20f, 0.15f});
    }

    public SignTextRenderer(TextureGallery textureGallery) {
        this.textureGallery = textureGallery;
        loadFallbackSigns();
    }

    private int getWhiteMaterial() {
        if (whiteMaterialIndex > 0) return whiteMaterialIndex;
        try {
            whiteMaterialIndex = textureGallery.get(new ResourcePath<>(Key.MINECRAFT_NAMESPACE, "block/white_concrete"));
            if (whiteMaterialIndex <= 0) {
                whiteMaterialIndex = textureGallery.get(new ResourcePath<>(Key.MINECRAFT_NAMESPACE, "block/snow"));
            }
            if (whiteMaterialIndex <= 0) {
                whiteMaterialIndex = textureGallery.get(new ResourcePath<>(Key.MINECRAFT_NAMESPACE, "block/white_wool"));
            }
            if (whiteMaterialIndex <= 0) {
                whiteMaterialIndex = textureGallery.get(new ResourcePath<>(Key.MINECRAFT_NAMESPACE, "block/stone"));
            }
            if (whiteMaterialIndex <= 0) {
                whiteMaterialIndex = textureGallery.get(new ResourcePath<>(Key.MINECRAFT_NAMESPACE, "block/oak_planks"));
            }
            if (whiteMaterialIndex <= 0) {
                whiteMaterialIndex = -1;
            }
        } catch (Exception e) {
            whiteMaterialIndex = -1;
        }
        return whiteMaterialIndex;
    }

    public void renderSign(BlockNeighborhood block, Variant variant, TileModelView tileModel) {
        int matIndex = getWhiteMaterial();
        if (matIndex <= 0) return;

        BlockState state = block.getBlockState();
        String path = state.getId().getValue();
        boolean isWallSign = path.contains("wall_sign");
        boolean isHangingSign = path.contains("hanging_sign");

        List<String> lines = new ArrayList<>();
        String colorName = "black";
        boolean glowing = false;

        // 1. Try reading from BlockEntity
        BlockEntity be = block.getBlockEntity();
        if (be instanceof SignBlockEntity signBe) {
            SignBlockEntity.TextData front = signBe.getFrontText();
            if (front != null) {
                colorName = front.getColor() != null ? front.getColor() : "black";
                glowing = front.isHasGlowingText();
                if (front.getMessages() != null) {
                    for (Object msg : front.getMessages()) {
                        String clean = cleanMessage(msg);
                        if (!clean.isEmpty()) lines.add(clean);
                    }
                }
            } else if (signBe instanceof SignBlockEntity.LegacySignBlockEntity legacy) {
                colorName = legacy.getColor() != null ? legacy.getColor() : "black";
                glowing = legacy.isHasGlowingText();
                addIfNotEmpty(lines, cleanMessage(legacy.getText1()));
                addIfNotEmpty(lines, cleanMessage(legacy.getText2()));
                addIfNotEmpty(lines, cleanMessage(legacy.getText3()));
                addIfNotEmpty(lines, cleanMessage(legacy.getText4()));
            }
        }

        // 2. Fallback to signs.json if BlockEntity text was empty
        if (lines.isEmpty()) {
            String key = block.getX() + "," + block.getY() + "," + block.getZ();
            FallbackSign fallback = FALLBACK_SIGNS.get(key);
            if (fallback != null && !fallback.lines.isEmpty()) {
                lines.addAll(fallback.lines);
                if (fallback.color != null) colorName = fallback.color;
                glowing = fallback.glowing;
            }
        }

        if (lines.isEmpty()) return;

        // 3. Obtain 2D quads in canvas normalized space [0..1]
        List<Quad> quads = getOrCreateQuads(lines);
        if (quads.isEmpty()) return;

        // 4. Calculate 3D bounds on the sign board front face
        // Coordinates are in local block space [0..1]
        // Wall sign board: height 0.5 (y: 0.2708..0.7708, center: 0.5208), front face z = 1.75/16 + 0.003
        // Standing sign board: height 0.5 (y: 0.5833..1.0833, center: 0.8333), front face z = 8.75/16 + 0.003
        // Hanging sign board: height 10/16 (y: 0..10/16, center: 5/16), front face z = 9/16 + 0.05/16
        float zPos;
        float yCenter;
        if (isHangingSign) {
            zPos = (9.0f + 0.05f) / 16.0f;
            yCenter = 5.0f / 16.0f;
        } else if (isWallSign) {
            zPos = (1.75f + 0.05f) / 16.0f;
            yCenter = (4.333f + 12.333f) / 2.0f / 16.0f;
        } else {
            zPos = (8.75f + 0.05f) / 16.0f;
            yCenter = (9.333f + 17.333f) / 2.0f / 16.0f;
        }
        float textWidth = 12.0f / 16.0f;   // 0.75f block width
        float textHeight = 6.0f / 16.0f;  // 0.375f block height
        float xMin = 0.5f - textWidth / 2.0f;
        float yMin = yCenter - textHeight / 2.0f;
        float yMax = yCenter + textHeight / 2.0f;

        float[] rgb = DYE_COLORS.getOrDefault(colorName.toLowerCase(Locale.ROOT), DYE_COLORS.get("black"));
        int sunlight = glowing ? 15 : block.getLightData().getSkyLight();
        int blocklight = glowing ? 15 : block.getLightData().getBlockLight();

        int faceCount = quads.size() * 2; // 2 triangles per quad
        int startIndex = tileModel.add(faceCount);
        TileModel tm = tileModel.getTileModel();

        for (int i = 0; i < quads.size(); i++) {
            Quad q = quads.get(i);
            int face1 = startIndex + i * 2;
            int face2 = face1 + 1;

            float px0 = xMin + q.u0 * textWidth;
            float px1 = xMin + q.u1 * textWidth;
            float py0 = yMax - q.v1 * textHeight; // bottom in world Y
            float py1 = yMax - q.v0 * textHeight; // top in world Y

            // Quad vertices:
            // TL: (px0, py1, zPos)
            // BL: (px0, py0, zPos)
            // BR: (px1, py0, zPos)
            // TR: (px1, py1, zPos)
            // Triangle 1 (TL, BL, BR): CCW facing +Z
            tm.setPositions(face1,
                    px0, py1, zPos,
                    px0, py0, zPos,
                    px1, py0, zPos
            );
            tm.setUvs(face1, 0.5f, 0.5f, 0.5f, 0.5f, 0.5f, 0.5f);
            tm.setColor(face1, rgb[0], rgb[1], rgb[2]);
            tm.setMaterialIndex(face1, matIndex);
            tm.setSunlight(face1, sunlight);
            tm.setBlocklight(face1, blocklight);
            tm.setAOs(face1, 1f, 1f, 1f);

            // Triangle 2 (TL, BR, TR): CCW facing +Z
            tm.setPositions(face2,
                    px0, py1, zPos,
                    px1, py0, zPos,
                    px1, py1, zPos
            );
            tm.setUvs(face2, 0.5f, 0.5f, 0.5f, 0.5f, 0.5f, 0.5f);
            tm.setColor(face2, rgb[0], rgb[1], rgb[2]);
            tm.setMaterialIndex(face2, matIndex);
            tm.setSunlight(face2, sunlight);
            tm.setBlocklight(face2, blocklight);
            tm.setAOs(face2, 1f, 1f, 1f);
        }

        // 5. Transform our newly added triangles by variant matrix to follow sign rotation/facing
        if (variant.isTransformed()) {
            tm.transform(startIndex, faceCount, variant.getTransformMatrix());
        }
    }

    private List<Quad> getOrCreateQuads(List<String> lines) {
        String cacheKey = String.join("\n", lines);
        return textQuadCache.computeIfAbsent(cacheKey, k -> generateQuads(lines));
    }

    private List<Quad> generateQuads(List<String> lines) {
        BufferedImage img = new BufferedImage(CANVAS_W, CANVAS_H, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = img.createGraphics();

        // Render with crisp text
        g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_OFF);

        int validLineCount = Math.min(4, lines.size());
        float baseSize;
        int lineHeight;

        if (validLineCount == 1) {
            baseSize = 16f;
            lineHeight = 18;
        } else if (validLineCount == 2) {
            baseSize = 13f;
            lineHeight = 15;
        } else if (validLineCount == 3) {
            baseSize = 11f;
            lineHeight = 12;
        } else {
            baseSize = 10f;
            lineHeight = 11;
        }

        int fontStyle = IS_PIXEL_FONT ? Font.PLAIN : Font.BOLD;
        Font font = BASE_SIGN_FONT.deriveFont(fontStyle, baseSize);
        g.setFont(font);
        FontMetrics baseFm = g.getFontMetrics();
        int ascent = baseFm.getAscent();
        int fontH = baseFm.getHeight();

        int totalBlockHeight = (validLineCount - 1) * lineHeight + fontH;
        int startY = Math.max(ascent, (CANVAS_H - totalBlockHeight) / 2 + ascent);

        g.setColor(Color.WHITE);
        for (int i = 0; i < validLineCount; i++) {
            String line = lines.get(i);
            Font lineFont = font;
            g.setFont(lineFont);
            FontMetrics fm = g.getFontMetrics();
            int strW = fm.stringWidth(line);
            if (strW > CANVAS_W - 6) {
                float scale = (float) (CANVAS_W - 6) / strW;
                lineFont = BASE_SIGN_FONT.deriveFont(fontStyle, baseSize * scale);
                g.setFont(lineFont);
                fm = g.getFontMetrics();
                strW = fm.stringWidth(line);
            }
            int x = Math.max(2, (CANVAS_W - strW) / 2);
            int y = startY + i * lineHeight;
            g.drawString(line, x, y);
        }
        g.dispose();

        // 1D Greedy Run-length Meshing
        List<Quad> result = new ArrayList<>();
        for (int y = 0; y < CANVAS_H; y++) {
            int runStart = -1;
            for (int x = 0; x < CANVAS_W; x++) {
                int alpha = (img.getRGB(x, y) >> 24) & 0xFF;
                boolean active = alpha > 128;
                if (active && runStart < 0) {
                    runStart = x;
                } else if (!active && runStart >= 0) {
                    float u0 = runStart / (float) CANVAS_W;
                    float u1 = x / (float) CANVAS_W;
                    float v0 = y / (float) CANVAS_H;
                    float v1 = (y + 1) / (float) CANVAS_H;
                    result.add(new Quad(u0, v0, u1, v1));
                    runStart = -1;
                }
            }
            if (runStart >= 0) {
                float u0 = runStart / (float) CANVAS_W;
                float u1 = 1.0f;
                float v0 = y / (float) CANVAS_H;
                float v1 = (y + 1) / (float) CANVAS_H;
                result.add(new Quad(u0, v0, u1, v1));
            }
        }
        return result;
    }

    private static String cleanMessage(Object msg) {
        if (msg == null) return "";
        String s = msg.toString().trim();
        if (s.isEmpty() || s.equals("\"\"") || s.equals("null")) return "";
        if (s.startsWith("{") && s.contains("\"text\":")) {
            int idx = s.indexOf("\"text\":");
            int start = s.indexOf('"', idx + 7);
            if (start != -1) {
                int end = s.indexOf('"', start + 1);
                if (end != -1) return s.substring(start + 1, end).replaceAll("(?i)§[0-9a-fk-or]", "").trim();
            }
        }
        if (s.startsWith("\"") && s.endsWith("\"") && s.length() >= 2) {
            s = s.substring(1, s.length() - 1);
        }
        s = s.replaceAll("(?i)§[0-9a-fk-or]", "");
        return s.trim();
    }

    private static void addIfNotEmpty(List<String> list, String s) {
        if (s != null && !s.isEmpty()) list.add(s);
    }

    private static void loadFallbackSigns() {
        if (fallbackLoaded) return;
        synchronized (FALLBACK_SIGNS) {
            if (fallbackLoaded) return;
            fallbackLoaded = true;

            File[] candidates = new File[]{
                    new File("signs.json"),
                    new File("../signs.json"),
                    new File("/home/mio/bluemap-render/signs.json")
            };
            for (File file : candidates) {
                if (file.exists() && file.isFile()) {
                    try (FileReader reader = new FileReader(file)) {
                        JsonElement elem = JsonParser.parseReader(reader);
                        if (elem.isJsonArray()) {
                            JsonArray arr = elem.getAsJsonArray();
                            for (JsonElement item : arr) {
                                if (!item.isJsonObject()) continue;
                                JsonObject obj = item.getAsJsonObject();
                                int x = obj.get("x").getAsInt();
                                int y = obj.get("y").getAsInt();
                                int z = obj.get("z").getAsInt();
                                String color = obj.has("color") ? obj.get("color").getAsString() : "black";
                                boolean glow = obj.has("glowing") && obj.get("glowing").getAsBoolean();
                                List<String> lines = new ArrayList<>();
                                if (obj.has("lines") && obj.get("lines").isJsonArray()) {
                                    for (JsonElement le : obj.get("lines").getAsJsonArray()) {
                                        String str = le.getAsString().trim();
                                        if (!str.isEmpty()) lines.add(str);
                                    }
                                }
                                FALLBACK_SIGNS.put(x + "," + y + "," + z, new FallbackSign(lines, color, glow));
                            }
                            LOGGER.info("Loaded " + FALLBACK_SIGNS.size() + " fallback signs from " + file.getAbsolutePath());
                            break;
                        }
                    } catch (Exception e) {
                        LOGGER.log(Level.WARNING, "Failed to load fallback signs from " + file, e);
                    }
                }
            }
        }
    }

    private record Quad(float u0, float v0, float u1, float v1) {}

    private record FallbackSign(List<String> lines, String color, boolean glowing) {}
}
