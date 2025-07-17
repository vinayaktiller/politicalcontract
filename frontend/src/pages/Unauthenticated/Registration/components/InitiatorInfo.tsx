import React, { useState } from 'react';
import { FormStepProps } from '../types/registrationTypes';
import { useInitiatorValidation } from '../hooks/useInitiatorValidation';
import { useSpeakerValidation } from '../hooks/useSpeakerValidation';
import { useGroupValidation } from '../hooks/useGroupValidation';
import { registrationService } from '../services/registrationService';
import { useNavigate } from 'react-router-dom';

const InitiatorInfo: React.FC<FormStepProps> = ({
  formData,
  setFormData,
  prevStep,
}) => {
  const {
    initiatorDetails,
    setInitiatorDetails,
    error: initiatorError,
    validateInitiatorID,
  } = useInitiatorValidation();

  const {
    speakerDetails,
    setSpeakerDetails,
    error: speakerError,
    validateSpeakerID,
  } = useSpeakerValidation();

  const {
    groupDetails,
    setGroupDetails,
    error: groupError,
    validateGroupID,
    getGroupMessage,
    getGroupCardText,
    isLoading: groupLoading,
  } = useGroupValidation();

  const [tempInitiatorID, setTempInitiatorID] = useState<string | number>('');
  const [hasEvent, setHasEvent] = useState<boolean>(false);
  const [tempEventId, setTempEventId] = useState<string | number>('');
  const [eventError, setEventError] = useState<string | null>(null);
  const [showSameIdPopup, setShowSameIdPopup] = useState(false);
  const [showGroupConfirm, setShowGroupConfirm] = useState(false);

  const [isSpeakerValidated, setIsSpeakerValidated] = useState(false);
  const [isGroupValidated, setIsGroupValidated] = useState(false);
  const [isInitiatorValidated, setIsInitiatorValidated] = useState(false);
  const navigate = useNavigate();

  const clearFields = () => {
    setTempEventId('');
    setTempInitiatorID('');
    setSpeakerDetails(null);
    setInitiatorDetails(null);
    setIsSpeakerValidated(false);
    setIsGroupValidated(false);
    setIsInitiatorValidated(false);
    setFormData(prev => ({
      ...prev,
      event_id: undefined,
      initiator_id: undefined
    }));
    setShowSameIdPopup(false);
    setShowGroupConfirm(false);
  };

  const checkSameIds = () => {
    if (tempInitiatorID && tempEventId) {
      if (Number(tempInitiatorID) === Number(tempEventId)) {
        setShowSameIdPopup(true);
        return true;
      }
    }
    return false;
  };

  const handleValidation = async () => {
    if (checkSameIds()) return;

    const isValid = await validateInitiatorID(Number(tempInitiatorID));
    if (isValid) {
      setIsInitiatorValidated(true);
      setFormData(prev => ({
        ...prev,
        initiator_id: Number(tempInitiatorID),
      }));
    } else {
      setIsInitiatorValidated(false);
    }
  };

  const handleSpeakerValidation = async () => {
    if (checkSameIds()) return;

    if (!tempEventId) {
      setEventError('Speaker ID is required.');
      return;
    }

    const isValid = await validateSpeakerID(Number(tempEventId));
    if (isValid) {
      setEventError(null);
      setIsSpeakerValidated(true);
      setFormData(prev => ({
        ...prev,
        event_id: Number(tempEventId),
      }));
    } else {
      setIsSpeakerValidated(false);
    }
  };

  const handleGroupValidation = async () => {
    if (checkSameIds()) return;

    if (!tempEventId) {
      setEventError('Group ID is required.');
      return;
    }

    const isValid = await validateGroupID(Number(tempEventId));
    if (isValid) {
      setEventError(null);
      setShowGroupConfirm(true);
    }
  };

  const handleEventValidation = () => {
    if (checkSameIds()) return;

    if (!tempEventId) {
      setEventError('Event ID or Speaker ID is required.');
    } else {
      setEventError(null);
      setIsSpeakerValidated(true);
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
      event_id: undefined,
    }));
    setTempEventId('');
    setIsSpeakerValidated(false);
    setIsGroupValidated(false);
    setSpeakerDetails(null);
    setGroupDetails(null);
  };

  const confirmGroupSelection = () => {
    if (groupDetails) {
      setIsGroupValidated(true);
      setFormData(prev => ({
        ...prev,
        event_id: groupDetails.id,
        event_name: groupDetails.name
      }));
      setShowGroupConfirm(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Special case for private events
    if (
      formData.event_type === 'private' &&
      formData.initiator_id &&
      formData.event_id &&
      formData.initiator_id === formData.event_id
    ) {
      setShowSameIdPopup(true);
      return;
    }

    // Special case for group events
    if (formData.event_type === 'group' && formData.initiator_id === formData.event_id) {
      setShowSameIdPopup(true);
      return;
    }

    if (formData.event_type === 'private' && !isSpeakerValidated) {
      setEventError('Please validate your Speaker ID');
      return;
    }

    if (formData.event_type === 'group' && !isGroupValidated) {
      setEventError('Please confirm your Group selection');
      return;
    }

    if (!isInitiatorValidated) {
      setEventError('Please validate your Agent ID');
      return;
    }

    try {
      const userEmail = localStorage.getItem('user_email') || '';
      const formDataToSend = new FormData();

      const submissionData = {
        ...formData,
        gmail: userEmail,
        event_id: tempEventId ? Number(tempEventId) : null,
      };

      Object.entries(submissionData).forEach(([key, value]) => {
        if (value instanceof File) {
          formDataToSend.append(key, value, value.name);
        } else if (value !== null && value !== undefined) {
          formDataToSend.append(key, value.toString());
        }
      });

      await registrationService.submitRegistration(
        Object.fromEntries(formDataToSend.entries())
      );
      alert('Registration successful!');
      navigate('/waiting');
    } catch (err) {
      console.error('Submission error:', err);
      alert('Registration failed. Please try again.');
    }
  };

  return (
    <form className="form-step" onSubmit={handleSubmit}>
      <h2>Event & Initiator Information</h2>

      <div className="form-section">
        <div className="form-group">
          <label>Is this initiation part of an event?</label>
          <div className="toggle-buttons">
            <button
              type="button"
              className={`toggle-btn ${!hasEvent ? 'active' : ''}`}
              onClick={() => {
                setHasEvent(false);
                setFormData(prev => ({ ...prev, event_type: undefined }));
              }}
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
                onChange={(e) =>
                  handleEventTypeChange(e.target.value as any)
                }
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
                    onClick={
                      formData.event_type === 'private'
                        ? handleSpeakerValidation
                        : formData.event_type === 'group'
                        ? handleGroupValidation
                        : handleEventValidation
                    }
                    className="validate-btn"
                    disabled={groupLoading}
                  >
                    {groupLoading ? 'Validating...' : 'OK'}
                  </button>
                </div>

                {formData.event_type === 'private' && speakerDetails && (
                  <div className="initiator-card">
                    {speakerDetails.profilepic && (
                      <img
                        src={speakerDetails.profilepic}
                        alt="Speaker"
                        className="initiator-image"
                      />
                    )}
                    <h4>{speakerDetails.name}</h4>
                    <p>{speakerDetails.text}</p>
                  </div>
                )}

                {formData.event_type === 'group' && groupDetails && (
                  <div className="initiator-card">
                    {groupDetails.profile_pic && (
                      <img
                        src={groupDetails.profile_pic}
                        alt="Group"
                        className="initiator-image"
                      />
                    )}
                    <h4>{groupDetails.name}</h4>
                    <p>{getGroupCardText()}</p>
                  </div>
                )}

                {formData.event_type === 'private' && speakerError && (
                  <div className="error-message">{speakerError}</div>
                )}

                {formData.event_type === 'group' && groupError && (
                  <div className="error-message">{groupError}</div>
                )}

                {eventError && (
                  <div className="error-message">{eventError}</div>
                )}
              </div>
            )}
          </>
        )}
      </div>

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
          {initiatorError && (
            <div className="error-message">{initiatorError}</div>
          )}
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

      {showSameIdPopup && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3>ID Conflict</h3>
            <p>
              {formData.event_type === 'private'
                ? 'Speaker ID and Agent ID cannot be the same.'
                : 'Group ID and Agent ID cannot be the same.'}
            </p>
            <button 
              type="button" 
              className="btn-primary"
              onClick={clearFields}
            >
              Clear & Retry
            </button>
          </div>
        </div>
      )}

      {showGroupConfirm && groupDetails && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3>Confirm Group Selection</h3>
            {groupDetails.profile_pic && (
              <img 
                src={groupDetails.profile_pic} 
                alt="Group" 
                className="modal-profile-image"
              />
            )}
            <p>{getGroupMessage()}</p>
            <div className="modal-buttons">
              <button 
                type="button" 
                className="btn-secondary"
                onClick={() => setShowGroupConfirm(false)}
              >
                Cancel
              </button>
              <button 
                type="button" 
                className="btn-primary"
                onClick={confirmGroupSelection}
              >
                Confirm Group
              </button>
            </div>
          </div>
        </div>
      )}
    </form>
  );
};

export default InitiatorInfo;