 
cmake_minimum_required(VERSION 3.28)
include("../../CMakeCommons.cmake")
file(GLOB_RECURSE kmakelib_SRC CONFIGURE_DEPENDS  "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp" "${CMAKE_CURRENT_SOURCE_DIR}/*.hpp" "${CMAKE_CURRENT_SOURCE_DIR}/*.c" "${CMAKE_CURRENT_SOURCE_DIR}/*.h")

add_library(kmakelib STATIC ${kmakelib_SRC})
PrecompileStdHeaders(kmakelib)

find_package(Lua REQUIRED)
target_include_directories(kmakelib PRIVATE ${LUA_INCLUDE_DIR})
target_link_libraries(kmakelib PRIVATE ${LUA_LIBRARIES})

add_custom_command(
    TARGET kmakelib POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy
            "${CMAKE_SOURCE_DIR}/out/build/${CMAKE_PRESET_NAME}/compile_commands.json"
            "${CMAKE_SOURCE_DIR}/compile_commands.json"
)
