// src/components/MilestonePreviewPage.tsx
import React, { useState } from 'react';
import { config } from '../../Unauthenticated/config';
import './MilestonePage.css';

const MilestonePreviewPage = () => {
  const [viewMode, setViewMode] = useState<'detail' | 'gallery'>('detail');
  const [filterType, setFilterType] = useState<string>('all');
  
  // Get frontend base URL from config
  const FRONTEND_BASE_URL = config.FRONTEND_BASE_URL;
  
  // Generate mock milestone data for preview
  const generateMockMilestones = () => {
    const milestones = [];
    const types = ['connection', 'initiation', 'influence']; // Added 'connection' first
    const titles = [
      "First Steps", "Rising Star", "Community Builder", "Network Pioneer", 
      "Influence Leader", "Connection Master", "Engagement Expert", "Social Catalyst",
      "Conversation Starter", "Network Navigator"
    ];
    const descriptions = [
      "For making your first meaningful connection",
      "For helping others find their way in the community",
      "For creating valuable networking opportunities",
      "For pioneering new connections between people",
      "For your growing influence in professional circles",
      "For mastering the art of making connections",
      "For your expertise in engaging with others",
      "For catalyzing important social interactions",
      "For starting valuable conversations",
      "For skillfully navigating professional networks"
    ];
    
    // Generate 12 connection milestones
    for (let i = 1; i <= 12; i++) {
      const titleIndex = Math.floor(Math.random() * titles.length);
      const descIndex = Math.floor(Math.random() * descriptions.length);
      
      milestones.push({
        id: `connection-${i}`,
        type: 'connection',
        photo_id: i,
        title: titles[titleIndex],
        text: descriptions[descIndex],
        created_at: new Date(Date.now() - Math.floor(Math.random() * 365 * 24 * 60 * 60 * 1000)).toISOString()
      });
    }
    
    // Generate 16 initiation milestones
    for (let i = 1; i <= 16; i++) {
      const titleIndex = Math.floor(Math.random() * titles.length);
      const descIndex = Math.floor(Math.random() * descriptions.length);
      
      milestones.push({
        id: `initiation-${i}`,
        type: 'initiation',
        photo_id: i,
        title: titles[titleIndex],
        text: descriptions[descIndex],
        created_at: new Date(Date.now() - Math.floor(Math.random() * 365 * 24 * 60 * 60 * 1000)).toISOString()
      });
    }
    
    // Generate 22 influence milestones
    for (let i = 1; i <= 22; i++) {
      const titleIndex = Math.floor(Math.random() * titles.length);
      const descIndex = Math.floor(Math.random() * descriptions.length);
      
      milestones.push({
        id: `influence-${i}`,
        type: 'influence',
        photo_id: i,
        title: titles[titleIndex],
        text: descriptions[descIndex],
        created_at: new Date(Date.now() - Math.floor(Math.random() * 365 * 24 * 60 * 60 * 1000)).toISOString()
      });
    }
    
    return milestones;
  };
  
  const milestones = generateMockMilestones();
  
  // Reverse milestones to show latest first
  const reversedMilestones = [...milestones].reverse();
  
  // Filter milestones for gallery view
  const filteredMilestones = filterType === 'all' 
    ? reversedMilestones 
    : reversedMilestones.filter(m => m.type === filterType);

  return (
    <div className="milestone-page-container">
      <div className="milestone-page-header">
        <h1>Milestone Gallery Preview</h1>
        <p>Previewing all milestone images - 12 connection, 16 initiation, 22 influence</p>
        
        <div className="view-controls">
          <button 
            className={`view-button ${viewMode === 'detail' ? 'active' : ''}`}
            onClick={() => setViewMode('detail')}
          >
            Detail View
          </button>
          <button 
            className={`view-button ${viewMode === 'gallery' ? 'active' : ''}`}
            onClick={() => setViewMode('gallery')}
          >
            Photo Gallery
          </button>
          
          {viewMode === 'gallery' && (
            <div className="type-filter">
              <label htmlFor="type-filter">Filter by type:</label>
              <select 
                id="type-filter"
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
              >
                <option value="all">All Types (50)</option>
                <option value="connection">Connection (12)</option>
                <option value="initiation">Initiation (16)</option>
                <option value="influence">Influence (22)</option>
              </select>
            </div>
          )}
        </div>
      </div>

      {milestones.length === 0 ? (
        <div className="milestone-page-empty">
          <div className="milestone-page-empty-icon">🏆</div>
          <h3>No Milestones Yet</h3>
          <p>Continue building your network to earn achievements!</p>
        </div>
      ) : viewMode === 'detail' ? (
        <div className="milestone-grid">
          {reversedMilestones.map((milestone) => {
            const imgUrl = `${FRONTEND_BASE_URL}/${milestone.type}/${milestone.photo_id}.jpg`;
            const badgeClass = `milestone-badge milestone-badge-${milestone.type}`;

            return (
              <div key={milestone.id} className="milestone-card">
                <div className="card-top-section">
                  <div className={badgeClass}>
                    For: {milestone.type}
                  </div>
                </div>
                
                <div className="milestone-image-container">
                  <img
                    src={imgUrl}
                    alt={milestone.title}
                    className="milestone-image"
                    onError={(e) => {
                      (e.target as HTMLImageElement).src = `${FRONTEND_BASE_URL}/connection/1.jpg`;
                    }}
                  />
                </div>
                
                <div className="milestone-content">
                  <h3 className="milestone-title">{milestone.title.toUpperCase()}</h3>
                  <p className="milestone-description">{milestone.text}</p>
                  <div className="milestone-date">
                    Awarded on {new Date(milestone.created_at).toLocaleDateString()}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="gallery-grid">
          {filteredMilestones.map((milestone) => {
            const imgUrl = `${FRONTEND_BASE_URL}/${milestone.type}/${milestone.photo_id}.jpg`;
            
            return (
              <div key={milestone.id} className="gallery-item">
                <div className="gallery-image-container">
                  <img
                    src={imgUrl}
                    alt={milestone.title}
                    className="gallery-image"
                    onError={(e) => {
                      (e.target as HTMLImageElement).src = `${FRONTEND_BASE_URL}/connection/1.jpg`;
                    }}
                  />
                </div>
                <div className="gallery-caption">
                  <span className="gallery-type">{milestone.title}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
      
      <div className="preview-summary">
        <p>Previewing {filteredMilestones.length} milestone images</p>
        <p>Total Connection: 12 | Total Initiation: 16 | Total Influence: 22</p>
      </div>
    </div>
  );
};

export default MilestonePreviewPage;