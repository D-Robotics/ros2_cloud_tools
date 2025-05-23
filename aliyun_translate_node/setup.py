from setuptools import find_packages, setup

package_name = 'aliyun_translate_node'

setup(
    name=package_name,
    version='1.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/translate_launch.py']),
        ('share/' + package_name + '/config', ['config/translate_params.yaml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='OPlin',
    maintainer_email='oplin@oplin.cn',
    description='Aliyun Translation Node for ROS2',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'aliyun_translate_node = aliyun_translate_node.aliyun_translate_node:main',
        ],
    },
)