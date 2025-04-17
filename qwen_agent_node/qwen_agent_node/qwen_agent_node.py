#!/usr/bin/env python3
# qwen_agent_node.py

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

# 导入 QwenAgent 和 MyTools.set_camera_image
from .QwenLangchain import QwenAgent
from .MyTools import set_camera_image
class QwenAgentNode(Node):
    """
    ROS2 节点：订阅 /asr_text （语音识别文本），调用 QwenAgent.chat 获取回复，
    并发布到 /tts_text；同时订阅 /publish_image_source （图像数据），
    将其转换为 OpenCV 图像传给 MyTools。
    """
    def __init__(self):
        super().__init__('qwen_agent_node')

        # 初始化 QwenAgent（开启对话记忆）
        self.agent = QwenAgent(use_memory=True)
        self.agent.chat("你的名字叫“地瓜”,是一个由地瓜机器人公司开发的人工智能体!接下来与我对话的过程中,你的回答应该尽量控制在50字内,情感丰富,表现自然!同时你的回答中不应该包括'你好'这两个字")
        # CvBridge 用于 Image<->CV2 转换
        self.bridge = CvBridge()

        #TODO 订阅 ASR 文本话题
        self.asr_sub = self.create_subscription(
            String,
            '/asr_text',
            self.asr_callback,
            10
        )
        #TODO 订阅 相机图像话题
        self.image_sub = self.create_subscription(
            Image,
            '/publish_image_source',
            self.image_callback,
            10
        )
        #TODO 发布 TTS 文本话题
        self.tts_pub = self.create_publisher(String, '/tts_text', 10)

        self.get_logger().info('QwenAgentNode 已启动，等待 /asr_text 输入...')

    def asr_callback(self, msg: String):
        text = msg.data.strip()
        if not text:
            return

        self.get_logger().info(f"[ASR] 收到: {text}")
        # 调用 QwenAgent 进行对话
        try:
            reply = self.agent.chat(text)
        except Exception as e:
            self.get_logger().error(f"调用 QwenAgent 出错: {e}")
            reply = "对不起，内部出错。"
        # 发布回复
        out_msg = String()
        out_msg.data = reply
        self.tts_pub.publish(out_msg)
        self.get_logger().info(f"[TTS] 发布: {reply}")

    def image_callback(self, msg: Image):
        """
        收到 Image 消息后，转换为 OpenCV 图像并存储到 MyTools.last_image。
        """
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            set_camera_image(cv_image)
        except Exception as e:
            self.get_logger().error(f"图像转换失败: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = QwenAgentNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.get_logger().info('QwenAgentNode 正在关闭...')
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
