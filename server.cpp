// servidor.cpp — Servidor OPC UA mínimo compatible con cliente_serializado.cpp
// Crea un único nodo Variable "Sensor1" de tipo UA_ByteString donde el cliente escribe

#include <csignal>
#include <iostream>

#include <open62541/server.h>
#include <open62541/server_config_default.h>

static volatile UA_Boolean running = true;
static void stopHandler(int) {
    running = false;
}

int main() {
    /* Capturar Ctrl‑C */
    std::signal(SIGINT, stopHandler);
    std::signal(SIGTERM, stopHandler);

    /* Configuración por defecto */
    UA_Server *server = UA_Server_new();
    UA_ServerConfig_setDefault(UA_Server_getConfig(server));

    /* ───────── Añadir Variable "Sensor1" (ByteString) ───────── */
    UA_VariableAttributes attr = UA_VariableAttributes_default;

    /* Valor inicial: ByteString vacío */
    UA_ByteString emptyData;
    UA_ByteString_init(&emptyData);           // length = 0, data = nullptr
    UA_Variant_setScalar(&attr.value, &emptyData, &UA_TYPES[UA_TYPES_BYTESTRING]);
    attr.displayName = UA_LOCALIZEDTEXT("es-ES", "Sensor1");
    attr.dataType    = UA_TYPES[UA_TYPES_BYTESTRING].typeId;

    UA_NodeId nodeId  = UA_NODEID_STRING(1, "Sensor1");
    UA_QualifiedName name = UA_QUALIFIEDNAME(1, "Sensor1");

    UA_StatusCode rc = UA_Server_addVariableNode(server,
                            nodeId,
                            UA_NODEID_NUMERIC(0, UA_NS0ID_OBJECTSFOLDER), // parent = Objects
                            UA_NODEID_NUMERIC(0, UA_NS0ID_ORGANIZES),      // reference type
                            name,
                            UA_NODEID_NUMERIC(0, UA_NS0ID_BASEDATAVARIABLETYPE),
                            attr, nullptr, nullptr);

    if(rc != UA_STATUSCODE_GOOD) {
        std::cerr << "Error al crear nodo Sensor1: " << UA_StatusCode_name(rc) << "\n";
        UA_Server_delete(server);
        return EXIT_FAILURE;
    }

    std::cout << "Servidor OPC UA iniciado en opc.tcp://localhost:4840\n"
              << "Nodo disponible: ns=1;s=Sensor1 (ByteString)\n"
              << "Presiona Ctrl+C para salir\n";

    /* Ejecutar bucle del servidor hasta que running sea false */
    UA_Server_run(server, &running);

    UA_Server_delete(server);
    return EXIT_SUCCESS;
}
