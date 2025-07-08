import { Routes, Route, Navigate } from 'react-router-dom'
import { useSelector } from 'react-redux'
import { Box } from '@mui/material'

import Layout from '@components/Layout/Layout'
import LoginPage from '@pages/LoginPage'
import ChatPage from '@pages/ChatPage'
import DashboardPage from '@pages/DashboardPage'
import SettingsPage from '@pages/SettingsPage'
import { RootState } from '@store/index'

function App() {
  const { isAuthenticated } = useSelector((state: RootState) => state.auth)

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Routes>
        {/* 로그인 페이지 */}
        <Route 
          path="/login" 
          element={
            isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginPage />
          } 
        />
        
        {/* 인증된 사용자만 접근 가능한 라우트 */}
        <Route 
          path="/*" 
          element={
            isAuthenticated ? (
              <Layout>
                <Routes>
                  <Route path="/" element={<Navigate to="/dashboard" replace />} />
                  <Route path="/dashboard" element={<DashboardPage />} />
                  <Route path="/chat" element={<ChatPage />} />
                  <Route path="/chat/:sessionId" element={<ChatPage />} />
                  <Route path="/settings" element={<SettingsPage />} />
                  <Route path="*" element={<Navigate to="/dashboard" replace />} />
                </Routes>
              </Layout>
            ) : (
              <Navigate to="/login" replace />
            )
          } 
        />
      </Routes>
    </Box>
  )
}

export default App 