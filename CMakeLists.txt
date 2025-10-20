
cmake_minimum_required(VERSION 3.28)
include("CMakeCommons.cmake")
project(kmake)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include_directories("src/kmakelib/include")
add_subdirectory("src/kmakelib")

include_directories("src/kmake/include")
add_subdirectory("src/kmake")
