from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import requests
from datetime import datetime

app = Flask(__name__)
CORS(app)  # 启用跨域支持

# 硅基流动 API 配置
API_KEY = "sk-refcdncfiuwuulyyzrtbmgrslcclcoyaqxrxmxxzgnehdchy"  # 硅基流动 API 密钥
BASE_URL = "https://api.siliconflow.cn/v1"
MODEL = "Pro/deepseek-ai/DeepSeek-V3"  # 使用硅基流动支持的模型

# 确保数据目录存在
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# 对话历史文件路径
HISTORY_FILE = os.path.join(DATA_DIR, "conversations.json")

def load_history():
    """加载对话历史"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_history(history):
    """保存对话历史"""
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        message = data.get('message')
        
        if not message:
            return jsonify({"error": "消息不能为空"}), 400

        # 加载历史记录
        history = load_history()
        
        # 构建历史记录文本
        history_text = "以下是我们的对话历史：\n"
        for i, entry in enumerate(history, 1):
            history_text += f"\n第{i}轮对话：\n"
            history_text += f"用户：{entry['user']}\n"
            history_text += f"AI：{entry['ai']}\n"
        
        # 添加当前用户消息
        current_round = len(history) + 1
        history_text += f"\n第{current_round}轮对话：\n"
        history_text += f"用户：{message}\n"
        history_text += "AI："

        # 构建请求数据
        payload = {
            "model": MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": history_text
                }
            ],
            "stream": False,
            "max_tokens": 1024,
            "stop": None,
            "temperature": 0.7,
            "top_p": 0.7,
            "top_k": 50,
            "frequency_penalty": 0.5,
            "n": 1,
            "response_format": {"type": "text"}
        }
        
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        # 打印调试信息
        print("发送到 API 的消息：")
        print(history_text)
        print("\n完整的请求数据：")
        print(json.dumps(payload, ensure_ascii=False, indent=2))

        # 调用硅基流动 API
        response = requests.post(f"{BASE_URL}/chat/completions", json=payload, headers=headers)
        
        if response.status_code != 200:
            print(f"API Error: {response.text}")  # 添加错误日志
            return jsonify({"error": f"API Error: {response.text}"}), response.status_code
            
        response_data = response.json()
        print("\nAPI 响应：")
        print(json.dumps(response_data, ensure_ascii=False, indent=2))
        
        # 获取 AI 响应
        ai_response = response_data['choices'][0]['message']['content']
        
        # 保存对话记录（保持 JSON 格式）
        history.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user": message,
            "ai": ai_response
        })
        save_history(history)
        
        return jsonify({
            "response": ai_response,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")  # 添加错误日志
        return jsonify({"error": str(e)}), 500

@app.route('/api/new-conversation', methods=['POST'])
def new_conversation():
    try:
        # 清空历史记录
        save_history([])
        return jsonify({"message": "对话已重置"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/get-history', methods=['GET'])
def get_history():
    try:
        history = load_history()
        return jsonify(history)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000) 