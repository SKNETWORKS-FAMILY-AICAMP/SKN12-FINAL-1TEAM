// 전역 변수
let sessionId = generateSessionId();
let userId = generateUserId();
let isLoading = false;

// DOM 요소들
const chatInput = document.getElementById('chatInput');
const sendButton = document.getElementById('sendButton');
const chatMessages = document.getElementById('chatMessages');
const chatbotToggle = document.getElementById('chatbotToggle');
const clearChatBtn = document.getElementById('clearChat');
const exportChatBtn = document.getElementById('exportChat');
const loadingOverlay = document.getElementById('loadingOverlay');

// 세션 ID 생성
function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// 사용자 ID 생성
function generateUserId() {
    return 'user_' + Math.random().toString(36).substr(2, 9);
}

// 이벤트 리스너 등록
document.addEventListener('DOMContentLoaded', function() {
    // 메시지 전송 이벤트
    sendButton.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Agent 시스템 정보 표시
    console.log('4개 전문 AI Agent 자동 라우팅 시스템 활성화');

    // 챗봇 토글 버튼 (현재 페이지이므로 사실상 필요 없지만 일단 구현)
    chatbotToggle.addEventListener('click', function() {
        // 현재 페이지에 이미 있으므로 스크롤을 채팅 영역으로 이동
        document.querySelector('.chat-area').scrollIntoView({ behavior: 'smooth' });
    });

    // 대화 지우기
    clearChatBtn.addEventListener('click', clearChat);
    
    // 대화 내보내기
    exportChatBtn.addEventListener('click', exportChat);

    // 네비게이션 메뉴 이벤트
    setupNavigation();

    console.log('NaruTalk AI Assistant 초기화 완료');
    console.log('Session ID:', sessionId);
    console.log('User ID:', userId);
    console.log('Main Agent Router: 4개 전문 Agent 자동 라우팅');
});

// 메시지 전송 함수
async function sendMessage() {
    const message = chatInput.value.trim();
    if (!message || isLoading) return;

    // 사용자 메시지 표시
    addMessage(message, 'user');
    chatInput.value = '';

    // 로딩 표시
    showLoading();

    try {
        // 단일 메인 Agent Router 엔드포인트
        const endpoint = '/api/v1/tool-calling/chat';
        console.log('API 호출:', endpoint);
        
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                session_id: sessionId
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // 새로운 Agent 시스템 응답 처리
        const responseText = data.response || '응답을 받지 못했습니다.';
        const agentType = data.agent || 'unknown';
        const arguments = data.arguments || {};
        
        // 봇 응답 표시 (Agent 타입 포함)
        addMessage(responseText, 'bot', agentType, arguments);
        
        // 소스 정보가 있으면 표시
        if (data.sources && data.sources.length > 0) {
            addSourcesInfo(data.sources);
        }

        // 메타데이터 로그
        if (data.metadata) {
            console.log('Agent 메타데이터:', data.metadata);
        }

    } catch (error) {
        console.error('메시지 전송 오류:', error);
        addMessage('죄송합니다. 오류가 발생했습니다. 다시 시도해 주세요.', 'bot');
    } finally {
        hideLoading();
    }
}

// 메시지 추가 함수
function addMessage(text, sender, agentType = null, agentArgs = null) {
    const messageContainer = document.createElement('div');
    messageContainer.className = 'message-container';

    const message = document.createElement('div');
    message.className = `message ${sender}-message`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    
    // 아바타 아이콘 설정
    if (sender === 'user') {
        avatar.innerHTML = '<i class="fas fa-user"></i>';
    } else if (sender === 'system') {
        avatar.innerHTML = '<i class="fas fa-cog"></i>';
    } else {
        avatar.innerHTML = '<i class="fas fa-robot"></i>';
    }

    const content = document.createElement('div');
    content.className = 'message-content';

    const messageText = document.createElement('div');
    messageText.className = 'message-text';
    messageText.textContent = text;

    const messageTime = document.createElement('div');
    messageTime.className = 'message-time';
    messageTime.textContent = formatTime(new Date());

    content.appendChild(messageText);
    content.appendChild(messageTime);

    // 봇 메시지인 경우 Agent 정보 추가
    if (sender === 'bot' && agentType) {
        const agentInfo = document.createElement('div');
        agentInfo.className = 'agent-info-badge';
        
        // Agent 타입별 아이콘 및 이름 매핑
        const agentDisplay = getAgentDisplayInfo(agentType);
        
        agentInfo.innerHTML = `
            <i class="${agentDisplay.icon}"></i>
            ${agentDisplay.name}
        `;
        content.appendChild(agentInfo);
    }

    message.appendChild(avatar);
    message.appendChild(content);
    messageContainer.appendChild(message);

    chatMessages.appendChild(messageContainer);
    scrollToBottom();
}

// Agent 표시 정보 반환 함수
function getAgentDisplayInfo(agentType) {
    const agentMap = {
        'chroma_db_agent': {
            name: '📄 문서 검색',
            icon: 'fas fa-file-search'
        },
        'employee_db_agent': {
            name: '👥 직원 정보',
            icon: 'fas fa-users'
        },
        'client_analysis_agent': {
            name: '📊 고객 분석',
            icon: 'fas fa-chart-line'
        },
        'rule_compliance_agent': {
            name: '📋 규정 분석',
            icon: 'fas fa-shield-alt'
        },
        'general_chat': {
            name: '💬 일반 대화',
            icon: 'fas fa-comments'
        }
    };
    
    return agentMap[agentType] || {
        name: `🤖 ${agentType}`,
        icon: 'fas fa-robot'
    };
}

// 소스 정보 추가 함수
function addSourcesInfo(sources) {
    const sourceContainer = document.createElement('div');
    sourceContainer.className = 'message-container';

    const sourceMessage = document.createElement('div');
    sourceMessage.className = 'message bot-message';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = '<i class="fas fa-book"></i>';

    const content = document.createElement('div');
    content.className = 'message-content';

    const sourceText = document.createElement('div');
    sourceText.className = 'message-text';
    sourceText.innerHTML = `
        <strong>참고 문서:</strong><br>
        ${sources.map(source => `• ${source.title || source.filename || '문서'}`).join('<br>')}
    `;

    const messageTime = document.createElement('div');
    messageTime.className = 'message-time';
    messageTime.textContent = formatTime(new Date());

    content.appendChild(sourceText);
    content.appendChild(messageTime);

    sourceMessage.appendChild(avatar);
    sourceMessage.appendChild(content);
    sourceContainer.appendChild(sourceMessage);

    chatMessages.appendChild(sourceContainer);
    scrollToBottom();
}

// 로딩 표시/숨기기
function showLoading() {
    isLoading = true;
    loadingOverlay.style.display = 'flex';
    sendButton.disabled = true;
}

function hideLoading() {
    isLoading = false;
    loadingOverlay.style.display = 'none';
    sendButton.disabled = false;
}

// 대화 지우기
function clearChat() {
    if (confirm('모든 대화를 지우시겠습니까?')) {
        // 초기 메시지만 남기고 모든 메시지 제거
        chatMessages.innerHTML = `
            <div class="message-container">
                <div class="message bot-message">
                    <div class="message-avatar">
                        <i class="fas fa-robot"></i>
                    </div>
                    <div class="message-content">
                        <div class="message-text">안녕하세요! NaruTalk AI Assistant입니다. 무엇을 도와드릴까요?</div>
                        <div class="message-time">${formatTime(new Date())}</div>
                    </div>
                </div>
            </div>
        `;
        
        // 새로운 세션 시작
        sessionId = generateSessionId();
        console.log('새 세션 시작:', sessionId);
    }
}

// 대화 내보내기
function exportChat() {
    const messages = [];
    const messageElements = chatMessages.querySelectorAll('.message');
    
    messageElements.forEach(msg => {
        const isUser = msg.classList.contains('user-message');
        const text = msg.querySelector('.message-text').textContent;
        const time = msg.querySelector('.message-time').textContent;
        
        messages.push({
            sender: isUser ? 'User' : 'AI',
            message: text,
            time: time
        });
    });

    const exportData = {
        session_id: sessionId,
        user_id: userId,
        exported_at: new Date().toISOString(),
        messages: messages
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `narutalk_chat_${sessionId}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// 네비게이션 설정
function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            
            // 모든 메뉴에서 active 클래스 제거
            navItems.forEach(nav => nav.classList.remove('active'));
            
            // 클릭된 메뉴에 active 클래스 추가
            this.classList.add('active');
            
            // 메뉴 이름 가져오기
            const menuName = this.querySelector('span').textContent;
            console.log('메뉴 선택:', menuName);
            
            // 여기에 메뉴별 동작 추가 (나중에 확장 가능)
            handleMenuSelection(menuName);
        });
    });
}

// 메뉴 선택 처리
function handleMenuSelection(menuName) {
    // 현재는 콘솔에만 로그 출력
    // 나중에 각 메뉴에 따른 컨텐츠 변경 기능 추가 가능
    switch(menuName) {
        case '홈':
            console.log('홈 메뉴 선택됨');
            break;
        case '대시보드':
            console.log('대시보드 메뉴 선택됨');
            break;
        case '고객 관리':
            console.log('고객 관리 메뉴 선택됨');
            break;
        case '문서 관리':
            console.log('문서 관리 메뉴 선택됨');
            break;
        case '일정 관리':
            console.log('일정 관리 메뉴 선택됨');
            break;
        case 'AI 분석':
            console.log('AI 분석 메뉴 선택됨');
            break;
        case '문서 검색':
            console.log('문서 검색 메뉴 선택됨');
            break;
        case '설정':
            console.log('설정 메뉴 선택됨');
            break;
        default:
            console.log('알 수 없는 메뉴:', menuName);
    }
}

// 유틸리티 함수들
function formatTime(date) {
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) { // 1분 미만
        return '방금 전';
    } else if (diff < 3600000) { // 1시간 미만
        return Math.floor(diff / 60000) + '분 전';
    } else if (diff < 86400000) { // 1일 미만
        return Math.floor(diff / 3600000) + '시간 전';
    } else {
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    }
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 키보드 단축키
document.addEventListener('keydown', function(e) {
    // Ctrl + / : 채팅 입력 포커스
    if (e.ctrlKey && e.key === '/') {
        e.preventDefault();
        chatInput.focus();
    }
    
    // ESC : 채팅 입력 블러
    if (e.key === 'Escape') {
        chatInput.blur();
    }
});

// 페이지 언로드 시 정리
window.addEventListener('beforeunload', function() {
    console.log('NaruTalk AI Assistant 종료');
}); 