import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from sensor_msgs.msg import Image, CompressedImage
from cv_bridge import CvBridge
import cv2
import numpy as np
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
        # Declare parameters with default values
        self.declare_parameter('asr_topic', '/asr_text')  # Default ASR topic name
        self.declare_parameter('tts_topic', '/tts_text')  # Default TTS topic name
        self.declare_parameter('image_topic', '/publish_image_source')  # Default TTS topic name
        self.declare_parameter('use_compressed', True) 
        # Retrieve parameter values
        asr_topic = self.get_parameter('asr_topic').get_parameter_value().string_value
        tts_topic = self.get_parameter('tts_topic').get_parameter_value().string_value
        image_topic = self.get_parameter('image_topic').get_parameter_value().string_value
        self.use_compressed = self.get_parameter('use_compressed').value 
        self.get_logger().info(rf'现在使用的asr_topic: {asr_topic}, 现在使用的tts_topic: {tts_topic}, 现在使用的image_topic: {image_topic}, 是否使用use_compressed: {self.use_compressed}')
        #TODO 订阅 ASR 文本话题
        self.asr_sub = self.create_subscription(
            String,
            asr_topic,
            self.asr_callback,
            10
        )
        #TODO 订阅 相机图像话题    
        if self.use_compressed:
            self.get_logger().info('使用 CompressedImage 话题订阅 JPEG 数据')
            self.create_subscription(
                CompressedImage,
                image_topic,
                self.compressed_image_callback,
                10
            )
        else:
            self.get_logger().info('使用 Image 话题订阅原始像素数据')
            self.create_subscription(
                Image,
                image_topic,
                self.image_callback,
                10
            )
        #TODO 发布 TTS 文本话题
        self.tts_pub = self.create_publisher(String, tts_topic, 10)

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
    
    def compressed_image_callback(self, msg: CompressedImage):
        """处理 sensor_msgs/CompressedImage（JPEG 格式）消息"""
        try:
            # ROS2 CompressedImage.data 在 Python 中是 List[int]
            np_arr = np.array(msg.data, dtype=np.uint8)
            cv_img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if cv_img is None:
                raise RuntimeError("JPEG 解码失败")
            set_camera_image(cv_img)
        except Exception as e:
            self.get_logger().error(f"CompressedImage 回调失败: {e}")

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
