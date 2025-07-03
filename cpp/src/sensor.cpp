// sends serialized and signed data

#include <chrono>
#include <csignal>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <random>
#include <thread>

#include <open62541/client.h>
#include <open62541/client_config_default.h>
#include <open62541/client_highlevel.h>
#include <openssl/evp.h>
#include <openssl/pem.h>
#include <openssl/err.h>

struct __attribute__((packed)) SensorData {
    int32_t sensor_id;
    float temperature;
    float pressure;
    float humidity;
    uint64_t timestamp;
};

static volatile bool running = true;
static EVP_PKEY *private_key = nullptr;

static void stop_handler(int) {
    running = false;
}

uint64_t now() {
    return std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::high_resolution_clock::now().time_since_epoch()
    ).count();
}

bool load_private_key(const char *keyPath) {
    FILE *key_file = fopen(keyPath, "rb");
    if (!key_file) {
        std::cerr << "Cannot open private key file: " << keyPath << std::endl;
        return false;
    }

    private_key = PEM_read_PrivateKey(key_file, nullptr, nullptr, nullptr);
    fclose(key_file);

    if (!private_key) {
        std::cerr << "Failed to load private key" << std::endl;
        ERR_print_errors_fp(stderr);
        return false;
    }

    return true;
}

bool sign_data(const void *data, uint64_t data_length, uint8_t **signature, uint64_t *signature_length) {
    EVP_MD_CTX *ctx = EVP_MD_CTX_new();
    if (!ctx) {
        std::cerr << "Failed to create EVP context" << std::endl;
        return false;
    }

    if (EVP_DigestSignInit(ctx, nullptr, EVP_sha256(), nullptr, private_key) <= 0) {
        std::cerr << "Failed to initialize signing" << std::endl;
        EVP_MD_CTX_free(ctx);
        return false;
    }

    if (EVP_DigestSignUpdate(ctx, data, data_length) <= 0) {
        std::cerr << "Failed to update digest" << std::endl;
        EVP_MD_CTX_free(ctx);
        return false;
    }

    if (EVP_DigestSignFinal(ctx, nullptr, signature_length) <= 0) {
        std::cerr << "Failed to get signature length" << std::endl;
        EVP_MD_CTX_free(ctx);
        return false;
    }

    *signature = static_cast<uint8_t *>(malloc(*signature_length));
    if (!*signature) {
        std::cerr << "Failed to allocate signature memory" << std::endl;
        EVP_MD_CTX_free(ctx);
        return false;
    }

    if (EVP_DigestSignFinal(ctx, *signature, signature_length) <= 0) {
        std::cerr << "Failed to generate signature" << std::endl;
        free(*signature);
        *signature = nullptr;
        EVP_MD_CTX_free(ctx);
        return false;
    }

    EVP_MD_CTX_free(ctx);
    return true;
}

UA_StatusCode serialize_signed_data(
    const SensorData *sensor_data,
    const uint8_t *signature,
    uint64_t signature_length,
    UA_ByteString *output
) {
    const uint64_t total_size = sizeof(SensorData) + sizeof(uint64_t) + signature_length;

    output->data = static_cast<uint8_t *>(UA_malloc(total_size));
    if (!output->data) {
        return UA_STATUSCODE_BADOUTOFMEMORY;
    }

    uint64_t offset = 0;

    memcpy(output->data + offset, sensor_data, sizeof(SensorData));
    offset += sizeof(SensorData);

    memcpy(output->data + offset, &signature_length, sizeof(uint64_t));
    offset += sizeof(uint64_t);

    memcpy(output->data + offset, signature, signature_length);
    offset += signature_length;

    output->length = offset;
    return UA_STATUSCODE_GOOD;
}

int main(const int argc, const char *argv[]) {
    if (argc != 2) {
        std::cerr << "Usage: ./sensor <sensorId>" << std::endl;
        return 1;
    }

    if (!load_private_key("../../../.keys/sensor_private.pem")) {
        return EXIT_FAILURE;
    }

    std::signal(SIGINT, stop_handler);
    std::signal(SIGTERM, stop_handler);

    UA_Client *client = UA_Client_new();
    UA_ClientConfig_setDefault(UA_Client_getConfig(client));

    UA_StatusCode status = UA_Client_connect(client, "opc.tcp://localhost:4840");
    if (status != UA_STATUSCODE_GOOD) {
        std::cerr << "Error connecting to OPC UA server: " << UA_StatusCode_name(status) << std::endl;
        UA_Client_delete(client);
        EVP_PKEY_free(private_key);
        return EXIT_FAILURE;
    }

    std::mt19937 gen(std::random_device{}());
    std::normal_distribution<float> temp_dist(13.5f, 1.09f);
    std::normal_distribution<float> pres_dist(1017.0f, 2.0f);
    std::normal_distribution<float> hum_dist(75.0f, 5.0f);
    std::normal_distribution<float> interval_dist(4.0f, 1.0f);

    const int32_t sensor_id = std::stoi(argv[1]);
    std::cout << "Sensor " << sensor_id << " started with digital signing enabled" << std::endl;

    while (running) {
        SensorData sensor_data{
            .sensor_id = sensor_id,
            .temperature = temp_dist(gen),
            .pressure = pres_dist(gen),
            .humidity = hum_dist(gen),
            .timestamp = now(),
        };

        unsigned char *signature = nullptr;
        size_t signature_length = 0;

        if (!sign_data(&sensor_data, sizeof(SensorData), &signature, &signature_length)) {
            std::cerr << "Failed to sign data" << std::endl;
            continue;
        }

        UA_ByteString bytes;
        if (serialize_signed_data(&sensor_data, signature, signature_length, &bytes) != UA_STATUSCODE_GOOD) {
            std::cerr << "Error when serializing" << std::endl;
            free(signature);
            continue;
        }

        UA_Variant value;
        UA_Variant_init(&value);
        UA_Variant_setScalar(&value, &bytes, &UA_TYPES[UA_TYPES_BYTESTRING]);

        UA_NodeId dest = UA_NODEID_STRING_ALLOC(1, "sensor");

        status = UA_Client_writeValueAttribute(client, dest, &value);
        if (status == UA_STATUSCODE_GOOD) {
            std::cout << "Signed data sent to node\n"
                      << "    signature_length = " << signature_length << '\n'
                      << "    sensor_id        = " << sensor_data.sensor_id << '\n'
                      << "    temperature      = " << sensor_data.temperature << '\n'
                      << "    pressure         = " << sensor_data.pressure << '\n'
                      << "    humidity         = " << sensor_data.humidity << '\n'
                      << "    timestamp        = " << sensor_data.timestamp << std::endl;
        } else {
            std::cerr << "Could not write to node: " << UA_StatusCode_name(status) << std::endl;
        }

        UA_NodeId_clear(&dest);
        UA_ByteString_clear(&bytes);
        free(signature);

        std::this_thread::sleep_for(std::chrono::milliseconds(static_cast<int>(interval_dist(gen) * 1000)));
    }

    UA_Client_disconnect(client);
    UA_Client_delete(client);
    EVP_PKEY_free(private_key);

    std::cout << "Sensor stopped." << std::endl;

    return 0;
}
