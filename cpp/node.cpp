// OPC UA server

#include <csignal>
#include <cstring>
#include <iostream>

#include <open62541/server.h>
#include <open62541/server_config_default.h>

static volatile UA_Boolean running = true;

static void stop_handler(int) {
    running = false;
}

int main() {
    std::signal(SIGINT, stop_handler);
    std::signal(SIGTERM, stop_handler);

    UA_Server *server = UA_Server_new();
    UA_ServerConfig_setDefault(UA_Server_getConfig(server));

    const auto const_locale = "es-US";
    const auto const_node_name = "sensor";
    const auto locale_size = strlen(const_locale) + 1;
    const auto node_name_size = strlen(const_node_name) + 1;
    char *locale = static_cast<char *>(malloc(locale_size));
    char *node_name = static_cast<char *>(malloc(node_name_size));
    strncpy(locale, const_locale, locale_size);
    strncpy(node_name, const_node_name, node_name_size);
    locale[locale_size - 1] = 0;
    node_name[node_name_size - 1] = 0;

    UA_VariableAttributes attr = UA_VariableAttributes_default;
    UA_ByteString empty_data;
    UA_ByteString_init(&empty_data);
    UA_Variant_setScalar(&attr.value, &empty_data, &UA_TYPES[UA_TYPES_BYTESTRING]);
    attr.displayName = UA_LOCALIZEDTEXT(locale, node_name);
    attr.dataType = UA_TYPES[UA_TYPES_BYTESTRING].typeId;
    attr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    attr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;

    const UA_NodeId node_id = UA_NODEID_STRING(1, node_name);
    const UA_QualifiedName name = UA_QUALIFIEDNAME(1, node_name);

    const UA_StatusCode rc = UA_Server_addVariableNode(
        server,
        node_id,
        UA_NODEID_NUMERIC(0, UA_NS0ID_OBJECTSFOLDER),
        UA_NODEID_NUMERIC(0, UA_NS0ID_ORGANIZES),
        name,
        UA_NODEID_NUMERIC(0, UA_NS0ID_BASEDATAVARIABLETYPE),
        attr,
        nullptr,
        nullptr
    );

    if (rc != UA_STATUSCODE_GOOD) {
        std::cerr << "Error when creating node '" << node_name << "': " << UA_StatusCode_name(rc) << "\n";
        UA_Server_delete(server);
        return EXIT_FAILURE;
    }

    std::cout << "OPC UA server running at opc.tcp://localhost:4840\n"
              << "Node available: ns=1;s=" << const_node_name << " (ByteString)\n"
              << "Press Ctrl+C to exit\n";

    UA_Server_run(server, &running);

    UA_Server_delete(server);
    return EXIT_SUCCESS;
}
