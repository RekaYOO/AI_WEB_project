from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import requests
from datetime import datetime
import uuid

app = Flask(__name__)
CORS(app)  # 启用跨域支持

# 硅基流动 API 配置
API_KEY = "sk-refcdncfiuwuulyyzrtbmgrslcclcoyaqxrxmxxzgnehdchy"  # 硅基流动 API 密钥
BASE_URL = "https://api.siliconflow.cn/v1"
MODEL = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"  # 使用硅基流动支持的模型

# AI 助手设定
AI_ASSISTANT_PROMPT = """你是一个AI助手，这是你的设定：
1. 你是由经管6班Reka开发的一个友好、专业、有礼貌的AI助手。
2. 你会用简洁、清晰的语言回答问题
3. 你不会编造信息，如果不知道就说不知道
4. 你会保持对话的连贯性和上下文理解
5. 你会用中文回复，除非用户特别要求使用其他语言
6. 你不会涉及任何违法、不当或有害的内容
7. 你会尊重用户的隐私和个人信息

在接下来与用户的对话中你需要严格遵守设定，以下是你们的对话："""

def clean_ai_response(response):
    """清理 AI 响应中的设定文本"""
    if response.startswith(AI_ASSISTANT_PROMPT):
        response = response[len(AI_ASSISTANT_PROMPT):].strip()
    return response

# 确保数据目录存在
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# 对话历史文件路径
CONVERSATIONS_LIST_FILE = os.path.join(DATA_DIR, "conversations_list.json")

def load_conversations_list():
    """加载对话列表"""
    if os.path.exists(CONVERSATIONS_LIST_FILE):
        with open(CONVERSATIONS_LIST_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_conversations_list(conversations_list):
    """保存对话列表"""
    with open(CONVERSATIONS_LIST_FILE, 'w', encoding='utf-8') as f:
        json.dump(conversations_list, f, ensure_ascii=False, indent=2)

def load_history(conversation_id):
    """加载指定对话的历史记录"""
    history_file = os.path.join(DATA_DIR, f"conversation_{conversation_id}.json")
    if os.path.exists(history_file):
        with open(history_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_history(conversation_id, history):
    """保存指定对话的历史记录"""
    history_file = os.path.join(DATA_DIR, f"conversation_{conversation_id}.json")
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

@app.route('/api/conversations', methods=['GET'])
def get_conversations():
    """获取所有对话列表"""
    try:
        conversations = load_conversations_list()
        return jsonify(conversations)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/conversations', methods=['POST'])
def create_conversation():
    """创建新对话"""
    try:
        conversation_id = str(uuid.uuid4())
        title = f"新对话 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # 创建新的对话记录
        conversations = load_conversations_list()
        conversations.append({
            "id": conversation_id,
            "title": title,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        save_conversations_list(conversations)
        
        # 创建空的对话历史
        save_history(conversation_id, [])
        
        return jsonify({
            "id": conversation_id,
            "title": title
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/conversations/<conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    """删除对话"""
    try:
        # 删除对话历史文件
        history_file = os.path.join(DATA_DIR, f"conversation_{conversation_id}.json")
        if os.path.exists(history_file):
            os.remove(history_file)
        
        # 从对话列表中移除
        conversations = load_conversations_list()
        conversations = [c for c in conversations if c["id"] != conversation_id]
        save_conversations_list(conversations)
        
        return jsonify({"message": "对话已删除"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        message = data.get('message')
        conversation_id = data.get('conversation_id')
        
        if not message:
            return jsonify({"error": "消息不能为空"}), 400
            
        if not conversation_id:
            return jsonify({"error": "对话ID不能为空"}), 400

        # 加载历史记录
        history = load_history(conversation_id)
        
        # 构建历史记录文本
        history_text = AI_ASSISTANT_PROMPT + "\n\n以下是我们的对话历史：\n"
        for i, entry in enumerate(history, 1):
            history_text += f"\n第{i}轮对话：\n"
            history_text += f"用户：{entry['user']}\n"
            history_text += f"AI：{entry['ai']}\n"
        
        # 添加当前用户消息
        current_round = len(history) + 1
        history_text += f"\n以上是我们之前的聊天，现在请你回复我最新的消息：\n"
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
        
        # 获取 AI 响应并清理设定文本
        ai_response = response_data['choices'][0]['message']['content']
        cleaned_response = clean_ai_response(ai_response)
        
        # 保存对话记录（保持 JSON 格式）
        history.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user": message,
            "ai": cleaned_response
        })
        save_history(conversation_id, history)
        
        # 更新对话列表中的更新时间
        conversations = load_conversations_list()
        for conv in conversations:
            if conv["id"] == conversation_id:
                conv["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                break
        save_conversations_list(conversations)
        
        return jsonify({
            "response": cleaned_response,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")  # 添加错误日志
        return jsonify({"error": str(e)}), 500

@app.route('/api/conversations/<conversation_id>/history', methods=['GET'])
def get_conversation_history(conversation_id):
    """获取指定对话的历史记录"""
    try:
        history = load_history(conversation_id)
        return jsonify(history)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000) 