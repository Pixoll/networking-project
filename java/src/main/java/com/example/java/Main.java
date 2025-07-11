package com.example.java;

import org.eclipse.milo.opcua.sdk.client.OpcUaClient;
import org.eclipse.milo.opcua.sdk.client.api.subscriptions.UaMonitoredItem;
import org.eclipse.milo.opcua.sdk.client.api.subscriptions.UaSubscription;
import org.eclipse.milo.opcua.stack.core.AttributeId;
import org.eclipse.milo.opcua.stack.core.types.builtin.*;
import org.eclipse.milo.opcua.stack.core.types.builtin.unsigned.UInteger;
import org.eclipse.milo.opcua.stack.core.types.enumerated.MonitoringMode;
import org.eclipse.milo.opcua.stack.core.types.enumerated.TimestampsToReturn;
import org.eclipse.milo.opcua.stack.core.types.structured.MonitoredItemCreateRequest;
import org.eclipse.milo.opcua.stack.core.types.structured.MonitoringParameters;
import org.eclipse.milo.opcua.stack.core.types.structured.ReadValueId;
import org.json.JSONObject;

import javax.crypto.Cipher;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.SecretKeySpec;
import java.io.IOException;
import java.io.PrintStream;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.security.*;
import java.security.spec.InvalidKeySpecException;
import java.security.spec.X509EncodedKeySpec;
import java.time.Instant;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutionException;

public class Main {
    private static final String NODE_URL = "opc.tcp://localhost:4840";
    private static final String PUBLIC_KEY_PATH = "../.keys/sensor_public.pem";
    private static final String AES_KEY_PATH = "../.keys/aes.key";
    private static final String AES_ALGORITHM = "AES/GCM/NoPadding";
    private static final int GCM_IV_LENGTH = 12;
    private static final int GCM_TAG_LENGTH = 16;
    private static final Base64.Decoder BASE64_DECODER = Base64.getDecoder();
    private static final Base64.Encoder BASE64_ENCODER = Base64.getEncoder();

    public record SensorData(
        int sensorId,
        float temperature,
        float pressure,
        float humidity,
        long timestamp
    ) {
        public String toJSON() {
            return new JSONObject()
                .put("sensor_id", this.sensorId)
                .put("temperature", this.temperature)
                .put("pressure", this.pressure)
                .put("humidity", this.humidity)
                .put("timestamp", this.timestamp)
                .toString();
        }
    }

    public record SignedDataResult(
        byte[] sensorData,
        byte[] signature
    ) {
    }

    public record EncryptedData(
        String encryptedData,
        String iv
    ) {
        public String toJSON() {
            return new JSONObject()
                .put("encrypted_data", this.encryptedData)
                .put("iv", this.iv)
                .toString();
        }
    }

    public static PublicKey loadPublicKey(final String keyPath) {
        try {
            final byte[] keyBytes = Files.readAllBytes(Paths.get(keyPath));
            final String keyContent = new String(keyBytes)
                .replace("-----BEGIN PUBLIC KEY-----", "")
                .replace("-----END PUBLIC KEY-----", "")
                .replaceAll("\\s", "");

            final byte[] decodedKey = BASE64_DECODER.decode(keyContent);
            final X509EncodedKeySpec keySpec = new X509EncodedKeySpec(decodedKey);
            final KeyFactory keyFactory = KeyFactory.getInstance("RSA");

            return keyFactory.generatePublic(keySpec);
        } catch (final IOException | NoSuchAlgorithmException | InvalidKeySpecException e) {
            System.err.println("Error loading public key: " + e.getMessage());
            return null;
        }
    }

    public static SecretKey loadAESKey(final String keyPath) {
        try {
            final byte[] keyBytes = Files.readAllBytes(Paths.get(keyPath));
            return new SecretKeySpec(keyBytes, "AES");
        } catch (final IOException e) {
            System.err.println("Error loading AES key: " + e.getMessage());
            return null;
        }
    }

    public static EncryptedData encryptData(final String data, final SecretKey key) {
        try {
            final Cipher cipher = Cipher.getInstance(AES_ALGORITHM);

            final byte[] iv = new byte[GCM_IV_LENGTH];
            new SecureRandom().nextBytes(iv);

            final GCMParameterSpec gcmSpec = new GCMParameterSpec(GCM_TAG_LENGTH * 8, iv);
            cipher.init(Cipher.ENCRYPT_MODE, key, gcmSpec);

            final byte[] encryptedData = cipher.doFinal(data.getBytes());

            return new EncryptedData(
                BASE64_ENCODER.encodeToString(encryptedData),
                BASE64_ENCODER.encodeToString(iv)
            );
        } catch (final Exception e) {
            System.err.println("Error encrypting data: " + e.getMessage());
            return null;
        }
    }

    public static boolean verifySignature(final byte[] data, final byte[] signature, final PublicKey publicKey) {
        try {
            final Signature sig = Signature.getInstance("SHA256withRSA");
            sig.initVerify(publicKey);
            sig.update(data);
            return sig.verify(signature);
        } catch (final NoSuchAlgorithmException | InvalidKeyException | SignatureException e) {
            System.err.println("Error during signature verification: " + e.getMessage());
            return false;
        }
    }

    public static SignedDataResult deserializeSignedData(final byte[] rawData) throws IllegalArgumentException {
        if (rawData.length < 24) {
            throw new IllegalArgumentException("Invalid data (len 24)");
        }

        final byte[] sensorData = new byte[24];
        System.arraycopy(rawData, 0, sensorData, 0, 24);

        if (rawData.length < 32) {
            throw new IllegalArgumentException("Invalid data (len 32)");
        }

        final ByteBuffer buffer = ByteBuffer.wrap(rawData, 24, 8);
        buffer.order(ByteOrder.LITTLE_ENDIAN);
        final long signatureLength = buffer.getLong();

        if (rawData.length < 32 + signatureLength) {
            throw new IllegalArgumentException("Invalid data (len " + (32 + signatureLength) + ")");
        }

        final byte[] signature = new byte[(int) signatureLength];
        System.arraycopy(rawData, 32, signature, 0, (int) signatureLength);

        return new SignedDataResult(sensorData, signature);
    }

    public static SensorData parseSensorData(final byte[] data) {
        final ByteBuffer buffer = ByteBuffer.wrap(data);
        buffer.order(ByteOrder.LITTLE_ENDIAN);

        final int sensorId = buffer.getInt();
        final float temperature = buffer.getFloat();
        final float pressure = buffer.getFloat();
        final float humidity = buffer.getFloat();
        final long timestamp = buffer.getLong();

        return new SensorData(sensorId, temperature, pressure, humidity, timestamp);
    }

    public static String formatTimestamp(final long timestamp) {
        final Instant instant = Instant.ofEpochMilli(timestamp);
        final DateTimeFormatter formatter = DateTimeFormatter
            .ofPattern("yyyy-MM-dd HH:mm:ss.SSS")
            .withZone(ZoneId.systemDefault());
        return formatter.format(instant);
    }

    public static UaMonitoredItem getMonitoredItem(final UaSubscription subscription, final String nodeIdString)
        throws ExecutionException, InterruptedException {
        final NodeId nodeId = NodeId.parse(nodeIdString);

        final MonitoringParameters parameters = new MonitoringParameters(
            UInteger.valueOf(1),
            subscription.getRequestedPublishingInterval(),
            null,
            UInteger.valueOf(10),
            true
        );

        final MonitoredItemCreateRequest request = new MonitoredItemCreateRequest(
            new ReadValueId(nodeId, AttributeId.Value.uid(), null, QualifiedName.NULL_VALUE),
            MonitoringMode.Reporting,
            parameters
        );

        return subscription.createMonitoredItems(
            TimestampsToReturn.Both,
            List.of(request)
        ).get().getFirst();
    }

    public static void consumeValue(
        final String apiBaseUrl,
        final PublicKey publicKey,
        final SecretKey aesKey,
        final DataValue value,
        final int nodeId
    ) {
        try {
            final Variant variant = value.getValue();
            if (variant == null || variant.getValue() == null) {
                System.out.println("No data received from sensor " + nodeId);
                return;
            }

            final byte[] rawData = ((ByteString) variant.getValue()).bytes();
            if (rawData == null || rawData.length == 0) {
                System.out.println("No data received from sensor " + nodeId);
                return;
            }

            final SignedDataResult result = deserializeSignedData(rawData);
            final boolean isValid = verifySignature(result.sensorData, result.signature, publicKey);

            final SensorData sensorData = parseSensorData(result.sensorData);
            final String timestampString = formatTimestamp(sensorData.timestamp);

            final String statusText = isValid ? "VALID" : "INVALID | will not send to API";
            final PrintStream out = isValid ? System.out : System.err;

            out.println("\n[sub] sensor " + nodeId + " signature: " + statusText);
            out.println("    sensor_id        = " + sensorData.sensorId);
            out.println("    temperature      = " + sensorData.temperature);
            out.println("    pressure         = " + sensorData.pressure);
            out.println("    humidity         = " + sensorData.humidity);
            out.println("    timestamp        = " + timestampString);
            out.println("    signature_length = " + result.signature.length);

            if (isValid) {
                sendEncryptedDataToApi(apiBaseUrl, sensorData, aesKey);
            }
        } catch (final Exception e) {
            System.err.println("Error processing data from sensor " + nodeId + ": " + e.getMessage());
        }
    }

    public static void sendEncryptedDataToApi(
        final String apiBaseUrl,
        final SensorData sensorData,
        final SecretKey aesKey
    ) {
        System.out.println("Encrypting and sending data to API for sensor " + sensorData.sensorId);

        try {
            final EncryptedData encryptedData = encryptData(sensorData.toJSON(), aesKey);
            if (encryptedData == null) {
                System.err.println("Failed to encrypt data for sensor " + sensorData.sensorId);
                return;
            }

            System.out.println("Data encrypted successfully for sensor " + sensorData.sensorId);

            try (final HttpClient client = HttpClient.newHttpClient()) {
                final HttpRequest request = HttpRequest
                    .newBuilder()
                    .uri(URI.create(apiBaseUrl + "/api/measurements"))
                    .header("Content-Type", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(encryptedData.toJSON()))
                    .build();

                client
                    .sendAsync(request, HttpResponse.BodyHandlers.ofString())
                    .thenAccept(response -> {
                        if (response.statusCode() == 201) {
                            System.out.println(
                                "Successfully sent encrypted data to API for sensor " + sensorData.sensorId
                            );
                        } else {
                            System.err.println(
                                "Could not send encrypted data to API for sensor " + sensorData.sensorId + ": "
                                + response.body()
                            );
                        }
                    })
                    .exceptionally(throwable -> {
                        System.err.println(
                            "Could not send encrypted data to API for sensor " + sensorData.sensorId + ": "
                            + throwable.getMessage()
                        );
                        return null;
                    });
            }
        } catch (final Exception e) {
            System.err.println(
                "Error sending encrypted data for sensor " + sensorData.sensorId + ": "
                + e.getMessage()
            );
        }
    }

    public static void main(final String[] args) {
        if (args.length != 2) {
            System.err.println("Usage: java -jar networking-project.jar <number_of_sensors> <api_base_url>");
            return;
        }

        final int numSensors = Integer.parseInt(args[0]);
        if (numSensors <= 0) {
            System.err.println("Number of sensors must be positive");
            return;
        }

        final String apiBaseUrl = args[1].replaceAll("/+$", "");

        if (!apiBaseUrl.matches("^https?://[^/]+$")) {
            System.err.println(
                "Invalid base API URL: " + apiBaseUrl + "\n"
                + "API URL must be in this format: ^https?://[^/]+$\n"
                + "For example: http://localhost:5000 | http://123.123.123.123:5000 | https://api.domain.tld"
            );
            return;
        }

        final PublicKey publicKey = loadPublicKey(PUBLIC_KEY_PATH);
        if (publicKey == null) {
            System.err.println("Failed to load public key");
            return;
        }

        final SecretKey aesKey = loadAESKey(AES_KEY_PATH);
        if (aesKey == null) {
            System.out.println("Failed to load AES key");
            return;
        }

        OpcUaClient client = null;

        while (client == null) {
            try {
                client = OpcUaClient.create(NODE_URL);
            } catch (final Exception e) {
                System.err.println("Error creating client: " + e.getMessage());
                try {
                    Thread.sleep(5_000);
                } catch (final InterruptedException ee) {
                    return;
                }
            }
        }

        final CountDownLatch shutdownLatch = new CountDownLatch(1);

        try {
            client.connect().get();
            System.out.println("Connected to OPC UA server.");

            final UaSubscription subscription = client
                .getSubscriptionManager()
                .createSubscription(500.0)
                .get();

            final List<UaMonitoredItem> monitoredItems = new ArrayList<>();

            for (int i = 1; i <= numSensors; i++) {
                final int sensorId = i;
                final String nodeIdString = "ns=1;s=sensor_" + sensorId;

                try {
                    final UaMonitoredItem monitoredItem = getMonitoredItem(subscription, nodeIdString);

                    monitoredItem.setValueConsumer((item, value) ->
                        consumeValue(apiBaseUrl, publicKey, aesKey, value, sensorId)
                    );

                    monitoredItems.add(monitoredItem);
                    System.out.println("Monitoring sensor " + sensorId);
                } catch (final Exception e) {
                    System.err.println(
                        "Failed to create monitored item for sensor " + sensorId + ": "
                        + e.getMessage()
                    );
                }
            }

            if (monitoredItems.isEmpty()) {
                System.err.println("No sensors could be monitored");
                return;
            }

            System.out.println("Successfully monitoring " + monitoredItems.size() + " sensors");

            Runtime.getRuntime().addShutdownHook(new Thread(shutdownLatch::countDown));

            shutdownLatch.await();
        } catch (final InterruptedException | ExecutionException e) {
            System.err.println("Error when connecting/reading: " + e.getMessage());
        } finally {
            client.disconnect();
            System.out.println("Closed connection.");
        }
    }
}
