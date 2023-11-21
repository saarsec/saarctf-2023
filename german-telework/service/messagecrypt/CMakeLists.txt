cmake_minimum_required(VERSION 3.7)

# set up project
set(PROJ_NAME "messagecrypt")
project(${PROJ_NAME} LANGUAGES CXX)

# debug symbols
set(CMAKE_BUILD_TYPE Debug)

# -pthread
set(THREADS_PREFER_PTHREAD_FLAG ON)
find_package(Threads REQUIRED)

# collect source files
file(GLOB SOURCES "src/*.cc")

# define resulting binary
add_executable(${PROJ_NAME} ${SOURCES})

# COMPILER FLAGS
# enable warnings
target_compile_options(${PROJ_NAME} PRIVATE "-Wall")
# enable C++17 support
target_compile_options(${PROJ_NAME} PRIVATE "-std=c++17")
# link it with -pthread
target_link_libraries(${PROJ_NAME} PRIVATE Threads::Threads)