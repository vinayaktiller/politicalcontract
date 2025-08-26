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
      <button onClick={() => navigate('/blog-creator')} className="navigate-btn">
        blog-creator  
      </button>
      <button onClick={() => navigate('/questions')} className="navigate-btn">
        questions
      </button>
      <button onClick={() => navigate('/claim-contribution')} className="navigate-btn">
        claim-contribution
      </button>
    </div>
  );
};

export default HomePage;
