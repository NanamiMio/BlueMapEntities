package de.bluecolored.bluemap.entities.renderer;

import de.bluecolored.bluemap.core.map.hires.TileModelView;
import de.bluecolored.bluemap.core.map.hires.block.BlockRenderer;
import de.bluecolored.bluemap.core.resources.pack.resourcepack.blockstate.Variant;
import de.bluecolored.bluemap.core.util.math.Color;
import de.bluecolored.bluemap.core.world.block.BlockNeighborhood;

public class DelegatingBlockRenderer implements BlockRenderer {

    private final BlockRenderer delegate;
    private final SignTextRenderer signTextRenderer;

    public DelegatingBlockRenderer(BlockRenderer delegate, SignTextRenderer signTextRenderer) {
        this.delegate = delegate;
        this.signTextRenderer = signTextRenderer;
    }

    @Override
    public void render(BlockNeighborhood block, Variant variant, TileModelView tileModel, Color color) {
        delegate.render(block, variant, tileModel, color);
        if (block.getBlockState().getId().getValue().contains("sign")) {
            signTextRenderer.renderSign(block, variant, tileModel);
        }
    }
}
