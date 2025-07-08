import { createSlice, PayloadAction } from '@reduxjs/toolkit'

export interface User {
  id: string
  username: string
  email: string
  role: 'admin' | 'doctor' | 'nurse' | 'user'
  department?: string
  isVerified: boolean
}

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  token: string | null
}

const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
  token: localStorage.getItem('token'),
}

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    loginStart: (state) => {
      state.isLoading = true
      state.error = null
    },
    loginSuccess: (state, action: PayloadAction<{ user: User; token: string }>) => {
      state.isLoading = false
      state.isAuthenticated = true
      state.user = action.payload.user
      state.token = action.payload.token
      state.error = null
      localStorage.setItem('token', action.payload.token)
    },
    loginFailure: (state, action: PayloadAction<string>) => {
      state.isLoading = false
      state.isAuthenticated = false
      state.user = null
      state.token = null
      state.error = action.payload
      localStorage.removeItem('token')
    },
    logout: (state) => {
      state.isAuthenticated = false
      state.user = null
      state.token = null
      state.error = null
      state.isLoading = false
      localStorage.removeItem('token')
    },
    clearError: (state) => {
      state.error = null
    },
    updateUser: (state, action: PayloadAction<Partial<User>>) => {
      if (state.user) {
        state.user = { ...state.user, ...action.payload }
      }
    },
  },
})

export const {
  loginStart,
  loginSuccess,
  loginFailure,
  logout,
  clearError,
  updateUser,
} = authSlice.actions

export default authSlice.reducer 