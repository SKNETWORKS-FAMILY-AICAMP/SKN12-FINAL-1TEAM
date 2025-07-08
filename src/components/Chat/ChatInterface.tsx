import React, { useState, useEffect, useRef } from 'react'
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Typography,
  Avatar,
  Divider,
  CircularProgress,
  Chip,
} from '@mui/material'
import {
  Send as SendIcon,
  Person as PersonIcon,
  SmartToy as BotIcon,
  AttachFile as AttachIcon,
} from '@mui/icons-material'
import { useSelector, useDispatch } from 'react-redux'
import { motion, AnimatePresence } from 'framer-motion'

import { RootState } from '@store/index'
import { sendMessage, addMessage } from '@store/slices/chatSlice'
import { useWebSocket } from '@hooks/useWebSocket'

interface Message {
  id: string
  type: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  metadata?: {
    confidence?: number
    sources?: string[]
    model?: string
  }
}

interface ChatInterfaceProps {
  sessionId?: string
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ sessionId }) => {
  const dispatch = useDispatch()
  const { currentSession, messages, isLoading } = useSelector(
    (state: RootState) => state.chat
  )
  const { user } = useSelector((state: RootState) => state.auth)

  const [inputMessage, setInputMessage] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // WebSocket 연결
  const { sendMessage: sendWebSocketMessage, isConnected } = useWebSocket({
    sessionId: sessionId || currentSession?.id,
    onMessage: (message) => {
      dispatch(addMessage(message))
      setIsTyping(false)
    },
    onTyping: () => setIsTyping(true),
  })

  // 메시지 전송
  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return

    const newMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputMessage.trim(),
      timestamp: new Date(),
    }

    // UI에 사용자 메시지 추가
    dispatch(addMessage(newMessage))
    setInputMessage('')
    setIsTyping(true)

    try {
      if (isConnected) {
        // WebSocket으로 전송
        sendWebSocketMessage({
          message: newMessage.content,
          type: 'user',
          sessionId: sessionId || currentSession?.id,
        })
      } else {
        // HTTP API로 전송
        dispatch(sendMessage({
          content: newMessage.content,
          sessionId: sessionId || currentSession?.id,
        }))
      }
    } catch (error) {
      console.error('메시지 전송 실패:', error)
      setIsTyping(false)
    }
  }

  // 엔터키 처리
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  // 메시지 자동 스크롤
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // 메시지 렌더링
  const renderMessage = (message: Message) => {
    const isUser = message.type === 'user'
    const isSystem = message.type === 'system'

    return (
      <motion.div
        key={message.id}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        transition={{ duration: 0.3 }}
      >
        <Box
          sx={{
            display: 'flex',
            flexDirection: isUser ? 'row-reverse' : 'row',
            alignItems: 'flex-start',
            mb: 2,
            gap: 1,
          }}
        >
          {/* 아바타 */}
          <Avatar
            sx={{
              bgcolor: isUser ? 'primary.main' : isSystem ? 'warning.main' : 'secondary.main',
              width: 36,
              height: 36,
            }}
          >
            {isUser ? <PersonIcon /> : <BotIcon />}
          </Avatar>

          {/* 메시지 내용 */}
          <Paper
            elevation={1}
            sx={{
              p: 2,
              maxWidth: '70%',
              bgcolor: isUser ? 'primary.main' : 'background.paper',
              color: isUser ? 'primary.contrastText' : 'text.primary',
              borderRadius: isUser ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
            }}
          >
            <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
              {message.content}
            </Typography>

            {/* 메타데이터 */}
            {message.metadata && (
              <Box sx={{ mt: 1, display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                {message.metadata.confidence && (
                  <Chip
                    size="small"
                    label={`신뢰도: ${(message.metadata.confidence * 100).toFixed(0)}%`}
                    variant="outlined"
                    sx={{ fontSize: '0.7rem' }}
                  />
                )}
                {message.metadata.model && (
                  <Chip
                    size="small"
                    label={message.metadata.model}
                    variant="outlined"
                    sx={{ fontSize: '0.7rem' }}
                  />
                )}
              </Box>
            )}

            {/* 타임스탬프 */}
            <Typography
              variant="caption"
              sx={{
                display: 'block',
                mt: 0.5,
                opacity: 0.7,
                textAlign: isUser ? 'right' : 'left',
              }}
            >
              {message.timestamp.toLocaleTimeString('ko-KR', {
                hour: '2-digit',
                minute: '2-digit',
              })}
            </Typography>
          </Paper>
        </Box>
      </motion.div>
    )
  }

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        bgcolor: 'background.default',
      }}
    >
      {/* 헤더 */}
      <Paper
        elevation={0}
        sx={{
          p: 2,
          borderBottom: 1,
          borderColor: 'divider',
          bgcolor: 'background.paper',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Avatar sx={{ bgcolor: 'primary.main' }}>
            <BotIcon />
          </Avatar>
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              QA 챗봇 어시스턴트
            </Typography>
            <Typography variant="body2" color="text.secondary">
              의료업계 전문 AI가 도와드립니다
              {isConnected && (
                <Chip
                  size="small"
                  label="실시간 연결"
                  color="success"
                  sx={{ ml: 1, fontSize: '0.7rem' }}
                />
              )}
            </Typography>
          </Box>
        </Box>
      </Paper>

      {/* 메시지 영역 */}
      <Box
        sx={{
          flex: 1,
          overflow: 'auto',
          p: 2,
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <AnimatePresence>
          {messages.map(renderMessage)}
        </AnimatePresence>

        {/* 타이핑 인디케이터 */}
        {isTyping && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <Avatar sx={{ bgcolor: 'secondary.main', width: 36, height: 36 }}>
                <BotIcon />
              </Avatar>
              <Paper
                elevation={1}
                sx={{
                  p: 2,
                  bgcolor: 'background.paper',
                  borderRadius: '18px 18px 18px 4px',
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CircularProgress size={16} />
                  <Typography variant="body2" color="text.secondary">
                    응답을 생성하고 있습니다...
                  </Typography>
                </Box>
              </Paper>
            </Box>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </Box>

      <Divider />

      {/* 입력 영역 */}
      <Paper
        elevation={0}
        sx={{
          p: 2,
          bgcolor: 'background.paper',
          borderTop: 1,
          borderColor: 'divider',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'flex-end', gap: 1 }}>
          <IconButton color="primary" disabled>
            <AttachIcon />
          </IconButton>

          <TextField
            fullWidth
            multiline
            maxRows={4}
            placeholder="질문을 입력하세요..."
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={isLoading}
            variant="outlined"
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: 3,
              },
            }}
          />

          <IconButton
            color="primary"
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isLoading}
            sx={{
              bgcolor: 'primary.main',
              color: 'primary.contrastText',
              '&:hover': {
                bgcolor: 'primary.dark',
              },
              '&:disabled': {
                bgcolor: 'action.disabled',
              },
            }}
          >
            {isLoading ? <CircularProgress size={20} /> : <SendIcon />}
          </IconButton>
        </Box>

        <Typography
          variant="caption"
          color="text.secondary"
          sx={{ display: 'block', mt: 1, textAlign: 'center' }}
        >
          💡 의료기기 영업, 병원 관리, 업계 동향 등에 대해 질문하세요
        </Typography>
      </Paper>
    </Box>
  )
}

export default ChatInterface 