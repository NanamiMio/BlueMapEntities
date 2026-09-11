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
public class Wolf extends MCAEntity {

    @NBTName("Sitting") boolean sitting;
    @NBTName("Owner") int[] owner;
    @NBTName("CollarColor") byte collarColor;

    public boolean isTame() {
        return owner != null && owner.length > 0;
    }
}
