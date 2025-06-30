#include <iostream>
#include <csignal>
#include <thread>
#include <random>
#include <open62541/client.h>
#include <open62541/client_config_default.h>
#include <open62541/client_highlevel.h>

static volatile bool running = true;

static void stopHandler(int sign) {
    running = false;
}

int main(int argc, char* argv[]) {
    if (argc != 2){
        std::cerr << "Cantidad erronea de argumentos\n";
        return -1;
    }
    // Manejo de señales para salir limpiamente
    std::signal(SIGINT, stopHandler);
    std::signal(SIGTERM, stopHandler);

    // Crear cliente y configurar
    UA_Client *client = UA_Client_new();
    UA_ClientConfig_setDefault(UA_Client_getConfig(client));

    // Conectar al servidor
    UA_StatusCode status = UA_Client_connect(client, "opc.tcp://localhost:4840");
    if (status != UA_STATUSCODE_GOOD) {
        std::cerr << "Error al conectar con el servidor OPC UA." << std::endl;
        UA_Client_delete(client);
        return EXIT_FAILURE;
    }


    std::random_device rd;
    std::mt19937 gen(rd());
    std::normal_distribution<> intervalo_entre_envios(4, 1); // en porciento



    std::normal_distribution<> temperaturas_random(13.5f, 1.09f); //en grados celcius
    std::normal_distribution<> presion_random(1017, 2.0f); //En var
    std::normal_distribution<> humedad_random(75, 5); // en porciento


    float intervalo = intervalo_entre_envios(gen);

    std::string id = argv[1];
    float temperatura = temperaturas_random(gen);
    float presion = presion_random(gen);
    float humedad = humedad_random(gen);
    std::string timestamp = "Lorem ipsum";

    // Preparar mensaje JSON
    std::string mensaje = "{\n"
        "    \"id\": " + id + ",\n"
        "    \"temperatura\": " + std::to_string(temperatura) + ",\n"
        "    \"presion\": " + std::to_string(presion) + ",\n"
        "    \"humedad\": " + std::to_string(humedad) + ",\n"
        "    \"timestamp\": \"" + timestamp + "\"\n"
    "}";

    UA_String ua_msg = UA_STRING_ALLOC(mensaje.c_str());
    UA_Variant valor;
    UA_Variant_init(&valor);
    UA_Variant_setScalar(&valor, &ua_msg, &UA_TYPES[UA_TYPES_STRING]);

    // Nodo destino
    UA_NodeId publicacionId = UA_NODEID_STRING(1, "Publicacion");

    // Loop principal con UA_Client_run_iterate
    bool enviado = false;
    // Dentro del while (running)
    while (running) {
        UA_Client_run_iterate(client, true);

        // Aquí quitamos el if (!enviado)
        status = UA_Client_writeValueAttribute(client, publicacionId, &valor);
        if (status == UA_STATUSCODE_GOOD) {
            std::cout << "Mensaje enviado exitosamente al nodo 'Publicacion'.\n";
        } else {
            std::cerr << "Error al escribir en el nodo: " << UA_StatusCode_name(status) << std::endl;
        }

        std::this_thread::sleep_for(std::chrono::duration<float>(intervalo)); // Para no escribir constantemente
    
        intervalo = intervalo_entre_envios(gen);
        
        std::string id = argv[1];
        float temperatura = temperaturas_random(gen);
        float presion = presion_random(gen);
        float humedad = humedad_random(gen);
        std::string timestamp = "Lorem ipsum";

        // Preparar mensaje JSON
        std::string mensaje = "{\n"
            "    \"id\": " + id + ",\n"
            "    \"temperatura\": " + std::to_string(temperatura) + ",\n"
            "    \"presion\": " + std::to_string(presion) + ",\n"
            "    \"humedad\": " + std::to_string(humedad) + ",\n"
            "    \"timestamp\": \"" + timestamp + "\"\n"
        "}";


    }

    UA_Client_disconnect(client);
    UA_Client_delete(client);
    std::cout << "Cliente finalizado.\n";
    return 0;
}
