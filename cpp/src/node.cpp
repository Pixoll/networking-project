// OPC UA server

#include <csignal>
#include <iostream>
#include <string>
#include <vector>

#include <open62541/server.h>
#include <open62541/server_config_default.h>

static volatile UA_Boolean running = true;

static void stop_handler(int) {
    running = false;
}

struct SensorNode {
    const std::string node_id;
    const std::string display_name;
};

int main(const int argc, const char *argv[]) {
    if (argc != 2) {
        std::cerr << "Usage: ./node <number_of_nodes>" << std::endl;
        return 1;
    }

    std::signal(SIGINT, stop_handler);
    std::signal(SIGTERM, stop_handler);

    UA_Server *server = UA_Server_new();
    UA_ServerConfig_setDefault(UA_Server_getConfig(server));

    const auto const_locale = "es-US";
    const int num_sensors = std::stoi(argv[1]);

    std::vector<SensorNode> sensors;
    sensors.reserve(num_sensors);

    for (int i = 1; i <= num_sensors; i++) {
        SensorNode sensor{
            .node_id = "sensor_" + std::to_string(i),
            .display_name = "Sensor " + std::to_string(i),
        };

        sensors.push_back(sensor);
    }

    for (const auto &sensor: sensors) {
        UA_VariableAttributes attr = UA_VariableAttributes_default;
        UA_ByteString empty_data;
        UA_ByteString_init(&empty_data);
        UA_Variant_setScalar(&attr.value, &empty_data, &UA_TYPES[UA_TYPES_BYTESTRING]);
        attr.displayName = UA_LOCALIZEDTEXT(
            const_cast<char *>(const_locale),
            const_cast<char *>(sensor.display_name.c_str())
        );
        attr.dataType = UA_TYPES[UA_TYPES_BYTESTRING].typeId;
        attr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
        attr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;

        const UA_NodeId node_id = UA_NODEID_STRING(1, const_cast<char *>(sensor.node_id.c_str()));
        const UA_QualifiedName name = UA_QUALIFIEDNAME(1, const_cast<char *>(sensor.node_id.c_str()));

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
            std::cerr << "Error when creating node '" << sensor.node_id << "': " << UA_StatusCode_name(rc) << "\n";
            UA_Server_delete(server);
            return EXIT_FAILURE;
        }
    }

    std::cout << "OPC UA server running at opc.tcp://localhost:4840\n"
              << "Available sensor nodes:\n";
    for (const auto &sensor: sensors) {
        std::cout << "  ns=1;s=" << sensor.node_id << " (" << sensor.display_name << ")\n";
    }
    std::cout << "Press Ctrl+C to exit\n";

    UA_Server_run(server, &running);

    UA_Server_delete(server);
    return EXIT_SUCCESS;
}
