package ac.dylanisa.command;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import net.minecraft.server.command.ServerCommandSource;
import net.minecraft.text.Text;

import static net.minecraft.server.command.CommandManager.*;

// Restore java.net.http imports
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpClient.Version;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.CompletableFuture;
import java.util.Map;

import ac.dylanisa.config.MinecraftAIConfig;
import me.shedaniel.autoconfig.AutoConfig;

import com.google.gson.Gson;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class AICommand {

    public static final Logger LOGGER = LoggerFactory.getLogger("MinecraftAI");

    // Restore standard Java HttpClient
    private static final HttpClient httpClient = HttpClient.newBuilder()
            .version(Version.HTTP_1_1)
            .build();
    private static final Gson gson = new Gson();
    // Remove OkHttp MediaType
    // public static final MediaType JSON = MediaType.get("application/json; charset=utf-8");

    public static void register(CommandDispatcher<ServerCommandSource> dispatcher) {
        dispatcher.register(literal("ai")
            .then(literal("message")
                .then(argument("message", StringArgumentType.greedyString())
                    .executes(AICommand::run)))
        );
    }

    private static int run(CommandContext<ServerCommandSource> context) throws CommandSyntaxException {
        ServerCommandSource source = context.getSource();
        try {
            String userMessage = StringArgumentType.getString(context, "message");

            // Restore original API key check and network request logic
            MinecraftAIConfig config = AutoConfig.getConfigHolder(MinecraftAIConfig.class).getConfig();
            String apiKey = config.apiKey;

            if (apiKey == null || apiKey.trim().isEmpty()) {
                source.sendError(Text.literal("Error: API Key not configured. Use ModMenu or edit config/minecraft-ai.json"));
                return 1;
            }

            source.sendFeedback(() -> Text.literal("Sending message to AI: " + userMessage), false);

            Map<String, String> payloadMap = Map.of("message", userMessage);
            String jsonPayload = gson.toJson(payloadMap);

            // Use configured endpoint from user settings
            String endpoint = config.apiEndpoint;
            LOGGER.info("Sending JSON payload to {}: {}", endpoint, jsonPayload);

            // Convert payload to bytes for logging
            byte[] jsonPayloadBytes = jsonPayload.getBytes(StandardCharsets.UTF_8);
            LOGGER.info("Payload byte length: {}", jsonPayloadBytes.length);

            // Build HTTP request with JSON payload via String publisher, let HttpClient set Content-Length
            HttpRequest request = HttpRequest.newBuilder()
                    .version(HttpClient.Version.HTTP_1_1) // Explicitly set HTTP/1.1
                    .uri(URI.create(endpoint))
                    .header("Content-Type", "application/json") // Plain Content-Type
                    .header("Accept", "application/json")
                    .header("X-API-Key", apiKey)
                    .POST(HttpRequest.BodyPublishers.ofString(jsonPayload, StandardCharsets.UTF_8))
                    .build();

            // Debug: log request headers
            LOGGER.info("Request Headers:");
            request.headers().map().forEach((key, value) -> LOGGER.info("  {}: {}", key, value));

            // Async network call
            CompletableFuture<HttpResponse<String>> responseFuture =
                    httpClient.sendAsync(request, HttpResponse.BodyHandlers.ofString());

            responseFuture.thenAcceptAsync(response -> {
                if (response.statusCode() >= 200 && response.statusCode() < 300) {
                    String responseBody = response.body();
                    try {
                        JsonObject jsonResponse = JsonParser.parseString(responseBody).getAsJsonObject();
                        String reply = jsonResponse.has("reply") ? jsonResponse.get("reply").getAsString() : "Error: Unexpected response format (missing 'reply')";

                        source.getServer().execute(() -> {
                            source.sendFeedback(() -> Text.literal("AI: " + reply), false);
                        });
                    } catch (Exception e) {
                        LOGGER.error("Error parsing AI response", e); // Keep enhanced logging
                        source.getServer().execute(() -> {
                            source.sendError(Text.literal("Error parsing AI response: " + e.getMessage()));
                        });
                    }
                } else {
                    String errorBody = response.body(); // Get error body
                    LOGGER.error("API Error: {} - {}", response.statusCode(), errorBody); // Log error body
                    source.getServer().execute(() -> {
                        source.sendError(Text.literal("API Error: " + response.statusCode() + " - " + errorBody));
                    });
                }
            }).exceptionally(ex -> {
                LOGGER.error("Error communicating with AI. Type: {}", ex.getClass().getName(), ex); // Log exception type and keep enhanced logging
                System.err.println("--- AICommand HTTP Exception Stack Trace START ---");
                ex.printStackTrace(); // Force print stack trace to standard error
                System.err.println("--- AICommand HTTP Exception Stack Trace END ---");
                source.getServer().execute(() -> {
                    source.sendError(Text.literal("Error communicating with AI: Check console/log.")); // Update message
                });
                return null;
            });

            return 1;
        } catch (Throwable t) {
            LOGGER.error("Exception in AICommand.run", t);
            source.sendError(Text.literal("Error: " + t.getMessage()));
            return 1;
        }
    }
}
