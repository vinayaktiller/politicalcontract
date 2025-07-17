import React from 'react';
import AddressSelection from './AddressSelection';
import FormInput from './FormInput';
import useGroupRegistrationForm from './useGroupRegistrationForm';
import './GroupRegistration.css';

const GroupRegistrationForm = () => {
  const {
    formData,
    isSubmitting,
    submitMessage,
    isError,
    handleChange,
    handleAddressChange,
    handleSubmit,
    countries,
    states,
    districts,
    subDistricts,
    villages
  } = useGroupRegistrationForm();

  return (
    <div className="gr-registration-container">
      <h1 className="gr-registration-title">Register New Group</h1>
      
      {submitMessage && (
        <div className={`gr-registration-message ${isError ? 'error' : 'success'}`}>
          {submitMessage}
        </div>
      )}
      
      <form onSubmit={handleSubmit} className="gr-registration-form">
        <FormInput
          label="Group Name *"
          id="name"
          name="name"
          value={formData.name}
          onChange={handleChange}
          required
          placeholder="e.g., Nizam College 2nd Political Science Branch 2nd Peer 3rd Section"
          helpText="Please follow the format: Institution + Department + Year + Section"
        />

        <FormInput
          label="Institution/Organization"
          id="institution"
          name="institution"
          value={formData.institution}
          onChange={handleChange}
          placeholder="e.g., Nizam College or Public Community Group"
          helpText="Leave blank if not affiliated with an institution"
        />

        <div className="gr-registration-section">
          <h2 className="gr-registration-section-title">Group Location</h2>
          <AddressSelection
            formData={formData}
            countries={countries}
            states={states}
            districts={districts}
            subDistricts={subDistricts}
            villages={villages}
            onAddressChange={handleAddressChange}
          />
        </div>

        <div className="gr-registration-submit">
          <button
            type="submit"
            disabled={isSubmitting}
            className="gr-registration-button"
          >
            {isSubmitting ? 'Creating Group...' : 'Register Group'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default GroupRegistrationForm;