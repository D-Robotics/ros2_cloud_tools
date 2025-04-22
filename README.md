# ros2_cloud_tools

This package aims to utilize aliyun dashscope api services

```python
ros2 run ros2_cloud_tools asr_node --ros-args -p awake_keyword:="你好" -p audio_device:="default"
```



### DashScope API Key (CRITICAL)

Before running any nodes in this package, you **MUST** set your DashScope API key as an environment variable. The node reads this variable for authentication.

```bash
export DASHSCOPE_API_KEY='sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx' # Replace with your actual key
```

### 