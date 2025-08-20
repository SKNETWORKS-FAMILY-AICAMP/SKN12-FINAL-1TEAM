import React, { useState, useEffect } from 'react';
import './News.css';

const News = () => {
  const [pharmaNews, setPharmaNews] = useState([]);
  const [generalNews, setGeneralNews] = useState([]);
  const [newsLoading, setNewsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('all'); // all, pharmaceutical, general

  // 오늘 날짜 가져오기
  const getTodayDate = () => {
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  useEffect(() => {
    fetchAllNews();
  }, []);

  const fetchAllNews = async () => {
    setNewsLoading(true);
    const token = localStorage.getItem('access_token') || localStorage.getItem('narutalk_token');
    const todayDate = getTodayDate();
    
    console.log('📰 오늘 날짜의 뉴스 API 호출 시작:', todayDate);
    
    try {
      // 오늘 날짜의 뉴스만 가져오기
      const [pharmaResponse, generalResponse] = await Promise.all([
        fetch(`http://localhost:8010/news/search?news_type=pharmaceutical&date=${todayDate}&limit=50`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }),
        fetch(`http://localhost:8010/news/search?news_type=general&date=${todayDate}&limit=50`, {
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
        console.log('💊 제약 뉴스 받음:', pharmaData.length, '개');
        
        // 오늘 날짜와 일치하는 뉴스만 필터링
        const todayNews = pharmaData.filter(news => {
          if (!news.published_date) return false;
          const newsDate = new Date(news.published_date).toISOString().split('T')[0];
          return newsDate === todayDate;
        });
        
        console.log(`💊 오늘 날짜(${todayDate}) 제약 뉴스:`, todayNews.length, '개');
        
        const formattedPharmaNews = todayNews.map(news => ({
          id: news.news_id,
          title: news.title,
          content: news.content,
          category: news.source || "제약 뉴스",
          date: news.published_date ? new Date(news.published_date).toLocaleDateString('ko-KR') : "날짜 없음",
          author: news.author,
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
        console.log('📰 일반 뉴스 받음:', generalData.length, '개');
        
        // 오늘 날짜와 일치하는 뉴스만 필터링
        const todayNews = generalData.filter(news => {
          if (!news.published_date) return false;
          const newsDate = new Date(news.published_date).toISOString().split('T')[0];
          return newsDate === todayDate;
        });
        
        console.log(`📰 오늘 날짜(${todayDate}) 일반 뉴스:`, todayNews.length, '개');
        
        const formattedGeneralNews = todayNews.map(news => ({
          id: news.news_id,
          title: news.title,
          content: news.content,
          category: news.source || "일반 뉴스",
          date: news.published_date ? new Date(news.published_date).toLocaleDateString('ko-KR') : "날짜 없음",
          author: news.author,
          url: news.url,
          type: 'general'
        }));
        setGeneralNews(formattedGeneralNews);
      } else {
        console.error('일반 뉴스 조회 실패:', generalResponse.status);
        setGeneralNews([]);
      }

    } catch (error) {
      console.error('뉴스 가져오기 오류:', error);
      setPharmaNews([]);
      setGeneralNews([]);
    } finally {
      setNewsLoading(false);
    }
  };

  // 탭에 따라 뉴스 필터링
  const getFilteredNews = () => {
    if (activeTab === 'pharmaceutical') return pharmaNews;
    if (activeTab === 'general') return generalNews;
    return [...pharmaNews, ...generalNews];
  };

  const filteredNews = getFilteredNews();

  return (
    <div className="news-page">
      <div className="news-header">
        <h1>뉴스
          
        </h1>
        <p>최신 의료 및 제약 업계 소식을 확인하세요</p>
      </div>

      {/* 탭 네비게이션 */}
      <div className="news-tabs">
        <button 
          className={`tab-btn ${activeTab === 'all' ? 'active' : ''}`}
          onClick={() => setActiveTab('all')}
        >
          전체 ({pharmaNews.length + generalNews.length})
        </button>
        <button 
          className={`tab-btn ${activeTab === 'pharmaceutical' ? 'active' : ''}`}
          onClick={() => setActiveTab('pharmaceutical')}
        >
          💊 제약 뉴스 ({pharmaNews.length})
        </button>
        <button 
          className={`tab-btn ${activeTab === 'general' ? 'active' : ''}`}
          onClick={() => setActiveTab('general')}
        >
          📰 일반 뉴스 ({generalNews.length})
        </button>
      </div>

      {/* 뉴스 목록 */}
      <div className="news-container">
        {newsLoading ? (
          <div className="loading-container">
            <p>뉴스를 불러오는 중입니다...</p>
          </div>
        ) : filteredNews.length > 0 ? (
          <div className="news-grid">
            {filteredNews.map((news) => (
              <div key={`${news.type}-${news.id}`} className="news-card">
                <div className="news-card-header">
                  <span className={`news-badge ${news.type === 'pharmaceutical' ? 'pharma' : 'general'}`}>
                    {news.type === 'pharmaceutical' ? '💊 제약' : '📰 일반'}
                  </span>
                  <span className="news-date">{news.date}</span>
                </div>
                <h3 className="news-card-title">{news.title}</h3>
                {news.content && (
                  <p className="news-card-content">
                    {news.content.length > 150 
                      ? news.content.substring(0, 150) + '...' 
                      : news.content}
                  </p>
                )}
                <div className="news-card-footer">
                  <div className="news-meta">
                    {news.author && <span className="news-author">✍️ {news.author}</span>}
                    {news.category && <span className="news-source">📍 {news.category}</span>}
                  </div>
                  {news.url && (
                    <a 
                      href={news.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="news-link"
                    >
                      원문 보기 →
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="no-news-container">
            <p>표시할 뉴스가 없습니다.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default News;