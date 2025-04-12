import os
from typing import Dict, List

class Config:
    def __init__(self):
        # 从config.txt读取配置
        try:
            print("开始读取配置文件...")  # 添加调试日志
            with open('config.txt', 'r', encoding='utf-8') as f:
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        if key == 'API_KEY':
                            self.API_KEY = value
                        elif key == 'BASE_URL':
                            self.BASE_URL = value
                        elif key == 'MODEL_NAME':
                            self.DEFAULT_MODEL = value
                        elif key == 'AI_ASSISTANT_PROMPT':
                            self.AI_ASSISTANT_PROMPT = value
                        elif key == 'AVAILABLE_MODELS':
                            # 从配置文件中读取模型列表，用逗号分隔
                            self.AVAILABLE_MODELS = [model.strip() for model in value.split(',')]
                            print(f"从配置文件读取到的模型列表: {self.AVAILABLE_MODELS}")  # 添加调试日志
            
            # 如果没有在配置文件中设置模型列表，使用默认值
            if not hasattr(self, 'AVAILABLE_MODELS'):
                self.AVAILABLE_MODELS = [
                    "gpt-3.5-turbo",
                    "gpt-4",
                    "gpt-4-turbo-preview"
                ]
                print("使用默认模型列表")  # 添加调试日志
            
            # 打印最终配置
            print(f"最终配置: API_KEY={self.API_KEY}, BASE_URL={self.BASE_URL}, DEFAULT_MODEL={self.DEFAULT_MODEL}, AVAILABLE_MODELS={self.AVAILABLE_MODELS}")
            
        except FileNotFoundError:
            print("错误: config.txt 文件不存在")
            exit(1)
        except Exception as e:
            print(f"错误: 读取 config.txt 时出错: {e}")
            exit(1)
        
        # 数据目录
        self.DATA_DIR = "data"
        
        # 对话历史文件
        self.CONVERSATIONS_LIST_FILE = os.path.join(self.DATA_DIR, "conversations_list.json")
        
        # 确保数据目录存在
        if not os.path.exists(self.DATA_DIR):
            os.makedirs(self.DATA_DIR)
    
    def validate(self) -> bool:
        """验证配置是否完整"""
        required_configs = [
            self.API_KEY,
            self.BASE_URL,
            self.DEFAULT_MODEL,
            self.AI_ASSISTANT_PROMPT
        ]
        return all(required_configs)
    
    def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        return self.AVAILABLE_MODELS
    
    def is_valid_model(self, model_name: str) -> bool:
        """验证模型名称是否有效"""
        return model_name in self.AVAILABLE_MODELS

# 创建全局配置实例
config = Config() 