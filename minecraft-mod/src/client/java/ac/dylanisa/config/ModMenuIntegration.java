package ac.dylanisa.config;

import com.terraformersmc.modmenu.api.ConfigScreenFactory;
import com.terraformersmc.modmenu.api.ModMenuApi;
import me.shedaniel.autoconfig.AutoConfig;
import net.fabricmc.api.EnvType;
import net.fabricmc.api.Environment;

@Environment(EnvType.CLIENT) // Config screens are client-side only
public class ModMenuIntegration implements ModMenuApi {

    @Override
    public ConfigScreenFactory<?> getModConfigScreenFactory() {
        // Return a lambda that creates the config screen using AutoConfig
        return parent -> AutoConfig.getConfigScreen(MinecraftAIConfig.class, parent).get();
    }
}
