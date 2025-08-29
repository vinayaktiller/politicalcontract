import React, { useState, useEffect } from "react";
import api from "../../../api";
import "./ContributionsList.css";

// ---------------------
// Types
// ---------------------
interface OwnerDetails {
  profile_pic?: string;
  name?: string;
}

interface TeamMember {
  id: number;
  profile_pic?: string;
  name: string;
}

export interface Contribution {
  id: number;
  title?: string;
  link: string;
  discription?: string; // (typo in API? maybe should be "description")
  created_at: string;
  owner_details?: OwnerDetails;
  team_member_details?: TeamMember[];
}

interface Pagination {
  count: number;
  next: string | null;
  previous: string | null;
  current: number;
}

interface ContributionsListProps {
  userId?: number | null;
}

// ---------------------
// Component
// ---------------------
const ContributionsList: React.FC<ContributionsListProps> = ({ userId = null }) => {
  const [contributions, setContributions] = useState<Contribution[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>("");

  const [pagination, setPagination] = useState<Pagination>({
    count: 0,
    next: null,
    previous: null,
    current: 1,
  });

  const fetchContributions = async (page: number = 1) => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        page: page.toString(),
        ...(searchQuery ? { search: searchQuery } : {}),
        ...(userId ? { user_id: userId.toString() } : {}),
      });

      const response = await api.get(`/api/blog_related/contributions/?${params}`);
      const data = response.data as {
        results: Contribution[];
        count: number;
        next: string | null;
        previous: string | null;
      };

      setContributions(data.results);
      setPagination({
        count: data.count,
        next: data.next,
        previous: data.previous,
        current: page,
      });
    } catch (err) {
      console.error("Error fetching contributions:", err);
      setError("Failed to fetch contributions. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchContributions(1);
  }, [userId, searchQuery]);

  const handleSearch = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    fetchContributions(1);
  };

  const handleDelete = async (contributionId: number) => {
    if (!window.confirm("Are you sure you want to delete this contribution?")) {
      return;
    }

    try {
      await api.delete(`/api/blog_related/contributions/${contributionId}/delete/`);
      setContributions(contributions.filter((c) => c.id !== contributionId));
    } catch (err) {
      console.error("Error deleting contribution:", err);
      setError("Failed to delete contribution. Please try again.");
    }
  };

  if (loading && contributions.length === 0) {
    return (
      <div className="contributions-loading">
        <div className="loading-spinner"></div>
        <p>Loading your contributions...</p>
      </div>
    );
  }

  return (
    <div className="contributions-container">
      <div className="contributions-header">
        <h1>{userId ? `Contributions of User #${userId}` : "My Contributions"}</h1>
        <p>Manage and view all your claimed contributions</p>
      </div>

      <div className="contributions-actions">
        <form onSubmit={handleSearch} className="search-form">
          <input
            type="text"
            placeholder="Search contributions..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />
          <button type="submit" className="search-button">
            <svg className="search-icon" viewBox="0 0 24 24">
              <path
                fill="currentColor"
                d="M9.5,3A6.5,6.5 0 0,1 16,9.5C16,11.11 15.41,12.59 14.44,13.73L14.71,14H15.5L20.5,19L19,20.5L14,15.5V14.71L13.73,14.44C12.59,15.41 11.11,16 9.5,16A6.5,6.5 0 0,1 3,9.5A6.5,6.5 0 0,1 9.5,3M9.5,5C7,5 5,7 5,9.5C5,12 7,14 9.5,14C12,14 14,12 14,9.5C14,7 12,5 9.5,5Z"
              />
            </svg>
          </button>
        </form>
      </div>

      {error && (
        <div className="contributions-error">
          <svg className="error-icon" viewBox="0 0 24 24">
            <path
              fill="currentColor"
              d="M13,13H11V7H13M13,17H11V15H13M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2Z"
            />
          </svg>
          <p>{error}</p>
        </div>
      )}

      {contributions.length === 0 ? (
        <div className="no-contributions">
          <svg className="empty-icon" viewBox="0 0 24 24">
            <path
              fill="currentColor"
              d="M20,6H16V4A2,2 0 0,0 14,2H10A2,2 0 0,0 8,4V6H4A2,2 0 0,0 2,8V19A2,2 0 0,0 4,21H20A2,2 0 0,0 22,19V8A2,2 0 0,0 20,6M10,4H14V6H10V4M12,9A2.5,2.5 0 0,1 14.5,11.5A2.5,2.5 0 0,1 12,14A2.5,2.5 0 0,1 9.5,11.5A2.5,2.5 0 0,1 12,9M17,19H7V17.75C7,16.37 9.24,15.25 12,15.25C14.76,15.25 17,16.37 17,17.75V19Z"
            />
          </svg>
          <h3>No contributions found</h3>
          <p>You haven't claimed any contributions yet.</p>
        </div>
      ) : (
        <>
          <div className="contributions-grid">
            {contributions.map((contribution) => (
              <div key={contribution.id} className="contribution-card">
                <div className="card-header">
                  <div className="owner-info">
                    <img
                      src={contribution.owner_details?.profile_pic || "/default-avatar.png"}
                      alt={contribution.owner_details?.name || "Owner"}
                      className="owner-avatar"
                    />
                    <span className="owner-name">{contribution.owner_details?.name}</span>
                  </div>
                  <span className="contribution-date">
                    {new Date(contribution.created_at).toLocaleDateString()}
                  </span>
                </div>

                <h3 className="contribution-title">
                  <a href={contribution.link} target="_blank" rel="noopener noreferrer">
                    {contribution.title || "Untitled Contribution"}
                  </a>
                </h3>

                <p className="contribution-link">
                  <a href={contribution.link} target="_blank" rel="noopener noreferrer">
                    {contribution.link}
                  </a>
                </p>

                {contribution.discription && (
                  <p className="contribution-description">{contribution.discription}</p>
                )}

                {contribution.team_member_details &&
                  contribution.team_member_details.length > 0 && (
                    <div className="team-members">
                      <h4>Team Members:</h4>
                      <div className="team-members-list">
                        {contribution.team_member_details.map((member) => (
                          <div key={member.id} className="team-member">
                            <img
                              src={member.profile_pic || "/default-avatar.png"}
                              alt={member.name}
                              className="member-avatar"
                            />
                            <span className="member-name">{member.name}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                <div className="card-actions">
                  <button
                    className="delete-btn"
                    onClick={() => handleDelete(contribution.id)}
                  >
                    <svg className="delete-icon" viewBox="0 0 24 24">
                      <path
                        fill="currentColor"
                        d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"
                      />
                    </svg>
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination Controls */}
          <div className="pagination-controls">
            <button
              onClick={() => fetchContributions(pagination.current - 1)}
              disabled={!pagination.previous}
              className="pagination-btn"
            >
              Previous
            </button>

            <span className="pagination-info">
              Page {pagination.current} of {Math.ceil(pagination.count / 10)}
            </span>

            <button
              onClick={() => fetchContributions(pagination.current + 1)}
              disabled={!pagination.next}
              className="pagination-btn"
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default ContributionsList;
