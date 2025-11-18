// components/Header.tsx
import React from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '../../store';

interface HeadbarProps {
  toggleNav: () => void;
  toggleNotifications: () => void;
  state: {
    butIsNotificationsVisible: boolean;
    butIsNavVisible: boolean;
  };
}

const Headbar: React.FC<HeadbarProps> = ({ toggleNav, toggleNotifications, state }) => {
  const { notifications } = useSelector((state: RootState) => state.notifications);
  
  // Count unread notifications (notification_freshness: false = unread)
  const unreadCount = notifications.filter(n => !n.notification_freshness).length;

  return (
    <div className='head'>
      <button
        className='nav-toggle'
        onClick={toggleNav}
        disabled={state.butIsNotificationsVisible}
      >
        ☰
      </button>
      <h2>POLITICAL CONTRACT</h2>
      <div className="notification-wrapper">
        <button
          className='noti-toggle'
          onClick={toggleNotifications}
          disabled={state.butIsNavVisible}
        >
          🔔
        </button>
        {unreadCount > 0 && (
          <span className="notification-badge">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </div>
    </div>
  );
};

export default Headbar;