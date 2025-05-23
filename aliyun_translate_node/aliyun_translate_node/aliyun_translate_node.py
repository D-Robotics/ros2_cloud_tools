#!/usr/bin/env python3
"""
阿里云翻译节点
使用DASHSCOPE API进行文本翻译的ROS2节点
订阅输入文本话题，翻译后发布到输出文本话题
"""
import os
import sys
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from rclpy.parameter import Parameter
import dashscope
import colorama

# 初始化 colorama，用于彩色终端输出
colorama.init(autoreset=True)


class AliyunTranslateNode(Node):
    """
    阿里云翻译ROS节点类
    提供文本翻译服务，支持多种语言互译
    """
    
    def __init__(self):
        """初始化翻译节点，设置参数、订阅者和发布者"""
        super().__init__('aliyun_translate_node')
        
        # 声明ROS参数，提供灵活的配置选项
        self.declare_parameter('api_key', '')  # DASHSCOPE API Key，为空时使用环境变量
        self.declare_parameter('model', 'qwen-mt-turbo')  # 翻译模型名称
        self.declare_parameter('source_lang', 'auto')  # 源语言，auto为自动检测
        self.declare_parameter('target_lang', 'English')  # 目标语言
        self.declare_parameter('input_topic', 'text_to_translate')  # 输入文本话题名
        self.declare_parameter('output_topic', 'translated_text')  # 输出文本话题名
        self.declare_parameter('result_format', 'message')  # 结果格式
        self.declare_parameter('enable_cache', True)  # 是否启用翻译缓存
        self.declare_parameter('max_retry_count', 3)  # 最大重试次数
        self.declare_parameter('retry_delay', 1.0)  # 重试延迟时间(秒)
        
        # 获取参数值
        self.api_key = self.get_parameter('api_key').value
        self.model = self.get_parameter('model').value
        self.source_lang = self.get_parameter('source_lang').value
        self.target_lang = self.get_parameter('target_lang').value
        self.input_topic = self.get_parameter('input_topic').value
        self.output_topic = self.get_parameter('output_topic').value
        self.result_format = self.get_parameter('result_format').value
        self.enable_cache = self.get_parameter('enable_cache').value
        self.max_retry_count = self.get_parameter('max_retry_count').value
        self.retry_delay = self.get_parameter('retry_delay').value
        
        # 设置API Key，优先使用参数，其次使用环境变量
        if self.api_key:
            os.environ["DASHSCOPE_API_KEY"] = self.api_key
            self.get_logger().info("使用参数中的API Key")
        elif os.getenv('DASHSCOPE_API_KEY'):
            self.get_logger().info("使用环境变量中的API Key")
        else:
            self.get_logger().error("未找到DASHSCOPE API Key！请设置api_key参数或DASHSCOPE_API_KEY环境变量")
            return
        
        # 验证API Key
        if not self.validate_api_key():
            self.get_logger().error("API Key验证失败，节点将无法正常工作")
            return
            
        # 创建参数回调函数，支持运行时参数修改
        self.add_on_set_parameters_callback(self.parameters_callback)
        
        # 创建订阅者，订阅需要翻译的文本
        self.subscription = self.create_subscription(
            String,
            self.input_topic,
            self.translate_callback,
            10  # 队列大小
        )
        
        # 创建发布者，发布翻译结果
        self.publisher = self.create_publisher(String, self.output_topic, 10)
        
        # 翻译缓存，避免重复翻译相同内容
        self.translation_cache = {}
        
        # 统计信息
        self.translation_count = 0
        self.error_count = 0
        self.cache_hit_count = 0
        
        self.get_logger().info(f'阿里云翻译节点启动成功')
        self.get_logger().info(f'订阅话题: {self.input_topic}')
        self.get_logger().info(f'发布话题: {self.output_topic}')
        self.get_logger().info(f'翻译方向: {self.source_lang} -> {self.target_lang}')
        self.get_logger().info(f'使用模型: {self.model}')
        
        # 创建定时器，定期输出统计信息
        self.stats_timer = self.create_timer(60.0, self.print_statistics)

    def validate_api_key(self):
        """
        验证API Key是否有效
        
        Returns:
            bool: API Key是否有效
        """
        try:
            # 尝试进行一个简单的翻译请求来验证API Key
            test_messages = [{"role": "user", "content": "test"}]
            test_options = {
                "source_lang": "auto",
                "target_lang": "English"
            }
            
            response = dashscope.Generation.call(
                api_key=os.getenv('DASHSCOPE_API_KEY'),
                model=self.model,
                messages=test_messages,
                result_format=self.result_format,
                translation_options=test_options
            )
            
            if response.status_code == 200:
                self.get_logger().info("API Key验证成功")
                return True
            else:
                self.get_logger().error(f"API Key验证失败: {response.message}")
                return False
                
        except Exception as e:
            self.get_logger().error(f"API Key验证时发生错误: {str(e)}")
            return False

    def parameters_callback(self, params):
        """
        参数回调函数，当ROS参数被修改时调用
        
        Args:
            params: 被修改的参数列表
        
        Returns:
            bool: 参数设置是否成功
        """
        for param in params:
            if param.name == 'api_key':
                self.api_key = param.value
                if param.value:
                    os.environ["DASHSCOPE_API_KEY"] = param.value
                    self.get_logger().info('已更新API Key')
                    
            elif param.name == 'model':
                self.model = param.value
                self.get_logger().info(f'更新翻译模型为: {param.value}')
                
            elif param.name == 'source_lang':
                self.source_lang = param.value
                self.get_logger().info(f'更新源语言为: {param.value}')
                # 清空缓存，因为语言设置改变了
                self.translation_cache.clear()
                
            elif param.name == 'target_lang':
                self.target_lang = param.value
                self.get_logger().info(f'更新目标语言为: {param.value}')
                # 清空缓存，因为语言设置改变了
                self.translation_cache.clear()
                
            elif param.name == 'input_topic':
                # 重新创建订阅者
                self.destroy_subscription(self.subscription)
                self.input_topic = param.value
                self.subscription = self.create_subscription(
                    String, self.input_topic, self.translate_callback, 10
                )
                self.get_logger().info(f'更新输入话题为: {param.value}')
                
            elif param.name == 'output_topic':
                # 重新创建发布者
                self.destroy_publisher(self.publisher)
                self.output_topic = param.value
                self.publisher = self.create_publisher(String, self.output_topic, 10)
                self.get_logger().info(f'更新输出话题为: {param.value}')
                
            elif param.name == 'result_format':
                self.result_format = param.value
                self.get_logger().info(f'更新结果格式为: {param.value}')
                
            elif param.name == 'enable_cache':
                self.enable_cache = param.value
                if not param.value:
                    self.translation_cache.clear()
                    self.get_logger().info('翻译缓存已禁用并清空')
                else:
                    self.get_logger().info('翻译缓存已启用')
                    
            elif param.name == 'max_retry_count':
                self.max_retry_count = param.value
                self.get_logger().info(f'更新最大重试次数为: {param.value}')
                
            elif param.name == 'retry_delay':
                self.retry_delay = param.value
                self.get_logger().info(f'更新重试延迟为: {param.value}秒')
        
        return True

    def translate_callback(self, msg):
        """
        翻译回调函数，处理接收到的文本并进行翻译
        
        Args:
            msg: 接收到的String消息
        """
        input_text = msg.data.strip()
        
        # 检查输入文本是否为空
        if not input_text:
            self.get_logger().warn("接收到空文本，跳过翻译")
            return
            
        self.get_logger().info(f"接收到待翻译文本: {input_text}")
        
        # 检查缓存
        if self.enable_cache and input_text in self.translation_cache:
            translated_text = self.translation_cache[input_text]
            self.cache_hit_count += 1
            self.get_logger().info(f"使用缓存翻译结果: {translated_text}")
            self.publish_translation(translated_text)
            return
        
        # 进行翻译
        translated_text = self.translate_text(input_text)
        
        if translated_text:
            # 缓存翻译结果
            if self.enable_cache:
                self.translation_cache[input_text] = translated_text
                
            # 发布翻译结果
            self.publish_translation(translated_text)
            
            # 更新统计
            self.translation_count += 1
            self.get_logger().info(f"翻译成功: {input_text} -> {translated_text}")
        else:
            self.error_count += 1
            self.get_logger().error(f"翻译失败: {input_text}")

    def translate_text(self, text):
        """
        使用DASHSCOPE API翻译文本
        
        Args:
            text: 需要翻译的文本
            
        Returns:
            str: 翻译后的文本，失败时返回None
        """
        # 构建消息格式
        messages = [
            {
                "role": "user",
                "content": text
            }
        ]
        
        # 构建翻译选项
        translation_options = {
            "source_lang": self.source_lang,
            "target_lang": self.target_lang,
        }
        
        # 重试机制
        for attempt in range(self.max_retry_count + 1):
            try:
                self.get_logger().debug(f"尝试翻译 (第{attempt + 1}次): {text}")
                
                # 调用DASHSCOPE API
                response = dashscope.Generation.call(
                    api_key=os.getenv('DASHSCOPE_API_KEY'),
                    model=self.model,
                    messages=messages,
                    result_format=self.result_format,
                    translation_options=translation_options
                )
                
                # 检查响应状态
                if response.status_code == 200:
                    # 提取翻译结果
                    translated_text = response.output.choices[0].message.content
                    self.get_logger().debug(f"API响应成功: {translated_text}")
                    return translated_text
                else:
                    error_msg = f"API请求失败: 状态码 {response.status_code}, 消息: {response.message}"
                    self.get_logger().error(error_msg)
                    
                    # 如果是最后一次尝试，返回None
                    if attempt == self.max_retry_count:
                        return None
                        
            except Exception as e:
                error_msg = f"翻译时发生异常: {str(e)}"
                self.get_logger().error(error_msg)
                
                # 如果是最后一次尝试，返回None
                if attempt == self.max_retry_count:
                    return None
            
            # 等待后重试
            if attempt < self.max_retry_count:
                self.get_logger().info(f"等待 {self.retry_delay} 秒后重试...")
                time.sleep(self.retry_delay)
        
        return None

    def publish_translation(self, translated_text):
        """
        发布翻译结果
        
        Args:
            translated_text: 翻译后的文本
        """
        msg = String()
        msg.data = translated_text
        self.publisher.publish(msg)
        self.get_logger().debug(f"已发布翻译结果: {translated_text}")

    def print_statistics(self):
        """定期打印统计信息"""
        self.get_logger().info(
            f"翻译统计 - 成功: {self.translation_count}, "
            f"失败: {self.error_count}, "
            f"缓存命中: {self.cache_hit_count}, "
            f"缓存大小: {len(self.translation_cache)}"
        )

    def get_supported_languages(self):
        """
        获取支持的语言列表（供参考）
        
        Returns:
            dict: 支持的语言映射
        """
        return {
            'auto': '自动检测',
            'Chinese': '中文',
            'English': '英文',
            'Japanese': '日文',
            'Korean': '韩文',
            'French': '法文',
            'German': '德文',
            'Spanish': '西班牙文',
            'Russian': '俄文',
            'Arabic': '阿拉伯文',
            'Italian': '意大利文',
            'Portuguese': '葡萄牙文',
            'Thai': '泰文',
            'Vietnamese': '越南文'
        }

    def destroy_node(self):
        """节点销毁时的清理工作"""
        self.get_logger().info("翻译节点正在关闭...")
        self.print_statistics()
        super().destroy_node()


def main(args=None):
    """
    主函数，启动翻译节点
    
    Args:
        args: 命令行参数
    """
    # 初始化ROS系统
    rclpy.init(args=args)
    
    # 创建翻译节点
    translate_node = AliyunTranslateNode()
    
    try:
        # 进入ROS事件循环
        rclpy.spin(translate_node)
    except KeyboardInterrupt:
        # 捕获Ctrl+C退出信号
        translate_node.get_logger().info("翻译节点即将关闭...")
    finally:
        # 确保正确清理资源
        translate_node.destroy_node()
        # 关闭ROS系统
        rclpy.shutdown()


if __name__ == '__main__':
    # 作为脚本直接运行时执行main函数
    main()