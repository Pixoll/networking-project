// sends serialized data

#include <chrono>
#include <csignal>
#include <cstring>
#include <iostream>
#include <random>
#include <thread>

#include <open62541/client.h>
#include <open62541/client_config_default.h>
#include <open62541/client_highlevel.h>

struct __attribute__((packed)) Sensor {
    int id;
    float temperature;
    float pression;
    float humidity;
    char timestamp[21];
};

static volatile bool running = true;

static void stopHandler(int) {
    running = false;
}

UA_StatusCode serializeSensor(const Sensor *input, UA_ByteString *output) {
    UA_UInt32 offset = 0;

    output->data = static_cast<UA_Byte *>(UA_malloc(sizeof(Sensor)));
    if (!output->data)
        return UA_STATUSCODE_BADOUTOFMEMORY;

    memcpy(output->data + offset, &input->id, sizeof(int));
    offset += sizeof(int);

    memcpy(output->data + offset, &input->temperature, sizeof(float));
    offset += sizeof(float);

    memcpy(output->data + offset, &input->pression, sizeof(float));
    offset += sizeof(float);

    memcpy(output->data + offset, &input->humidity, sizeof(float));
    offset += sizeof(float);

    memcpy(output->data + offset, input->timestamp, sizeof(input->timestamp));
    offset += sizeof(input->timestamp);

    output->length = offset;
    return UA_STATUSCODE_GOOD;
}

int main(const int argc, const char *argv[]) {
    if (argc != 2) {
        std::cerr << "Usage: ./client <sensorId>" << std::endl;
        return 1;
    }

    std::signal(SIGINT, stopHandler);
    std::signal(SIGTERM, stopHandler);

    UA_Client *client = UA_Client_new();
    UA_ClientConfig_setDefault(UA_Client_getConfig(client));

    UA_StatusCode status = UA_Client_connect(client, "opc.tcp://localhost:4840");
    if (status != UA_STATUSCODE_GOOD) {
        std::cerr << "Error when connecting to OPC UA server." << std::endl;
        UA_Client_delete(client);
        return EXIT_FAILURE;
    }

    std::mt19937 gen(std::random_device{}());
    std::normal_distribution<float> temp_dist(13.5f, 1.09f);
    std::normal_distribution<float> pres_dist(1017.0f, 2.0f);
    std::normal_distribution<float> hum_dist(75.0f, 5.0f);
    std::normal_distribution<float> interval_dist(4.0f, 1.0f);

    const int sensorId = std::stoi(argv[1]);

    while (running) {
        Sensor s{
            .id = sensorId,
            .temperature = temp_dist(gen),
            .pression = pres_dist(gen),
            .humidity = hum_dist(gen),
        };
        strncpy(s.timestamp, "2025-07-01T12:00:00Z", sizeof(s.timestamp));

        UA_ByteString bytes;
        if (serializeSensor(&s, &bytes) != UA_STATUSCODE_GOOD) {
            std::cerr << "Error when serializing" << std::endl;
            continue;
        }

        UA_Variant value;
        UA_Variant_init(&value);
        UA_Variant_setScalar(&value, &bytes, &UA_TYPES[UA_TYPES_BYTESTRING]);

        UA_NodeId dest = UA_NODEID_STRING_ALLOC(1, "sensor");

        status = UA_Client_writeValueAttribute(client, dest, &value);
        if (status == UA_STATUSCODE_GOOD) {
            std::cout << "Data sent to node\n"
                << "    id = " << s.id << '\n'
                << "    temp = " << s.temperature << '\n'
                << "    pres = " << s.pression << '\n'
                << "    hum = " << s.humidity << '\n'
                << "    time = " << s.timestamp << std::endl;
        } else {
            std::cerr << "Could not write to node: " << UA_StatusCode_name(status) << std::endl;
        }

        UA_NodeId_clear(&dest);
        UA_ByteString_clear(&bytes);
        std::this_thread::sleep_for(std::chrono::milliseconds(static_cast<int>(interval_dist(gen) * 1000)));
    }

    UA_Client_disconnect(client);
    UA_Client_delete(client);
    std::cout << "Client stopped." << std::endl;

    return 0;
}
