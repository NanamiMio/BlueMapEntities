/*
 * This file is part of BlueMap, licensed under the MIT License (MIT).
 *
 * Copyright (c) Blue (Lukas Rieger) <https://bluecolored.de>
 * Copyright (c) contributors
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */
package de.bluecolored.bluemap.entities.renderer;

import de.bluecolored.bluemap.core.map.TextureGallery;
import de.bluecolored.bluemap.core.map.hires.RenderSettings;
import de.bluecolored.bluemap.core.map.hires.TileModelView;
import de.bluecolored.bluemap.core.resources.ResourcePath;
import de.bluecolored.bluemap.core.resources.pack.resourcepack.ResourcePack;
import de.bluecolored.bluemap.core.resources.pack.resourcepack.entitystate.Part;
import de.bluecolored.bluemap.core.resources.pack.resourcepack.model.Model;
import de.bluecolored.bluemap.core.util.Key;
import de.bluecolored.bluemap.core.world.Entity;
import de.bluecolored.bluemap.core.world.block.BlockNeighborhood;
import de.bluecolored.bluemap.entities.entity.Sheep;

public class SheepRenderer extends CustomResourceModelRenderer {

    private static final float[][] DYE_COLORS = new float[][] {
        {1.0f, 1.0f, 1.0f}, // 0 white
        {0.94f, 0.50f, 0.15f}, // 1 orange
        {0.78f, 0.31f, 0.74f}, // 2 magenta
        {0.40f, 0.60f, 0.85f}, // 3 light blue
        {0.96f, 0.80f, 0.22f}, // 4 yellow
        {0.50f, 0.78f, 0.12f}, // 5 lime
        {0.93f, 0.58f, 0.68f}, // 6 pink
        {0.30f, 0.33f, 0.35f}, // 7 gray
        {0.60f, 0.60f, 0.56f}, // 8 light gray
        {0.10f, 0.55f, 0.58f}, // 9 cyan
        {0.52f, 0.22f, 0.72f}, // 10 purple
        {0.24f, 0.29f, 0.65f}, // 11 blue
        {0.45f, 0.30f, 0.19f}, // 12 brown
        {0.37f, 0.50f, 0.15f}, // 13 green
        {0.69f, 0.18f, 0.15f}, // 14 red
        {0.12f, 0.12f, 0.14f}  // 15 black
    };

    private final ResourcePath<Model>
            SHEEP_ADULT = new ResourcePath<>(Key.MINECRAFT_NAMESPACE, "entity/sheep/adult"),
            SHEEP_BABY = new ResourcePath<>(Key.MINECRAFT_NAMESPACE, "entity/sheep/baby"),
            SHEEP_ADULT_WOOL = new ResourcePath<>(Key.MINECRAFT_NAMESPACE, "entity/sheep/adult_wool"),
            SHEEP_BABY_WOOL = new ResourcePath<>(Key.MINECRAFT_NAMESPACE, "entity/sheep/baby_wool");

    public SheepRenderer(ResourcePack resourcePack, TextureGallery textureGallery, RenderSettings renderSettings) {
        super(resourcePack, textureGallery, renderSettings);
    }

    @Override
    public void render(Entity entity, BlockNeighborhood block, Part part, TileModelView tileModel) {
        if (!(entity instanceof Sheep sheep)) return;

        // render base body
        ResourcePath<Model> baseModel = sheep.getAge() < 0 ? SHEEP_BABY : SHEEP_ADULT;
        super.render(entity, block, baseModel.getResource(getModelProvider()), TintColorProvider.NO_TINT, tileModel);

        // render wool layer if not sheared
        if (!sheep.isSheared()) {
            ResourcePath<Model> woolModel = sheep.getAge() < 0 ? SHEEP_BABY_WOOL : SHEEP_ADULT_WOOL;
            int colorIdx = Math.max(0, Math.min(15, (int) sheep.getColor()));
            float[] rgb = DYE_COLORS[colorIdx];
            super.render(entity, block, woolModel.getResource(getModelProvider()), (idx, col) -> col.set(rgb[0], rgb[1], rgb[2], 1f, true), tileModel);
        }

        // apply part transform
        if (part.isTransformed())
            tileModel.transform(part.getTransformMatrix());
    }

}
