package de.bluecolored.bluemap.entities.data;

import de.bluecolored.bluemap.core.util.Key;
import de.bluecolored.bluenbt.NBTName;
import lombok.Data;

@Data
public class ItemStack {

    @NBTName("id")
    private Key id;

    @NBTName("Count")
    private int count;

    public String getItemName() {
        if (id == null) return null;
        return id.getValue();
    }
}
