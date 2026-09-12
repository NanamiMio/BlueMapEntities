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
public class ItemFrame extends MCAEntity {

    @NBTName("Facing") byte facing;
    @NBTName("Invisible") boolean invisible;
    @NBTName("Item") ItemStack item;
    @NBTName("ItemRotation") byte itemRotation;
}
