// components/Mainbar.tsx
import React from 'react';
import Headbar from './Header';
import Navigationbar from './Navigationbar';
import Notificationbar from './Notificationbar';
import { Outlet } from 'react-router-dom';
import '../css/Mainbar.css';
import { useNavAndNotification } from '../hooks/useNavAndNotification';

const Mainbar: React.FC = () => {
  const { state, toggleNav, toggleNotifications } = useNavAndNotification();

  return (
    <div className="main-container">
      <Headbar
        toggleNav={toggleNav}
        toggleNotifications={toggleNotifications}
        state={state}
      />
      <div className="container">
        {state.isNavVisible && <Navigationbar toggleNav={toggleNav} />}

        <main className="center">
          <Outlet />
        </main>

        {state.isNotificationsVisible && (
          <Notificationbar toggleNotifications={toggleNotifications} />
        )}
      </div>
    </div>
  );
};

export default Mainbar;
