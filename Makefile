# Nombre del ejecutable
TARGET = build/servidor

# Compilador (usa C++ porque open62541 es compatible)
CXX = g++

# Opciones de compilación
CXXFLAGS = -std=c++11 -Wall -g

# Include paths (headers)
INCLUDES = \
    -I open62541/include \
    -I open62541/build \
    -I open62541/build/src_generated \
    -I open62541/build/src_generated/open62541 \
    -I open62541/plugins/include

# Librería estática
STATIC_LIB = open62541/build/bin/libopen62541.a

# Archivo fuente único
SRC = verificar_instalacion.cpp

# Directorio de salida
OBJ_DIR = build

# Archivo objeto
OBJ = $(OBJ_DIR)/verificar_instalacion.o

.PHONY: all clean run debug

# Regla principal
all: $(TARGET)

# Compilar y enlazar
$(TARGET): $(OBJ)
	$(CXX) $(CXXFLAGS) $(OBJ) $(STATIC_LIB) -o $@

# Compilar archivo fuente
$(OBJ_DIR)/%.o: %.cpp | $(OBJ_DIR)
	$(CXX) $(CXXFLAGS) $(INCLUDES) -c $< -o $@

# Crear directorio build si no existe
$(OBJ_DIR):
	@mkdir -p $(OBJ_DIR)

# Ejecutar
run: $(TARGET)
	./$(TARGET)

# Debug con GDB
debug: $(TARGET)
	gdb ./$(TARGET)

# Limpiar
clean:
	rm -rf $(OBJ_DIR) $(TARGET)
