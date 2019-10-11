cmake_minimum_required(VERSION 3.4)
project(pyMille)

add_subdirectory(${CMAKE_SOURCE_DIR}/../../pybind11 ${CMAKE_CURRENT_BINARY_DIR}/pybind11)

link_directories($ENV{SIMPATH}/lib)

include_directories(
  $ENV{SIMPATH}/include
  ${CMAKE_SOURCE_DIR}/../../pybind11
)

pybind11_add_module(pyMille MillePythonInterface.cpp)

target_link_libraries(pyMille
  PRIVATE Mille
)