package de.bluecolored.bluemap.entities.entity;

import de.bluecolored.bluemap.core.world.mca.entity.MCAEntity;
import de.bluecolored.bluemap.entities.data.ItemStack;
import de.bluecolored.bluenbt.NBTName;
import lombok.EqualsAndHashCode;
import lombok.Getter;
import lombok.ToString;

@Getter
@EqualsAndHashCode(callSuper = true)
@ToString
@SuppressWarnings("FieldMayBeFinal")
public class ArmorStand extends MCAEntity {

    @NBTName("Small") boolean small;
    @NBTName("ShowArms") boolean showArms;
    @NBTName("NoBasePlate") boolean noBasePlate;
    @NBTName("ArmorItems") ItemStack[] armorItems;
    @NBTName("HandItems") ItemStack[] handItems;

    public ItemStack getBoots() {
        return (armorItems != null && armorItems.length > 0) ? armorItems[0] : null;
    }

    public ItemStack getLeggings() {
        return (armorItems != null && armorItems.length > 1) ? armorItems[1] : null;
    }

    public ItemStack getChestplate() {
        return (armorItems != null && armorItems.length > 2) ? armorItems[2] : null;
    }

    public ItemStack getHelmet() {
        return (armorItems != null && armorItems.length > 3) ? armorItems[3] : null;
    }

    @Override
    public com.flowpowered.math.vector.Vector2f getRotation() {
        com.flowpowered.math.vector.Vector2f rot = super.getRotation();
        if (rot == null) return com.flowpowered.math.vector.Vector2f.ZERO;
        return new com.flowpowered.math.vector.Vector2f(rot.getX(), 0f);
    }
}
