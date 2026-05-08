cmake_minimum_required(VERSION 3.14)
project(hello_clearpath)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
  set(CMAKE_CXX_STANDARD_REQUIRED ON)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclpy REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(nav_msgs REQUIRED)

# C++ node
add_executable(hello_square_cpp src/hello_square.cpp)
ament_target_dependencies(hello_square_cpp rclcpp geometry_msgs nav_msgs)
install(TARGETS hello_square_cpp
  DESTINATION lib/${PROJECT_NAME})

# Python node
ament_python_install_package(${PROJECT_NAME})
install(PROGRAMS
  scripts/hello_square_py
  DESTINATION lib/${PROJECT_NAME})

install(DIRECTORY launch config
  DESTINATION share/${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
