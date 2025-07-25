import React, { useEffect, useState } from 'react';
import { logout } from '../../login/login_logoutSlice';
import { useDispatch } from 'react-redux';
import handleLogout from '../../login/logout';
import { Link } from 'react-router-dom';
import '../css/Navigationbar.css';

interface NavigationbarProps {
  toggleNav: () => void;
}

const Navigationbar: React.FC<NavigationbarProps> = ({ toggleNav }) => {
  const dispatch = useDispatch();
  const [userId, setUserId] = useState<string | null>(null);

  useEffect(() => {
    const id = localStorage.getItem("user_id");
    if (id) {
      setUserId(id);
    }
  }, []);

  const handlelLogout = (): void => {
    handleLogout();
  };

  const handleNavClick = (): void => {
    toggleNav();
  };

  return (
    <div className='navbar'>
      <div className='navbar-top'>
        <Link to={`/breakdown-id`} onClick={handleNavClick}>MY ID</Link>
        <Link to={'/heartbeat/'} onClick={handleNavClick}>Home</Link>
        
        <Link to={`/timeline/1`} onClick={handleNavClick}>Timeline</Link>
        <Link to={`/profile/`} onClick={handleNavClick}>Profile</Link>
        
        {userId && (
          <>
            <Link to={`/children/${userId}`} onClick={handleNavClick}>Children's Page</Link>
            <Link to={`/connections/${userId}`} onClick={handleNavClick}>Friends</Link>
          </>
        )}
        
        <Link to={'/my-groups/'} onClick={handleNavClick}>My Groups</Link>
        <Link to={'dashboards/'} onClick={handleNavClick}>Dashboard</Link>
        <Link to={`/home/`} onClick={handleNavClick}>testing page</Link>
        <Link to={`/messages/chatlist`} onClick={handleNavClick}>Messages</Link>
      </div>
      <div className='navbar-bottom'>
        <button onClick={handlelLogout}>Logout</button>
      </div>
    </div>
  );
};

export default Navigationbar;