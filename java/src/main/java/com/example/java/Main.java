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

import java.io.IOException;
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
import java.util.Base64;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutionException;

public class Main {
    private static final String NODE_URL = "opc.tcp://localhost:4840";
    private static final String ENDPOINT_URL = "http://localhost:5000/api/measurements";
    private static final String PUBLIC_KEY_PATH = "../.keys/sensor_public.pem";
    private static final String NODE_ID = "ns=1;s=sensor";

    public record SensorData(
        int sensorId,
        float temperature,
        float pressure,
        float humidity,
        long timestamp
    ) {
        String toJSON() {
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

    public static PublicKey loadPublicKey(final String keyPath) {
        try {
            final byte[] keyBytes = Files.readAllBytes(Paths.get(keyPath));
            final String keyContent = new String(keyBytes)
                .replace("-----BEGIN PUBLIC KEY-----", "")
                .replace("-----END PUBLIC KEY-----", "")
                .replaceAll("\\s", "");

            final byte[] decodedKey = Base64.getDecoder().decode(keyContent);
            final X509EncodedKeySpec keySpec = new X509EncodedKeySpec(decodedKey);
            final KeyFactory keyFactory = KeyFactory.getInstance("RSA");

            return keyFactory.generatePublic(keySpec);
        } catch (final IOException | NoSuchAlgorithmException | InvalidKeySpecException e) {
            System.err.println("Error loading public key: " + e.getMessage());
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

    public static UaMonitoredItem getMonitoredItem(final OpcUaClient client)
        throws ExecutionException, InterruptedException {
        final NodeId nodeId = NodeId.parse(NODE_ID);

        final UaSubscription subscription = client
            .getSubscriptionManager()
            .createSubscription(500.0)
            .get();

        final MonitoringParameters parameters = new MonitoringParameters(
            UInteger.valueOf(1),
            500.0,
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

    public static void consumeValue(final PublicKey publicKey, final DataValue value) {
        try {
            final Variant variant = value.getValue();
            if (variant == null || variant.getValue() == null) {
                System.out.println("No data received");
                return;
            }

            final byte[] rawData = ((ByteString) variant.getValue()).bytes();
            if (rawData == null || rawData.length == 0) {
                System.out.println("No data received");
                return;
            }

            final SignedDataResult result = deserializeSignedData(rawData);
            final boolean isValid = verifySignature(result.sensorData, result.signature, publicKey);

            final SensorData sensorData = parseSensorData(result.sensorData);
            final String timestampString = formatTimestamp(sensorData.timestamp);

            final String statusText = isValid ? "VALID" : "INVALID";

            System.out.println("\n[sub] signature: " + statusText);
            System.out.println("    sensor_id        = " + sensorData.sensorId);
            System.out.println("    temperature      = " + sensorData.temperature);
            System.out.println("    pressure         = " + sensorData.pressure);
            System.out.println("    humidity         = " + sensorData.humidity);
            System.out.println("    timestamp        = " + timestampString);
            System.out.println("    signature_length = " + result.signature.length);

            sendDataToApi(sensorData);
        } catch (final Exception e) {
            System.err.println("Error processing data: " + e.getMessage());
        }
    }

    public static void sendDataToApi(final SensorData sensorData) {
        System.out.println("Sending data to API");

        try (final HttpClient client = HttpClient.newHttpClient()) {
            final HttpRequest request = HttpRequest
                .newBuilder()
                .uri(URI.create(ENDPOINT_URL))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(sensorData.toJSON()))
                .build();

            client
                .sendAsync(request, HttpResponse.BodyHandlers.ofString())
                .thenAccept(response -> {
                    if (response.statusCode() == 201) {
                        System.out.println("Successfully sent data to API");
                    } else {
                        System.err.println("Could not send data to API: " + response.body());
                    }
                });
        }
    }

    public static void main(final String[] args) {
        final PublicKey publicKey = loadPublicKey(PUBLIC_KEY_PATH);
        if (publicKey == null) {
            System.err.println("Failed to load public key");
            return;
        }

        final OpcUaClient client;

        try {
            client = OpcUaClient.create(NODE_URL);
        } catch (final Exception e) {
            System.err.println("Error creating client: " + e.getMessage());
            return;
        }

        final CountDownLatch shutdownLatch = new CountDownLatch(1);

        try {
            client.connect().get();
            System.out.println("Connected to OPC UA server.");

            final UaMonitoredItem monitoredItem = getMonitoredItem(client);

            monitoredItem.setValueConsumer((item, value) ->
                consumeValue(publicKey, value)
            );

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
