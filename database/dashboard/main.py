"""
Streamlit 통합 대시보드
PostgreSQL, MinIO, OpenSearch 연동 및 엔티티 관리, 승인 시스템
"""

import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any
import time

# 페이지 설정
st.set_page_config(
    page_title="시스템 통합 대시보드",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API 기본 URL
API_BASE_URL = "http://localhost:8010"

# 세션 상태 초기화
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'access_token' not in st.session_state:
    st.session_state.access_token = None
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'login_time' not in st.session_state:
    st.session_state.login_time = None

def check_api_connection():
    """API 연결 상태 확인"""
    try:
        response = requests.get(f"{API_BASE_URL}/ping", timeout=5)
        return response.status_code == 200
    except:
        return False

def login_user(email: str, password: str):
    """사용자 로그인"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/user/login",
            data={
                "username": email,
                "password": password
            }
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token"), None
        else:
            return None, "이메일 또는 비밀번호가 올바르지 않습니다."
    except Exception as e:
        return None, f"로그인 중 오류가 발생했습니다: {str(e)}"

def get_current_user_info(token: str):
    """현재 사용자 정보 조회"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_BASE_URL}/user/me", headers=headers)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def validate_token(token: str):
    """토큰 유효성 검증"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_BASE_URL}/user/me", headers=headers, timeout=5)
        return response.status_code == 200
    except:
        return False

def check_session_validity():
    """세션 유효성 확인 및 자동 로그아웃 처리"""
    if not st.session_state.authenticated or not st.session_state.access_token:
        return False
    
    # 로그인 시간 확인 (24시간 제한)
    if st.session_state.login_time:
        login_time = datetime.fromisoformat(st.session_state.login_time)
        if datetime.now() - login_time > timedelta(hours=24):
            logout_user()
            return False
    
    # 토큰 유효성 확인
    if not validate_token(st.session_state.access_token):
        logout_user()
        return False
    
    return True

def logout_user():
    """사용자 로그아웃"""
    st.session_state.authenticated = False
    st.session_state.access_token = None
    st.session_state.current_user = None
    st.session_state.login_time = None

def get_dashboard_stats(days: int = 30):
    """대시보드 통계 조회"""
    try:
        headers = {"Authorization": f"Bearer {st.session_state.access_token}"} if st.session_state.access_token else {}
        response = requests.get(f"{API_BASE_URL}/dashboard/stats?days={days}", headers=headers)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def get_approval_stats():
    """승인 시스템 통계 조회"""
    try:
        headers = {"Authorization": f"Bearer {st.session_state.access_token}"} if st.session_state.access_token else {}
        response = requests.get(f"{API_BASE_URL}/approval/stats", headers=headers)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def get_pending_approvals(entity_type: str = None):
    """승인 대기 목록 조회"""
    try:
        headers = {"Authorization": f"Bearer {st.session_state.access_token}"} if st.session_state.access_token else {}
        url = f"{API_BASE_URL}/approval/pending"
        if entity_type:
            url += f"?entity_type={entity_type}"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def approve_entity(entity_type: str, entity_id: int, notes: str = None):
    """엔티티 승인"""
    try:
        headers = {"Authorization": f"Bearer {st.session_state.access_token}"} if st.session_state.access_token else {}
        url = f"{API_BASE_URL}/approval/approve/{entity_type}/{entity_id}"
        params = {}
        if notes:
            params['notes'] = notes
        response = requests.post(url, params=params, headers=headers)
        return response.status_code == 200
    except:
        return False

def reject_entity(entity_type: str, entity_id: int, notes: str):
    """엔티티 거부"""
    try:
        headers = {"Authorization": f"Bearer {st.session_state.access_token}"} if st.session_state.access_token else {}
        url = f"{API_BASE_URL}/approval/reject/{entity_type}/{entity_id}"
        response = requests.post(url, params={'notes': notes}, headers=headers)
        return response.status_code == 200
    except:
        return False

def get_system_documents(system_type: str):
    """시스템별 문서 정보 조회"""
    try:
        headers = {"Authorization": f"Bearer {st.session_state.access_token}"} if st.session_state.access_token else {}
        response = requests.get(f"{API_BASE_URL}/dashboard/system-documents?system={system_type}", headers=headers)
        
        # 디버깅을 위한 로그 추가
        st.write(f"🔍 API 응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            st.write(f"📊 받은 데이터: {data}")
            return data
        else:
            st.error(f"❌ API 오류: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"❌ 연결 오류: {str(e)}")
        return None

def show_login_page():
    """로그인 페이지 표시"""
    st.title("🔐 관리자 로그인")
    st.markdown("---")
    
    # API 연결 상태 확인
    if not check_api_connection():
        st.error("❌ API 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
        return
    
    # 초기 관리자 생성 상태 관리
    if 'show_init_admin' not in st.session_state:
        st.session_state.show_init_admin = False
    
    # 로그인 폼
    with st.form("login_form"):
        st.subheader("관리자 계정으로 로그인")
        
        email = st.text_input("이메일", placeholder="admin@example.com")
        password = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            submitted = st.form_submit_button("로그인", type="primary")
        
        with col2:
            init_admin_clicked = st.form_submit_button("초기 관리자 생성")
        
        if submitted:
            if not email or not password:
                st.error("이메일과 비밀번호를 모두 입력해주세요.")
                return
            
            token, error = login_user(email, password)
            if token:
                # 사용자 정보 조회
                user_info = get_current_user_info(token)
                if user_info and user_info.get("role") == "admin":
                    st.session_state.authenticated = True
                    st.session_state.access_token = token
                    st.session_state.current_user = user_info
                    st.session_state.login_time = datetime.now().isoformat()
                    st.success("로그인 성공!")
                    st.rerun()
                else:
                    st.error("관리자 권한이 필요합니다.")
            else:
                st.error(error)
        
        if init_admin_clicked:
            st.session_state.show_init_admin = True
            st.rerun()
    
    # 초기 관리자 생성 섹션 (폼 외부)
    if st.session_state.show_init_admin:
        show_init_admin_section()

def show_init_admin_section():
    """초기 관리자 생성 섹션"""
    st.markdown("---")
    st.subheader("🔐 초기 관리자 계정 생성")
    st.warning("⚠️ 이 기능은 시스템 초기 설정 시에만 사용하세요!")
    st.info("관리자 계정은 모든 시스템 기능에 접근할 수 있는 최고 권한을 가집니다.")
    
    # 폼 상태 관리
    if 'init_admin_submitted' not in st.session_state:
        st.session_state.init_admin_submitted = False
    
    if not st.session_state.init_admin_submitted:
        with st.form("init_admin_form"):
            st.markdown("### 🔐 보안 확인")
            secret_key = st.text_input("관리자 생성 시크릿 키 *", type="password", 
                                     placeholder="시스템 관리자에게 문의하세요")
            
            st.markdown("### 👤 관리자 정보")
            col1, col2 = st.columns(2)
            
            with col1:
                username = st.text_input("사용자명 *", placeholder="admin")
                email = st.text_input("이메일 *", placeholder="admin@company.com")
                name = st.text_input("이름 *", placeholder="시스템관리자")
            
            with col2:
                password = st.text_input("비밀번호 *", type="password", 
                                       help="8자 이상, 영문/숫자/특수문자 포함")
                confirm_password = st.text_input("비밀번호 확인 *", type="password")
                role = st.selectbox("역할", ["admin"], disabled=True)
            
            # 비밀번호 강도 검사
            password_strength = 0
            if password:
                if len(password) >= 8:
                    password_strength += 1
                if any(c.isupper() for c in password):
                    password_strength += 1
                if any(c.islower() for c in password):
                    password_strength += 1
                if any(c.isdigit() for c in password):
                    password_strength += 1
                if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
                    password_strength += 1
            
            # 비밀번호 강도 표시
            if password:
                strength_text = ["매우 약함", "약함", "보통", "강함", "매우 강함"][min(password_strength - 1, 4)]
                strength_color = ["red", "orange", "yellow", "lightgreen", "green"][min(password_strength - 1, 4)]
                st.markdown(f"**비밀번호 강도: :{strength_color}[{strength_text}]**")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                submitted = st.form_submit_button("관리자 생성", type="primary")
            with col2:
                cancel_clicked = st.form_submit_button("취소")
            
            if submitted:
                # 시크릿 키 검증 (실제로는 환경 변수나 설정 파일에서 가져와야 함)
                expected_secret = "ADMIN_SETUP_2025"  # 실제로는 환경 변수에서 가져와야 함
                
                if secret_key != expected_secret:
                    st.error("❌ 시크릿 키가 올바르지 않습니다.")
                    return
                
                if not all([username, email, name, password, confirm_password]):
                    st.error("모든 필수 필드를 입력해주세요.")
                    return
                
                if password != confirm_password:
                    st.error("비밀번호가 일치하지 않습니다.")
                    return
                
                if password_strength < 3:
                    st.error("비밀번호가 너무 약합니다. 더 강한 비밀번호를 사용하세요.")
                    return
                
                # 이메일 형식 검증
                if "@" not in email or "." not in email:
                    st.error("올바른 이메일 형식을 입력해주세요.")
                    return
                
                # 폼 데이터를 세션에 저장
                st.session_state.init_admin_data = {
                    "username": username,
                    "email": email,
                    "name": name,
                    "password": password,
                    "role": "admin"
                }
                st.session_state.init_admin_submitted = True
                st.rerun()
            
            if cancel_clicked:
                st.session_state.show_init_admin = False
                st.rerun()
    else:
        # 관리자 생성 처리
        data = st.session_state.init_admin_data
        
        st.markdown("### 🔍 관리자 생성 확인")
        st.info("다음 정보로 관리자 계정을 생성합니다:")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**사용자명:** {data['username']}")
            st.write(f"**이름:** {data['name']}")
        with col2:
            st.write(f"**이메일:** {data['email']}")
            st.write(f"**역할:** {data['role']}")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("✅ 관리자 계정 생성", type="primary"):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/admin/init-admin",
                        json=data,
                        timeout=10,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if response.status_code == 200:
                        st.success("✅ 관리자 계정이 성공적으로 생성되었습니다!")
                        st.info("이제 로그인 페이지로 돌아가서 새로 생성된 계정으로 로그인하세요.")
                        
                        # 보안을 위해 생성 후 시크릿 키 변경 권장
                        st.warning("⚠️ 보안을 위해 관리자 생성 시크릿 키를 변경하는 것을 권장합니다.")
                        
                        # 상태 초기화
                        st.session_state.init_admin_submitted = False
                        st.session_state.show_init_admin = False
                        if st.button("로그인 페이지로 돌아가기"):
                            st.rerun()
                    else:
                        try:
                            error_data = response.json()
                            error_message = error_data.get('detail', '알 수 없는 오류')
                            if isinstance(error_message, list):
                                error_message = error_message[0].get('msg', '알 수 없는 오류')
                            st.error(f"❌ 관리자 생성 실패: {error_message}")
                        except:
                            st.error(f"❌ 관리자 생성 실패: HTTP {response.status_code}")
                        
                        # 상태 초기화하여 다시 시도할 수 있도록 함
                        st.session_state.init_admin_submitted = False
                        if st.button("다시 시도"):
                            st.rerun()
                except requests.exceptions.Timeout:
                    st.error("❌ 요청 시간이 초과되었습니다. 서버 상태를 확인해주세요.")
                    st.session_state.init_admin_submitted = False
                    if st.button("다시 시도"):
                        st.rerun()
                except requests.exceptions.ConnectionError:
                    st.error("❌ API 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
                    st.session_state.init_admin_submitted = False
                    if st.button("다시 시도"):
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ 관리자 생성 중 오류가 발생했습니다: {str(e)}")
                    st.info("💡 디버깅 정보:")
                    st.code(f"오류 타입: {type(e).__name__}")
                    st.code(f"오류 메시지: {str(e)}")
                    # 상태 초기화
                    st.session_state.init_admin_submitted = False
                    if st.button("다시 시도"):
                        st.rerun()
        
        with col2:
            if st.button("← 수정하기"):
                st.session_state.init_admin_submitted = False
                st.rerun()
    
    # 뒤로가기 버튼
    if st.button("← 로그인으로 돌아가기"):
        st.session_state.show_init_admin = False
        st.rerun()

def show_dashboard():
    """대시보드 메인 페이지"""
    # 세션 유효성 재확인
    if not check_session_validity():
        st.error("세션이 만료되었습니다. 다시 로그인해주세요.")
        logout_user()
        st.rerun()
        return
    
    # 헤더에 사용자 정보 표시
    if st.session_state.current_user:
        user_info = st.session_state.current_user
        
        # 로그인 시간 표시
        login_time_str = ""
        if st.session_state.login_time:
            login_time = datetime.fromisoformat(st.session_state.login_time)
            login_time_str = login_time.strftime("%Y-%m-%d %H:%M")
        
        st.sidebar.markdown(f"**👤 {user_info.get('name', '관리자')}**")
        st.sidebar.markdown(f"📧 {user_info.get('email', '')}")
        if login_time_str:
            st.sidebar.markdown(f"🕐 로그인: {login_time_str}")
        
        # 세션 상태 표시
        if st.session_state.login_time:
            login_time = datetime.fromisoformat(st.session_state.login_time)
            elapsed_time = datetime.now() - login_time
            hours = int(elapsed_time.total_seconds() // 3600)
            minutes = int((elapsed_time.total_seconds() % 3600) // 60)
            st.sidebar.markdown(f"⏱️ 세션 시간: {hours}시간 {minutes}분")
        
        if st.sidebar.button("🚪 로그아웃"):
            logout_user()
            st.rerun()
    
    st.title("🚀 시스템 통합 대시보드")
    
    # 사이드바
    st.sidebar.title("📊 대시보드 메뉴")
    page = st.sidebar.selectbox(
        "페이지 선택",
        ["📈 시스템 현황", "👥 엔티티 관리", "✅ 승인 시스템", "⚙️ 설정"]
    )
    
    # API 연결 상태 확인
    if not check_api_connection():
        st.error("❌ API 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
        return
    
    if page == "📈 시스템 현황":
        show_system_status()
    elif page == "👥 엔티티 관리":
        show_entity_management()
    elif page == "✅ 승인 시스템":
        show_approval_system()
    elif page == "⚙️ 설정":
        show_settings()

def show_system_status():
    """시스템 현황 페이지"""
    st.header("📈 시스템 현황")
    
    # 통계 조회
    stats = get_dashboard_stats()
    approval_stats = get_approval_stats()
    
    if not stats:
        st.warning("통계 데이터를 불러올 수 없습니다.")
        return
    
    # 메트릭 카드
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        recent_uploads = stats.get('recent_uploads', {})
        recent_count = 0
        if isinstance(recent_uploads, dict):
            recent_count = recent_uploads.get('count', 0)
        elif isinstance(recent_uploads, list):
            recent_count = len(recent_uploads)
        
        st.metric(
            "📄 총 문서 수",
            f"{stats.get('total_documents', 0):,}",
            f"+{recent_count}"
        )
    
    with col2:
        auto_created_by_type = stats.get('auto_created_by_type', {})
        employee_count = 0
        if isinstance(auto_created_by_type, dict):
            employee_count = auto_created_by_type.get('employee', 0)
        
        st.metric(
            "🤖 자동 생성 수",
            f"{stats.get('total_auto_created', 0):,}",
            f"+{employee_count}"
        )
    
    with col3:
        success_rate = stats.get('upload_success_rate', 0)
        st.metric(
            "📊 업로드 성공률",
            f"{success_rate:.1f}%",
            f"{'🟢' if success_rate >= 90 else '🟡' if success_rate >= 70 else '🔴'}"
        )
    
    with col4:
        if approval_stats:
            pending_total = (
                approval_stats.get('employee', {}).get('pending', 0) +
                approval_stats.get('customer', {}).get('pending', 0) +
                approval_stats.get('product', {}).get('pending', 0)
            )
            st.metric(
                "⏳ 승인 대기",
                f"{pending_total}",
                f"직원: {approval_stats.get('employee', {}).get('pending', 0)}"
            )
    
    # 차트 섹션
    st.subheader("📊 데이터 분석")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 자동 생성 타입별 분포
        auto_created_by_type = stats.get('auto_created_by_type', {})
        if isinstance(auto_created_by_type, dict) and auto_created_by_type:
            fig = px.pie(
                values=list(auto_created_by_type.values()),
                names=list(auto_created_by_type.keys()),
                title="자동 생성 타입별 분포"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("자동 생성 데이터가 없습니다.")
    
    with col2:
        # 최근 업로드 현황
        recent_uploads = stats.get('recent_uploads', [])
        if isinstance(recent_uploads, list) and recent_uploads:
            try:
                df = pd.DataFrame(recent_uploads)
                if not df.empty:
                    fig = px.bar(
                        df,
                        x='created_at',
                        y='count',
                        title="최근 업로드 현황"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("최근 업로드 데이터가 없습니다.")
            except Exception as e:
                st.info("최근 업로드 차트를 표시할 수 없습니다.")
        else:
            st.info("최근 업로드 데이터가 없습니다.")
    
    # 시스템 상태
    st.subheader("🔧 시스템 상태")
    
    # 시스템 클릭 상태 관리
    if 'selected_system' not in st.session_state:
        st.session_state.selected_system = None
    
    # 시스템 카드들
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="border: 2px solid #4CAF50; border-radius: 10px; padding: 15px; text-align: center; background-color: #f0f8f0;">
            <h3>🟢 PostgreSQL</h3>
            <p>데이터베이스 연결됨</p>
            <p style="font-size: 12px; color: #666;">pgAdmin: localhost:5050</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1_1, col1_2 = st.columns([1, 1])
        with col1_1:
            if st.button("🌐 열기", key="postgres_open", use_container_width=True):
                st.markdown("""
                <script>
                    window.open('http://localhost:5050', '_blank');
                </script>
                """, unsafe_allow_html=True)
                st.success("pgAdmin이 새 탭에서 열립니다!")
        
        with col1_2:
            if st.button("📊 목록", key="postgres_list", use_container_width=True):
                st.session_state.selected_system = "postgresql"
                st.rerun()
    
    with col2:
        st.markdown("""
        <div style="border: 2px solid #2196F3; border-radius: 10px; padding: 15px; text-align: center; background-color: #f0f8ff;">
            <h3>🟢 MinIO</h3>
            <p>파일 저장소 연결됨</p>
            <p style="font-size: 12px; color: #666;">Console: localhost:9001</p>
        </div>
        """, unsafe_allow_html=True)
        
        col2_1, col2_2 = st.columns([1, 1])
        with col2_1:
            if st.button("🌐 열기", key="minio_open", use_container_width=True):
                st.markdown("""
                <script>
                    window.open('http://localhost:9001', '_blank');
                </script>
                """, unsafe_allow_html=True)
                st.success("MinIO Console이 새 탭에서 열립니다!")
        
        with col2_2:
            if st.button("📁 목록", key="minio_list", use_container_width=True):
                st.session_state.selected_system = "minio"
                st.rerun()
    
    with col3:
        st.markdown("""
        <div style="border: 2px solid #FF9800; border-radius: 10px; padding: 15px; text-align: center; background-color: #fff8f0;">
            <h3>🟢 OpenSearch</h3>
            <p>검색 엔진 연결됨</p>
            <p style="font-size: 12px; color: #666;">Dashboards: localhost:5601</p>
        </div>
        """, unsafe_allow_html=True)
        
        col3_1, col3_2 = st.columns([1, 1])
        with col3_1:
            if st.button("🌐 열기", key="opensearch_open", use_container_width=True):
                st.markdown("""
                <script>
                    window.open('http://localhost:5601', '_blank');
                </script>
                """, unsafe_allow_html=True)
                st.success("OpenSearch Dashboards가 새 탭에서 열립니다!")
        
        with col3_2:
            if st.button("🔍 목록", key="opensearch_list", use_container_width=True):
                st.session_state.selected_system = "opensearch"
                st.rerun()
    
    # 선택된 시스템의 상세 정보 표시
    if st.session_state.selected_system:
        st.markdown("---")
        
        if st.session_state.selected_system == "postgresql":
            st.success("📊 PostgreSQL 문서 목록")
            st.write("🔍 PostgreSQL 문서 조회 중...")
            documents = get_system_documents("postgresql")
            
            if documents is None:
                st.error("❌ 문서 조회에 실패했습니다.")
            elif documents and documents.get('documents'):
                df = pd.DataFrame(documents['documents'])
                st.dataframe(df, use_container_width=True)
                st.success(f"✅ 총 {len(documents['documents'])}개의 문서가 데이터베이스에 저장되어 있습니다.")
            else:
                st.warning("⚠️ 데이터베이스에 저장된 문서가 없습니다.")
                st.info("💡 문서를 업로드하면 여기에 표시됩니다.")
        
        elif st.session_state.selected_system == "minio":
            st.success("📁 MinIO 파일 목록")
            st.write("🔍 MinIO 파일 조회 중...")
            documents = get_system_documents("minio")
            
            if documents is None:
                st.error("❌ 파일 조회에 실패했습니다.")
            elif documents and documents.get('files'):
                df = pd.DataFrame(documents['files'])
                st.dataframe(df, use_container_width=True)
                st.success(f"✅ 총 {len(documents['files'])}개의 파일이 MinIO에 저장되어 있습니다.")
            else:
                st.warning("⚠️ MinIO에 저장된 파일이 없습니다.")
                st.info("💡 문서를 업로드하면 여기에 표시됩니다.")
        
        elif st.session_state.selected_system == "opensearch":
            st.success("🔍 OpenSearch 인덱스 목록")
            st.write("🔍 OpenSearch 인덱스 조회 중...")
            documents = get_system_documents("opensearch")
            
            if documents is None:
                st.error("❌ 인덱스 조회에 실패했습니다.")
            elif documents and documents.get('indices'):
                # 데이터프레임 생성 및 컬럼 정리
                df = pd.DataFrame(documents['indices'])
                
                # 컬럼명 한글로 변경
                df = df.rename(columns={
                    'index_name': '인덱스명',
                    'document_count': '문서 수',
                    'size_bytes': '크기 (bytes)',
                    'created_date': '생성일',
                    'title': '문서 제목'
                })
                
                # 크기를 읽기 쉬운 형태로 변환
                df['크기 (KB)'] = (df['크기 (bytes)'] / 1024).round(2)
                
                # 생성일을 한국 시간으로 변환
                df['생성일'] = pd.to_datetime(df['생성일']).dt.strftime('%Y-%m-%d %H:%M:%S')
                
                # 표시할 컬럼만 선택
                display_df = df[['문서 제목', '인덱스명', '문서 수', '크기 (KB)', '생성일']]
                
                st.dataframe(display_df, use_container_width=True)
                
                # 통계 정보 표시
                total_documents = df['문서 수'].sum()
                total_size_kb = df['크기 (KB)'].sum()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📊 총 인덱스 수", len(df))
                with col2:
                    st.metric("📄 총 문서 수", total_documents)
                with col3:
                    st.metric("💾 총 크기", f"{total_size_kb:.2f} KB")
                
                st.success(f"✅ 총 {len(documents['indices'])}개의 인덱스가 OpenSearch에 있습니다.")
            else:
                st.warning("⚠️ OpenSearch에 인덱스가 없습니다.")
                st.info("💡 문서를 업로드하면 여기에 표시됩니다.")
        
        # 뒤로가기 버튼
        if st.button("← 시스템 상태로 돌아가기"):
            st.session_state.selected_system = None
            st.rerun()

def show_entity_management():
    """엔티티 관리 페이지"""
    st.header("👥 엔티티 관리")
    
    # 탭 구성
    tab1, tab2, tab3 = st.tabs(["👤 직원 관리", "🏥 고객 관리", "📦 제품 관리"])
    
    with tab1:
        st.subheader("👤 직원 관리")
        st.info("직원 정보는 문서 업로드를 통해 자동으로 생성됩니다.")
        
        # 직원 등록 폼 (수동 등록용)
        with st.expander("➕ 수동 직원 등록"):
            with st.form("employee_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    name = st.text_input("이름 *")
                    employee_number = st.text_input("사번 *")
                    team = st.text_input("팀")
                    position = st.text_input("직급")
                
                with col2:
                    business_unit = st.text_input("사업부")
                    branch = st.text_input("지점")
                    contact_number = st.text_input("연락처")
                    base_salary = st.number_input("기본급", min_value=0)
                
                submitted = st.form_submit_button("등록")
                if submitted:
                    st.success("직원 등록 기능은 API를 통해 구현됩니다.")
    
    with tab2:
        st.subheader("🏥 고객 관리")
        st.info("고객 정보는 문서 업로드를 통해 자동으로 생성됩니다.")
        
        # 고객 등록 폼
        with st.expander("➕ 수동 고객 등록"):
            with st.form("customer_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    customer_name = st.text_input("고객명 *")
                    address = st.text_input("주소")
                    doctor_name = st.text_input("담당의사")
                
                with col2:
                    total_patients = st.number_input("총 환자수", min_value=0)
                    customer_grade = st.selectbox("등급", ["A", "B", "C", "VIP"])
                    notes = st.text_area("메모")
                
                submitted = st.form_submit_button("등록")
                if submitted:
                    st.success("고객 등록 기능은 API를 통해 구현됩니다.")
    
    with tab3:
        st.subheader("📦 제품 관리")
        st.info("제품 정보는 문서 업로드를 통해 자동으로 생성됩니다.")
        
        # 제품 등록 폼
        with st.expander("➕ 수동 제품 등록"):
            with st.form("product_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    product_name = st.text_input("제품명 *")
                    description = st.text_area("설명")
                
                with col2:
                    category = st.selectbox("카테고리", ["의약품", "의료기기", "건강기능식품", "기타"])
                    is_active = st.checkbox("활성화", value=True)
                
                submitted = st.form_submit_button("등록")
                if submitted:
                    st.success("제품 등록 기능은 API를 통해 구현됩니다.")

def show_approval_system():
    """승인 시스템 페이지"""
    st.header("✅ 승인 시스템")
    
    # 승인 통계
    approval_stats = get_approval_stats()
    
    if approval_stats:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            emp_stats = approval_stats.get('employee', {})
            st.metric("👤 직원 승인", f"{emp_stats.get('pending', 0)} 대기", f"{emp_stats.get('approved', 0)} 승인됨")
        
        with col2:
            cust_stats = approval_stats.get('customer', {})
            st.metric("🏥 고객 승인", f"{cust_stats.get('pending', 0)} 대기", f"{cust_stats.get('approved', 0)} 승인됨")
        
        with col3:
            prod_stats = approval_stats.get('product', {})
            st.metric("📦 제품 승인", f"{prod_stats.get('pending', 0)} 대기", f"{prod_stats.get('approved', 0)} 승인됨")
    
    # 승인 대기 목록
    st.subheader("⏳ 승인 대기 목록")
    
    entity_type = st.selectbox("엔티티 타입", ["전체", "employee", "customer", "product"])
    
    pending_items = get_pending_approvals(None if entity_type == "전체" else entity_type)
    
    if pending_items and pending_items.get('items'):
        items = pending_items['items']
        
        for item in items:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                
                with col1:
                    st.write(f"**{item['name']}**")
                    if item['entity_type'] == 'employee':
                        st.write(f"사번: {item.get('employee_number', 'N/A')}")
                        st.write(f"팀: {item.get('team', 'N/A')}")
                    elif item['entity_type'] == 'customer':
                        st.write(f"주소: {item.get('address', 'N/A')}")
                        st.write(f"담당의: {item.get('doctor_name', 'N/A')}")
                    elif item['entity_type'] == 'product':
                        st.write(f"카테고리: {item.get('category', 'N/A')}")
                        st.write(f"설명: {item.get('description', 'N/A')}")
                
                with col2:
                    st.write(f"타입: {item['entity_type']}")
                    st.write(f"생성일: {item.get('created_at', 'N/A')}")
                
                with col3:
                    if st.button(f"✅ 승인", key=f"approve_{item['entity_type']}_{item['entity_id']}"):
                        notes = st.text_input("승인 메모 (선택사항)", key=f"approve_notes_{item['entity_id']}")
                        if approve_entity(item['entity_type'], item['entity_id'], notes):
                            st.success("승인 완료!")
                            st.rerun()
                        else:
                            st.error("승인 실패")
                
                with col4:
                    if st.button(f"❌ 거부", key=f"reject_{item['entity_type']}_{item['entity_id']}"):
                        notes = st.text_input("거부 사유 *", key=f"reject_notes_{item['entity_id']}")
                        if notes and reject_entity(item['entity_type'], item['entity_id'], notes):
                            st.success("거부 완료!")
                            st.rerun()
                        elif not notes:
                            st.error("거부 사유를 입력해주세요")
                        else:
                            st.error("거부 실패")
                
                st.divider()
    else:
        st.info("승인 대기 중인 항목이 없습니다.")

def show_settings():
    """설정 페이지"""
    st.header("⚙️ 설정")
    
    st.subheader("🔧 시스템 설정")
    
    # API URL 설정
    api_url = st.text_input("API 서버 URL", value=API_BASE_URL)
    
    # 새로고침 간격 설정
    refresh_interval = st.slider("자동 새로고침 간격 (초)", 10, 300, 60)
    
    # 데이터 보존 기간 설정
    retention_days = st.number_input("데이터 보존 기간 (일)", 30, 365, 90)
    
    if st.button("설정 저장"):
        st.success("설정이 저장되었습니다.")
    
    st.subheader("📊 데이터 내보내기")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 문서 데이터 내보내기"):
            st.info("문서 데이터 내보내기 기능은 API를 통해 구현됩니다.")
    
    with col2:
        if st.button("📊 통계 데이터 내보내기"):
            st.info("통계 데이터 내보내기 기능은 API를 통해 구현됩니다.")

if __name__ == "__main__":
    # 세션 유효성 확인
    if st.session_state.authenticated:
        if not check_session_validity():
            st.warning("세션이 만료되었습니다. 다시 로그인해주세요.")
            show_login_page()
        else:
            show_dashboard()
    else:
        show_login_page() 