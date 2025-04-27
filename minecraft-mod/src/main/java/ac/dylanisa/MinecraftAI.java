package ac.dylanisa;

import ac.dylanisa.command.AICommand;
import ac.dylanisa.config.MinecraftAIConfig;
import me.shedaniel.autoconfig.AutoConfig;
import me.shedaniel.autoconfig.serializer.GsonConfigSerializer;
import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class MinecraftAI implements ModInitializer {
	public static final String MOD_ID = "minecraft-ai";

	// This logger is used to write text to the console and the log file.
	// It is considered best practice to use your mod id as the logger's name.
	// That way, it's clear which mod wrote info, warnings, and errors.
	public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

	// Config Holder
	private static me.shedaniel.autoconfig.ConfigHolder<MinecraftAIConfig> configHolder;

	@Override
	public void onInitialize() {
		// This code runs as soon as Minecraft is in a mod-load-ready state.
		// However, some things (like resources) may still be uninitialized.
		// Proceed with mild caution.

		LOGGER.info("Initializing Minecraft AI Mod!");

		// Register and load config
		configHolder = AutoConfig.register(MinecraftAIConfig.class, GsonConfigSerializer::new);

		// Register commands
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> {
			AICommand.register(dispatcher);
		});
	}

	// Static getter for easy access to the config instance
	public static MinecraftAIConfig getConfig() {
		return configHolder.getConfig();
	}
}
