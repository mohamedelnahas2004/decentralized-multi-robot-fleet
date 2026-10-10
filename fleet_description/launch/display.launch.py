"""RViz + robot_state_publisher + joint_state_publisher_gui for one robot.

ros2 launch fleet_description display.launch.py
ros2 launch fleet_description display.launch.py robot_name:=robot_2 accent_color:="1.0 0.5 0.0 1.0"
"""
import os
import tempfile

import xacro
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _launch_setup(context, *args, **kwargs):
    pkg = get_package_share_directory('fleet_description')
    cfg = lambda name: LaunchConfiguration(name).perform(context)  # noqa: E731

    robot_name = cfg('robot_name')
    tf_per_robot = cfg('tf_per_robot').lower() == 'true'

    robot_description = xacro.process_file(
        os.path.join(pkg, 'urdf', 'amr.urdf.xacro'),
        mappings={
            'robot_name': robot_name,
            'accent_color': cfg('accent_color'),
            'use_sim': 'false',
            'use_zed_wrapper_frames': cfg('use_zed_wrapper_frames'),
        },
    ).toxml()

    # Patch the RViz config for this robot (fixed frame, description topic, TF prefix).
    with open(os.path.join(pkg, 'rviz', 'robot.rviz')) as f:
        rviz_text = f.read().replace('robot_1', robot_name)
    rviz_file = tempfile.NamedTemporaryFile(
        mode='w', suffix='.rviz', prefix='fleet_display_', delete=False)
    rviz_file.write(rviz_text)
    rviz_file.close()

    if tf_per_robot:
        rsp_remaps = [('/tf', 'tf'), ('/tf_static', 'tf_static')]
        rviz_remaps = [('/tf', f'/{robot_name}/tf'),
                       ('/tf_static', f'/{robot_name}/tf_static')]
    else:
        rsp_remaps, rviz_remaps = [], []

    return [
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            namespace=robot_name,
            output='screen',
            parameters=[{
                'robot_description': robot_description,
                'frame_prefix': f'{robot_name}/',
                'use_sim_time': False,
            }],
            remappings=rsp_remaps,
        ),
        Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui',
            namespace=robot_name,
            output='screen',
            parameters=[{'robot_description': robot_description}],
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', rviz_file.name],
            output='screen',
            remappings=rviz_remaps,
        ),
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('robot_name', default_value='robot_1'),
        DeclareLaunchArgument('accent_color', default_value='0.0 0.70 0.75 1.0'),
        DeclareLaunchArgument('use_zed_wrapper_frames', default_value='false'),
        DeclareLaunchArgument(
            'tf_per_robot', default_value='false',
            description='true: TF on /<robot_name>/tf instead of the shared /tf'),
        OpaqueFunction(function=_launch_setup),
    ])
