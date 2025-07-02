package com.example.java;

import org.eclipse.milo.opcua.sdk.client.OpcUaClient;
import org.eclipse.milo.opcua.stack.core.types.builtin.ByteString;
import org.eclipse.milo.opcua.stack.core.types.builtin.NodeId;
import org.eclipse.milo.opcua.stack.core.types.builtin.Variant;
import org.eclipse.milo.opcua.stack.core.types.enumerated.TimestampsToReturn;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.security.InvalidKeyException;
import java.security.KeyFactory;
import java.security.NoSuchAlgorithmException;
import java.security.PublicKey;
import java.security.Signature;
import java.security.SignatureException;
import java.security.spec.InvalidKeySpecException;
import java.security.spec.X509EncodedKeySpec;
import java.time.Instant;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.Base64;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.atomic.AtomicBoolean;

public class Main {
    private static final String URL = "opc.tcp://localhost:4840";
    private static final String PUBLIC_KEY_PATH = "../.keys/sensor_public.pem";
    private static final String NODE_ID = "ns=1;s=sensor";

    public static class SensorData {
        public final int sensorId;
        public final float temperature;
        public final float pressure;
        public final float humidity;
        public final long timestamp;

        public SensorData(
            final int sensorId,
            final float temperature,
            final float pressure,
            final float humidity,
            final long timestamp
        ) {
            this.sensorId = sensorId;
            this.temperature = temperature;
            this.pressure = pressure;
            this.humidity = humidity;
            this.timestamp = timestamp;
        }
    }

    public static class SignedDataResult {
        public final byte[] sensorData;
        public final byte[] signature;

        public SignedDataResult(final byte[] sensorData, final byte[] signature) {
            this.sensorData = sensorData;
            this.signature = signature;
        }
    }

    public static PublicKey loadPublicKey(final String keyPath) {
        try {
            final byte[] keyBytes = Files.readAllBytes(Paths.get(keyPath));
            String keyContent = new String(keyBytes);

            keyContent = keyContent
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

    public static void main(final String[] args) {
        final PublicKey publicKey = loadPublicKey(PUBLIC_KEY_PATH);
        if (publicKey == null) {
            System.err.println("Failed to load public key");
            return;
        }

        try {
            final OpcUaClient client = OpcUaClient.create(URL);
            final AtomicBoolean running = new AtomicBoolean(true);

            try {
                client.connect().get();
                System.out.println("Connected to OPC UA server.");

                final NodeId nodeId = NodeId.parse(NODE_ID);

                Runtime.getRuntime().addShutdownHook(new Thread(() ->
                    running.compareAndSet(true, false)
                ));

                while (running.get()) {
                    try {
                        final Variant variant = client.readValue(0.0, TimestampsToReturn.Neither, nodeId).get().getValue();

                        if (variant == null || variant.getValue() == null) {
                            System.out.println("No data received");
                            Thread.sleep(500);
                            continue;
                        }

                        final byte[] rawData = ((ByteString)variant.getValue()).bytes();
                        if (rawData == null || rawData.length == 0) {
                            System.out.println("No data received");
                            Thread.sleep(500);
                            continue;
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
                    } catch (final InterruptedException e) {
                        break;
                    } catch (final Exception e) {
                        System.err.println("Error processing data: " + e.getMessage());
                    }

                    Thread.sleep(500);
                }
            } catch (final InterruptedException | ExecutionException e) {
                System.err.println("Error when connecting/reading: " + e.getMessage());
            } finally {
                client.disconnect();
                System.out.println("Closed connection.");
            }
        } catch (final Exception e) {
            System.err.println("Error creating client: " + e.getMessage());
        }
    }
}
