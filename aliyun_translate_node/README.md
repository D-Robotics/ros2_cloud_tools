<h1 style="color:#00CCFF; text-shadow:2px 2px #000; text-align: center;">
🌐 aliyun_translate_node (ROS 2) 🔄 
</h1>

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

A ROS 2 node for real-time text translation using Alibaba Cloud's DashScope service (`qwen-mt-turbo`). It subscribes to a text topic, translates the received text using DashScope translation API, and publishes the translated result to another ROS topic. Supports multiple languages with intelligent caching and retry mechanisms.

## Features

- Integrates Alibaba Cloud DashScope translation service (`qwen-mt-turbo`).
- Supports **multi-language translation** with auto-detection capabilities.
- Subscribes to configurable `std_msgs/msg/String` input topic for source text.
- Publishes translated text to configurable `std_msgs/msg/String` output topic.
- **Intelligent caching system**: Avoids retranslating identical content.
- **Automatic retry mechanism** with configurable retry count and delay.
- **Real-time statistics**: Tracks translation success/failure rates and cache performance.
- Configurable source/target languages, topics, model, and retry settings via ROS 2 parameters.
- Supports dynamic parameter updates during runtime (e.g., changing target language).
- Uses `colorama` for enhanced terminal logging output.

## Prerequisites

```bash
source /opt/tros/humble/setup.bash
python -m pip install dashscope colorama
```

## Installation

1. **Build the package using `colcon`:**

   ```bash
   cd ~/your_ros2_ws
   colcon build --packages-select aliyun_translate_node
   ```

2. **Source the Workspace:** Source your workspace's setup file:

   ```bash
   source install/setup.bash
   ```

## Configuration

### 1. DashScope API Key (CRITICAL)

**IMPORTANT:** You **MUST** set your API key as an environment variable **BEFORE** launching the node.

```bash
export DASHSCOPE_API_KEY='sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx' # Replace with your actual key
```

### 2. ROS 2 Parameters

| Parameter Name    | Description                                                  | Type    | Default Value       |
| ----------------- | ------------------------------------------------------------ | ------- | ------------------- |
| `api_key`         | DashScope API key (optional, uses environment variable if empty). | string  | `""`                |
| `model`           | Translation model name used by DashScope.                    | string  | `qwen-mt-turbo`     |
| `source_lang`     | Source language for translation ('auto' for auto-detection). | string  | `auto`              |
| `target_lang`     | Target language for translation (e.g., 'English', 'Chinese'). | string  | `English`           |
| `input_topic`     | Topic name to subscribe for text to translate (`std_msgs/msg/String`). | string  | `text_to_translate` |
| `output_topic`    | Topic name to publish translated text (`std_msgs/msg/String`). | string  | `translated_text`   |
| `result_format`   | Result format for DashScope API response.                    | string  | `message`           |
| `enable_cache`    | Enable/disable translation result caching.                   | boolean | `True`              |
| `max_retry_count` | Maximum number of retry attempts for failed translations.    | integer | `3`                 |
| `retry_delay`     | Delay in seconds between retry attempts.                     | double  | `1.0`               |

### 3. Supported Languages

The node supports multiple languages including:

- `auto` (输入语言可选)
- `Chinese` (中文)
- `English` (英文)
- `Japanese` (日文)
- `Korean` (韩文)
- `French` (法文)
- `German` (德文)
- `Spanish` (西班牙文)
- `Russian` (俄文)
- `Arabic` (阿拉伯文)
- `Italian` (意大利文)
- `Portuguese` (葡萄牙文)
- `Thai` (泰文)
- `Vietnamese` (越南文)

## Usage

### Basic Usage

```bash
ros2 run aliyun_translate_node aliyun_translate_node
```

### With Custom Parameters

```bash
ros2 run aliyun_translate_node aliyun_translate_node \
--ros-args \
-p source_lang:="Chinese" \
-p target_lang:="English" \
-p input_topic:="/asr_text" \
-p output_topic:="/translated_asr_text"
```

### Using Launch File

```bash
ros2 launch aliyun_translate_node translate_launch.py \
source_lang:=Chinese \
target_lang:=English \
input_topic:=asr_text \
output_topic:=translated_text
```

### Integration with ASR Node

```bash
# Terminal 1: Start ASR node
ros2 run aliyun_asr_node asr_node

# Terminal 2: Start translation node (subscribes to ASR output)
ros2 run aliyun_translate_node aliyun_translate_node \
--ros-args \
-p input_topic:="/asr_text" \
-p source_lang:="Chinese" \
-p target_lang:="English"
```

### Runtime Parameter Updates

```bash
# Change target language to Japanese
ros2 param set /aliyun_translate_node target_lang "Japanese"

# Enable/disable caching
ros2 param set /aliyun_translate_node enable_cache false

# Change input topic
ros2 param set /aliyun_translate_node input_topic "new_input_topic"
```

### Testing the Node

```bash
# Terminal 1: Start translation node
ros2 run aliyun_translate_node aliyun_translate_node

# Terminal 2: Publish test text
ros2 topic pub /text_to_translate std_msgs/msg/String "data: '你好，世界！'"

# Terminal 3: Monitor translation output
ros2 topic echo /translated_text
```

## Performance Features

- **Intelligent Caching**: Identical input text is cached to avoid redundant API calls
- **Retry Mechanism**: Automatic retry with exponential backoff for failed requests
- **Statistics Monitoring**: Real-time tracking of translation success/failure rates
- **Parameter Validation**: API key validation on startup
- **Dynamic Reconfiguration**: All parameters can be updated during runtime

## Error Handling

The node includes comprehensive error handling:

- API key validation on startup
- Network timeout and retry logic
- Malformed response handling
- Input validation (empty text filtering)
- Graceful degradation on API failures
