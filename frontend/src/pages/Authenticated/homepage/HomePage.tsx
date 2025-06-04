import React from 'react';
import { useNavigate } from 'react-router-dom';

const HomePage: React.FC = () => {
  const navigate = useNavigate(); // Initialize navigation

  return (
    <div>
      <h1>This is Home Page</h1>
      <button onClick={() => navigate('/make-connections')} className="navigate-btn">
        Go to Connexion Verification
      </button>
    </div>
  );
};

export default HomePage;
