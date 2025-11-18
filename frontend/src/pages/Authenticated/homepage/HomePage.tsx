// components/HomePage.tsx
import React from 'react';
import { useNavigate } from 'react-router-dom';
import './HomePage.css';

interface HomePageProps {
  // optional: pass a flag to show admin card only to admins
  isAdmin?: boolean;
}

const HomePage: React.FC<HomePageProps> = ({ isAdmin = true }) => {
  const navigate = useNavigate();

  return (
    <div className="home-container">
      <div className="home-buttons-grid">
        {/* 
          Existing cards (kept as in your file). 
          We're adding an Admin Dashboard card below that matches style.
        */}

        <div
          className="home-button-card"
          onClick={() => navigate('/group-registration')}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') navigate('/group-registration'); }}
          aria-label="Create a group"
        >
          <div className="button-icon">
            <img
              src="http://localhost:3000/emojies/group.png"
              alt="Create a group"
              onError={(e) => {
                const target = e.target as HTMLImageElement;
                target.src = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9ImN1cnJlbnRDb2xvciIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiIGNsYXNzPSJmZWF0aGVyIGZlYXRoZXItdXNlcnMiPjxwYXRoIGQ9Ik0xNyAyMXYtMmE0IDQgMCAwIDAtNC00SDVhNCA0IDAgMCAwLTQgNHYyIj48L3BhdGg+PGNpcmNsZSBjeD0iOSIgY3k9IjciIHI9IjQiPjwvY2lyY2xlPjxwYXRoIGQ9Ik0yMyAyMXYtMmE0IDQgMCAwIDAtMy0zLjg3Ij48L3BhdGg+PHBhdGggZD0iTTE2IDMuMTNhNCA0IDAgMCAxIDAgNy43NSI+PC9wYXRoPjwvc3ZnPg==';
              }}
            />
          </div>
          <span className="button-text">Create a group</span>
        </div>

        <div
          className="home-button-card"
          onClick={() => navigate('/questions')}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') navigate('/questions'); }}
          aria-label="Questions"
        >
          <div className="button-icon">
            <img
              src="http://localhost:3000/emojies/question.png"
              alt="Questions"
              onError={(e) => {
                const target = e.target as HTMLImageElement;
                target.src = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9ImN1cnJlbnRDb2xvciIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiIGNsYXNzPSJmZWF0aGVyIGZlYXRoZXItaGVscC1jaXJjbGUiPjxjaXJjbGUgY3g9IjEyIiBjeT0iMTIiIHI9IjEwIj48L2NpcmNsZT48cGF0aCBkPSJNOS4wOSA5YTMgMyAwIDAgMSA1LjgzIDFjMCAyLTMgMy0zIDMiPjwvcGF0aD48bGluZSB4MT0iMTIiIHkxPSIxNyIgeDI9IjEyIiB5Mj0iMTciPjwvbGluZT48L3N2Zz4=';
              }}
            />
          </div>
          <span className="button-text">Questions</span>
        </div>

        <div
          className="home-button-card"
          onClick={() => navigate('/claim-contribution')}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') navigate('/claim-contribution'); }}
          aria-label="Claim contribution"
        >
          <div className="button-icon">
            <img
              src="http://localhost:3000/emojies/contribution.png"
              alt="Claim contribution"
              onError={(e) => {
                const target = e.target as HTMLImageElement;
                target.src = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9ImN1cnJlbnRDb2xvciIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiIGNsYXNzPSJmZWF0aGVyIGZlYXRoZXItdHJvcGh5Ij48cG9seWdvbiBwb2ludHM9IjEyIDIgMTUgMTEgMjIgMTIgMTYgMTcgMTkgMjIgMTIgMTkgNSAyMiA4IDE3IDIgMTIgOSAxMSAxMiAyIj48L3BvbHlnb24+PC9zdmc+';
              }}
            />
          </div>
          <span className="button-text">Claim contribution</span>
        </div>

        {/* --- ADMIN DASHBOARD CARD --- */}
        {isAdmin && (
          <div
            className="home-button-card admin-card"
            onClick={() => navigate('/admin/pending-users')}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') navigate('/admin/pending-users'); }}
            aria-label="Admin Pending Users"
            title="Admin Dashboard — Pending Users"
          >
            <div className="button-icon">
              <img
                src="http://localhost:3000/emojies/admin.png"
                alt="Admin dashboard"
                onError={(e) => {
                  const target = e.target as HTMLImageElement;
                  // fallback simple gear icon SVG (base64)
                  target.src = 'data:image/svg+xml;base64,PHN2ZyB2ZXJzaW9uPSIxLjEiIGlkPSJMYXllcl8xIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCI+PHBhdGggZD0iTTExLjUsMy4xYy0uMy0uNi0xLjEtLjYtMS40IDBsLS41LjkuMyAxYy0uNC4yLS44LjUtMS4xLjlMMi45IDEyLjNjLS4zLjUtLjEuNS4yLjhsLjkuNi4xIDEuMmMtLjEuNC0uMS44IDAgMS4ybC45LjcuM2wxLjItLjMuOGMuMy40Ljc1LjcuMSAxLjNsLS40IDEuOGMuMS41LjYgMSAxLjEgMS4zLjcuNC4yLjkuMyAxLjMuOSAxLjV2LjljLjUgMC0uMS0uMy0uNS0uOGwuNS0uMWMxLjQtLjIgMi4zLS40IDMuNi0xLjIuOC0uNSAxLjYtMS4xIDEuOC0xLjcuMi0uNi4yLTEuMSAwLTEuNmwuMy0xLjEuNi0uN2MuMy0uMy4yLS44LS4yLTEuM2wtLjYtMS4xYy4yLS42LjQtMS4xLjUtMS4zLjMtLjYtLjItMS4xLS43LTEuNS0uNS0uNC0xLjEtLjktMi0xLjItMS4xLS4yLTIuMy0uNC0zLjQtLjZsLS4xLTEuM3ptLTEuNSA1LjVjMS4yIDAgMi4xIDEgMi4xIDIuMXMtMSAxLjktMi4xIDEuOS0yLjEtMS0yLjEtMSAxLjEtMi4xIDIuMS0yLjF6Ii8+PC9zdmc+';
                }}
              />
            </div>
            <span className="button-text">Admin Dashboard</span>
            
          </div>
          
        )}


        {/* other commented buttons kept for future */}
      </div>
      <div>
              <button 
                    onClick={() => navigate('/reports/generate')}
                    className="generate-reports-btn"
                  >
                    Generate Reports
                  </button>
            </div>
    </div>
  );
};

export default HomePage;
