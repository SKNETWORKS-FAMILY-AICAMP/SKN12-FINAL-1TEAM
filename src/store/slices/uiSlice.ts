import { createSlice, PayloadAction } from '@reduxjs/toolkit'

export interface Notification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message: string
  duration?: number
  timestamp: string
  isRead: boolean
}

export interface Modal {
  isOpen: boolean
  type: 'login' | 'register' | 'profile' | 'settings' | 'help' | 'confirmation' | null
  title?: string
  content?: string
  data?: any
}

interface UIState {
  // 레이아웃 관련
  sidebarOpen: boolean
  sidebarCollapsed: boolean
  isMobile: boolean
  
  // 테마 관련
  theme: 'light' | 'dark' | 'auto'
  primaryColor: string
  
  // 로딩 상태
  globalLoading: boolean
  loadingMessage: string
  
  // 알림 관련
  notifications: Notification[]
  showNotifications: boolean
  
  // 모달 관련
  modal: Modal
  
  // 채팅 UI 상태
  chatPanelOpen: boolean
  chatInputFocused: boolean
  showChatHistory: boolean
  
  // 검색 관련
  searchOpen: boolean
  searchQuery: string
  searchResults: any[]
  
  // 사용자 설정
  settings: {
    fontSize: 'small' | 'medium' | 'large'
    language: 'ko' | 'en'
    autoSave: boolean
    soundEnabled: boolean
    animationsEnabled: boolean
    compactMode: boolean
  }
  
  // 페이지 상태
  currentPage: string
  breadcrumbs: { label: string; path: string }[]
  
  // 에러 상태
  error: {
    isOpen: boolean
    title: string
    message: string
    code?: string
  }
}

const initialState: UIState = {
  // 레이아웃 관련
  sidebarOpen: true,
  sidebarCollapsed: false,
  isMobile: false,
  
  // 테마 관련
  theme: 'light',
  primaryColor: '#1976d2',
  
  // 로딩 상태
  globalLoading: false,
  loadingMessage: '',
  
  // 알림 관련
  notifications: [],
  showNotifications: false,
  
  // 모달 관련
  modal: {
    isOpen: false,
    type: null,
  },
  
  // 채팅 UI 상태
  chatPanelOpen: true,
  chatInputFocused: false,
  showChatHistory: false,
  
  // 검색 관련
  searchOpen: false,
  searchQuery: '',
  searchResults: [],
  
  // 사용자 설정
  settings: {
    fontSize: 'medium',
    language: 'ko',
    autoSave: true,
    soundEnabled: true,
    animationsEnabled: true,
    compactMode: false,
  },
  
  // 페이지 상태
  currentPage: 'home',
  breadcrumbs: [],
  
  // 에러 상태
  error: {
    isOpen: false,
    title: '',
    message: '',
  },
}

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    // 레이아웃 관련
    toggleSidebar: (state) => {
      state.sidebarOpen = !state.sidebarOpen
    },
    
    setSidebarOpen: (state, action: PayloadAction<boolean>) => {
      state.sidebarOpen = action.payload
    },
    
    setSidebarCollapsed: (state, action: PayloadAction<boolean>) => {
      state.sidebarCollapsed = action.payload
    },
    
    setMobileMode: (state, action: PayloadAction<boolean>) => {
      state.isMobile = action.payload
      // 모바일 모드에서는 기본적으로 사이드바 닫기
      if (action.payload) {
        state.sidebarOpen = false
      }
    },
    
    // 테마 관련
    setTheme: (state, action: PayloadAction<UIState['theme']>) => {
      state.theme = action.payload
    },
    
    setPrimaryColor: (state, action: PayloadAction<string>) => {
      state.primaryColor = action.payload
    },
    
    // 로딩 상태
    setGlobalLoading: (state, action: PayloadAction<boolean>) => {
      state.globalLoading = action.payload
    },
    
    setLoadingMessage: (state, action: PayloadAction<string>) => {
      state.loadingMessage = action.payload
    },
    
    // 알림 관련
    addNotification: (state, action: PayloadAction<Omit<Notification, 'id' | 'timestamp' | 'isRead'>>) => {
      const newNotification: Notification = {
        ...action.payload,
        id: Date.now().toString(),
        timestamp: new Date().toISOString(),
        isRead: false,
      }
      state.notifications.unshift(newNotification)
      
      // 최대 20개까지만 보관
      if (state.notifications.length > 20) {
        state.notifications = state.notifications.slice(0, 20)
      }
    },
    
    removeNotification: (state, action: PayloadAction<string>) => {
      state.notifications = state.notifications.filter(n => n.id !== action.payload)
    },
    
    markNotificationAsRead: (state, action: PayloadAction<string>) => {
      const notification = state.notifications.find(n => n.id === action.payload)
      if (notification) {
        notification.isRead = true
      }
    },
    
    clearAllNotifications: (state) => {
      state.notifications = []
    },
    
    setShowNotifications: (state, action: PayloadAction<boolean>) => {
      state.showNotifications = action.payload
    },
    
    // 모달 관련
    openModal: (state, action: PayloadAction<Omit<Modal, 'isOpen'>>) => {
      state.modal = {
        isOpen: true,
        ...action.payload,
      }
    },
    
    closeModal: (state) => {
      state.modal = {
        isOpen: false,
        type: null,
      }
    },
    
    // 채팅 UI 상태
    setChatPanelOpen: (state, action: PayloadAction<boolean>) => {
      state.chatPanelOpen = action.payload
    },
    
    setChatInputFocused: (state, action: PayloadAction<boolean>) => {
      state.chatInputFocused = action.payload
    },
    
    setShowChatHistory: (state, action: PayloadAction<boolean>) => {
      state.showChatHistory = action.payload
    },
    
    // 검색 관련
    setSearchOpen: (state, action: PayloadAction<boolean>) => {
      state.searchOpen = action.payload
    },
    
    setSearchQuery: (state, action: PayloadAction<string>) => {
      state.searchQuery = action.payload
    },
    
    setSearchResults: (state, action: PayloadAction<any[]>) => {
      state.searchResults = action.payload
    },
    
    // 사용자 설정
    updateSettings: (state, action: PayloadAction<Partial<UIState['settings']>>) => {
      state.settings = { ...state.settings, ...action.payload }
    },
    
    // 페이지 상태
    setCurrentPage: (state, action: PayloadAction<string>) => {
      state.currentPage = action.payload
    },
    
    setBreadcrumbs: (state, action: PayloadAction<{ label: string; path: string }[]>) => {
      state.breadcrumbs = action.payload
    },
    
    // 에러 상태
    showError: (state, action: PayloadAction<{ title: string; message: string; code?: string }>) => {
      state.error = {
        isOpen: true,
        ...action.payload,
      }
    },
    
    hideError: (state) => {
      state.error = {
        isOpen: false,
        title: '',
        message: '',
      }
    },
    
    // 전체 초기화
    resetUI: (state) => {
      return initialState
    },
  },
})

export const {
  toggleSidebar,
  setSidebarOpen,
  setSidebarCollapsed,
  setMobileMode,
  setTheme,
  setPrimaryColor,
  setGlobalLoading,
  setLoadingMessage,
  addNotification,
  removeNotification,
  markNotificationAsRead,
  clearAllNotifications,
  setShowNotifications,
  openModal,
  closeModal,
  setChatPanelOpen,
  setChatInputFocused,
  setShowChatHistory,
  setSearchOpen,
  setSearchQuery,
  setSearchResults,
  updateSettings,
  setCurrentPage,
  setBreadcrumbs,
  showError,
  hideError,
  resetUI,
} = uiSlice.actions

export default uiSlice.reducer 