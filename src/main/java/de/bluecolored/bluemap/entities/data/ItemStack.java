package de.bluecolored.bluemap.entities.data;

import de.bluecolored.bluenbt.NBTName;
import lombok.Data;

@Data
public class ItemStack {

    @NBTName("id")
    private String id;

    @NBTName("Count")
    private int count;

    public String getItemName() {
        if (id == null) return null;
        if (id.startsWith("minecraft:")) return id.substring(10);
        return id;
    }
}
