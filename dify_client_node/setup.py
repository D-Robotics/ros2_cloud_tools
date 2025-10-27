from setuptools import find_packages, setup

package_name = 'dify_client_node'

setup(
    name=package_name,
    version='1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='zixi01.chen',
    maintainer_email='zixi01.chen@horizon.cc',
    description='Dify Client Node package for ROS2',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'dify_client = dify_client_node.dify_client:main'
        ],
    },
)
