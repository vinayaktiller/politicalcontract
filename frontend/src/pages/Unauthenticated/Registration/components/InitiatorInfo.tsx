import React, { useState } from 'react';
import { FormStepProps } from '../types/registrationTypes';
import { useInitiatorValidation } from '../hooks/useInitiatorValidation';
import { registrationService } from '../services/registrationService';
import { useNavigate } from 'react-router-dom'

const InitiatorInfo: React.FC<FormStepProps> = ({
  formData,
  setFormData,
  prevStep,
}) => {
  const { initiatorDetails, error, validateInitiatorID } = useInitiatorValidation();
  const [tempInitiatorID, setTempInitiatorID] = useState<string | number>('');
  const [hasEvent, setHasEvent] = useState<boolean>(false);
  const [tempEventId, setTempEventId] = useState<string | number>('');
  const [eventError, setEventError] = useState<string | null>(null);
  const navigate = useNavigate(); // Initialize the navigate function
  const handleValidation = () => {
    validateInitiatorID(Number(tempInitiatorID));
    setFormData(prev => ({ 
      ...prev, 
      initiator_id: Number(tempInitiatorID),
      event_type: hasEvent ? undefined : 'no_event' 
    }));
  };

  const handleEventValidation = () => {
    if (!tempEventId) {
      setEventError("Event ID or Speaker ID is required.");
    } else {
      setEventError(null);
      setFormData(prev => ({
        ...prev,
        event_id: Number(tempEventId),
      }));
    }
  };

  const handleEventTypeChange = (type: 'group' | 'public' | 'private') => {
    setFormData(prev => ({
      ...prev,
      event_type: type,
      event_id: undefined
    }));
    setTempEventId('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    

    try {
        const userEmail = localStorage.getItem('user_email') || '';
        const formDataToSend = new FormData();
      
        const submissionData = {
            ...formData,
            gmail: userEmail,
            event_id: tempEventId ? Number(tempEventId) : null
        };

        Object.entries(submissionData).forEach(([key, value]) => {
            if (value instanceof File) {
                formDataToSend.append(key, value, value.name);
            } else if (value !== null && value !== undefined) {
                formDataToSend.append(key, value.toString());
            }
        });

        await registrationService.submitRegistration(Object.fromEntries(formDataToSend.entries()));
        alert('Registration successful!');
        navigate('/waiting'); // Navigate to the waiting page after success
        
    } catch (err) {
        console.error("Submission error:", err);
        alert('Registration failed. Please try again.');
    }
};
  return (
    <form className="form-step" onSubmit={handleSubmit}>
      <h2>Event & Initiator Information</h2>

      {/* Event-related fields appear first */}
      <div className="form-section">
        <div className="form-group">
          <label>Is this initiation part of an event?</label>
          <div className="toggle-buttons">
            <button
              type="button"
              className={`toggle-btn ${!hasEvent ? 'active' : ''}`}
              onClick={() => setHasEvent(false)}
            >
              No
            </button>
            <button
              type="button"
              className={`toggle-btn ${hasEvent ? 'active' : ''}`}
              onClick={() => setHasEvent(true)}
            >
              Yes
            </button>
          </div>
        </div>

        {hasEvent && (
          <>
            <div className="form-group">
              <label>Event Type</label>
              <select
                value={formData.event_type || ''}
                onChange={(e) => handleEventTypeChange(e.target.value as any)}
                required
              >
                <option value="">Select Event Type</option>
                <option value="public">Public Event</option>
                <option value="private">Private Event</option>
                <option value="group">Group Event</option>
              </select>
            </div>

            {formData.event_type && (
              <div className="form-group">
               <label>
                  {formData.event_type === 'private' 
                    ? 'Speaker ID' 
                    : formData.event_type === 'group' 
                    ? 'Group ID' 
                    : 'Event ID'}
                </label>

                <div className="input-wrapper">
                  <input
                    type="number"
                    value={tempEventId}
                    onChange={(e) => setTempEventId(e.target.value)}
                    required
                  />
                  <button 
                    type="button" 
                    onClick={handleEventValidation}
                    className="validate-btn"
                  >
                    OK
                  </button>
                </div>
                {eventError && <div className="error-message">{eventError}</div>}
              </div>
            )}
          </>
        )}
      </div>

      {/* Always show Initiator Verification, but adjust label based on event participation */}
      <div className="form-section">
        <h3>Initiator Verification</h3>
        <div className="form-group">
          <label>{hasEvent ? 'Agent ID' : 'Initiator ID'}</label>
          <div className="input-wrapper">
            <input
              type="number"
              value={tempInitiatorID}
              onChange={(e) => setTempInitiatorID(e.target.value)}
              required
            />
            <button 
              type="button" 
              onClick={handleValidation}
              className="validate-btn"
            >
              Verify
            </button>
          </div>
          {error && <div className="error-message">{error}</div>}
        </div>

        {initiatorDetails && (
          <div className="initiator-card">
            {initiatorDetails.profilepic && (
              <img
                src={initiatorDetails.profilepic}
                alt="Initiator"
                className="initiator-image"
              />
            )}
            <h4>{initiatorDetails.name}</h4>
            <p>@{initiatorDetails.text}</p>
          </div>
        )}
      </div>

      <div className="form-navigation">
        <button type="button" onClick={prevStep} className="btn-secondary">
          Previous
        </button>
        <button type="submit" className="btn-primary">
          Complete Registration
        </button>
      </div>
    </form>
  );
};

export default InitiatorInfo;
