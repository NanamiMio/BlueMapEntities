package de.bluecolored.bluemap.entities.renderer;

import de.bluecolored.bluemap.core.map.TextureGallery;
import de.bluecolored.bluemap.core.map.hires.RenderSettings;
import de.bluecolored.bluemap.core.map.hires.TileModel;
import de.bluecolored.bluemap.core.map.hires.TileModelView;
import de.bluecolored.bluemap.core.map.hires.entity.EntityRenderer;
import de.bluecolored.bluemap.core.resources.ResourcePath;
import de.bluecolored.bluemap.core.resources.pack.resourcepack.ResourcePack;
import de.bluecolored.bluemap.core.resources.pack.resourcepack.entitystate.Part;
import de.bluecolored.bluemap.core.resources.pack.resourcepack.texture.Texture;
import de.bluecolored.bluemap.core.util.Key;
import de.bluecolored.bluemap.core.world.Entity;
import de.bluecolored.bluemap.core.world.block.BlockNeighborhood;
import de.bluecolored.bluemap.entities.entity.Painting;

import java.util.Map;

public class PaintingRenderer implements EntityRenderer {

    private static final Map<String, int[]> SIZES = Map.ofEntries(
            Map.entry("kebab", new int[]{1, 1}),
            Map.entry("aztec", new int[]{1, 1}),
            Map.entry("alban", new int[]{1, 1}),
            Map.entry("aztec2", new int[]{1, 1}),
            Map.entry("bomb", new int[]{1, 1}),
            Map.entry("plant", new int[]{1, 1}),
            Map.entry("wasteland", new int[]{1, 1}),
            Map.entry("pool", new int[]{2, 1}),
            Map.entry("courbet", new int[]{2, 1}),
            Map.entry("sea", new int[]{2, 1}),
            Map.entry("sunset", new int[]{2, 1}),
            Map.entry("creebet", new int[]{2, 1}),
            Map.entry("wanderer", new int[]{1, 2}),
            Map.entry("graham", new int[]{1, 2}),
            Map.entry("match", new int[]{2, 2}),
            Map.entry("bust", new int[]{2, 2}),
            Map.entry("stage", new int[]{2, 2}),
            Map.entry("void", new int[]{2, 2}),
            Map.entry("skull_and_roses", new int[]{2, 2}),
            Map.entry("wither", new int[]{2, 2}),
            Map.entry("fighters", new int[]{4, 2}),
            Map.entry("donkey_kong", new int[]{4, 3}),
            Map.entry("skeleton", new int[]{4, 3}),
            Map.entry("burning_skull", new int[]{4, 4}),
            Map.entry("pigscene", new int[]{4, 4}),
            Map.entry("pointer", new int[]{4, 4}),
            Map.entry("earth", new int[]{2, 2}),
            Map.entry("wind", new int[]{2, 2}),
            Map.entry("fire", new int[]{2, 2}),
            Map.entry("water", new int[]{2, 2})
    );

    private final TextureGallery textureGallery;
    private final RenderSettings renderSettings;

    public PaintingRenderer(ResourcePack resourcePack, TextureGallery textureGallery, RenderSettings renderSettings) {
        this.textureGallery = textureGallery;
        this.renderSettings = renderSettings;
    }

    @Override
    public void render(Entity entity, BlockNeighborhood block, Part part, TileModelView tileModel) {
        if (!(entity instanceof Painting painting)) return;

        String variant = painting.getCleanVariant();
        int[] size = SIZES.getOrDefault(variant, new int[]{1, 1});
        float w = size[0];
        float h = size[1];
        float halfW = w * 0.5f;
        float halfH = h * 0.5f;
        float halfD = 0.03125f; // 1/32 block thickness

        ResourcePath<Texture> frontTex = new ResourcePath<>(Key.MINECRAFT_NAMESPACE, "painting/" + variant);
        ResourcePath<Texture> backTex = new ResourcePath<>(Key.MINECRAFT_NAMESPACE, "painting/back");

        int frontMat = textureGallery.get(frontTex);
        int backMat = textureGallery.get(backTex);
        if (frontMat == 0) frontMat = backMat;

        int sunlight = block.getLightData().getSkyLight();
        int blocklight = block.getLightData().getBlockLight();

        // 6 faces: front, back, top, bottom, left, right (12 triangles)
        int startFace = tileModel.add(12);
        TileModel tm = tileModel.getTileModel();

        // Front face (+Z)
        addQuad(tm, startFace,
                -halfW, halfH, halfD,
                -halfW, -halfH, halfD,
                halfW, -halfH, halfD,
                halfW, halfH, halfD,
                0f, 0f, 1f, 1f, frontMat, sunlight, blocklight);

        // Back face (-Z)
        addQuad(tm, startFace + 2,
                halfW, halfH, -halfD,
                halfW, -halfH, -halfD,
                -halfW, -halfH, -halfD,
                -halfW, halfH, -halfD,
                0f, 0f, 1f, 1f, backMat, sunlight, blocklight);

        // Top face (+Y)
        addQuad(tm, startFace + 4,
                -halfW, halfH, -halfD,
                -halfW, halfH, halfD,
                halfW, halfH, halfD,
                halfW, halfH, -halfD,
                0f, 0f, 1f, 1f, backMat, sunlight, blocklight);

        // Bottom face (-Y)
        addQuad(tm, startFace + 6,
                -halfW, -halfH, halfD,
                -halfW, -halfH, -halfD,
                halfW, -halfH, -halfD,
                halfW, -halfH, halfD,
                0f, 0f, 1f, 1f, backMat, sunlight, blocklight);

        // Left face (-X)
        addQuad(tm, startFace + 8,
                -halfW, halfH, -halfD,
                -halfW, -halfH, -halfD,
                -halfW, -halfH, halfD,
                -halfW, halfH, halfD,
                0f, 0f, 1f, 1f, backMat, sunlight, blocklight);

        // Right face (+X)
        addQuad(tm, startFace + 10,
                halfW, halfH, halfD,
                halfW, -halfH, halfD,
                halfW, -halfH, -halfD,
                halfW, halfH, -halfD,
                0f, 0f, 1f, 1f, backMat, sunlight, blocklight);
    }

    private void addQuad(TileModel tm, int faceIndex,
                         float x0, float y0, float z0,
                         float x1, float y1, float z1,
                         float x2, float y2, float z2,
                         float x3, float y3, float z3,
                         float u0, float v0, float u1, float v1,
                         int matIndex, int sunlight, int blocklight) {
        int f1 = faceIndex;
        int f2 = faceIndex + 1;

        tm.setPositions(f1, x0, y0, z0, x1, y1, z1, x2, y2, z2);
        tm.setPositions(f2, x0, y0, z0, x2, y2, z2, x3, y3, z3);

        tm.setUvs(f1, u0, v0, u0, v1, u1, v1);
        tm.setUvs(f2, u0, v0, u1, v1, u1, v0);

        tm.setMaterialIndex(f1, matIndex);
        tm.setMaterialIndex(f2, matIndex);

        tm.setColor(f1, 1f, 1f, 1f);
        tm.setColor(f2, 1f, 1f, 1f);

        tm.setSunlight(f1, sunlight);
        tm.setSunlight(f2, sunlight);

        tm.setBlocklight(f1, blocklight);
        tm.setBlocklight(f2, blocklight);

        tm.setAOs(f1, 1f, 1f, 1f);
        tm.setAOs(f2, 1f, 1f, 1f);
    }
}
