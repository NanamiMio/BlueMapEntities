package de.bluecolored.bluemap.entities.entity;

import com.flowpowered.math.vector.Vector2f;
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
public class ItemFrame extends MCAEntity {

    @NBTName("Facing") byte facing;
    @NBTName("Invisible") boolean invisible;
    @NBTName("Item") ItemStack item;
    @NBTName("ItemRotation") byte itemRotation;

    @Override
    public Vector2f getRotation() {
        Vector2f rot = super.getRotation();
        if (rot == null) return Vector2f.ZERO;
        // Invert yaw (-rot.getX()) to match BlueMap's counter-clockwise rotation with Minecraft's clockwise yaw
        return new Vector2f(-rot.getX(), rot.getY());
    }
}
