cmake_minimum_required(VERSION 3.8)
project(pink_kinematics_server)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(generate_parameter_library REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(moveit_msgs REQUIRED)
find_package(rosidl_default_generators REQUIRED)

generate_parameter_module(
  pink_kinematics_server_parameters
  pink_kinematics_server/pink_kinematics_server_parameters.yaml
)

install(
  PROGRAMS ${PROJECT_NAME}/pink_kinematics_server.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME pink_kinematics_server
)

install(
  DIRECTORY launch config
  DESTINATION share/${PROJECT_NAME}
)

ament_export_dependencies(rosidl_default_runtime)

ament_package()
