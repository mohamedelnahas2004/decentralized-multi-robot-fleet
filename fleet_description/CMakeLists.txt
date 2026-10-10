cmake_minimum_required(VERSION 3.8)
project(fleet_description)

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY urdf meshes launch config rviz worlds
  DESTINATION share/${PROJECT_NAME}
)

# `ros2 run fleet_description inspect_mesh.py <file.stl>`
install(
  PROGRAMS scripts/inspect_mesh.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
