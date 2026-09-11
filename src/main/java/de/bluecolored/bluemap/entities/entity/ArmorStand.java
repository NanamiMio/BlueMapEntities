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
public class ArmorStand extends MCAEntity {

    @NBTName("Small") boolean small;
}
