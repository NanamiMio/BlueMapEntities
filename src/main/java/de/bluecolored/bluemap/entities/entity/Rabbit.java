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
public class Rabbit extends MCAEntity {

    @NBTName("RabbitType") int rabbitType;

    public String getRawVariant() {
        return switch (rabbitType) {
            case 1 -> "white";
            case 2 -> "black";
            case 3 -> "white_splotched";
            case 4 -> "gold";
            case 5 -> "salt";
            case 99 -> "caerbannog";
            default -> "brown";
        };
    }
}
