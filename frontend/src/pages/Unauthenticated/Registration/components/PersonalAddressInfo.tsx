// PersonalAddressInfo.tsx
import React, { useCallback, useEffect } from 'react';
import { FormStepProps, AddressEntity } from '../types/registrationTypes';
import { useAddressSelection } from '../hooks/useAddressSelection';

const PersonalAddressInfo: React.FC<FormStepProps> = ({
  formData,
  setFormData,
  nextStep,
  prevStep,
}) => {
  const {
    countries,
    states,
    districts,
    subDistricts,
    villages,
    fetchCountries,
    fetchStates,
    fetchDistricts,
    fetchSubdistricts,
    fetchVillages,
    setStates,
    setDistricts,
    setSubDistricts,
    setVillages,
  } = useAddressSelection();

  useEffect(() => {
    fetchCountries();
  }, [fetchCountries]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  const handleAddressChange = useCallback(async (type: string, value: string) => {
    const updateFormData = (updates: any) => {
      setFormData(prev => ({ ...prev, ...updates }));
    };

    switch (type) {
      case 'country':
        updateFormData({ country: value, state: '', district: '', subdistrict: '', village: '' });
        setStates([]);
        setDistricts([]);
        setSubDistricts([]);
        setVillages([]);
        await fetchStates(Number(value));
        break;
      case 'state':
        updateFormData({ state: value, district: '', subdistrict: '', village: '' });
        setDistricts([]);
        setSubDistricts([]);
        setVillages([]);
        await fetchDistricts(Number(value));
        break;
      case 'district':
        updateFormData({ district: value, subdistrict: '', village: '' });
        setSubDistricts([]);
        setVillages([]);
        await fetchSubdistricts(Number(value));
        break;
      case 'subdistrict':
        updateFormData({ subdistrict: value, village: '' });
        setVillages([]);
        await fetchVillages(Number(value));
        break;
      default:
        break;
    }
  }, [fetchStates, fetchDistricts, fetchSubdistricts, fetchVillages, setStates, setDistricts, setSubDistricts, setVillages, setFormData]);

  return (
    <form className="form-step" onSubmit={(e) => { e.preventDefault(); nextStep(); }}>
      

      {/* Personal Info Section */}
      <div className="form-section">
        
        <div className="form-group">
          <label>First Name:</label>
          <input
            type="text"
            name="first_name"
            value={formData.first_name}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label>Last Name:</label>
          <input
            type="text"
            name="last_name"
            value={formData.last_name}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label>Date of Birth:</label>
          <input
            type="date"
            name="date_of_birth"
            value={formData.date_of_birth}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label>Gender:</label>
          <select
            name="gender"
            value={formData.gender}
            onChange={handleChange}
            required
          >
            <option value="">Select Gender</option>
            <option value="Male">Male</option>
            <option value="Female">Female</option>
            <option value="Other">Other</option>
          </select>
        </div>
      </div>

      {/* Address Info Section */}
      <div className="form-section">
        <h2>submit your original address</h2>
        <div className="form-group">
          <label>Country:</label>
          <select
            name="country"
            value={formData.country}
            onChange={(e) => handleAddressChange('country', e.target.value)}
            required
          >
            <option value="">Select Country</option>
            {countries.map((country: AddressEntity) => (
              <option key={country.id} value={String(country.id)}>
                {country.name}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>State:</label>
          <select
            name="state"
            value={formData.state}
            onChange={(e) => handleAddressChange('state', e.target.value)}
            required
            disabled={!states.length}
          >
            <option value="">Select State</option>
            {states.map((state: AddressEntity) => (
              <option key={state.id} value={String(state.id)}>
                {state.name}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>District:</label>
          <select
            name="district"
            value={formData.district}
            onChange={(e) => handleAddressChange('district', e.target.value)}
            required
            disabled={!districts.length}
          >
            <option value="">Select District</option>
            {districts.map((district: AddressEntity) => (
              <option key={district.id} value={String(district.id)}>
                {district.name}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>Subdistrict:</label>
          <select
            name="subdistrict"
            value={formData.subdistrict}
            onChange={(e) => handleAddressChange('subdistrict', e.target.value)}
            required
            disabled={!subDistricts.length}
          >
            <option value="">Select Subdistrict</option>
            {subDistricts.map((subdistrict: AddressEntity) => (
              <option key={subdistrict.id} value={String(subdistrict.id)}>
                {subdistrict.name}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>Village:</label>
          <select
            name="village"
            value={formData.village}
            onChange={(e) => setFormData(prev => ({ ...prev, village: e.target.value }))}
            required
            disabled={!villages.length}
          >
            <option value="">Select Village</option>
            {villages.map((village: AddressEntity) => (
              <option key={village.id} value={String(village.id)}>
                {village.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="form-navigation">
        <button type="button" className="btn-secondary" disabled>
          Previous
        </button>
        <button type="submit" className="btn-primary">
          Next
        </button>
      </div>
    </form>
  );
};

export default PersonalAddressInfo;