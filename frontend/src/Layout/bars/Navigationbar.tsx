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
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

  useEffect(() => {
    const id = localStorage.getItem("user_id");
    if (id) {
      setUserId(id);
    }
  }, []);

  const handleLogoutConfirm = (): void => {
    setShowLogoutConfirm(true);
  };

  const handleLogoutCancel = (): void => {
    setShowLogoutConfirm(false);
  };

  const handleLogoutProceed = (): void => {
    setShowLogoutConfirm(false);
    handleLogout();
  };

  const handleNavClick = (): void => {
    toggleNav();
  };

  return (
    <div className='navbar'>
      <div className='navbar-top'>
        <Link to={`/breakdown-id`} onClick={handleNavClick}>MY ID</Link>
        <Link to={'/app'} onClick={handleNavClick}>Home</Link>
        
        <Link to={`/timeline/1`} onClick={handleNavClick}>Timeline</Link>
        
        
        {userId && (
          <>
            <Link to={`/profile/${userId} `} onClick={handleNavClick}>Profile</Link>
            <Link to={`/children/${userId}`} onClick={handleNavClick}>Children's Page</Link>
            <Link to={`/connections/${userId}`} onClick={handleNavClick}>Friends</Link>
          </>
        )}

        <Link to={'dashboards/'} onClick={handleNavClick}>Dashboard</Link>
        
        <Link to={`/messages/chatlist`} onClick={handleNavClick}>Conversations</Link>
        <Link to={'/blogs/'} onClick={handleNavClick}>Blogs</Link>
        <Link to={`/milestones`} onClick={handleNavClick}>Milestones</Link>
        <Link to={'/my-groups/'} onClick={handleNavClick}>My Groups</Link>
        <Link to={'/contributions/'} onClick={handleNavClick}>My Contributions</Link>
        
        <Link to={`/home/`} onClick={handleNavClick}>More</Link>
        
      </div>
      <div className='navbar-bottom'>
        <button onClick={handleLogoutConfirm}>Logout</button>
      </div>

      {/* Custom Confirmation Modal */}
      {showLogoutConfirm && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3>Confirm Logout</h3>
            <p>Are you sure you want to log out?</p>
            <div className="modal-actions">
              <button className="cancel-btn" onClick={handleLogoutCancel}>
                Cancel
              </button>
              <button className="logout-btn" onClick={handleLogoutProceed}>
                Yes, Logout
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Navigationbar;