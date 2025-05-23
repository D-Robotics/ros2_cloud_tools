from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'source_lang',
            default_value='auto',
            description='Source language for translation'
        ),
        DeclareLaunchArgument(
            'target_lang',
            default_value='English',
            description='Target language for translation'
        ),
        DeclareLaunchArgument(
            'input_topic',
            default_value='text_to_translate',
            description='Input text topic name'
        ),
        DeclareLaunchArgument(
            'output_topic',
            default_value='translated_text',
            description='Output text topic name'
        ),
        
        Node(
            package='aliyun_translate_node',
            executable='aliyun_translate_node',
            name='aliyun_translate_node',
            parameters=[{
                'source_lang': LaunchConfiguration('source_lang'),
                'target_lang': LaunchConfiguration('target_lang'),
                'input_topic': LaunchConfiguration('input_topic'),
                'output_topic': LaunchConfiguration('output_topic'),
                'model': 'qwen-mt-turbo',
                'enable_cache': True,
                'max_retry_count': 3,
                'retry_delay': 1.0,
            }],
            output='screen'
        )
    ])