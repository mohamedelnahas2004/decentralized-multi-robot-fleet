"""Spawn one namespaced AMR into a running gz-sim world, with its own bridge.

ros2 launch fleet_description spawn_robot.launch.py start_gz:=true
ros2 launch fleet_description spawn_robot.launch.py robot_name:=robot_2 x:=2.0 y:=1.0 \
    accent_color:="1.0 0.5 0.0 1.0"
"""
import os
import tempfile

import xacro
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, IncludeLaunchDescription,
                            OpaqueFunction, TimerAction)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _launch_setup(context, *args, **kwargs):
    pkg = get_package_share_directory('fleet_description')
    cfg = lambda name: LaunchConfiguration(name).perform(context)  # noqa: E731
    is_true = lambda name: cfg(name).lower() == 'true'  # noqa: E731

    robot_name = cfg('robot_name')
    world_name = cfg('world_name')
    use_sim_time = is_true('use_sim_time')
    tf_per_robot = is_true('tf_per_robot')
    tf_topic = f'/{robot_name}/tf' if tf_per_robot else '/tf'

    robot_description = xacro.process_file(
        os.path.join(pkg, 'urdf', 'amr.urdf.xacro'),
        mappings={
            'robot_name': robot_name,
            'accent_color': cfg('accent_color'),
            'use_sim': 'true',
            'use_zed_wrapper_frames': cfg('use_zed_wrapper_frames'),
        },
    ).toxml()

    # Per-robot bridge config from the template.
    with open(os.path.join(pkg, 'config', 'ros_gz_bridge.yaml')) as f:
        bridge_text = (f.read()
                       .replace('<robot_name>', robot_name)
                       .replace('<tf_topic>', tf_topic))
    bridge_file = tempfile.NamedTemporaryFile(
        mode='w', suffix='.yaml', prefix=f'bridge_{robot_name}_', delete=False)
    bridge_file.write(bridge_text)
    bridge_file.close()

    rsp_remaps = ([('/tf', 'tf'), ('/tf_static', 'tf_static')]
                  if tf_per_robot else [])

    actions = []

    start_gz = is_true('start_gz')
    if start_gz:
        actions.append(IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(
                get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')),
            launch_arguments={'gz_args': f'-r {cfg("world_file")}'}.items()))

    if start_gz or is_true('bridge_clock'):
        actions.append(Node(
            package='ros_gz_bridge', executable='parameter_bridge',
            name='clock_bridge', output='screen',
            arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock']))

    robot_nodes = [
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            namespace=robot_name,
            output='screen',
            parameters=[{
                'robot_description': robot_description,
                'frame_prefix': f'{robot_name}/',
                'use_sim_time': use_sim_time,
            }],
            remappings=rsp_remaps,
        ),
        Node(
            package='ros_gz_sim',
            executable='create',
            output='screen',
            arguments=[
                '-world', world_name,
                '-name', robot_name,
                '-string', robot_description,
                '-x', cfg('x'), '-y', cfg('y'), '-z', cfg('z'), '-Y', cfg('yaw'),
            ],
        ),
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name='ros_gz_bridge',
            namespace=robot_name,
            output='screen',
            parameters=[{'config_file': bridge_file.name,
                         'use_sim_time': use_sim_time}],
        ),
    ]
    # Give gz-sim time to bring up the create service when we started it ourselves.
    if start_gz:
        actions.append(TimerAction(period=6.0, actions=robot_nodes))
    else:
        actions.extend(robot_nodes)
    return actions


def generate_launch_description():
    pkg = get_package_share_directory('fleet_description')
    return LaunchDescription([
        DeclareLaunchArgument('robot_name', default_value='robot_1'),
        DeclareLaunchArgument('x', default_value='0.0'),
        DeclareLaunchArgument('y', default_value='0.0'),
        DeclareLaunchArgument('z', default_value='0.01'),
        DeclareLaunchArgument('yaw', default_value='0.0'),
        DeclareLaunchArgument('accent_color', default_value='0.0 0.70 0.75 1.0'),
        DeclareLaunchArgument('use_zed_wrapper_frames', default_value='false'),
        DeclareLaunchArgument('world_name', default_value='fleet_world',
                              description='name of the running gz world'),
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument(
            'tf_per_robot', default_value='false',
            description='true: TF on /<robot_name>/tf instead of the shared /tf'),
        DeclareLaunchArgument(
            'start_gz', default_value='false',
            description='also start gz-sim with world_file and bridge /clock'),
        DeclareLaunchArgument(
            'bridge_clock', default_value='false',
            description='bridge /clock (only ONE launch per fleet should do this)'),
        DeclareLaunchArgument(
            'world_file',
            default_value=os.path.join(pkg, 'worlds', 'fleet_world.sdf')),
        OpaqueFunction(function=_launch_setup),
    ])
