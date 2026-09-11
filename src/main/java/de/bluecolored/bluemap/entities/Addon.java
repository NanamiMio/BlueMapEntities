package de.bluecolored.bluemap.entities;

import de.bluecolored.bluemap.core.map.hires.entity.EntityRendererType;
import de.bluecolored.bluemap.core.util.Key;
import de.bluecolored.bluemap.core.world.mca.entity.EntityType;
import de.bluecolored.bluemap.entities.entity.*;
import de.bluecolored.bluemap.entities.renderer.*;

import java.util.logging.Logger;

@SuppressWarnings("unused")
public class Addon implements Runnable {

    public static Logger LOGGER = Logger.getLogger("BlueMap Entities Addon");

    @Override
    public void run() {
        EntityType.REGISTRY.register(new EntityType.Impl(Key.minecraft("llama"), Llama.class));
        EntityType.REGISTRY.register(new EntityType.Impl(Key.minecraft("trader_llama"), TraderLlama.class));
        EntityType.REGISTRY.register(new EntityType.Impl(Key.minecraft("bee"), Bee.class));
        EntityType.REGISTRY.register(new EntityType.Impl(Key.minecraft("cat"), Cat.class));
        EntityType.REGISTRY.register(new EntityType.Impl(Key.minecraft("ocelot"), Ocelot.class));
        EntityType.REGISTRY.register(new EntityType.Impl(Key.minecraft("chicken"), AgeVariantEntity.class));
        EntityType.REGISTRY.register(new EntityType.Impl(Key.minecraft("fox"), Fox.class));
        EntityType.REGISTRY.register(new EntityType.Impl(Key.minecraft("pig"), Pig.class));
        EntityType.REGISTRY.register(new EntityType.Impl(Key.minecraft("tropical_fish"), TropicalFish.class));
        EntityType.REGISTRY.register(new EntityType.Impl(Key.minecraft("zombie"), Zombie.class));
        EntityType.REGISTRY.register(new EntityType.Impl(Key.minecraft("husk"), Zombie.class));
        EntityType.REGISTRY.register(new EntityType.Impl(Key.minecraft("drowned"), Zombie.class));
        EntityType.REGISTRY.register(new EntityType.Impl(Key.minecraft("cow"), AgeVariantEntity.class));
        EntityType.REGISTRY.register(new EntityType.Impl(Key.minecraft("sheep"), Sheep.class));
        EntityType.REGISTRY.register(new EntityType.Impl(Key.minecraft("skeleton"), Skeleton.class));
        EntityType.REGISTRY.register(new EntityType.Impl(Key.minecraft("wither_skeleton"), WitherSkeleton.class));
        EntityType.REGISTRY.register(new EntityType.Impl(Key.minecraft("stray"), Stray.class));
        EntityType.REGISTRY.register(new EntityType.Impl(Key.minecraft("bogged"), Bogged.class));
        EntityType.REGISTRY.register(new EntityType.Impl(Key.minecraft("parched"), Parched.class));
        EntityType.REGISTRY.register(new EntityType.Impl(Key.minecraft("dolphin"), AgeEntity.class));
        EntityType.REGISTRY.register(new EntityType.Impl(Key.minecraft("squid"), Squid.class));
        EntityType.REGISTRY.register(new EntityType.Impl(Key.minecraft("glow_squid"), GlowSquid.class));
        EntityType.REGISTRY.register(new EntityType.Impl(Key.minecraft("horse"), Horse.class));
        EntityType.REGISTRY.register(new EntityType.Impl(Key.minecraft("zombie_horse"), ZombieHorse.class));
        EntityType.REGISTRY.register(new EntityType.Impl(Key.minecraft("skeleton_horse"), SkeletonHorse.class));
        EntityType.REGISTRY.register(new EntityType.Impl(Key.minecraft("donkey"), Donkey.class));
        EntityType.REGISTRY.register(new EntityType.Impl(Key.minecraft("mule"), Mule.class));
        EntityType.REGISTRY.register(new EntityType.Impl(Key.minecraft("armadillo"), Armadillo.class));
        EntityType.REGISTRY.register(new EntityType.Impl(Key.minecraft("snow_golem"), SnowGolem.class));
        EntityType.REGISTRY.register(new EntityType.Impl(Key.minecraft("axolotl"), Axolotl.class));
        EntityType.REGISTRY.register(new EntityType.Impl(Key.minecraft("camel"), Camel.class));
        EntityType.REGISTRY.register(new EntityType.Impl(Key.minecraft("camel_husk"), CamelHusk.class));
        EntityType.REGISTRY.register(new EntityType.Impl(Key.minecraft("copper_golem"), CopperGolem.class));
        EntityType.REGISTRY.register(new EntityType.Impl(Key.minecraft("frog"), AgeVariantEntity.class));
        EntityType.REGISTRY.register(new EntityType.Impl(Key.minecraft("iron_golem"), de.bluecolored.bluemap.core.world.mca.entity.MCAEntity.class));
        EntityType.REGISTRY.register(new EntityType.Impl(Key.minecraft("minecart"), de.bluecolored.bluemap.core.world.mca.entity.MCAEntity.class));
        EntityType.REGISTRY.register(new EntityType.Impl(Key.minecraft("chest_minecart"), de.bluecolored.bluemap.core.world.mca.entity.MCAEntity.class));
        EntityType.REGISTRY.register(new EntityType.Impl(Key.minecraft("hopper_minecart"), de.bluecolored.bluemap.core.world.mca.entity.MCAEntity.class));
        EntityType.REGISTRY.register(new EntityType.Impl(Key.minecraft("boat"), de.bluecolored.bluemap.core.world.mca.entity.MCAEntity.class));
        EntityType.REGISTRY.register(new EntityType.Impl(Key.minecraft("chest_boat"), de.bluecolored.bluemap.core.world.mca.entity.MCAEntity.class));


        EntityRendererType.REGISTRY.register(new EntityRendererType.Impl(Key.minecraft("llama"), LlamaRenderer::new));
        EntityRendererType.REGISTRY.register(new EntityRendererType.Impl(Key.minecraft("trader_llama"), LlamaRenderer::new));
        EntityRendererType.REGISTRY.register(new EntityRendererType.Impl(Key.minecraft("bee"), BeeRenderer::new));
        EntityRendererType.REGISTRY.register(new EntityRendererType.Impl(Key.minecraft("cat"), CatRenderer::new));
        EntityRendererType.REGISTRY.register(new EntityRendererType.Impl(Key.minecraft("ocelot"), OcelotRenderer::new));
        EntityRendererType.REGISTRY.register(new EntityRendererType.Impl(Key.minecraft("chicken"), ChickenRenderer::new));
        EntityRendererType.REGISTRY.register(new EntityRendererType.Impl(Key.minecraft("fox"), FoxRenderer::new));
        EntityRendererType.REGISTRY.register(new EntityRendererType.Impl(Key.minecraft("pig"), PigRenderer::new));
        EntityRendererType.REGISTRY.register(new EntityRendererType.Impl(Key.minecraft("tropical_fish"), TropicalFishRenderer::new));
        EntityRendererType.REGISTRY.register(new EntityRendererType.Impl(Key.minecraft("zombie"), ZombieRenderer::new));
        EntityRendererType.REGISTRY.register(new EntityRendererType.Impl(Key.minecraft("husk"), HuskRenderer::new));
        EntityRendererType.REGISTRY.register(new EntityRendererType.Impl(Key.minecraft("drowned"), DrownedRenderer::new));
        EntityRendererType.REGISTRY.register(new EntityRendererType.Impl(Key.minecraft("cow"), CowRenderer::new));
        EntityRendererType.REGISTRY.register(new EntityRendererType.Impl(Key.minecraft("sheep"), SheepRenderer::new));
        EntityRendererType.REGISTRY.register(new EntityRendererType.Impl(Key.minecraft("skeleton"), SkeletonRenderer::new));
        EntityRendererType.REGISTRY.register(new EntityRendererType.Impl(Key.minecraft("wither_skeleton"), SkeletonRenderer::new));
        EntityRendererType.REGISTRY.register(new EntityRendererType.Impl(Key.minecraft("stray"), SkeletonRenderer::new));
        EntityRendererType.REGISTRY.register(new EntityRendererType.Impl(Key.minecraft("bogged"), SkeletonRenderer::new));
        EntityRendererType.REGISTRY.register(new EntityRendererType.Impl(Key.minecraft("parched"), SkeletonRenderer::new));
        EntityRendererType.REGISTRY.register(new EntityRendererType.Impl(Key.minecraft("dolphin"), DolphinRenderer::new));
        EntityRendererType.REGISTRY.register(new EntityRendererType.Impl(Key.minecraft("squid"), SquidRenderer::new));
        EntityRendererType.REGISTRY.register(new EntityRendererType.Impl(Key.minecraft("glow_squid"), SquidRenderer::new));
        EntityRendererType.REGISTRY.register(new EntityRendererType.Impl(Key.minecraft("horse"), HorseRenderer::new));
        EntityRendererType.REGISTRY.register(new EntityRendererType.Impl(Key.minecraft("zombie_horse"), HostileHorseRenderer::new));
        EntityRendererType.REGISTRY.register(new EntityRendererType.Impl(Key.minecraft("skeleton_horse"), HostileHorseRenderer::new));
        EntityRendererType.REGISTRY.register(new EntityRendererType.Impl(Key.minecraft("donkey"), ChestedHorseRenderer::new));
        EntityRendererType.REGISTRY.register(new EntityRendererType.Impl(Key.minecraft("mule"), ChestedHorseRenderer::new));
        EntityRendererType.REGISTRY.register(new EntityRendererType.Impl(Key.minecraft("armadillo"), ArmadilloRenderer::new));
        EntityRendererType.REGISTRY.register(new EntityRendererType.Impl(Key.minecraft("snow_golem"), SnowGolemRenderer::new));
        EntityRendererType.REGISTRY.register(new EntityRendererType.Impl(Key.minecraft("axolotl"), AxolotlRenderer::new));
        EntityRendererType.REGISTRY.register(new EntityRendererType.Impl(Key.minecraft("camel"), CamelRenderer::new));
        EntityRendererType.REGISTRY.register(new EntityRendererType.Impl(Key.minecraft("camel_husk"), CamelRenderer::new));
        EntityRendererType.REGISTRY.register(new EntityRendererType.Impl(Key.minecraft("copper_golem"), CopperGolemRenderer::new));
        EntityRendererType.REGISTRY.register(new EntityRendererType.Impl(Key.minecraft("frog"), FrogRenderer::new));
        EntityRendererType.REGISTRY.register(new EntityRendererType.Impl(Key.minecraft("iron_golem"), CustomResourceModelRenderer::new));
        EntityRendererType.REGISTRY.register(new EntityRendererType.Impl(Key.minecraft("minecart"), CustomResourceModelRenderer::new));
        EntityRendererType.REGISTRY.register(new EntityRendererType.Impl(Key.minecraft("chest_minecart"), CustomResourceModelRenderer::new));
        EntityRendererType.REGISTRY.register(new EntityRendererType.Impl(Key.minecraft("hopper_minecart"), CustomResourceModelRenderer::new));
        EntityRendererType.REGISTRY.register(new EntityRendererType.Impl(Key.minecraft("boat"), CustomResourceModelRenderer::new));
        EntityRendererType.REGISTRY.register(new EntityRendererType.Impl(Key.minecraft("chest_boat"), CustomResourceModelRenderer::new));

        // Install Sign Renderer interceptor
        try {
            de.bluecolored.bluemap.core.map.hires.block.BlockRendererType originalDefault = de.bluecolored.bluemap.core.map.hires.block.BlockRendererType.DEFAULT;
            de.bluecolored.bluemap.core.map.hires.block.BlockRendererType wrappedDefault = new de.bluecolored.bluemap.core.map.hires.block.BlockRendererType.Impl(
                    Key.bluemap("default"),
                    (resourcePack, textureGallery, renderSettings) -> {
                        de.bluecolored.bluemap.core.map.hires.block.BlockRenderer original = originalDefault.create(resourcePack, textureGallery, renderSettings);
                        SignTextRenderer signTextRenderer = new SignTextRenderer(textureGallery);
                        return new DelegatingBlockRenderer(original, signTextRenderer);
                    }
            );

            de.bluecolored.bluemap.core.map.hires.block.BlockRendererType.REGISTRY.register(wrappedDefault);
            de.bluecolored.bluemap.core.map.hires.block.BlockRendererType.REGISTRY.register(new de.bluecolored.bluemap.core.map.hires.block.BlockRendererType.Impl(
                    Key.bluemap("sign"),
                    (resourcePack, textureGallery, renderSettings) -> {
                        de.bluecolored.bluemap.core.map.hires.block.BlockRenderer original = originalDefault.create(resourcePack, textureGallery, renderSettings);
                        SignTextRenderer signTextRenderer = new SignTextRenderer(textureGallery);
                        return new DelegatingBlockRenderer(original, signTextRenderer);
                    }
            ));

            java.lang.reflect.Field unsafeField = sun.misc.Unsafe.class.getDeclaredField("theUnsafe");
            unsafeField.setAccessible(true);
            sun.misc.Unsafe unsafe = (sun.misc.Unsafe) unsafeField.get(null);

            java.lang.reflect.Field defaultField = de.bluecolored.bluemap.core.map.hires.block.BlockRendererType.class.getDeclaredField("DEFAULT");
            Object base = unsafe.staticFieldBase(defaultField);
            long offset = unsafe.staticFieldOffset(defaultField);
            unsafe.putObject(base, offset, wrappedDefault);
            LOGGER.info("Successfully hooked BlockRendererType.DEFAULT with SignTextRenderer!");
        } catch (Throwable t) {
            LOGGER.log(java.util.logging.Level.WARNING, "Failed to hook BlockRendererType.DEFAULT", t);
        }
    }

}
