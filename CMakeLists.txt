cmake_minimum_required(VERSION 3.10)
project(Open62541Project)

set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -g")

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/build)

include_directories(
    open62541/include
    open62541/build
    open62541/build/src_generated
    open62541/build/src_generated/open62541
    open62541/plugins/include
)

find_library(OPEN62541_LIB
    NAMES libopen62541.a open62541
    PATHS open62541/build/bin
    NO_DEFAULT_PATH
)

if (NOT OPEN62541_LIB)
    message(FATAL_ERROR "libopen62541.a not found in open62541/build/bin")
endif ()

if (WIN32)
    set(PLATFORM_LIBS ws2_32 iphlpapi)
else ()
    set(PLATFORM_LIBS)
endif ()

add_executable(node cpp/node.cpp)
target_link_libraries(node ${OPEN62541_LIB} ${PLATFORM_LIBS})

add_executable(sensor cpp/sensor.cpp)
target_link_libraries(sensor ${OPEN62541_LIB} ${PLATFORM_LIBS})
