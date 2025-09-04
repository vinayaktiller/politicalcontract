import React from 'react';
import { useNavigate } from 'react-router-dom';
import './HomePage.css';

const HomePage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="home-container">
      
      
      <div className="home-buttons-grid">
        {/* Commented buttons - keeping them as is but commented */}
        {/* 
        <button onClick={() => navigate('/make-connections')} className="navigate-btn">
          make connections
        </button> 
        */}
        
        <div className="home-button-card" onClick={() => navigate('/group-registration')}>
          <div className="button-icon">
            <img src="http://localhost:3000/emojies/group.png" alt="Create a group" onError={(e) => {
              const target = e.target as HTMLImageElement;
              target.src = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9ImN1cnJlbnRDb2xvciIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiIGNsYXNzPSJmZWF0aGVyIGZlYXRoZXItdXNlcnMiPjxwYXRoIGQ9Ik0xNyAyMXYtMmE0IDQgMCAwIDAtNC00SDVhNCA0IDAgMCAwLTQgNHYyIj48L3BhdGg+PGNpcmNsZSBjeD0iOSIgY3k9IjciIHI9IjQiPjwvY2lyY2xlPjxwYXRoIGQ9Ik0yMyAyMXYtMmE0IDQgMCAwIDAtMy0zLjg3Ij48L3BhdGg+PHBhdGggZD0iTTE2IDMuMTNhNCA0IDAgMCAxIDAgNy43NSI+PC9wYXRoPjwvc3ZnPg==';
            }} />
          </div>
          <span className="button-text">Create a group</span>
        </div>
        
        {/* 
        <button onClick={() => navigate('/blog-creator')} className="navigate-btn">
          blog-creator  
        </button> 
        */}
        
        <div className="home-button-card" onClick={() => navigate('/questions')}>
          <div className="button-icon">
            <img src="http://localhost:3000/emojies/question.png" alt="Questions" onError={(e) => {
              const target = e.target as HTMLImageElement;
              target.src = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9ImN1cnJlbnRDb2xvciIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiIGNsYXNzPSJmZWF0aGVyIGZlYXRoZXItaGVscC1jaXJjbGUiPjxjaXJjbGUgY3g9IjEyIiBjeT0iMTIiIHI9IjEwIj48L2NpcmNsZT48cGF0aCBkPSJNOS4wOSA5YTMgMyAwIDAgMSA1LjgzIDFjMCAyLTMgMy0zIDMiPjwvcGF0aD48bGluZSB4MT0iMTIiIHkxPSIxNyIgeDI9IjEyIiB5Mj0iMTciPjwvbGluZT48L3N2Zz4=';
            }} />
          </div>
          <span className="button-text">Questions</span>
        </div>
        
        <div className="home-button-card" onClick={() => navigate('/claim-contribution')}>
          <div className="button-icon">
            <img src="http://localhost:3000/emojies/contribution.png" alt="Claim contribution" onError={(e) => {
              const target = e.target as HTMLImageElement;
              target.src = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9ImN1cnJlbnRDb2xvciIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiIGNsYXNzPSJmZWF0aGVyIGZlYXRoZXItdHJvcGh5Ij48cG9seWdvbiBwb2ludHM9IjEyIDIgMTUgMTEgMjIgMTIgMTYgMTcgMTkgMjIgMTIgMTkgNSAyMiA4IDE3IDIgMTIgOSAxMSAxMiAyIj48L3BvbHlnb24+PC9zdmc+';
            }} />
          </div>
          <span className="button-text">Claim contribution</span>
        </div>
        
        {/* 
        <button onClick={() => navigate('/blogs')} className="navigate-btn">
          blogs
        </button> 
        */}
      </div>
    </div>
  );
};

export default HomePage;