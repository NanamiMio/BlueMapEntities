package de.bluecolored.bluemap.entities.entity;

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
}
