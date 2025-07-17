import React from 'react';
import { useNavigate } from 'react-router-dom';

const HomePage: React.FC = () => {
  const navigate = useNavigate(); // Initialize navigation

  return (
    <div>
      <h1>This is Home Page</h1>
      <button onClick={() => navigate('/make-connections')} className="navigate-btn">
        make connections
      </button>
      <button onClick={() => navigate('/group-registration')} className="navigate-btn">
        create a group
      </button>
    </div>
  );
};

export default HomePage;
