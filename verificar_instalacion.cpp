#include <open62541/server.h>
#include <open62541/server_config_default.h>
#include <open62541/plugin/log_stdout.h>
#include <csignal>
#include <iostream>

static UA_Boolean running = true;

static void stopHandler(int sign) {
    running = false;
}

int main() {
    signal(SIGINT, stopHandler);
    signal(SIGTERM, stopHandler);

    // Crear y configurar el servidor
    UA_Server *server = UA_Server_new();
    UA_ServerConfig_setDefault(UA_Server_getConfig(server));

    // Crear variable "Publicacion"
    UA_VariableAttributes attr = UA_VariableAttributes_default;
    UA_String inicial = UA_STRING("Esperando datos...");
    UA_Variant_setScalar(&attr.value, &inicial, &UA_TYPES[UA_TYPES_STRING]);
    attr.displayName = UA_LOCALIZEDTEXT("es-ES", "Publicacion");

    // Habilitar lectura y escritura para todos los usuarios
    attr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    attr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;

    UA_NodeId publicacionId = UA_NODEID_STRING(1, "Publicacion");
    UA_QualifiedName name = UA_QUALIFIEDNAME(1, "Publicacion");
    UA_NodeId parentNode = UA_NODEID_NUMERIC(0, UA_NS0ID_OBJECTSFOLDER);
    UA_NodeId referenceType = UA_NODEID_NUMERIC(0, UA_NS0ID_ORGANIZES);

    UA_StatusCode status = UA_Server_addVariableNode(
        server,
        publicacionId,
        parentNode,
        referenceType,
        name,
        UA_NODEID_NUMERIC(0, UA_NS0ID_BASEDATAVARIABLETYPE),
        attr,
        nullptr,
        nullptr
    );

    if (status != UA_STATUSCODE_GOOD) {
        std::cerr << "Error al crear el nodo Publicacion." << std::endl;
        return EXIT_FAILURE;
    }

    std::cout << "Servidor OPC UA corriendo en opc.tcp://localhost:4840\n";
    std::cout << "Nodo 'Publicacion' creado. Esperando clientes que escriban datos...\n";

    UA_Server_run(server, &running);
    UA_Server_delete(server);
    return 0;
}
