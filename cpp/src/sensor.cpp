// sends serialized and signed data for multiple sensors

#include <chrono>
#include <csignal>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <mutex>
#include <random>
#include <string>
#include <thread>
#include <vector>

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
static std::mutex cout_mutex;

static void stop_handler(int) {
    running = false;
}

uint64_t now() {
    return std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::high_resolution_clock::now().time_since_epoch()
    ).count();
}

bool load_private_key(const char *keyPath, const char *password) {
    FILE *key_file = fopen(keyPath, "rb");
    if (!key_file) {
        std::cerr << "Cannot open private key file: " << keyPath << std::endl;
        return false;
    }

    private_key = PEM_read_PrivateKey(key_file, nullptr, nullptr, (void *) password);
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

void sensor_thread(const int sensor_id) {
    UA_Client *client = UA_Client_new();
    UA_ClientConfig_setDefault(UA_Client_getConfig(client));

    UA_StatusCode status = UA_Client_connect(client, "opc.tcp://localhost:4840");
    while (status != UA_STATUSCODE_GOOD && running) {
        {
            std::lock_guard<std::mutex> lock(cout_mutex);
            std::cerr << "Sensor " << sensor_id << " - Error connecting to OPC UA server: "
                      << UA_StatusCode_name(status) << std::endl;
        }
        std::this_thread::sleep_for(std::chrono::seconds(1));
        status = UA_Client_connect(client, "opc.tcp://localhost:4840");
    }

    if (!running) {
        UA_Client_delete(client);
        return;
    }

    std::mt19937 gen(std::random_device{}());
    std::normal_distribution<float> temp_dist(13.5f, 1.09f);
    std::normal_distribution<float> pres_dist(1017.0f, 2.0f);
    std::normal_distribution<float> hum_dist(75.0f, 5.0f);
    std::normal_distribution<float> interval_dist(4.0f, 1.0f);

    const std::string node_id = "sensor_" + std::to_string(sensor_id);

    {
        std::lock_guard<std::mutex> lock(cout_mutex);
        std::cout << "Sensor " << sensor_id << " started with digital signing enabled" << std::endl;
    }

    UA_Variant value;
    UA_Variant_init(&value);

    UA_NodeId dest = UA_NODEID_STRING_ALLOC(1, const_cast<char *>(node_id.c_str()));

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
            std::lock_guard<std::mutex> lock(cout_mutex);
            std::cerr << "Sensor " << sensor_id << " - Failed to sign data" << std::endl;
            continue;
        }

        UA_ByteString bytes;
        if (serialize_signed_data(&sensor_data, signature, signature_length, &bytes) != UA_STATUSCODE_GOOD) {
            std::lock_guard<std::mutex> lock(cout_mutex);
            std::cerr << "Sensor " << sensor_id << " - Error when serializing" << std::endl;
            free(signature);
            continue;
        }

        UA_Variant_setScalar(&value, &bytes, &UA_TYPES[UA_TYPES_BYTESTRING]);

        status = UA_Client_writeValueAttribute(client, dest, &value);
        if (status == UA_STATUSCODE_GOOD) {
            std::lock_guard<std::mutex> lock(cout_mutex);
            std::cout << "Sensor " << sensor_id << " - Signed data sent to node\n"
                      << "    signature_length = " << signature_length << '\n'
                      << "    sensor_id        = " << sensor_data.sensor_id << '\n'
                      << "    temperature      = " << sensor_data.temperature << '\n'
                      << "    pressure         = " << sensor_data.pressure << '\n'
                      << "    humidity         = " << sensor_data.humidity << '\n'
                      << "    timestamp        = " << sensor_data.timestamp << std::endl;
        } else {
            std::lock_guard<std::mutex> lock(cout_mutex);
            std::cerr << "Sensor " << sensor_id << " - Could not write to node: "
                      << UA_StatusCode_name(status) << std::endl;
        }

        UA_ByteString_clear(&bytes);
        free(signature);

        std::this_thread::sleep_for(std::chrono::milliseconds(static_cast<int>(interval_dist(gen) * 1000)));
    }

    UA_NodeId_clear(&dest);
    UA_Client_disconnect(client);
    UA_Client_delete(client);

    {
        std::lock_guard<std::mutex> lock(cout_mutex);
        std::cout << "Sensor " << sensor_id << " stopped." << std::endl;
    }
}

int main(const int argc, const char *argv[]) {
    if (argc != 3) {
        std::cerr << "Usage: ./sensor <num_sensors> <password>" << std::endl;
        return 1;
    }

    const int num_sensors = std::stoi(argv[1]);
    if (num_sensors <= 0) {
        std::cerr << "Number of sensors must be positive" << std::endl;
        return 1;
    }

    if (!load_private_key("../../.keys/sensor_private.pem", argv[2])) {
        return EXIT_FAILURE;
    }

    std::signal(SIGINT, stop_handler);
    std::signal(SIGTERM, stop_handler);

    std::cout << "Starting " << num_sensors << " sensors..." << std::endl;

    std::vector<std::thread> sensor_threads;
    for (int i = 1; i <= num_sensors; ++i) {
        sensor_threads.emplace_back(sensor_thread, i);
    }

    for (auto &thread : sensor_threads) {
        thread.join();
    }

    EVP_PKEY_free(private_key);

    std::cout << "All sensors stopped." << std::endl;

    return 0;
}
