import React, { useState } from 'react';
import './ClientPage.css';

const ClientPage = () => {
  const [clients, setClients] = useState([
    {
      id: 1,
      name: 'A병원',
      type: '병원',
      contact: '김의사',
      phone: '02-1234-5678',
      address: '서울시 강남구',
      status: '활성',
      lastVisit: '2024-07-15',
    },
    {
      id: 2,
      name: 'B약국',
      type: '약국',
      contact: '이약사',
      phone: '02-2345-6789',
      address: '서울시 서초구',
      status: '활성',
      lastVisit: '2024-07-14',
    },
    {
      id: 3,
      name: 'C의원',
      type: '의원',
      contact: '박원장',
      phone: '02-3456-7890',
      address: '서울시 마포구',
      status: '비활성',
      lastVisit: '2024-07-10',
    },
  ]);

  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');

  const filteredClients = clients.filter(client => {
    const matchesSearch = client.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         client.contact.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterType === 'all' || client.type === filterType;
    return matchesSearch && matchesFilter;
  });

  return (
    <div className="client-page">
      <div className="client-header">
        <h1>👥 고객 관리</h1>
        <p>고객 정보를 관리하고 방문 일정을 확인하세요</p>
      </div>

      <div className="client-controls">
        <div className="search-control">
          <input
            type="text"
            placeholder="고객명 또는 담당자로 검색..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="client-search"
          />
        </div>
        
        <div className="filter-control">
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="client-filter"
          >
            <option value="all">전체</option>
            <option value="병원">병원</option>
            <option value="약국">약국</option>
            <option value="의원">의원</option>
          </select>
        </div>

        <button className="add-client-btn">+ 새 고객 추가</button>
      </div>

      <div className="client-stats">
        <div className="stat-card">
          <h3>총 고객 수</h3>
          <div className="stat-value">{clients.length}</div>
        </div>
        <div className="stat-card">
          <h3>활성 고객</h3>
          <div className="stat-value">{clients.filter(c => c.status === '활성').length}</div>
        </div>
        <div className="stat-card">
          <h3>이번 달 방문</h3>
          <div className="stat-value">12</div>
        </div>
      </div>

      <div className="client-list">
        <div className="client-list-header">
          <h3>고객 목록</h3>
          <span className="client-count">총 {filteredClients.length}개</span>
        </div>
        
        <div className="client-table">
          <div className="table-header">
            <div className="header-cell">고객명</div>
            <div className="header-cell">유형</div>
            <div className="header-cell">담당자</div>
            <div className="header-cell">연락처</div>
            <div className="header-cell">주소</div>
            <div className="header-cell">상태</div>
            <div className="header-cell">최근 방문</div>
            <div className="header-cell">작업</div>
          </div>
          
          {filteredClients.map(client => (
            <div key={client.id} className="table-row">
              <div className="table-cell client-name">{client.name}</div>
              <div className="table-cell">
                <span className={`client-type ${client.type}`}>{client.type}</span>
              </div>
              <div className="table-cell">{client.contact}</div>
              <div className="table-cell">{client.phone}</div>
              <div className="table-cell">{client.address}</div>
              <div className="table-cell">
                <span className={`status-badge ${client.status}`}>
                  {client.status}
                </span>
              </div>
              <div className="table-cell">{client.lastVisit}</div>
              <div className="table-cell actions">
                <button className="action-btn edit">수정</button>
                <button className="action-btn visit">방문</button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ClientPage; 