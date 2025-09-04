import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import api from '../../../api';
import { ProfileData } from './types';
import './ProfilePage.css';

const fetchUserProfile = async (userId: number): Promise<ProfileData> => {
  const response = await api.get<ProfileData>(`/api/users/profile/${userId}/`);
  return response.data;
};

const ProfilePage: React.FC = () => {
  const { userId } = useParams<{ userId: string }>();
  const [profileData, setProfileData] = useState<ProfileData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!userId) return;
    const loadData = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchUserProfile(parseInt(userId, 10));
        setProfileData(data);
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [userId]);

  if (loading) return <div className="profile-loading">Loading profile...</div>;
  if (error) return <div className="profile-error">Error: {error}</div>;
  if (!profileData) return <div className="profile-not-found">Profile not found</div>;

  const { user, user_tree, profile_description, milestones, founded_groups, speaking_groups, streak } = profileData;

  return (
    <div className="profile-container">
      {/* Author photo only in header */}
      <div className="author-header">
        {user_tree?.profilepic ? (
          <img
            src={user_tree.profilepic}
            alt={`${user.first_name} ${user.last_name}`}
            className="author-photo"
          />
        ) : (
          <div className="author-photo-placeholder">
            {user.first_name.charAt(0)}{user.last_name.charAt(0)}
          </div>
        )}
      </div>

      {/* Author name */}
      {/* <h1 className="author-name">{user.first_name} {user.last_name}</h1> */}

      {/* Book-style flowing text */}
      <div className="author-text">
        {/* <p><em>{user.age} years old, {user.gender}.</em></p>
        <p>
          From {user.village?.name ? `${user.village.name}, ` : ""}
          {user.subdistrict?.name ? `${user.subdistrict.name}, ` : ""}
          {user.district?.name ? `${user.district.name}, ` : ""}
          {user.state?.name ? `${user.state.name}, ` : ""}
          {user.country?.name || ""}
        </p>
        <p><em>Joined on {new Date(user.date_joined).toLocaleDateString()}.</em></p> */}

        {profile_description && (
          <p>{profile_description}</p>
        )}

        {user_tree && (
          <>
            <p>
              <strong>Activity streak:</strong> {streak} days of continuous work.
            </p>
            <p>
              <strong>Direct initiations:</strong> {user_tree.childcount} members brought into the movement.
            </p>
            <p>
              <strong>Network influence:</strong> {user_tree.influence} people reached through connections.
            </p>
          </>
        )}

        {founded_groups.length > 0 && (
          <>
            <h2>Groups Founded</h2>
            {founded_groups.map((group) => (
              <p key={group.id}>
                <strong>{group.name}</strong> — founded on {new Date(group.created_at).toLocaleDateString()}.
              </p>
            ))}
          </>
        )}

        {speaking_groups.length > 0 && (
          <>
            <h2>Groups as Speaker</h2>
            {speaking_groups.map((group) => (
              <p key={group.id}>
                <strong>{group.name}</strong> — member since {new Date(group.created_at).toLocaleDateString()}.
              </p>
            ))}
          </>
        )}

        {milestones.length > 0 && (
          <>
            <h2>Milestones</h2>
            {milestones.map((milestone) => (
              <p key={milestone.id}>
                <strong>{milestone.title}</strong> ({milestone.type}, {new Date(milestone.created_at).toLocaleDateString()}) — {milestone.text}
              </p>
            ))}
          </>
        )}
      </div>
    </div>
  );
};

export default ProfilePage;
