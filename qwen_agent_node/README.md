##REMEMBER export dashscope_api_key
export DASHSCOPE_API_KEY=something....

colcon build --packages-select qwen_agent_node

ros2 run qwen_agent_node qwen_agent_node

parameters: asr_topic , tts_topic , image_topic , use_compressed

if use_compressed=true, node will subscribe to image topic with JPEG format (from sensor_msgs.msg import CompressedImage)
if use_compressed=false, node will subscribe to image topic with sensor_msgs/msg/Image.msg

ros2 run qwen_agent_node qwen_agent_node --ros-args -p image_topic:=/image_jpeg -p use_compressed:=true

ros2 topic pub --once /asr_text std_msgs/msg/String "{data: ""你是谁？""}"