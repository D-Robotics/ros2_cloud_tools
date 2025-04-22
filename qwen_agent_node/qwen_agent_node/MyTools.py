import os
import json
from datetime import datetime
from dashscope import MultiModalConversation
from pydantic import BaseModel, Field
from langchain.tools import tool

# 全局存储从 ROS 话题回调设置的最新图像（OpenCV BGR 格式）
last_image = None

def set_camera_image(image):
    """
    ROS 节点在收到 /publish_image_source 的 Image 消息后，
    会调用此函数更新全局 last_image。
    """
    global last_image
    last_image = image

# === 定义工具的输入模型 ===
class ObserveArgs(BaseModel):
    prompt: str = Field(..., description="触发字符串，如 'start' ，开始取用上游话题中的图像并描述。")

# === 重构 observe_surroundings 工具 ===
@tool(
    description="通过上游话题 /publish_image 获取一张图像，并且可以得到描述画面的内容。调用前请发送 'start'。",
    return_direct=False,
    args_schema=ObserveArgs
)
def observe_surroundings_with_camera(prompt: str) -> str:
    from cv2 import resize
    global last_image

    if prompt.lower() != "start":
        return "要开始观察，请输入 'start'。"

    if last_image is None:
        return "尚未收到图像，请检查 /publish_image 话题是否有发布。"

    # 拷贝并调整大小为 (448, 448)
    frame = last_image.copy()
    frame = resize(frame, (448, 448))

    # 保存临时文件
    # output_dir = "/app"
    # os.makedirs(output_dir, exist_ok=True)
    # image_path = os.path.join(output_dir, f"captured4vllm.jpg")
    image_path = "captured4vllm.jpg"
    from cv2 import imwrite
    imwrite(image_path, frame)

    # 调用多模态模型进行描述
    image_uri = f"file://{image_path}"
    messages = [
        {"role": "system", "content": [{"text": "You are an assistant skilled in interpreting images."}]},
        {"role": "user", "content": [{"image": image_uri}, {"text": "请简要描述图像内容，控制在60字内。"}]}
    ]
    resp = MultiModalConversation.call(
        api_key=os.environ["DASHSCOPE_API_KEY"],
        model="qwen-vl-plus-latest",
        messages=messages
    )
    # 提取文本
    description = resp["output"]["choices"][0]["message"]["content"][0]["text"]
    return description


# === 定义 get_current_time 工具 ===
class GetTimeArgs(BaseModel):
    format: str = Field(..., description="时间格式: 'iso' | 'rfc' | 'local'")

from datetime import datetime
@tool(
    description="获取当前时间，输入格式之一: iso, rfc, local，返回对应格式的时间字符串。",
    return_direct=False,
    args_schema=GetTimeArgs
)
def get_current_time(format: str) -> str:
    now = datetime.now()
    if format == "iso":
        return now.isoformat()
    elif format == "rfc":
        return now.strftime("%a, %d %b %Y %H:%M:%S %z")
    else:  # local
        return now.strftime("%Y-%m-%d %H:%M:%S")
