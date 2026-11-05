cmake_minimum_required(VERSION 3.16)
project(handpilot_core)
find_package(ament_cmake REQUIRED)
add_library(${PROJECT_NAME}
  src/planar_arm.cpp src/inverse_kinematics.cpp
  src/constraints.cpp src/controller.cpp)
target_compile_features(${PROJECT_NAME} PUBLIC cxx_std_17)
target_include_directories(${PROJECT_NAME} PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>)
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  target_compile_options(${PROJECT_NAME} PRIVATE -Wall -Wextra -Wpedantic)
endif()
install(DIRECTORY include/ DESTINATION include)
install(TARGETS ${PROJECT_NAME} EXPORT export_${PROJECT_NAME}
  ARCHIVE DESTINATION lib LIBRARY DESTINATION lib RUNTIME DESTINATION bin)
ament_export_targets(export_${PROJECT_NAME} HAS_LIBRARY_TARGET)
if(BUILD_TESTING)
  find_package(ament_cmake_gtest REQUIRED)
  foreach(test_name kinematics constraints controller)
    ament_add_gtest(test_${test_name} test/test_${test_name}.cpp)
    target_link_libraries(test_${test_name} ${PROJECT_NAME})
  endforeach()
endif()
ament_package()
