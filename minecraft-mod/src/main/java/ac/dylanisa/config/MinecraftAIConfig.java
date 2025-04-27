package ac.dylanisa.config;

import me.shedaniel.autoconfig.ConfigData;
import me.shedaniel.autoconfig.annotation.Config;
import me.shedaniel.autoconfig.annotation.ConfigEntry;

@Config(name = "minecraft-ai") // This will be the filename (minecraft-ai.json)
public class MinecraftAIConfig implements ConfigData {

    @ConfigEntry.Gui.Tooltip // Adds a hover tooltip in the config screen
    public String apiKey = ""; // Default value is an empty string

    // The base URL of the AI backend; change this if your server is on a different host or port
    @ConfigEntry.Gui.Tooltip
    public String apiEndpoint = "http://localhost:8000/chat";

    // You can add more config options here later
    // Example:
    // @ConfigEntry.Gui.Tooltip
    // public String model = "gpt-4o";

    // @ConfigEntry.Gui.Tooltip
    // @ConfigEntry.BoundedDiscrete(min = 1, max = 2000) // Example with validation
    // public int maxTokens = 500;
}
