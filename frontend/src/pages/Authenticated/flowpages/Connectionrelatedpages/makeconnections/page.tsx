import React, { useState } from 'react';
import { useConnexionValidation } from './hook';
import './ConnexionVerification.css';

const ConnexionVerification: React.FC = () => {
  const { connexionDetails, error, validateConnexionID } = useConnexionValidation();
  const [tempConnexionID, setTempConnexionID] = useState<string | number>('');
  const [loading, setLoading] = useState(false);

  const handleValidation = () => {
    validateConnexionID(Number(tempConnexionID));
  };

  const handleSubmit = async () => {
    if (!connexionDetails) {
      alert("Please verify an ID first!");
      return;
    }

    const applicant_id = localStorage.getItem("user_id"); 
    const connection_id = Number(tempConnexionID);

    if (!applicant_id || !connection_id) {
      alert("Missing required data. Please check and try again.");
      return;
    }

    try {
      setLoading(true);
      const response = await fetch('http://127.0.0.1:8000/api/users/connections/create/', { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          applicant_id: Number(applicant_id),
          connection_id,
        })
      });

      if (!response.ok) throw new Error("Submission failed");

      alert("Connexion request submitted successfully!");
      setTempConnexionID('');
    } catch (err) {
      alert("Error submitting connexion request. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const canSendRequest = connexionDetails && Number(tempConnexionID) > 0;

  return (
    <div className="connexion-verification-container">
      <div className="connexion-verification-card">
        {/* Header */}
        <div className="connexion-header">
          <div className="connexion-emoji">🤝</div>
          <h2 className="connexion-title">Establish Connection</h2>
          <p className="connexion-subtitle">
            If your friends, family, acquaintances are already initiated, don't worry. 
            Just make connexions and show the world that you have your people already in the moment.
          </p>
        </div>
        
        {/* Input + Validate */}
        <div className="connexion-form-group">
          <div className="connexion-input-wrapper">
            <input
              type="number"
              value={tempConnexionID}
              onChange={(e) => setTempConnexionID(e.target.value)}
              placeholder="Enter user ID"
              className="connexion-input"
              required
            />
            <button 
              type="button" 
              onClick={handleValidation} 
              className="connexion-validate-btn"
            >
              Verify
            </button>
          </div>
          {error && <div className="connexion-error-message">{error}</div>}
        </div>

        {/* Profile Info */}
        {connexionDetails && (
          <div className="connexion-profile-card">
            {connexionDetails.profilepic ? (
              <img 
                src={connexionDetails.profilepic} 
                alt="Connexion" 
                className="connexion-profile-image" 
              />
            ) : (
              <div className="connexion-profile-placeholder">
                {connexionDetails.name.charAt(0)}
              </div>
            )}
            <div className="connexion-profile-details">
              <h3 className="connexion-profile-name">{connexionDetails.name}</h3>
              <p className="connexion-profile-text">{connexionDetails.text}</p>
            </div>
          </div>
        )}

        {/* Submit Button */}
        {canSendRequest && (
          <button 
            type="button" 
            onClick={handleSubmit} 
            className="connexion-submit-btn" 
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="connexion-spinner"></span> Processing...
              </>
            ) : (
              "Send Connection Request"
            )}
          </button>
        )}
        
        <div className="connexion-footer">
          <p>Building community connections</p>
        </div>
      </div>
    </div>
  );
};

export default ConnexionVerification;