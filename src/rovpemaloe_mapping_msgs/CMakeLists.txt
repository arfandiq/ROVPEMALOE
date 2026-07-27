cmake_minimum_required(VERSION 3.16)
project(rovpemaloe_mapping_msgs)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(std_msgs REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/OpticalFlowData.msg"
  "msg/DepthData.msg"
  "msg/IMUData.msg"
  "msg/RobotState.msg"
  "msg/Trajectory2D.msg"
  "msg/ThrusterCommand.msg"
  DEPENDENCIES geometry_msgs std_msgs
)

ament_package()
