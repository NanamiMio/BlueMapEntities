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
import de.bluecolored.bluemap.entities.entity.Wolf;

public class WolfRenderer extends CustomResourceModelRenderer {

    public WolfRenderer(ResourcePack resourcePack, TextureGallery textureGallery, RenderSettings renderSettings) {
        super(resourcePack, textureGallery, renderSettings);
    }

    @Override
    public void render(Entity entity, BlockNeighborhood block, Part part, TileModelView tileModel) {
        if (!(entity instanceof Wolf wolf)) return;

        String modelName = wolf.isSitting() ? "entity/wolf/wolf_sitting" : "entity/wolf/wolf";
        ResourcePath<Model> modelPath = new ResourcePath<>(Key.MINECRAFT_NAMESPACE, modelName);
        Model model = modelPath.getResource(getModelProvider());
        if (model == null) {
            modelPath = new ResourcePath<>(Key.MINECRAFT_NAMESPACE, "entity/wolf/wolf");
            model = modelPath.getResource(getModelProvider());
        }

        super.render(entity, block, model, TintColorProvider.NO_TINT, tileModel);

        if (part.isTransformed())
            tileModel.transform(part.getTransformMatrix());
    }
}
