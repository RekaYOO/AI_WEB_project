from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import requests
from datetime import datetime
import uuid
from config import config

app = Flask(__name__)
CORS(app)  # 启用跨域支持

# 确保配置完整
if not config.validate():
    print("配置不完整，请检查环境变量")
    exit(1)

def clean_ai_response(response):
    """清理 AI 响应中的设定文本"""
    if response.startswith(config.AI_ASSISTANT_PROMPT):
        response = response[len(config.AI_ASSISTANT_PROMPT):].strip()
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
        try:
            with open(CONVERSATIONS_LIST_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("对话列表文件损坏，创建新的对话列表")
            return []
    return []

def save_conversations_list(conversations_list):
    """保存对话列表"""
    try:
        with open(CONVERSATIONS_LIST_FILE, 'w', encoding='utf-8') as f:
            json.dump(conversations_list, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存对话列表失败: {e}")

def load_history(conversation_id):
    """加载指定对话的历史记录"""
    history_file = os.path.join(DATA_DIR, f"conversation_{conversation_id}.json")
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"对话历史文件 {conversation_id} 损坏，创建新的历史记录")
            return []
    return []

def save_history(conversation_id, history):
    """保存指定对话的历史记录"""
    try:
        history_file = os.path.join(DATA_DIR, f"conversation_{conversation_id}.json")
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存对话历史失败: {e}")

def init_app():
    """初始化应用"""
    try:
        conversations = load_conversations_list()
        print(f"已加载 {len(conversations)} 个对话")
        for conv in conversations:
            history = load_history(conv["id"])
            print(f"对话 {conv['id']} 已加载 {len(history)} 条历史记录")
    except Exception as e:
        print(f"加载对话失败: {e}")

# 初始化应用
init_app()

@app.route('/api/conversations', methods=['GET'])
def get_conversations():
    """获取所有对话列表"""
    try:
        conversations = load_conversations_list()
        return jsonify(conversations)
    except Exception as e:
        print(f"获取对话列表失败: {e}")  # 添加错误日志
        return jsonify({"error": str(e)}), 500

@app.route('/api/conversations', methods=['POST'])
def create_conversation():
    """创建新对话"""
    try:
        conversation_id = str(uuid.uuid4())
        title = f"新对话 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # 创建新的对话记录
        conversations = load_conversations_list()
        new_conversation = {
            "id": conversation_id,
            "title": title,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        conversations.append(new_conversation)
        
        # 保存对话列表
        save_conversations_list(conversations)
        
        # 创建空的对话历史
        save_history(conversation_id, [])
        
        print(f"创建新对话成功: {conversation_id}")  # 添加成功日志
        return jsonify(new_conversation)
    except Exception as e:
        print(f"创建新对话失败: {e}")  # 添加错误日志
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

def summarize_conversation(history):
    """总结对话主题"""
    try:
        # 构建提示词
        prompt = "请总结以下对话的主题，用简短的一句话描述（不超过10个字）：\n\n"
        for entry in history:
            prompt += f"用户: {entry['user']}\n"
            prompt += f"AI: {entry['ai']}\n"
        
        # 调用API获取总结
        response = requests.post(
            f"{config.BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {config.API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": config.DEFAULT_MODEL,
                "messages": [
                    {"role": "system", "content": "你是一个专业的对话总结助手，请用简短的几个词总结对话主题。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        else:
            print(f"总结主题失败: {response.text}")
            return None
    except Exception as e:
        print(f"总结主题时出错: {str(e)}")
        return None

@app.route('/api/default_model', methods=['GET'])
def get_default_model():
    """获取默认模型"""
    return jsonify(config.DEFAULT_MODEL)

@app.route('/api/models', methods=['GET'])
def get_available_models():
    """获取可用的模型列表"""
    return jsonify(config.get_available_models())

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        print("接收到的请求数据:", data)  # 添加调试日志
        
        message = data.get('message')
        conversation_id = data.get('conversation_id')
        model_name = data.get('model_name', config.DEFAULT_MODEL)
        
        print(f"解析后的参数: message={message}, conversation_id={conversation_id}, model_name={model_name}")  # 添加调试日志
        
        if not message or not conversation_id:
            print("错误: 消息或对话ID为空")  # 添加调试日志
            return jsonify({'error': '消息和对话ID不能为空'}), 400
            
        # 验证模型名称是否有效
        if not config.is_valid_model(model_name):
            print(f"错误: 无效的模型名称 {model_name}")  # 添加调试日志
            return jsonify({'error': '无效的模型名称'}), 400
            
        # 加载对话历史
        history = load_history(conversation_id)
        if not history:
            history = []
            
        # 构建消息历史
        messages = [
            {"role": "system", "content": config.AI_ASSISTANT_PROMPT}
        ]
        
        # 添加历史消息
        for entry in history:
            messages.append({"role": "user", "content": entry['user']})
            messages.append({"role": "assistant", "content": entry['ai']})
            
        # 添加当前消息
        messages.append({"role": "user", "content": message})
        
        # 调用API
        response = requests.post(
            f"{config.BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {config.API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": model_name,
                "messages": messages,
                "temperature": 0.7
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result['choices'][0]['message']['content']
            reasoning_content = result['choices'][0]['message'].get('reasoning_content', '')
            
            # 保存对话记录
            history.append({
                'user': message,
                'ai': ai_response,
                'reasoning': reasoning_content,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            
            # 如果对话次数达到3次，尝试更新主题
            if len(history) >= 3:
                new_title = summarize_conversation(history)
                if new_title:
                    # 更新对话列表中的标题
                    conversations_list = load_conversations_list()
                    for conv in conversations_list:
                        if conv['id'] == conversation_id:
                            conv['title'] = new_title
                            break
                    save_conversations_list(conversations_list)
            
            save_history(conversation_id, history)
            
            return jsonify({
                'response': ai_response,
                'reasoning_content': reasoning_content,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        else:
            print(f"API调用失败: {response.text}")
            return jsonify({'error': 'AI响应失败'}), 500
            
    except Exception as e:
        print(f"处理消息时出错: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

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