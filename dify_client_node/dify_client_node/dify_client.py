import json
import os
import requests
import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from collections import Counter

from std_msgs.msg import String



class DifyClientNode(Node):
    def __init__(self):
        super().__init__('dify_client_node')
        self.get_logger().warn('Dify Client Node has been started.')

        self.url = "https://api.dify.ai/v1/chat-messages"
        self.key = os.getenv("DIFY_KEY")
        if self.key == None:
            self.get_logger().error(f'dify key should not be none.')
            self.get_logger().error(f'Please set Dify Key like: export DIFY_KEY=app-xxx')
            return

        # Declare parameters
        self.declare_parameter('asr_msg_sub_topic_name', "/asr_text")
        self.declare_parameter('string_msg_pub_topic_name', '/tts_text')

        # Get parameter values
        self.asr_msg_sub_topic_name = self.get_parameter('asr_msg_sub_topic_name').get_parameter_value().string_value
        self.string_msg_pub_topic_name = self.get_parameter('string_msg_pub_topic_name').get_parameter_value().string_value

        self.subscription_asr = self.create_subscription(
            String,
            self.asr_msg_sub_topic_name,
            self.asr_callback,
            10
        )

        self.publisher = self.create_publisher(String, self.string_msg_pub_topic_name, 10)

    def client(self, query: str, user: str = "abc-123"):

        headers = {
            "Authorization": "Bearer " + self.key ,
            "Content-Type": "application/json"
        }
        payload = {
            "inputs": {},
            "query": query,
            "response_mode": "blocking",
            "conversation_id": "",
            "user": user
        }

        response = requests.post(self.url, headers=headers, data=json.dumps(payload))

        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer") or data.get("data", {}).get("outputs", {}).get("answer")
            return answer
        else:
            return None


    def asr_callback(self, msg: String):
        
        if msg.data == None:
            self.get_logger().error(f'收到ASR文本为空.')
            return

        self.get_logger().info(f'收到ASR文本: {msg.data}')
        answer = self.client(msg.data)

        self.get_logger().warn(f'{answer}')

        self.publish_result(answer)

    def publish_result(self, text: str):
        """
        辅助函数：向 /tts_text 话题发布文本。
        """
        msg = String()
        msg.data = text
        self.publisher.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = DifyClientNode()
    executor = MultiThreadedExecutor()
    rclpy.spin(node, executor=executor)

    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
