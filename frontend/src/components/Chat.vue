<template>
  <div class="chat-container">
    <div class="chat-history" ref="chatHistory">
      <div v-for="(message, index) in history" :key="index" class="message">
        <div class="message-time">{{ message.timestamp }}</div>
        <div class="message-content">
          <div class="user-message">{{ message.user }}</div>
          <div class="ai-message">{{ message.ai }}</div>
        </div>
      </div>
    </div>
    <div class="chat-input">
      <textarea
        v-model="userInput"
        @keydown.enter.prevent="sendMessage"
        placeholder="输入消息..."
        rows="3"
      ></textarea>
      <button @click="sendMessage">发送</button>
    </div>
    <div class="chat-actions">
      <button @click="newConversation">新建对话</button>
      <button @click="refreshHistory">刷新历史</button>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'Chat',
  data() {
    return {
      history: [],
      userInput: '',
      apiBaseUrl: 'http://localhost:5000/api'
    }
  },
  methods: {
    async sendMessage() {
      if (!this.userInput.trim()) return;
      
      try {
        const response = await axios.post(`${this.apiBaseUrl}/chat`, {
          message: this.userInput
        });
        
        this.history.push({
          timestamp: response.data.timestamp,
          user: this.userInput,
          ai: response.data.response
        });
        
        this.userInput = '';
        this.$nextTick(() => {
          this.scrollToBottom();
        });
      } catch (error) {
        console.error('发送消息失败:', error);
        alert('发送消息失败，请重试');
      }
    },
    
    async newConversation() {
      try {
        await axios.post(`${this.apiBaseUrl}/new-conversation`);
        this.history = [];
      } catch (error) {
        console.error('新建对话失败:', error);
        alert('新建对话失败，请重试');
      }
    },
    
    async refreshHistory() {
      try {
        const response = await axios.get(`${this.apiBaseUrl}/get-history`);
        this.history = response.data;
        this.$nextTick(() => {
          this.scrollToBottom();
        });
      } catch (error) {
        console.error('刷新历史失败:', error);
        alert('刷新历史失败，请重试');
      }
    },
    
    scrollToBottom() {
      const chatHistory = this.$refs.chatHistory;
      chatHistory.scrollTop = chatHistory.scrollHeight;
    }
  },
  mounted() {
    this.refreshHistory();
  }
}
</script>

<style scoped>
.chat-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.chat-history {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #f5f5f5;
  border-radius: 8px;
  margin-bottom: 20px;
}

.message {
  margin-bottom: 20px;
}

.message-time {
  font-size: 12px;
  color: #666;
  margin-bottom: 5px;
}

.message-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.user-message, .ai-message {
  padding: 10px 15px;
  border-radius: 8px;
  max-width: 80%;
}

.user-message {
  background: #007AFF;
  color: white;
  align-self: flex-end;
}

.ai-message {
  background: white;
  color: #333;
  align-self: flex-start;
}

.chat-input {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

textarea {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  resize: none;
}

button {
  padding: 10px 20px;
  background: #007AFF;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button:hover {
  background: #0056b3;
}

.chat-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
}

.chat-actions button {
  background: #6c757d;
}

.chat-actions button:hover {
  background: #5a6268;
}
</style> 