import React, { useState } from 'react';
import { useConnexionValidation } from './hook';

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
    const connection_id = tempConnexionID; // Verified ID

    if (!applicant_id || !connection_id) {
      alert("Missing required data. Please check and try again.");
      return;
    }

    const requestData = {
      applicant_id: Number(applicant_id), 
      connection_id: Number(connection_id)
    };

    try {
      setLoading(true);
      const response = await fetch('http://127.0.0.1:8000/api/users/connections/create/', { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestData)
      });

      if (!response.ok) throw new Error("Submission failed");

      alert("Connexion request submitted successfully!");
    } catch (err) {
      alert("Error submitting connexion request. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="form-section">
      <h3>Connexion Verification</h3>
      <div className="form-group">
        <label>Enter ID to establish connexion</label>
        <div className="input-wrapper">
          <input
            type="number"
            value={tempConnexionID}
            onChange={(e) => setTempConnexionID(e.target.value)}
            required
          />
          <button type="button" onClick={handleValidation} className="validate-btn">
            Verify
          </button>
        </div>
        {error && <div className="error-message">{error}</div>}
      </div>

      {connexionDetails && (
        <div className="initiator-card">
          {connexionDetails.profilepic && (
            <img src={connexionDetails.profilepic} alt="Connexion" className="initiator-image" />
          )}
          <h4>{connexionDetails.name}</h4>
          <p>@{connexionDetails.text}</p>
        </div>
      )}

      {connexionDetails && (
        <button type="button" onClick={handleSubmit} className="submit-btn" disabled={loading}>
          {loading ? "Submitting..." : "Submit Connexion"}
        </button>
      )}
    </div>
  );
};

export default ConnexionVerification;
