import React from 'react';
import { logout } from '../../login/login_logoutSlice';
import { useDispatch } from 'react-redux';
import handleLogout from '../../login/logout';


import { Link } from 'react-router-dom';
import '../css/Navigationbar.css'; // Import your CSS file for styling


// Define the props type
interface NavigationbarProps {
  toggleNav: () => void;
}

const Navigationbar: React.FC<NavigationbarProps> = ({ toggleNav }) => {
  const dispatch = useDispatch();

  const handlelLogout = (): void => {
    handleLogout();
  };

  const handleNavClick = (): void => {
    toggleNav(); // Toggle the navigation bar visibility
  };

  return (
    <div className='navbar'>
      <div className='navbar-top'>
        <Link to={`/home/`} onClick={handleNavClick}>Home</Link>
        <Link to={`/timeline/`} onClick={handleNavClick}>Timeline</Link>
        <Link to={`/profile/`} onClick={handleNavClick}>Profile</Link>
        <Link to={`/children/`} onClick={handleNavClick}>Children's Page</Link>
        <Link to={`/connections/`} onClick={handleNavClick}>Friends</Link>
        <Link to={`/dashboard/`} onClick={handleNavClick}>Dashboard</Link>
        {/* <Link to={`/search-reports/`} onClick={handleNavClick}>Search Reports</Link>
        <Link to={`/reports/`} onClick={handleNavClick}>Reports</Link> */}
      </div>
      <div className='navbar-bottom'>
        <button onClick={handlelLogout}>Logout</button>
      </div>
    </div>
  );
};

export default Navigationbar;
