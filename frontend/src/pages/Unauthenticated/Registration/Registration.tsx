// Registration.tsx
import React, { useState } from 'react';
import { FormDataTypes } from './types/registrationTypes';
import PersonalAddressInfo from './components/PersonalAddressInfo';
import ProfilePicture from './components/ProfilePicture';
import InitiatorInfo from './components/InitiatorInfo';
import './css/registration.css';

const Registration: React.FC = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const totalSteps = 3;
  
  const initialFormData: FormDataTypes = {
    gmail: localStorage.getItem('user_email') || '',
    first_name: '',
    last_name: '',
    date_of_birth: '',
    gender: '',
    country: '',
    state: '',
    district: '',
    subdistrict: '',
    village: '',
    initiator_id: undefined,
    profile_picture: null,
    event_type: 'no_event',
    event_id: undefined,
  };

  const [formData, setFormData] = useState<FormDataTypes>(initialFormData);

  const nextStep = () => setCurrentStep(prev => Math.min(prev + 1, totalSteps));
  const prevStep = () => setCurrentStep(prev => Math.max(prev - 1, 1));

  return (
    <div className="registration-container">
      <div className="progress-bar">
        {[...Array(totalSteps)].map((_, i) => (
          <div 
            key={i} 
            className={`progress-step ${i + 1 <= currentStep ? 'active' : ''}`}
          />
        ))}
      </div>

      {currentStep === 1 && (
        <PersonalAddressInfo
          formData={formData}
          setFormData={setFormData}
          nextStep={nextStep}
          prevStep={prevStep}
          currentStep={currentStep}
          totalSteps={totalSteps}
        />
      )}

      {currentStep === 2 && (
        <ProfilePicture
          formData={formData}
          setFormData={setFormData}
          nextStep={nextStep}
          prevStep={prevStep}
          currentStep={currentStep}
          totalSteps={totalSteps}
        />
      )}

      {currentStep === 3 && (
        <InitiatorInfo
          formData={formData}
          setFormData={setFormData}
          nextStep={nextStep}
          prevStep={prevStep}
          currentStep={currentStep}
          totalSteps={totalSteps}
        />
      )}
    </div>
  );
};

export default Registration;