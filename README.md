# OurWebAI - AI 对话助手

一个基于 Web 的 AI 对话助手应用，支持多模型切换和对话历史管理等基础功能



### 后端配置
```bash
# 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 安装依赖
cd backend
pip install -r requirements.txt

# 配置 API 密钥
cp config.txt.example config.txt
# 编辑 config.txt 填入你的 API 密钥

# 启动服务
python app.py
```

### 前端配置
```bash
cd frontend
npm install
npm run dev
```
