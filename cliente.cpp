// cliente_serializado.cpp - Envia struct Sensor como UA_ByteString serializado

#include <iostream>
#include <csignal>
#include <thread>
#include <random>
#include <chrono>
#include <cstring>

#include <open62541/client.h>
#include <open62541/client_config_default.h>
#include <open62541/client_highlevel.h>

// Estructura base del sensor
#pragma pack(push, 1)  // Desactiva padding
struct Sensor{
    int id;
    float temperatura;
    float presion;
    float humedad;
    char timestamp[64]; // tamaño fijo
} ;
#pragma pack(pop) 
static volatile bool running = true;
static void stopHandler(int) {
    running = false;
}

// Serializador manual
UA_StatusCode serializeSensor(const Sensor *input, UA_ByteString *output) {
    UA_StatusCode retval = UA_STATUSCODE_GOOD;
    UA_UInt32 offset = 0;
    UA_UInt32 bufferSize = sizeof(Sensor);

    output->data = (UA_Byte *)UA_malloc(bufferSize);
    if (!output->data)
        return UA_STATUSCODE_BADOUTOFMEMORY;

    memcpy(output->data + offset, &input->id, sizeof(int));
    offset += sizeof(int);

    memcpy(output->data + offset, &input->temperatura, sizeof(float));
    offset += sizeof(float);

    memcpy(output->data + offset, &input->presion, sizeof(float));
    offset += sizeof(float);

    memcpy(output->data + offset, &input->humedad, sizeof(float));
    offset += sizeof(float);

    memcpy(output->data + offset, input->timestamp, sizeof(input->timestamp));
    offset += sizeof(input->timestamp);

    output->length = offset;
    return retval;
}

int main(int argc, char* argv[]) {
    if (argc != 2) {
        std::cerr << "Uso: ./cliente <idSensor>" << std::endl;
        return 1;
    }

    std::signal(SIGINT, stopHandler);
    std::signal(SIGTERM, stopHandler);

    UA_Client *client = UA_Client_new();
    UA_ClientConfig_setDefault(UA_Client_getConfig(client));

    UA_StatusCode status = UA_Client_connect(client, "opc.tcp://localhost:4840");
    if (status != UA_STATUSCODE_GOOD) {
        std::cerr << "Error al conectar con el servidor OPC UA." << std::endl;
        UA_Client_delete(client);
        return EXIT_FAILURE;
    }

    std::random_device rd;
    std::mt19937 gen(rd());
    std::normal_distribution<> temp_dist(13.5, 1.09);
    std::normal_distribution<> pres_dist(1017, 2.0);
    std::normal_distribution<> hum_dist(75, 5);
    std::normal_distribution<> intv_dist(4.0, 1.0);

    int sensorId = std::stoi(argv[1]);

    while (running) {
        Sensor s;
        s.id = sensorId;
        s.temperatura = temp_dist(gen);
        s.presion = pres_dist(gen);
        s.humedad = hum_dist(gen);
        strncpy(s.timestamp, "2025-07-01T12:00:00Z", sizeof(s.timestamp));

        UA_ByteString bytes;
        if (serializeSensor(&s, &bytes) != UA_STATUSCODE_GOOD) {
            std::cerr << "Fallo en la serialización" << std::endl;
            continue;
        }

        UA_Variant valor;
        UA_Variant_init(&valor);
        UA_Variant_setScalar(&valor, &bytes, &UA_TYPES[UA_TYPES_BYTESTRING]);

        std::string nodeName = "Sensor" + std::to_string(sensorId);
        UA_NodeId destino = UA_NODEID_STRING_ALLOC(1, nodeName.c_str());

        status = UA_Client_writeValueAttribute(client, destino, &valor);
        if (status == UA_STATUSCODE_GOOD)
            std::cout << "Mensaje enviado al nodo '" << nodeName << "'\n";
        else
            std::cerr << "Fallo al escribir nodo: " << UA_StatusCode_name(status) << std::endl;

        UA_NodeId_clear(&destino);
        UA_ByteString_clear(&bytes);
        std::cout << "Tamaño de Sensor: " << sizeof(Sensor) << std::endl; // Debe ser 80 bytes
        std::this_thread::sleep_for(std::chrono::milliseconds((int)(intv_dist(gen) * 1000)));
    }

    UA_Client_disconnect(client);
    UA_Client_delete(client);
    std::cout << "Cliente finalizado.\n";
    return 0;
}