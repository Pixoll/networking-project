package com.example.java;

import org.eclipse.milo.opcua.sdk.client.OpcUaClient;
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

        public SensorData(int sensorId, float temperature, float pressure, float humidity, long timestamp) {
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

        public SignedDataResult(byte[] sensorData, byte[] signature) {
            this.sensorData = sensorData;
            this.signature = signature;
        }
    }

    public static PublicKey loadPublicKey(String keyPath) {
        try {
            byte[] keyBytes = Files.readAllBytes(Paths.get(keyPath));
            String keyContent = new String(keyBytes);

            keyContent = keyContent
                    .replace("-----BEGIN PUBLIC KEY-----", "")
                    .replace("-----END PUBLIC KEY-----", "")
                    .replaceAll("\\s", "");

            byte[] decodedKey = Base64.getDecoder().decode(keyContent);
            X509EncodedKeySpec keySpec = new X509EncodedKeySpec(decodedKey);
            KeyFactory keyFactory = KeyFactory.getInstance("RSA");

            return keyFactory.generatePublic(keySpec);

        } catch (IOException | NoSuchAlgorithmException | InvalidKeySpecException e) {
            System.err.println("Error loading public key: " + e.getMessage());
            return null;
        }
    }

    public static boolean verifySignature(byte[] data, byte[] signature, PublicKey publicKey) {
        try {
            Signature sig = Signature.getInstance("SHA256withRSA");
            sig.initVerify(publicKey);
            sig.update(data);
            return sig.verify(signature);

        } catch (NoSuchAlgorithmException | InvalidKeyException | SignatureException e) {
            System.err.println("Error during signature verification: " + e.getMessage());
            return false;
        }
    }

    public static SignedDataResult deserializeSignedData(byte[] rawData) throws IllegalArgumentException {
        if (rawData.length < 24) {
            throw new IllegalArgumentException("Invalid data (len 24)");
        }

        byte[] sensorData = new byte[24];
        System.arraycopy(rawData, 0, sensorData, 0, 24);

        if (rawData.length < 32) {
            throw new IllegalArgumentException("Invalid data (len 32)");
        }

        ByteBuffer buffer = ByteBuffer.wrap(rawData, 24, 8);
        buffer.order(ByteOrder.LITTLE_ENDIAN);
        long signatureLength = buffer.getLong();

        if (rawData.length < 32 + signatureLength) {
            throw new IllegalArgumentException("Invalid data (len " + (32 + signatureLength) + ")");
        }

        byte[] signature = new byte[(int)signatureLength];
        System.arraycopy(rawData, 32, signature, 0, (int)signatureLength);

        return new SignedDataResult(sensorData, signature);
    }

    public static SensorData parseSensorData(byte[] data) {
        ByteBuffer buffer = ByteBuffer.wrap(data);
        buffer.order(ByteOrder.LITTLE_ENDIAN);

        int sensorId = buffer.getInt();
        float temperature = buffer.getFloat();
        float pressure = buffer.getFloat();
        float humidity = buffer.getFloat();
        long timestamp = buffer.getLong();

        return new SensorData(sensorId, temperature, pressure, humidity, timestamp);
    }

    public static String formatTimestamp(long timestamp) {
        Instant instant = Instant.ofEpochMilli(timestamp);
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss.SSS")
                .withZone(ZoneId.systemDefault());
        return formatter.format(instant);
    }

    public static void main(String[] args) {
        PublicKey publicKey = loadPublicKey(PUBLIC_KEY_PATH);
        if (publicKey == null) {
            System.err.println("Failed to load public key");
            return;
        }

        try {
            OpcUaClient client = OpcUaClient.create(URL);

            try {
                client.connect().get();
                System.out.println("Connected to OPC UA server.");

                NodeId nodeId = NodeId.parse(NODE_ID);

                while (true) {
                    try {
                        Variant variant = client.readValue(0.0, TimestampsToReturn.Neither, nodeId).get().getValue();

                        if (variant == null || variant.getValue() == null) {
                            System.out.println("No data received");
                            Thread.sleep(500);
                            continue;
                        }

                        byte[] rawData = (byte[]) variant.getValue();
                        if (rawData.length == 0) {
                            System.out.println("No data received");
                            Thread.sleep(500);
                            continue;
                        }

                        SignedDataResult result = deserializeSignedData(rawData);
                        boolean isValid = verifySignature(result.sensorData, result.signature, publicKey);

                        SensorData sensorData = parseSensorData(result.sensorData);
                        String timestampString = formatTimestamp(sensorData.timestamp);

                        String statusText = isValid ? "VALID" : "INVALID";

                        System.out.println("\n[sub] signature: " + statusText);
                        System.out.println("    sensor_id        = " + sensorData.sensorId);
                        System.out.println("    temperature      = " + sensorData.temperature);
                        System.out.println("    pressure         = " + sensorData.pressure);
                        System.out.println("    humidity         = " + sensorData.humidity);
                        System.out.println("    timestamp        = " + timestampString);
                        System.out.println("    signature_length = " + result.signature.length);

                    } catch (Exception e) {
                        System.err.println("Error processing data: " + e.getMessage());
                    }

                    Thread.sleep(500);
                }

            } catch (InterruptedException | ExecutionException e) {
                System.err.println("Error when connecting/reading: " + e.getMessage());
            } finally {
                client.disconnect();
                System.out.println("Closed connection.");
            }

        } catch (Exception e) {
            System.err.println("Error creating client: " + e.getMessage());
        }
    }
}