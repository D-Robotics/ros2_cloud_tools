#!/usr/bin/env python3
import os
import time
import alsaaudio  # 使用alsaaudio替代pyaudio
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import colorama
import ctypes
# 禁用 PulseAudio，令其无法连接
os.environ["PULSE_SERVER"] = ""
# 初始化 colorama，用于彩色终端输出
colorama.init(autoreset=True)
#TODO 这是LWT个人账号开通的API Key 请不要泄露，防止余额被刷爆
os.environ["DASHSCOPE_API_KEY"] = 'sk-5c3a3354fbbe4dcdb87d080f41154041'

# 导入dashscope的ASR相关模块
from dashscope.audio.asr import Recognition, RecognitionCallback, RecognitionResult

class ASRCallbackClass(RecognitionCallback):
    """
    语音识别回调类，处理语音识别事件和状态
    管理音频设备，以及处理识别结果和唤醒机制
    """
    def __init__(self) -> None:
        """初始化ASR回调类"""
        super().__init__()
        self.stream = None  # 音频输入流对象
        self.asr_text: str = ''  # 当前识别的文本
        self.max_chars: int = 50  # 识别文本的最大字符数
        self.clear_flag: bool = False  # 清除标志，用于判断是否需要清空识别的文本
        self.user_input: str = ''  # 处理后的用户输入
        self.awake_keyword = "你好"  # 唤醒关键词
        self.awoken = False  # 是否已被唤醒
        self.audio_buffer = bytearray()
        self.buffer_size = 3200  # 与原PyAudio设置相同，确保数据块大小一致
        
        # 用于处理唤醒词后的停顿
        self.waiting_for_more = False  # 是否正在等待更多内容
        self.waiting_start_time = 0  # 开始等待的时间戳
        self.waiting_timeout = 3.0  # 最长等待时间(秒)

    def on_open(self):
        """
        开启语音识别器，初始化音频设备
        在识别开始时调用
        """
        print(colorama.Fore.GREEN + '语音识别器已打开。')
        # 避免重复打开设备
        if self.stream is not None:
            try:
                self.stream.close()
            except:
                pass
            
        try:
            # 使用pyalsaaudio替代PyAudio初始化音频设备
            self.stream = alsaaudio.PCM(
                type=alsaaudio.PCM_CAPTURE,  # 音频捕获模式
                mode=alsaaudio.PCM_NONBLOCK,  # 非阻塞模式，提高响应速度
                device='default',  # 使用系统默认音频设备
                channels=1,  # 单声道录音
                rate=16000,  # 采样率16kHz
                format=alsaaudio.PCM_FORMAT_S16_LE,  # 16位小端格式
                periodsize=1600  # 每次读取的样本数量，减小以提高读取频率，这个参数非常影响ASR识别性能，太小的话片段太短了
            )
            # 重置音频缓冲区
            self.audio_buffer = bytearray()
            # 重置等待状态
            self.waiting_for_more = False
            print(colorama.Fore.GREEN + '成功打开音频设备')
        except Exception as e:
            print(colorama.Fore.RED + f'打开音频设备失败: {e}')
            # 尝试列出可用设备以便诊断
            try:
                print("可用音频设备:", alsaaudio.pcms(alsaaudio.PCM_CAPTURE))
            except:
                pass

    def on_close(self):
        """
        关闭语音识别器，释放音频设备资源
        在识别停止时调用
        """
        print(colorama.Fore.RED + '语音识别器已关闭。')
        if self.stream:
            try:
                # 关闭pyalsaaudio的音频流
                self.stream.close()
                self.stream = None
                print(colorama.Fore.YELLOW + '音频设备已关闭')
            except Exception as e:
                print(colorama.Fore.RED + f'关闭音频设备时出错: {e}')

    def on_event(self, result: RecognitionResult):
        """
        处理ASR识别事件回调，更新识别结果并处理唤醒逻辑
        
        Args:
            result: ASR识别结果对象
        """
        # 获取识别句子和是否句子结束的标志
        sentence = result.get_sentence()
        is_end = result.is_sentence_end(sentence)
        
        # 如果需要清空识别文本，则重置
        if self.clear_flag:
            self.clear_flag = False
            self.asr_text = ''

        # 更新当前识别的文本
        self.asr_text = sentence['text']
        
        # 唤醒词检测逻辑
        if not self.awoken and self.awake_keyword in self.asr_text:
            # 检测到唤醒词，设置唤醒状态
            self.awoken = True
            print(colorama.Fore.BLUE + f"检测到唤醒词: {self.awake_keyword}")
            # 启动等待更多内容的计时器
            self.waiting_for_more = True
            self.waiting_start_time = time.time()
        
        # 如果已唤醒且句子结束，处理用户输入
        if self.awoken and is_end:
            # 从识别文本中提取唤醒词后的内容
            idx = self.asr_text.find(self.awake_keyword)
            if idx != -1:
                raw_text = self.asr_text[idx + len(self.awake_keyword):]
                # 去除开头所有中文标点符号和空白字符
                self.user_input = raw_text.lstrip(' ，。,.')
            else:
                self.user_input = self.asr_text.strip()

            # 检查是否只是唤醒词，或者用户输入内容为空
            if not self.user_input or self.user_input.isspace():
                # 如果只有唤醒词，但还没超时，继续等待更多内容
                if self.waiting_for_more and (time.time() - self.waiting_start_time < self.waiting_timeout):
                    print(colorama.Fore.YELLOW + f"检测到唤醒词后无内容，等待更多输入... ({int(self.waiting_timeout - (time.time() - self.waiting_start_time))}秒)")
                    return  # 继续等待，不重置唤醒状态
                else:
                    # 如果等待超时，重置等待状态
                    self.waiting_for_more = False
            else:
                # 有实际内容，停止等待
                self.waiting_for_more = False
                print(colorama.Fore.GREEN + f"接收到用户指令: {self.user_input}")

            # 如果识别文本长度超过最大字符数，标记需要清空
            if len(self.asr_text) > self.max_chars:
                self.clear_flag = True
                
            # 完成处理后重置唤醒状态，除非仍在等待更多内容
            if not self.waiting_for_more:
                self.awoken = False

class ASRNode(Node):
    """
    ROS2节点类，负责创建和管理语音识别服务
    将识别结果发布到ROS话题
    """
    def __init__(self):
        """初始化ASR节点，设置发布者和定时器"""
        super().__init__('asr_node')
        # Declare parameters
        self.declare_parameter('pub_topic_name', "/asr_text")

        # Get parameter values
        self.pub_topic_name = self.get_parameter('pub_topic_name').get_parameter_value().string_value

        # 创建ROS发布者，用于发布识别到的文本
        self.publisher = self.create_publisher(String, self.pub_topic_name, 10)
        self.get_logger().info('ASR 节点启动成功。')

        # 创建ASR回调对象
        self.asr_callback = ASRCallbackClass()
        # 不在这里调用on_open，因为Recognition.start()会自动调用它
        # 避免设备被打开两次

        # 初始化识别器
        self.recognition = Recognition(
            model='paraformer-realtime-v1',  # 使用实时语音识别模型
            format='pcm',  # PCM音频格式
            sample_rate=16000,  # 16kHz采样率
            callback=self.asr_callback  # 设置回调对象
        )
        # 启动识别服务
        self.recognition.start()
        # 跟踪上一次的识别结果，用于检测变化
        self.last_asr_result = ''
        # 创建定时器，定期调用timer_callback函数处理音频数据
        self.timer = self.create_timer(0.1, self.timer_callback)

    def timer_callback(self):
        if self.asr_callback.stream is not None:
            try:
                # 读取多次，积累足够的数据
                for _ in range(5):  # 多次读取以获取足够的数据
                    try:
                        # 使用pyalsaaudio的read方法，返回(长度,数据)元组
                        length, data = self.asr_callback.stream.read()
                        if length > 0:  # 只在实际读取到数据时处理
                            # 将读取的数据追加到缓冲区
                            self.asr_callback.audio_buffer.extend(data)
                    except alsaaudio.ALSAAudioError as e:
                        if "Resource temporarily unavailable" not in str(e):
                            self.get_logger().error(f"ALSA音频读取错误: {e}")
                        # 这个错误在非阻塞模式下是正常的，表示没有新数据
                        break
                
                # 如果缓冲区积累了足够的数据，发送到ASR引擎
                if len(self.asr_callback.audio_buffer) >= self.asr_callback.buffer_size:
                    # 提取一个完整的音频块
                    audio_chunk = bytes(self.asr_callback.audio_buffer[:self.asr_callback.buffer_size])
                    # 发送到ASR引擎
                    self.recognition.send_audio_frame(audio_chunk)
                    # 保留剩余的数据
                    self.asr_callback.audio_buffer = self.asr_callback.audio_buffer[self.asr_callback.buffer_size:]
                
                # 检查是否有新的识别结果
                if self.asr_callback.user_input and (self.asr_callback.user_input != self.last_asr_result):
                    self.last_asr_result = self.asr_callback.user_input
                    msg = String()
                    msg.data = self.last_asr_result
                    self.publisher.publish(msg)
                    self.get_logger().info(f"发布 ASR 文本: {self.last_asr_result}")
                    # 清空用户输入以避免重复处理
                    self.asr_callback.user_input = ""
                    
                    # 重置识别器和缓冲区
                    self.recognition.stop()
                    self.asr_callback.audio_buffer = bytearray()
                    time.sleep(0.1)
                    self.recognition.start()
                    
            except Exception as e:
                self.get_logger().error(f"处理音频数据时出错: {e}")
                # 如果遇到严重错误，尝试重新初始化
                try:
                    self.asr_callback.on_close()
                    time.sleep(0.5)
                    self.asr_callback.on_open()
                except Exception as re_err:
                    self.get_logger().error(f"重新初始化音频设备失败: {re_err}")
            if self.asr_callback.user_input and (self.asr_callback.user_input != self.last_asr_result):
                self.last_asr_result = self.asr_callback.user_input
                msg = String()
                msg.data = self.last_asr_result
                self.publisher.publish(msg)
                self.get_logger().info(f"发布 ASR 文本: {self.last_asr_result}")
                self.recognition.stop()
                time.sleep(0.1)
                self.recognition.start()

    def destroy_node(self):
        self.recognition.stop()
        self.asr_callback.on_close()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = ASRNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("ASR 节点即将关闭。")
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
