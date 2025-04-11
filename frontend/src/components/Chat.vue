<template>
  <div class="chat-container">
    <div class="conversations-sidebar">
      <button class="new-conversation-btn" @click="createNewConversation">新建对话</button>
      <div class="conversations-list">
        <div 
          v-for="conv in conversations" 
          :key="conv.id" 
          class="conversation-item"
          :class="{ active: currentConversationId === conv.id }"
          @click="switchConversation(conv.id)"
        >
          <span class="conversation-title">{{ conv.title }}</span>
          <button class="delete-btn" @click.stop="deleteConversation(conv.id)">×</button>
        </div>
      </div>
    </div>
    <div class="chat-main">
      <div class="chat-messages" ref="messagesContainer">
        <div v-for="(message, index) in messages" :key="index" class="message">
          <div class="message-wrapper" :class="{ 'user-message': message.isUser }">
            <div class="avatar" v-if="!message.isUser">
              <img src="@/assets/images/head.jpg" alt="AI Avatar">
            </div>
            <div class="message-content" v-html="renderMarkdown(message.content)"></div>
          </div>
        </div>
        <!-- 添加加载状态显示 -->
        <div v-if="isLoading" class="message">
          <div class="message-wrapper">
            <div class="avatar">
              <img src="@/assets/images/head.jpg" alt="AI Avatar">
            </div>
            <div class="message-content ai-message loading">
              <div class="loading-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="chat-input-container">
        <div class="chat-input">
          <input 
            type="text" 
            v-model="newMessage" 
            @keyup.enter="sendMessage"
            placeholder="输入消息..."
            :disabled="isLoading || !currentConversationId"
          >
          <button @click="sendMessage" :disabled="isLoading || !currentConversationId">发送</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { marked } from 'marked';
import hljs from 'highlight.js';
import 'highlight.js/styles/github-dark.css';

export default {
  name: 'Chat',
  data() {
    return {
      messages: [],
      newMessage: '',
      isLoading: false,
      apiUrl: 'http://localhost:5000/api',
      conversations: [],
      currentConversationId: null
    }
  },
  methods: {
    renderMarkdown(content) {
      // 配置 marked
      marked.setOptions({
        highlight: function(code, lang) {
          if (lang && hljs.getLanguage(lang)) {
            try {
              return hljs.highlight(code, { language: lang }).value;
            } catch (__) {}
          }
          return hljs.highlightAuto(code).value;
        },
        breaks: true,
        gfm: true
      });

      // 渲染 Markdown
      return marked(content);
    },
    async loadConversations() {
      try {
        const response = await fetch(`${this.apiUrl}/conversations`);
        if (!response.ok) throw new Error('加载对话列表失败');
        this.conversations = await response.json();
      } catch (error) {
        console.error('Error:', error);
        alert('加载对话列表失败，请重试');
      }
    },
    async createNewConversation() {
      try {
        const response = await fetch(`${this.apiUrl}/conversations`, {
          method: 'POST'
        });
        if (!response.ok) throw new Error('创建对话失败');
        const data = await response.json();
        this.conversations.push(data);
        this.switchConversation(data.id);
      } catch (error) {
        console.error('Error:', error);
        alert('创建对话失败，请重试');
      }
    },
    async deleteConversation(conversationId) {
      if (!confirm('确定要删除这个对话吗？')) return;
      
      try {
        const response = await fetch(`${this.apiUrl}/conversations/${conversationId}`, {
          method: 'DELETE'
        });
        if (!response.ok) throw new Error('删除对话失败');
        
        this.conversations = this.conversations.filter(c => c.id !== conversationId);
        if (this.currentConversationId === conversationId) {
          this.currentConversationId = null;
          this.messages = [];
        }
      } catch (error) {
        console.error('Error:', error);
        alert('删除对话失败，请重试');
      }
    },
    async switchConversation(conversationId) {
      this.currentConversationId = conversationId;
      this.messages = [];
      this.newMessage = '';
      
      try {
        const response = await fetch(`${this.apiUrl}/conversations/${conversationId}/history`);
        if (!response.ok) throw new Error('加载对话历史失败');
        const history = await response.json();
        
        this.messages = history.map(entry => [
          { content: entry.user, isUser: true, timestamp: entry.timestamp },
          { content: entry.ai, isUser: false, timestamp: entry.timestamp }
        ]).flat();
        
        // 滚动到最新消息
        this.scrollToBottom();
      } catch (error) {
        console.error('Error:', error);
        alert('加载对话历史失败，请重试');
      }
    },
    async sendMessage() {
      if (!this.newMessage.trim() || this.isLoading || !this.currentConversationId) return;
      
      // 立即显示用户消息
      this.messages.push({
        content: this.newMessage,
        isUser: true,
        timestamp: new Date().toLocaleString()
      });
      
      // 滚动到最新消息
      this.scrollToBottom();
      
      const messageToSend = this.newMessage;
      this.newMessage = '';
      this.isLoading = true;
      
      try {
        const response = await fetch(`${this.apiUrl}/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ 
            message: messageToSend,
            conversation_id: this.currentConversationId
          })
        });
        
        if (!response.ok) {
          throw new Error('发送消息失败');
        }
        
        const data = await response.json();
        
        // 添加 AI 回复
        this.messages.push({
          content: data.response,
          isUser: false,
          timestamp: data.timestamp
        });
        
        // 滚动到最新消息
        this.scrollToBottom();
      } catch (error) {
        console.error('Error:', error);
        this.messages.push({
          content: '抱歉，发送消息失败，请重试',
          isUser: false,
          timestamp: new Date().toLocaleString()
        });
        // 滚动到最新消息
        this.scrollToBottom();
      } finally {
        this.isLoading = false;
      }
    },
    scrollToBottom() {
      const container = this.$refs.messagesContainer;
      // 使用 nextTick 确保 DOM 更新后再滚动
      this.$nextTick(() => {
        container.scrollTop = container.scrollHeight;
        // 添加一个小延时，确保内容完全渲染
        setTimeout(() => {
          container.scrollTop = container.scrollHeight;
        }, 100);
      });
    },
    // 添加滚动事件监听
    handleScroll() {
      const container = this.$refs.messagesContainer;
      // 如果用户手动滚动到顶部，可以在这里添加加载更多历史记录的逻辑
      if (container.scrollTop === 0) {
        // 这里可以添加加载更多历史记录的逻辑
      }
    },
    mounted() {
      this.loadConversations();
      this.scrollToBottom();
      
      // 添加滚动事件监听
      const container = this.$refs.messagesContainer;
      container.addEventListener('scroll', this.handleScroll);
    },
    beforeDestroy() {
      // 移除滚动事件监听
      const container = this.$refs.messagesContainer;
      container.removeEventListener('scroll', this.handleScroll);
    }
  }
}
</script>

<style scoped>
.chat-container {
  display: flex;
  height: 100vh;
  width: 100vw;
  margin: 0;
  padding: 0;
  overflow: hidden;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

.conversations-sidebar {
  width: 280px;
  background: #f5f5f5;
  display: flex;
  flex-direction: column;
  gap: 15px;
  padding: 15px;
  border-right: 1px solid #ddd;
  overflow: hidden;
  flex-shrink: 0;
  height: 100%;
}

.new-conversation-btn {
  width: 100%;
  padding: 10px;
  background: #007AFF;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  white-space: nowrap;
}

.new-conversation-btn:hover {
  background: #0056b3;
}

.conversations-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.conversation-item {
  padding: 10px;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: background-color 0.2s;
  white-space: nowrap;
}

.conversation-item:hover {
  background: #e9ecef;
}

.conversation-item.active {
  background: #e3f2fd;
  border-left: 4px solid #007AFF;
}

.conversation-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.delete-btn {
  background: none;
  border: none;
  color: #dc3545;
  font-size: 20px;
  cursor: pointer;
  padding: 0 5px;
  flex-shrink: 0;
}

.delete-btn:hover {
  color: #c82333;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  overflow: hidden;
  min-width: 0;
  height: 100%;
  position: relative;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 15px;
  max-width: 100%;
  height: calc(100% - 80px); /* 减去输入框的高度 */
}

.message {
  display: flex;
  flex-direction: column;
}

.message-wrapper {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  max-width: 85%;
}

.message-wrapper.user-message {
  margin-left: auto;
  flex-direction: row-reverse;
}

.avatar {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  border-radius: 50%;
  overflow: hidden;
  background: #f0f0f0;
}

.avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.message-content {
  padding: 12px 16px;
  border-radius: 15px;
  word-wrap: break-word;
  white-space: pre-wrap;
  line-height: 1.5;
}

.user-message .message-content {
  background: #007AFF;
  color: white;
  border-bottom-right-radius: 4px;
}

.ai-message {
  background: #f5f5f5;
  color: #333;
  border-bottom-left-radius: 4px;
}

.chat-input-container {
  padding: 15px;
  background: white;
  border-top: 1px solid #eee;
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 80px;
  display: flex;
  align-items: center;
}

.chat-input {
  display: flex;
  gap: 10px;
  max-width: 800px;
  margin: 0 auto;
  width: 100%;
}

input {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
  min-width: 0;
}

input:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
}

button {
  padding: 10px 20px;
  background: #007AFF;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  white-space: nowrap;
  flex-shrink: 0;
}

button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

button:hover:not(:disabled) {
  background: #0056b3;
}

/* 加载动画样式 */
.loading {
  display: flex;
  align-items: center;
  min-height: 40px;
}

.loading-dots {
  display: flex;
  gap: 4px;
}

.loading-dots span {
  width: 8px;
  height: 8px;
  background: #007AFF;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out;
}

.loading-dots span:nth-child(1) { animation-delay: -0.32s; }
.loading-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

/* 响应式布局 */
@media (max-width: 1440px) {
  .conversations-sidebar {
    width: 250px;
  }
  
  .message-content {
    max-width: 70%;
  }
}

@media (max-width: 1200px) {
  .conversations-sidebar {
    width: 220px;
  }
  
  .message-content {
    max-width: 75%;
  }
}

@media (max-width: 992px) {
  .conversations-sidebar {
    width: 200px;
  }
  
  .message-content {
    max-width: 80%;
  }
}

@media (max-width: 768px) {
  .chat-container {
    flex-direction: column;
  }

  .conversations-sidebar {
    width: 100%;
    height: auto;
    max-height: 180px;
    border-right: none;
    border-bottom: 1px solid #ddd;
    flex-shrink: 0;
  }

  .chat-messages {
    height: calc(100% - 180px - 80px); /* 减去侧边栏和输入框的高度 */
  }

  .message-wrapper {
    max-width: 90%;
  }
  
  .avatar {
    width: 32px;
    height: 32px;
  }
  
  .chat-input {
    max-width: 100%;
  }
}

@media (max-width: 576px) {
  .conversations-sidebar {
    max-height: 160px;
  }
  
  .chat-messages {
    height: calc(100% - 160px - 80px);
  }
  
  .chat-input-container {
    height: 100px;
  }
  
  .chat-input {
    flex-direction: column;
    gap: 8px;
  }

  .chat-input button {
    width: 100%;
  }

  .message-wrapper {
    max-width: 95%;
  }
  
  .avatar {
    width: 28px;
    height: 28px;
  }
  
  .message-content {
    padding: 10px 14px;
  }
  
  .chat-messages {
    padding: 15px;
  }
}

/* 处理超宽屏幕 */
@media (min-width: 1920px) {
  .chat-container {
    max-width: 1800px;
    margin: 0 auto;
  }
  
  .conversations-sidebar {
    width: 300px;
  }
  
  .message-content {
    max-width: 60%;
  }
  
  .chat-input {
    max-width: 1000px;
  }
}

/* 处理高屏幕 */
@media (min-height: 900px) {
  .conversations-sidebar {
    padding: 20px;
  }
  
  .chat-messages {
    padding: 25px;
  }
  
  .message-content {
    padding: 14px 18px;
  }
}

/* 处理低屏幕 */
@media (max-height: 600px) {
  .conversations-sidebar {
    padding: 10px;
  }
  
  .chat-messages {
    padding: 15px;
  }
  
  .message-content {
    padding: 8px 12px;
  }
  
  .conversations-list {
    max-height: 100px;
  }
}

/* Markdown 样式 */
.message-content :deep(p) {
  margin: 0;
  line-height: 1.6;
}

.message-content :deep(pre) {
  background: #1e1e1e;
  border-radius: 6px;
  padding: 16px;
  overflow-x: auto;
  margin: 8px 0;
}

.message-content :deep(code) {
  font-family: 'Fira Code', monospace;
  font-size: 14px;
}

.message-content :deep(p code) {
  background: rgba(0, 0, 0, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.9em;
}

.message-content :deep(ul), 
.message-content :deep(ol) {
  margin: 8px 0;
  padding-left: 24px;
}

.message-content :deep(li) {
  margin: 4px 0;
}

.message-content :deep(blockquote) {
  border-left: 4px solid #ddd;
  margin: 8px 0;
  padding-left: 16px;
  color: #666;
}

.message-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 8px 0;
}

.message-content :deep(th),
.message-content :deep(td) {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}

.message-content :deep(th) {
  background: #f5f5f5;
}

.message-content :deep(a) {
  color: #007AFF;
  text-decoration: none;
}

.message-content :deep(a:hover) {
  text-decoration: underline;
}

.message-content :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 4px;
}

/* 用户消息中的 Markdown 样式 */
.user-message :deep(pre) {
  background: rgba(255, 255, 255, 0.1);
}

.user-message :deep(code) {
  color: #fff;
}

.user-message :deep(p code) {
  background: rgba(255, 255, 255, 0.2);
}

.user-message :deep(blockquote) {
  border-left-color: rgba(255, 255, 255, 0.3);
  color: rgba(255, 255, 255, 0.8);
}

.user-message :deep(a) {
  color: #fff;
  text-decoration: underline;
}

/* 代码块滚动条样式 */
.message-content :deep(pre::-webkit-scrollbar) {
  height: 8px;
}

.message-content :deep(pre::-webkit-scrollbar-track) {
  background: #1e1e1e;
}

.message-content :deep(pre::-webkit-scrollbar-thumb) {
  background: #444;
  border-radius: 4px;
}

.message-content :deep(pre::-webkit-scrollbar-thumb:hover) {
  background: #555;
}
</style> 