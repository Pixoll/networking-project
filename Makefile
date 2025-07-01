# Ejecutables
TARGET_SERVER = build/servidor
TARGET_CLIENT = build/cliente

# Compilador
CXX = g++

# Opciones de compilación
CXXFLAGS = -std=c++11 -Wall -g

# Include paths
INCLUDES = \
    -I open62541/include \
    -I open62541/build \
    -I open62541/build/src_generated \
    -I open62541/build/src_generated/open62541 \
    -I open62541/plugins/include

# Librería estática
STATIC_LIB = open62541/build/bin/libopen62541.a

# Archivos fuente
SRC_SERVER = verificar_instalacion.cpp
SRC_CLIENT = cliente.cpp

# Directorio de salida
OBJ_DIR = build

# Archivos objeto
OBJ_SERVER = $(OBJ_DIR)/verificar_instalacion.o
OBJ_CLIENT = $(OBJ_DIR)/cliente.o

.PHONY: all clean run_server run_client debug_server debug_client

# Regla principal
all: $(TARGET_SERVER) $(TARGET_CLIENT)

# Compilar servidor
$(TARGET_SERVER): $(OBJ_SERVER)
	$(CXX) $(CXXFLAGS) $(OBJ_SERVER) $(STATIC_LIB) -o $@

# Compilar cliente
$(TARGET_CLIENT): $(OBJ_CLIENT)
	$(CXX) $(CXXFLAGS) $(OBJ_CLIENT) $(STATIC_LIB) -o $@

# Regla genérica para compilar archivos fuente
$(OBJ_DIR)/%.o: %.cpp | $(OBJ_DIR)
	$(CXX) $(CXXFLAGS) $(INCLUDES) -c $< -o $@

# Crear directorio de salida
$(OBJ_DIR):
	@mkdir -p $(OBJ_DIR)

# Ejecutar servidor
run_server: $(TARGET_SERVER)
	./$(TARGET_SERVER)

# Ejecutar cliente
run_client: $(TARGET_CLIENT)
	./$(TARGET_CLIENT)

# Debug servidor
debug_server: $(TARGET_SERVER)
	gdb ./$(TARGET_SERVER)

# Debug cliente
debug_client: $(TARGET_CLIENT)
	gdb ./$(TARGET_CLIENT)

# Limpiar
clean:
	rm -rf $(OBJ_DIR) $(TARGET_SERVER) $(TARGET_CLIENT)
