
cmake_minimum_required(VERSION 3.28)
include("CMakeCommons.cmake")
project(kmake)

include_directories("src/kmakelib/include")
add_subdirectory("src/kmakelib")

include_directories("src/kmake/include")
add_subdirectory("src/kmake")
