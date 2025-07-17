import React, { useEffect } from 'react';
import './HeartbeatPage.css';
import { useDispatch, useSelector } from 'react-redux';
import type { AppDispatch, RootState } from "../../../store";
import { 
  checkUserActivity, 
  markUserActive, 
  invalidateIfStale,
  fetchActivityHistory
} from './heartbeatSlice';
import HeartbeatGraph from './HeartbeatGraph/HeartbeatGraph';

const HeartbeatPage: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const heartbeatState = useSelector((state: RootState) => state.heartbeat);
  
  const {
    heartState,
    streak,
    lastActiveDate,
    status,
    error,
    activityHistory,
    historyStatus
  } = heartbeatState;
  
  const userId = 11021801300001;

  useEffect(() => {
    dispatch(invalidateIfStale());
    
    if (status === 'idle') {
      dispatch(checkUserActivity(userId));
    }
    
    if (historyStatus === 'idle') {
      dispatch(fetchActivityHistory(userId));
    }
  }, [dispatch, status, historyStatus, userId]);

  const handleMarkActive = () => {
    if (heartState !== 'active' && heartState !== 'hyperactive') {
      dispatch(markUserActive(userId));
    }
  };

  const statusMessages = {
    inactive: "Your support is missed. Please contribute today!",
    passive: "You supported yesterday. Keep the momentum!",
    active: "Thank you for supporting the movement today!",
    hyperactive: "Amazing! Your daily support is fueling the movement!"
  };

  const getStreakInfo = () => {
    if (!lastActiveDate) return "No recent support";
    if (streak === 0) return "Start your support streak today!";
    if (streak === 1) return "Current streak: 1 day";
    if (streak >= 5) return `Current streak: ${streak} days! Keep going!`;
    return `Current streak: ${streak} days`;
  };

  const getHeartEmoji = () => {
    switch(heartState) {
      case 'inactive': return '🤍';
      case 'passive': return '❤️';
      case 'active': return '💓';
      case 'hyperactive': return '❤️‍🔥';
      default: return '🤍';
    }
  };

  const isLoading = status === 'loading';
  const showFireAnimation = heartState === 'hyperactive';
  const isHeartClickable = heartState !== 'active' && heartState !== 'hyperactive';

  return (
    <div className="heartbeat-page">
      <div className="heartbeat-container">
        <div className="heartbeat-header">
          <h1 className="heartbeat-title">Movement Heartbeat</h1>
          <p className="heartbeat-subtitle">Keep the movement alive with your daily support</p>
        </div>
        
        <div 
          className={`heartbeat-visual ${heartState} ${isHeartClickable ? 'clickable' : ''}`}
          onClick={isHeartClickable ? handleMarkActive : undefined}
        >
          <div className="heartbeat-emoji">
            {getHeartEmoji()}
            {showFireAnimation && (
              <div className="fire-effect">
                <div className="fire-particle"></div>
                <div className="fire-particle"></div>
                <div className="fire-particle"></div>
                <div className="fire-particle"></div>
                <div className="fire-particle"></div>
              </div>
            )}
          </div>
          {(heartState === 'active' || heartState === 'hyperactive') && (
            <>
              <div className="heartbeat-ripple"></div>
              <div className="heartbeat-ripple ripple-2"></div>
              <div className="heartbeat-ripple ripple-3"></div>
            </>
          )}
          {isHeartClickable && (
            <div className="heartbeat-click-prompt">
              Click to support!
            </div>
          )}
        </div>
        
        <div className="heartbeat-status">
          {isLoading ? (
            <div className="heartbeat-loading">
              <div className="heartbeat-spinner"></div>
              <p>Checking your status...</p>
            </div>
          ) : error ? (
            <p className="heartbeat-error">{error}</p>
          ) : (
            <>
              <p className="heartbeat-message">
                {statusMessages[heartState]}
              </p>
              <p className="heartbeat-streak">{getStreakInfo()}</p>
            </>
          )}
        </div>
        
        {historyStatus === 'succeeded' && activityHistory && activityHistory.length > 0 && (
          <HeartbeatGraph activityHistory={activityHistory} />
        )}
        
        {historyStatus === 'loading' && (
          <div className="history-loading">
            <div className="heartbeat-spinner"></div>
            <p>Loading activity history...</p>
          </div>
        )}
      </div>
      
      <div className="heartbeat-footer">
        <p>Every contribution keeps the movement alive</p>
        <p>Join thousands supporting daily</p>
      </div>
    </div>
  );
};

export default HeartbeatPage;