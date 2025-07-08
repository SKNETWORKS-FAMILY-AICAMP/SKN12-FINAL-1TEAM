import { createSlice, PayloadAction } from '@reduxjs/toolkit'

export interface ChatMessage {
  id: string
  content: string
  sender: 'user' | 'ai' | 'system'
  timestamp: string
  type: 'text' | 'image' | 'file' | 'error'
  metadata?: {
    fileName?: string
    fileSize?: number
    fileType?: string
    confidence?: number
    sources?: string[]
  }
}

export interface ChatSession {
  id: string
  title: string
  messages: ChatMessage[]
  createdAt: string
  updatedAt: string
  isActive: boolean
  category: 'medical' | 'general' | 'emergency' | 'consultation'
}

interface ChatState {
  sessions: ChatSession[]
  currentSessionId: string | null
  isLoading: boolean
  isTyping: boolean
  error: string | null
  connectionStatus: 'connected' | 'disconnected' | 'connecting' | 'error'
  unreadCount: number
  settings: {
    autoSave: boolean
    soundEnabled: boolean
    notificationsEnabled: boolean
    theme: 'light' | 'dark'
  }
}

const initialState: ChatState = {
  sessions: [],
  currentSessionId: null,
  isLoading: false,
  isTyping: false,
  error: null,
  connectionStatus: 'disconnected',
  unreadCount: 0,
  settings: {
    autoSave: true,
    soundEnabled: true,
    notificationsEnabled: true,
    theme: 'light',
  },
}

const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    // 세션 관리
    createSession: (state, action: PayloadAction<{ title: string; category: ChatSession['category'] }>) => {
      const newSession: ChatSession = {
        id: Date.now().toString(),
        title: action.payload.title,
        messages: [],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        isActive: true,
        category: action.payload.category,
      }
      state.sessions.push(newSession)
      state.currentSessionId = newSession.id
    },
    
    setCurrentSession: (state, action: PayloadAction<string>) => {
      state.currentSessionId = action.payload
      // 현재 세션의 읽지 않은 메시지 초기화
      state.unreadCount = 0
    },
    
    deleteSession: (state, action: PayloadAction<string>) => {
      state.sessions = state.sessions.filter(session => session.id !== action.payload)
      if (state.currentSessionId === action.payload) {
        state.currentSessionId = state.sessions.length > 0 ? state.sessions[0].id : null
      }
    },
    
    // 메시지 관리
    addMessage: (state, action: PayloadAction<Omit<ChatMessage, 'id' | 'timestamp'>>) => {
      const currentSession = state.sessions.find(s => s.id === state.currentSessionId)
      if (currentSession) {
        const newMessage: ChatMessage = {
          ...action.payload,
          id: Date.now().toString(),
          timestamp: new Date().toISOString(),
        }
        currentSession.messages.push(newMessage)
        currentSession.updatedAt = new Date().toISOString()
        
        // AI 메시지인 경우 읽지 않은 메시지 수 증가
        if (action.payload.sender === 'ai') {
          state.unreadCount += 1
        }
      }
    },
    
    updateMessage: (state, action: PayloadAction<{ messageId: string; content: string }>) => {
      const currentSession = state.sessions.find(s => s.id === state.currentSessionId)
      if (currentSession) {
        const message = currentSession.messages.find(m => m.id === action.payload.messageId)
        if (message) {
          message.content = action.payload.content
          currentSession.updatedAt = new Date().toISOString()
        }
      }
    },
    
    deleteMessage: (state, action: PayloadAction<string>) => {
      const currentSession = state.sessions.find(s => s.id === state.currentSessionId)
      if (currentSession) {
        currentSession.messages = currentSession.messages.filter(m => m.id !== action.payload)
        currentSession.updatedAt = new Date().toISOString()
      }
    },
    
    // 상태 관리
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload
    },
    
    setTyping: (state, action: PayloadAction<boolean>) => {
      state.isTyping = action.payload
    },
    
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
    },
    
    setConnectionStatus: (state, action: PayloadAction<ChatState['connectionStatus']>) => {
      state.connectionStatus = action.payload
    },
    
    clearUnreadCount: (state) => {
      state.unreadCount = 0
    },
    
    // 설정 관리
    updateSettings: (state, action: PayloadAction<Partial<ChatState['settings']>>) => {
      state.settings = { ...state.settings, ...action.payload }
    },
    
    // 세션 데이터 로드
    loadSessions: (state, action: PayloadAction<ChatSession[]>) => {
      state.sessions = action.payload
    },
    
    // 전체 초기화
    resetChat: (state) => {
      state.sessions = []
      state.currentSessionId = null
      state.isLoading = false
      state.isTyping = false
      state.error = null
      state.unreadCount = 0
    },
  },
})

export const {
  createSession,
  setCurrentSession,
  deleteSession,
  addMessage,
  updateMessage,
  deleteMessage,
  setLoading,
  setTyping,
  setError,
  setConnectionStatus,
  clearUnreadCount,
  updateSettings,
  loadSessions,
  resetChat,
} = chatSlice.actions

export default chatSlice.reducer 