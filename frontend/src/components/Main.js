import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getTodaySchedules, getDashboardStats } from '../services/api';
import './Main.css';

const Main = ({ currentUser }) => {
  const navigate = useNavigate();
  const isAdmin = currentUser?.role === 'admin';

  // 오늘 날짜 가져오기
  const getTodayDate = () => {
    // 임시로 2025-08-16 날짜 사용
    return '2025-08-16';
    // const today = new Date();
    // const year = today.getFullYear();
    // const month = String(today.getMonth() + 1).padStart(2, '0');
    // const day = String(today.getDate()).padStart(2, '0');
    // return `${year}-${month}-${day}`;
  };

  // 오늘 일정 상태
  const [todaySchedules, setTodaySchedules] = useState([]);
  const [scheduleLoading, setScheduleLoading] = useState(false);
  
  // 실적 달성률 상태
  const [achievementRate, setAchievementRate] = useState('0%');
  const [monthlyGrowth, setMonthlyGrowth] = useState('0%');
  const [quarterTotal, setQuarterTotal] = useState('₩0');
  const [statsLoading, setStatsLoading] = useState(false);

  // 관리자용 요약 카드
  const adminSummaryCards = [
    { title: '전체 사용자 수', value: '0명', color: '#6f42c1' },
    { title: '오늘 로그인 사용자', value: '0명', color: '#20c997' },
    { title: '시스템 알림', value: '0건', color: '#fd7e14' },
  ];

  // 오늘 날짜 포맷팅
  const today = new Date();
  const todayFormatted = `${today.getMonth() + 1}월 ${today.getDate()}일`;
  const dayOfWeek = ['일', '월', '화', '수', '목', '금', '토'][today.getDay()];
  
  // 일반 사용자용 요약 카드
  const userSummaryCards = [
    { title: '오늘 날짜', value: `${todayFormatted} (${dayOfWeek})`, color: '#8a63d2' },
    { title: '오늘 방문 일정', value: `${todaySchedules.length}건`, color: '#6f42c1' },
    { title: '이번달 실적 달성률', value: achievementRate, color: '#4b2c91' },
  ];

  const summaryCards = isAdmin ? adminSummaryCards : userSummaryCards;

  // 현재 일정 (관리자/사용자 구분)
  const dailySchedule = isAdmin ? [] : todaySchedules;

  // AI 제안 내용
  const aiSuggestion = isAdmin 
    ? "서버 리소스 모니터링을 권장합니다."
    : "오늘 일정을 확인하고 계획을 세워보세요.";

  const scheduleTitle = isAdmin ? "관리 업무 일정" : "나의 일일 계획";
  const scheduleIcon = isAdmin ? "⚙️" : "💼";

  // 뉴스 상태
  const [pharmaNews, setPharmaNews] = useState([]);
  const [generalNews, setGeneralNews] = useState([]);
  const [newsLoading, setNewsLoading] = useState(false);

  // 컴포넌트 마운트 시 데이터 가져오기
  useEffect(() => {
    fetchAllNews();
    if (!isAdmin) {
      fetchTodaySchedules();
      fetchDashboardStats();
    }
  }, [isAdmin]);

  // 오늘 일정 가져오기
  const fetchTodaySchedules = async () => {
    setScheduleLoading(true);
    try {
      const schedules = await getTodaySchedules();
      console.log('📅 오늘 일정 조회 결과:', schedules);
      setTodaySchedules(schedules || []);
    } catch (error) {
      console.error('일정 가져오기 실패:', error);
      setTodaySchedules([]);
    } finally {
      setScheduleLoading(false);
    }
  };

  // 대시보드 통계 가져오기
  const fetchDashboardStats = async () => {
    setStatsLoading(true);
    try {
      const stats = await getDashboardStats();
      console.log('📊 대시보드 통계:', stats);
      if (stats && stats.stats) {
        // 목표 달성률 (첫 번째 stat)
        if (stats.stats[0]) {
          setAchievementRate(stats.stats[0].value);
          console.log('🎯 목표 달성률:', stats.stats[0].value);
        }
        // 매출 증감률 (두 번째 stat)
        if (stats.stats[1]) {
          setMonthlyGrowth(stats.stats[1].value);
          console.log('📈 매출 증감률:', stats.stats[1].value);
        }
        // 분기 총 실적 (세 번째 stat)
        if (stats.stats[2]) {
          setQuarterTotal(stats.stats[2].value);
          console.log('💰 분기 총 실적:', stats.stats[2].value);
        }
      } else {
        console.log('⚠️ 통계 데이터가 비어있음');
      }
    } catch (error) {
      console.error('❌ 통계 가져오기 실패:', error);
      if (error.response) {
        console.error('응답 상태:', error.response.status);
        console.error('응답 데이터:', error.response.data);
      }
      setAchievementRate('0%');
      setMonthlyGrowth('0%');
      setQuarterTotal('₩0');
    } finally {
      setStatsLoading(false);
    }
  };

  // 모든 뉴스 가져오기
  const fetchAllNews = async () => {
    setNewsLoading(true);
    const token = localStorage.getItem('access_token') || localStorage.getItem('narutalk_token');
    
    console.log('📰 뉴스 API 호출 시작');
    
    try {
      // 검색 API를 사용하여 날짜 제한 없이 뉴스 가져오기
      const [pharmaResponse, generalResponse] = await Promise.all([
        fetch(`http://localhost:8010/news/search?news_type=pharmaceutical&limit=10`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }),
        fetch(`http://localhost:8010/news/search?news_type=general&limit=10`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        })
      ]);

      // 제약 뉴스 처리
      if (pharmaResponse.ok) {
        const pharmaData = await pharmaResponse.json();
        console.log('💊 제약 뉴스:', pharmaData.length, '개');
        
        // 랜덤하게 2개 선택
        const shuffledPharma = [...pharmaData].sort(() => Math.random() - 0.5);
        const formattedPharmaNews = shuffledPharma.slice(0, 2).map(news => ({
          id: news.news_id,
          title: news.title,
          category: news.source || "제약 뉴스",
          date: news.published_date ? new Date(news.published_date).toLocaleDateString('ko-KR') : "날짜 없음",
          url: news.url,
          type: 'pharmaceutical'
        }));
        setPharmaNews(formattedPharmaNews);
      } else {
        console.error('제약 뉴스 조회 실패:', pharmaResponse.status);
        setPharmaNews([]);
      }

      // 일반 뉴스 처리
      if (generalResponse.ok) {
        const generalData = await generalResponse.json();
        console.log('📰 일반 뉴스:', generalData.length, '개');
        
        // 랜덤하게 1개 선택
        const randomIndex = Math.floor(Math.random() * generalData.length);
        const selectedNews = generalData[randomIndex] || generalData[0];
        
        const formattedGeneralNews = selectedNews ? [{
          id: selectedNews.news_id,
          title: selectedNews.title,
          category: selectedNews.source || "일반 뉴스",
          date: selectedNews.published_date ? new Date(selectedNews.published_date).toLocaleDateString('ko-KR') : "날짜 없음",
          url: selectedNews.url,
          type: 'general'
        }] : [];
        setGeneralNews(formattedGeneralNews);
      } else {
        console.error('일반 뉴스 조회 실패:', generalResponse.status);
        setGeneralNews([]);
      }

    } catch (error) {
      console.error('❌ 뉴스 가져오기 오류:', error);
      setPharmaNews([]);
      setGeneralNews([]);
    } finally {
      setNewsLoading(false);
    }
  };

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>{currentUser?.name || '사용자'}님, 좋은 하루입니다!</h1>
        {isAdmin && (
          <div className="admin-badge" style={{
            backgroundColor: '#dc3545',
            color: 'white',
            padding: '4px 12px',
            borderRadius: '20px',
            fontSize: '12px',
            fontWeight: 'bold',
            marginTop: '8px',
            display: 'inline-block'
          }}>
            🛡️ 시스템 관리자
          </div>
        )}
      </div>

      {/* 요약 정보 카드 */}
      <div className="summary-cards">
        {summaryCards.map((card, index) => (
          <div key={index} className="summary-card">
            <h3>{card.title}</h3>
            <div className="card-value" style={{ color: card.color }}>
              {card.value}
            </div>
          </div>
        ))}
      </div>

      {/* 뉴스 섹션 - 관리자/직원 공통 */}
      <div className="pharma-news-section">
        <div className="news-section-header">
          <h3>
            <span style={{ marginRight: '8px' }}>📰</span>
            오늘의 뉴스
          </h3>
          <button 
            className="news-more-btn"
            onClick={() => navigate('/news')}
            style={{
              padding: '6px 16px',
              backgroundColor: '#6f42c1',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              fontSize: '0.9rem',
              cursor: 'pointer',
              transition: 'background-color 0.3s'
            }}
            onMouseOver={(e) => e.target.style.backgroundColor = '#5a32a3'}
            onMouseOut={(e) => e.target.style.backgroundColor = '#6f42c1'}
          >
            더보기 →
          </button>
        </div>
        <div className="news-list">
          {newsLoading ? (
            <div className="no-news">
              <p style={{ color: '#999', textAlign: 'center', padding: '20px' }}>
                뉴스를 불러오는 중입니다...
              </p>
            </div>
          ) : (pharmaNews.length > 0 || generalNews.length > 0) ? (
            <>
              {/* 제약 뉴스 표시 (최대 2개) */}
              {pharmaNews.map((news) => (
                <div 
                  key={`pharma-${news.id}`} 
                  className="news-item"
                  onClick={() => news.url && window.open(news.url, '_blank')}
                  style={{ cursor: news.url ? 'pointer' : 'default' }}
                >
                  <div className="news-content">
                    <div className="news-header">
                      <span className="news-category" style={{ backgroundColor: '#667eea' }}>
                        💊 {news.category}
                      </span>
                      <span className="news-date">{news.date}</span>
                    </div>
                    <div className="news-title">{news.title}</div>
                  </div>
                </div>
              ))}
              
              {/* 일반 뉴스 표시 (최대 1개) */}
              {generalNews.map((news) => (
                <div 
                  key={`general-${news.id}`} 
                  className="news-item"
                  onClick={() => news.url && window.open(news.url, '_blank')}
                  style={{ cursor: news.url ? 'pointer' : 'default' }}
                >
                  <div className="news-content">
                    <div className="news-header">
                      <span className="news-category">
                        📰 {news.category}
                      </span>
                      <span className="news-date">{news.date}</span>
                    </div>
                    <div className="news-title">{news.title}</div>
                  </div>
                </div>
              ))}
            </>
          ) : (
            <div className="no-news">
              <p style={{ color: '#999', textAlign: 'center', padding: '20px' }}>
                오늘의 뉴스가 없습니다.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* 일일 계획 섹션 - 일반 사용자만 */}
      {!isAdmin && (
        <div className="daily-plan">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h3>{scheduleTitle}</h3>
            <button 
              className="schedule-more-btn"
              onClick={() => navigate('/schedule')}
              style={{
                padding: '6px 16px',
                backgroundColor: '#6f42c1',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                fontSize: '0.9rem',
                cursor: 'pointer',
                transition: 'background-color 0.3s'
              }}
              onMouseOver={(e) => e.target.style.backgroundColor = '#5a32a3'}
              onMouseOut={(e) => e.target.style.backgroundColor = '#6f42c1'}
            >
              일정 관리 →
            </button>
          </div>
          <div className="schedule-list">
            {scheduleLoading ? (
              <div className="no-schedule">
                <p style={{ color: '#999', textAlign: 'center', padding: '20px' }}>
                  일정을 불러오는 중...
                </p>
              </div>
            ) : dailySchedule.length > 0 ? (
              dailySchedule.map((schedule, index) => (
                <div key={index} className="schedule-item">
                  <div className="schedule-icon">{scheduleIcon}</div>
                  <div className="schedule-details">
                    <div className="schedule-time">
                      {schedule.schedule_time ? schedule.schedule_time.substring(0, 5) : '시간 미정'}
                    </div>
                    <div className="schedule-location">
                      {schedule.location || schedule.title || '일정'}
                    </div>
                    {schedule.contact_person && (
                      <div className="schedule-contact" style={{ fontSize: '0.85rem', color: '#666' }}>
                        담당자: {schedule.contact_person}
                      </div>
                    )}
                  </div>
                  {index < dailySchedule.length - 1 && <div className="schedule-connector"></div>}
                </div>
              ))
            ) : (
              <div className="no-schedule">
                <p style={{ color: '#999', textAlign: 'center', padding: '20px' }}>
                  오늘 등록된 일정이 없습니다.
                </p>
                <button 
                  onClick={() => navigate('/schedule')}
                  style={{
                    display: 'block',
                    margin: '0 auto',
                    padding: '8px 20px',
                    backgroundColor: '#6f42c1',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer'
                  }}
                >
                  일정 추가하기
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Main; 