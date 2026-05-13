cmake_minimum_required(VERSION 3.8)
project(mm_demo)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

add_compile_options(-Wall -Wextra -Wpedantic)

find_package(ament_cmake REQUIRED)
find_package(generate_parameter_library REQUIRED)
find_package(moveit_msgs REQUIRED)
find_package(moveit_ros_planning_interface REQUIRED)
find_package(moveit_visual_tools REQUIRED)
find_package(moveit_task_constructor_core REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rviz_visual_tools REQUIRED)
find_package(shape_msgs REQUIRED)

add_executable(
  plan_with_obstacle
  src/plan_with_obstacle.cpp
)

target_link_libraries(plan_with_obstacle
  PRIVATE
    rclcpp::rclcpp
    ${moveit_ros_planning_interface_TARGETS}
    ${rviz_visual_tools_TARGETS}
)


target_include_directories(plan_with_obstacle
  PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
         $<INSTALL_INTERFACE:include>)

add_library(mm_task_base SHARED
  src/task_base.cpp
)

generate_parameter_library(base_params src/base_params.yaml)

target_link_libraries(mm_task_base
  PUBLIC
    base_params
    ${moveit_msgs_TARGETS}
    ${moveit_task_constructor_core_TARGETS}
    rclcpp::rclcpp
)

target_include_directories(mm_task_base
  PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
         $<INSTALL_INTERFACE:include>)

generate_parameter_library(draw_square_params src/draw_square_params.yaml)
generate_parameter_library(write_letters_params src/write_letters_params.yaml)

add_library(mm_tasks SHARED
  src/draw_square_task.cpp
  src/write_letters_task.cpp
)

target_link_libraries(mm_tasks
  PUBLIC
    mm_task_base
    base_params
    draw_square_params
    write_letters_params
    ${moveit_msgs_TARGETS}
    ${moveit_task_constructor_core_TARGETS}
    rclcpp::rclcpp
)

target_include_directories(mm_tasks
  PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
         $<INSTALL_INTERFACE:include>)

add_executable(
  cartesian_demo
  src/cartesian_demo.cpp
)

target_link_libraries(cartesian_demo
  PRIVATE
    rclcpp::rclcpp
    mm_tasks
    ${moveit_visual_tools_TARGETS}
)

install(
  TARGETS plan_with_obstacle mm_task_base base_params mm_tasks cartesian_demo draw_square_params write_letters_params
  EXPORT ${PROJECT_NAME}Targets
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION lib/${PROJECT_NAME}
)

install(
  DIRECTORY
    config
    launch
  DESTINATION
    share/${PROJECT_NAME}/
)
ament_export_targets(${PROJECT_NAME}Targets HAS_LIBRARY_TARGET)
ament_export_dependencies(
  generate_parameter_library
  moveit_msgs
  moveit_visual_tools
  moveit_task_constructor_core
  rclcpp
)
ament_package()
