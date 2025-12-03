import React, { useEffect, useState, useRef } from 'react';
import { logout } from '../../login/login_logoutSlice';
import { useDispatch } from 'react-redux';
import handleLogout from '../../login/logout';
import { Link } from 'react-router-dom';
import '../css/Navigationbar.css';
import MyBlogsPage from '../../pages/Authenticated/blogrelated/blogpage/myblog/MyBlogsPage';

interface NavigationbarProps {
  toggleNav: () => void;
}

const Navigationbar: React.FC<NavigationbarProps> = ({ toggleNav }) => {
  const dispatch = useDispatch();
  const [userId, setUserId] = useState<string | null>(null);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
  const [showTopShadow, setShowTopShadow] = useState(false);
  const [showBottomShadow, setShowBottomShadow] = useState(false);
  const navContentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const id = localStorage.getItem("user_id");
    if (id) {
      setUserId(id);
    }
  }, []);

  useEffect(() => {
    const checkScroll = () => {
      if (navContentRef.current) {
        const { scrollTop, scrollHeight, clientHeight } = navContentRef.current;
        setShowTopShadow(scrollTop > 10);
        setShowBottomShadow(scrollTop + clientHeight < scrollHeight - 10);
      }
    };

    const navContent = navContentRef.current;
    if (navContent) {
      navContent.addEventListener('scroll', checkScroll);
      // Initial check
      checkScroll();
    }

    return () => {
      if (navContent) {
        navContent.removeEventListener('scroll', checkScroll);
      }
    };
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

  const handleScrollToTop = (): void => {
    if (navContentRef.current) {
      navContentRef.current.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const handleScrollToBottom = (): void => {
    if (navContentRef.current) {
      navContentRef.current.scrollTo({ 
        top: navContentRef.current.scrollHeight, 
        behavior: 'smooth' 
      });
    }
  };

  return (
    <div className='navbar'>
      {/* Top scroll indicator */}
      {/* {showTopShadow && <div className="scroll-shadow top-shadow"></div>}
       */}
      {/* Bottom scroll indicator */}
      {/* {showBottomShadow && <div className="scroll-shadow bottom-shadow"></div>} */}
      
      {/* Scroll to top button */}
      {/* {showTopShadow && (
        <button 
          className="scroll-to-top-btn"
          onClick={handleScrollToTop}
          title="Scroll to top"
        >
          ↑
        </button>
      )} */}
      
      {/* Scroll to bottom button */}
      {/* {showBottomShadow && (
        <button 
          className="scroll-to-bottom-btn"
          onClick={handleScrollToBottom}
          title="Scroll to bottom"
        >
          ↓
        </button>
      )}
       */}
      <div className='nav-content' ref={navContentRef}>
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
          <Link to={'/my-blogs/'} onClick={handleNavClick}>My Blogs</Link> 
          <Link to={`/milestones`} onClick={handleNavClick}>Milestones</Link>
          <Link to={'/my-groups/'} onClick={handleNavClick}>My Groups</Link>
          <Link to={'/contributions/'} onClick={handleNavClick}>My Contributions</Link>
          
          <Link to={`/home/`} onClick={handleNavClick}>More</Link>
          
          {/* Additional links to make it scrollable */}
          {/* <Link to={'/settings'} onClick={handleNavClick}>Settings</Link>
          <Link to={'/help'} onClick={handleNavClick}>Help & Support</Link>
          <Link to={'/faq'} onClick={handleNavClick}>FAQ</Link>
          <Link to={'/privacy'} onClick={handleNavClick}>Privacy Policy</Link>
          <Link to={'/terms'} onClick={handleNavClick}>Terms of Service</Link>
          <Link to={'/about'} onClick={handleNavClick}>About Us</Link>
          <Link to={'/contact'} onClick={handleNavClick}>Contact Us</Link>
          <Link to={'/feedback'} onClick={handleNavClick}>Feedback</Link>
          <Link to={'/report'} onClick={handleNavClick}>Report Issue</Link> */}
        </div>
        
        <div className='navbar-bottom'>
          <button onClick={handleLogoutConfirm}>Logout</button>
        </div>
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