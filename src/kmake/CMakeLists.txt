 
cmake_minimum_required(VERSION 3.28)
include("../../CMakeCommons.cmake")
file(GLOB_RECURSE kmake_SRC CONFIGURE_DEPENDS  "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp" "${CMAKE_CURRENT_SOURCE_DIR}/*.hpp" "${CMAKE_CURRENT_SOURCE_DIR}/*.c" "${CMAKE_CURRENT_SOURCE_DIR}/*.h")

add_executable(kmake  ${kmake_SRC})
PrecompileStdHeaders(kmake)
target_link_libraries( kmakelib)
add_custom_command(
    TARGET kmake POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy
            "${CMAKE_SOURCE_DIR}/out/build/${CMAKE_PRESET_NAME}/compile_commands.json"
            "${CMAKE_SOURCE_DIR}/compile_commands.json"
)
