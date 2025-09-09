// components/PhoneNumberForm.tsx
import React, { useState, useEffect } from 'react';
import { phoneNumberService } from './phoneNumberService';

interface PhoneNumberFormProps {
  userEmail: string;
  onPhoneNumberUpdated: () => void;
}

const PhoneNumberForm: React.FC<PhoneNumberFormProps> = ({ userEmail, onPhoneNumberUpdated }) => {
  const [phoneNumber, setPhoneNumber] = useState('');
  const [originalPhoneNumber, setOriginalPhoneNumber] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchPhoneNumber();
  }, [userEmail]);

  const fetchPhoneNumber = async () => {
    try {
      const response = await phoneNumberService.getPhoneNumber(userEmail);
      if (response.phone_number) {
        setPhoneNumber(response.phone_number);
        setOriginalPhoneNumber(response.phone_number);
        setIsEditing(false);
      } else {
        setPhoneNumber('');
        setOriginalPhoneNumber('');
        setIsEditing(true); // auto-edit if first time
      }
      setMessage('');
    } catch (error) {
      console.error('Error fetching phone number:', error);
      setMessage('Failed to load phone number.');
    }
  };

  const handleSave = async () => {
    setIsLoading(true);
    setMessage('');

    try {
      await phoneNumberService.updatePhoneNumber(userEmail, phoneNumber);
      setMessage('Phone number updated successfully!');
      setOriginalPhoneNumber(phoneNumber);
      setIsEditing(false);
      onPhoneNumberUpdated();
    } catch (error) {
      setMessage('Error updating phone number. Please try again.');
      console.error('Error updating phone number:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    setPhoneNumber(originalPhoneNumber);
    setIsEditing(false);
    setMessage('');
  };

  return (
    <div className="phone-number-form">
      <h3>Contact Information</h3>
      <p>Please provide your phone number for verification purposes.</p>

      {message && (
        <div className={`message ${message.includes('Error') ? 'error' : 'success'}`}>
          {message}
        </div>
      )}

      <div className="form-group">
        <label htmlFor="phoneNumber">Phone Number</label>
        <input
          type="tel"
          id="phoneNumber"
          value={phoneNumber}
          onChange={(e) => setPhoneNumber(e.target.value)}
          disabled={!isEditing}
          placeholder="Enter your phone number"
          required
        />
      </div>

      <div className="form-actions">
        {isEditing ? (
          <>
            <button
              type="button"
              className="btn-primary"
              onClick={handleSave}
              disabled={isLoading}
            >
              {isLoading ? 'Saving...' : 'OK'}
            </button>
            {originalPhoneNumber && (
              <button
                type="button"
                className="btn-secondary"
                onClick={handleCancel}
              >
                Cancel
              </button>
            )}
          </>
        ) : (
          <button
            type="button"
            className="btn-secondary"
            onClick={() => setIsEditing(true)}
          >
            Edit
          </button>
        )}
      </div>
    </div>
  );
};

export default PhoneNumberForm;
