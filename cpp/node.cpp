// OPC UA server

#include <csignal>
#include <cstring>
#include <iostream>

#include <open62541/server.h>
#include <open62541/server_config_default.h>

static volatile UA_Boolean running = true;

static void stopHandler(int) {
    running = false;
}

int main() {
    std::signal(SIGINT, stopHandler);
    std::signal(SIGTERM, stopHandler);

    UA_Server *server = UA_Server_new();
    UA_ServerConfig_setDefault(UA_Server_getConfig(server));

    const auto constLocale = "es-US";
    const auto constNodeName = "sensor";
    const auto localeSize = strlen(constLocale) + 1;
    const auto nodeNameSize = strlen(constNodeName) + 1;
    char *locale = static_cast<char *>(malloc(localeSize));
    char *nodeName = static_cast<char *>(malloc(nodeNameSize));
    strncpy(locale, constLocale, localeSize);
    strncpy(nodeName, constNodeName, nodeNameSize);
    locale[localeSize - 1] = 0;
    nodeName[nodeNameSize - 1] = 0;

    UA_VariableAttributes attr = UA_VariableAttributes_default;
    UA_ByteString emptyData;
    UA_ByteString_init(&emptyData);
    UA_Variant_setScalar(&attr.value, &emptyData, &UA_TYPES[UA_TYPES_BYTESTRING]);
    attr.displayName = UA_LOCALIZEDTEXT(locale, nodeName);
    attr.dataType = UA_TYPES[UA_TYPES_BYTESTRING].typeId;
    attr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    attr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;

    const UA_NodeId nodeId = UA_NODEID_STRING(1, nodeName);
    const UA_QualifiedName name = UA_QUALIFIEDNAME(1, nodeName);

    const UA_StatusCode rc = UA_Server_addVariableNode(
            server,
            nodeId,
            UA_NODEID_NUMERIC(0, UA_NS0ID_OBJECTSFOLDER),
            UA_NODEID_NUMERIC(0, UA_NS0ID_ORGANIZES),
            name,
            UA_NODEID_NUMERIC(0, UA_NS0ID_BASEDATAVARIABLETYPE),
            attr,
            nullptr,
            nullptr
    );

    if (rc != UA_STATUSCODE_GOOD) {
        std::cerr << "Error when creating node '" << nodeName << "': " << UA_StatusCode_name(rc) << "\n";
        UA_Server_delete(server);
        return EXIT_FAILURE;
    }

    std::cout << "OPC UA server running at opc.tcp://localhost:4840\n"
              << "Node available: ns=1;s=" << constNodeName << " (ByteString)\n"
              << "Press Ctrl+C to exit\n";

    UA_Server_run(server, &running);

    UA_Server_delete(server);
    return EXIT_SUCCESS;
}
