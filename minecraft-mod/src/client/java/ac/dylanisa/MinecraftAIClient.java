package ac.dylanisa;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.command.v2.ClientCommandRegistrationCallback;
import ac.dylanisa.command.AICommand; // Import the command class

public class MinecraftAIClient implements ClientModInitializer {
    @Override
    public void onInitializeClient() {
        // Client initialization logic will go here
        System.out.println("Minecraft AI Client Initializing...");

        // Register commands
        ClientCommandRegistrationCallback.EVENT.register((dispatcher, registryAccess) -> {
            // AICommand.register(dispatcher); // REMOVED - Command registered in main initializer
            // Register other client commands here if needed
        });

        // System.out.println("AI Command Registered!"); // Optional: Remove this log too if command isn't registered here
    }
}
