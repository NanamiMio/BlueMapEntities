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
import de.bluecolored.bluemap.core.resources.pack.resourcepack.ResourcePack;
import de.bluecolored.bluemap.core.resources.pack.resourcepack.entitystate.Part;
import de.bluecolored.bluemap.core.resources.pack.resourcepack.model.Model;
import de.bluecolored.bluemap.core.world.Entity;
import de.bluecolored.bluemap.core.world.block.BlockNeighborhood;
import de.bluecolored.bluemap.entities.entity.VillagerData;
import de.bluecolored.bluemap.entities.entity.VillagerDataHolder;

public class VillagerRenderer extends CustomResourceModelRenderer {

    public VillagerRenderer(ResourcePack resourcePack, TextureGallery textureGallery, RenderSettings renderSettings) {
        super(resourcePack, textureGallery, renderSettings);
    }

    @Override
    public void render(Entity entity, BlockNeighborhood block, Part part, TileModelView tileModel) {
        // 1. Render base villager model (skin, arms, legs, plains coat)
        Model base = model("entity/villager/villager");
        if (base != null) {
            super.render(entity, block, base, TintColorProvider.NO_TINT, tileModel);
        }

        // 2. Render profession clothing layer if applicable
        if (entity instanceof VillagerDataHolder villager && !villager.isBaby()) {
            VillagerData data = villager.getVillagerData();
            String profession = data != null ? data.getRawProfession() : VillagerData.PROFESSION_NONE;

            if (!VillagerData.PROFESSION_NONE.equals(profession)) {
                Model job = model("entity/villager/profession_" + profession);
                if (job != null) {
                    super.render(entity, block, job, TintColorProvider.NO_TINT, tileModel);
                }
            }
        }

        // 3. Apply part transformation
        if (part.isTransformed()) {
            tileModel.transform(part.getTransformMatrix());
        }

        // 4. Correct body tilt: counteract pitch rotation from EntityModelRenderer
        // keeping the villager standing straight and upright
        float pitch = entity.getRotation().getY();
        if (Math.abs(pitch) > 1e-4) {
            tileModel.rotate(-pitch, 0, 0);
        }
    }
}
