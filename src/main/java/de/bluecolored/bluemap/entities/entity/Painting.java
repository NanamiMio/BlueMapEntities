package de.bluecolored.bluemap.entities.entity;

import com.flowpowered.math.vector.Vector2f;
import de.bluecolored.bluemap.core.world.mca.entity.MCAEntity;
import de.bluecolored.bluenbt.NBTName;
import lombok.EqualsAndHashCode;
import lombok.Getter;
import lombok.ToString;

@Getter
@EqualsAndHashCode(callSuper = true)
@ToString
@SuppressWarnings("FieldMayBeFinal")
public class Painting extends MCAEntity {

    @NBTName("variant") String variant;
    @NBTName("facing") byte facing;

    public String getCleanVariant() {
        if (variant == null || variant.isEmpty()) return "kebab";
        int idx = variant.indexOf(':');
        return idx >= 0 ? variant.substring(idx + 1) : variant;
    }

    @Override
    public Vector2f getRotation() {
        Vector2f rot = super.getRotation();
        if (rot == null) return Vector2f.ZERO;
        return new Vector2f(-rot.getX(), rot.getY());
    }
}
