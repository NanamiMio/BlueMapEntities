package de.bluecolored.bluemap.entities.renderer;

import com.flowpowered.math.vector.Vector3f;
import com.flowpowered.math.vector.Vector4f;
import de.bluecolored.bluemap.core.map.TextureGallery;
import de.bluecolored.bluemap.core.map.hires.RenderSettings;
import de.bluecolored.bluemap.core.map.hires.TileModelView;
import de.bluecolored.bluemap.core.resources.ResourcePath;
import de.bluecolored.bluemap.core.resources.pack.resourcepack.ResourcePack;
import de.bluecolored.bluemap.core.resources.pack.resourcepack.entitystate.Part;
import de.bluecolored.bluemap.core.resources.pack.resourcepack.model.Element;
import de.bluecolored.bluemap.core.resources.pack.resourcepack.model.Face;
import de.bluecolored.bluemap.core.resources.pack.resourcepack.model.Model;
import de.bluecolored.bluemap.core.resources.pack.resourcepack.model.TextureVariable;
import de.bluecolored.bluemap.core.resources.pack.resourcepack.texture.Texture;
import de.bluecolored.bluemap.core.util.Direction;
import de.bluecolored.bluemap.core.util.Key;
import de.bluecolored.bluemap.core.world.Entity;
import de.bluecolored.bluemap.core.world.block.BlockNeighborhood;
import de.bluecolored.bluemap.entities.data.ItemStack;
import de.bluecolored.bluemap.entities.entity.ItemFrame;

import java.util.EnumMap;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class ItemFrameRenderer extends CustomResourceModelRenderer {

    private final Map<String, Model> dynamicItemModelCache = new ConcurrentHashMap<>();
    private static final Model NULL_MODEL = new Model(); // sentinel to avoid recomputing missing items

    public ItemFrameRenderer(ResourcePack resourcePack, TextureGallery textureGallery, RenderSettings renderSettings) {
        super(resourcePack, textureGallery, renderSettings);
    }

    private Model getItemModel(ItemStack stack) {
        if (stack == null || stack.getId() == null) return null;
        Key itemId = stack.getId();
        String formatted = itemId.getFormatted();

        Model cached = dynamicItemModelCache.get(formatted);
        if (cached != null) {
            return cached == NULL_MODEL ? null : cached;
        }

        String namespace = itemId.getNamespace();
        String value = itemId.getValue();

        // 1. Try explicit custom item frame model
        Model itemModel = model("entity/item_frame/items/" + value);
        if (itemModel != null) {
            dynamicItemModelCache.put(formatted, itemModel);
            return itemModel;
        }

        // 2. Check if item texture exists in TextureGallery
        ResourcePath<Texture> texPath = new ResourcePath<>(new Key(namespace, "item/" + value));
        int texId = getTextureGallery().get(texPath);
        if (texId == 0) {
            // Check block texture fallback: e.g. "block/" + value
            texPath = new ResourcePath<>(new Key(namespace, "block/" + value));
            texId = getTextureGallery().get(texPath);
        }

        if (texId > 0) {
            // Create dynamic 2D quad model
            Vector3f from = new Vector3f(-4.0f, -4.0f, 0.42f);
            Vector3f to = new Vector3f(4.0f, 4.0f, 0.45f);
            Map<Direction, Face> faces = new EnumMap<>(Direction.class);
            TextureVariable var0 = new TextureVariable("0");
            Vector4f uv = new Vector4f(0, 0, 16, 16);
            faces.put(Direction.SOUTH, new Face(uv, var0));
            faces.put(Direction.NORTH, new Face(uv, var0));
            Element elem = new Element(from, to, faces);

            Map<String, TextureVariable> textures = new HashMap<>();
            textures.put("0", new TextureVariable(texPath));
            textures.put("particle", new TextureVariable(texPath));

            Model generated = new Model(textures, elem);
            dynamicItemModelCache.put(formatted, generated);
            return generated;
        }

        // If not found in gallery, cache NULL_MODEL sentinel so we do not generate missing texture
        dynamicItemModelCache.put(formatted, NULL_MODEL);
        return null;
    }

    @Override
    public void render(Entity entity, BlockNeighborhood block, Part part, TileModelView tileModel) {
        if (!(entity instanceof ItemFrame frame)) {
            super.render(entity, block, part, tileModel);
            return;
        }

        int initialStart = tileModel.getStart();

        // 1. Render frame border and backing plate unless invisible
        if (!frame.isInvisible()) {
            boolean isGlow = "glow_item_frame".equals(entity.getId().getValue());
            Model frameModel = model(isGlow ? "entity/item_frame/glow_item_frame" : "entity/item_frame/item_frame");
            if (frameModel != null) {
                super.render(entity, block, frameModel, TintColorProvider.NO_TINT, tileModel);
            }
        }

        // 2. Render item inside the frame
        ItemStack stack = frame.getItem();
        if (stack != null) {
            Model itemModel = getItemModel(stack);
            if (itemModel != null) {
                super.render(entity, block, itemModel, TintColorProvider.NO_TINT, tileModel);
            }
        }

        // 3. Apply part transformation if any
        if (part.isTransformed()) {
            tileModel.initialize(initialStart);
            tileModel.transform(part.getTransformMatrix());
        }
    }
}
