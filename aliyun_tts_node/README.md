## REMEMBER export dashscope_api_key!
export DASHSCOPE_API_KEY=something....

colcon build --packages-select aliyun_tts_node

ros2 run aliyun_tts_node aliyun_tts_node \
  --ros-args \
  -p tts_method:=sambert

ros2 run aliyun_tts_node aliyun_tts_node \
  --ros-args \
  -p tts_method:=cosyvoice \
  -p text_topic:="/tts_input" \
  -p result_topic:="/tts_output" \
  -p cosy_voice:="longjielidou"
  <!-- -p cosy_voice:="loongstella" -->

ros2 topic pub --once /tts_input std_msgs/msg/String "{data: ""你是谁？""}"
ros2 topic pub --once /tts_input std_msgs/msg/String "{data: ""你叫什么名字可以和我讲个故事吗非常感谢你！哈哈哈哈哈哈你是谁呀！？你也太搞笑了""}"


可选的音色请参考以下文档
https://bailian.console.aliyun.com/?tab=doc#/api/?type=model&url=https%3A%2F%2Fhelp.aliyun.com%2Fdocument_detail%2F2840914.html