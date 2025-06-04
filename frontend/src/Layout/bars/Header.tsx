import React from 'react';

interface HeadbarProps {
  toggleNav: () => void;
  toggleNotifications: () => void;
  state: {
    butIsNotificationsVisible: boolean;
    butIsNavVisible: boolean;
  };
}

const Headbar: React.FC<HeadbarProps> = ({ toggleNav, toggleNotifications, state }) => {
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
      <button
        className='noti-toggle'
        onClick={toggleNotifications}
        disabled={state.butIsNavVisible}
      >
        🔔
      </button>
    </div>
  );
};

export default Headbar;
