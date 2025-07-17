import React from 'react';
import FormInput from './FormInput';

interface AddressSelectionProps {
  formData: any;
  countries: any[];
  states: any[];
  districts: any[];
  subDistricts: any[];
  villages: any[];
  onAddressChange: (type: string, value: string) => void;
}

const AddressSelection: React.FC<AddressSelectionProps> = ({
  formData,
  countries,
  states,
  districts,
  subDistricts,
  villages,
  onAddressChange
}) => {
  const handleSelectChange = (e: React.ChangeEvent<HTMLSelectElement | HTMLInputElement>, type: string) => {
    onAddressChange(type, e.target.value);
  };

  return (
    <>
      <FormInput
        label="Country *"
        id="country"
        name="country"
        value={formData.country}
        onChange={(e) => handleSelectChange(e, 'country')}
        type="select"
        options={countries}
        required
      />

      <FormInput
        label="State *"
        id="state"
        name="state"
        value={formData.state}
        onChange={(e) => handleSelectChange(e, 'state')}
        type="select"
        options={states}
        required
        disabled={!states.length}
      />

      <FormInput
        label="District *"
        id="district"
        name="district"
        value={formData.district}
        onChange={(e) => handleSelectChange(e, 'district')}
        type="select"
        options={districts}
        required
        disabled={!districts.length}
      />

      <FormInput
        label="Subdistrict *"
        id="subdistrict"
        name="subdistrict"
        value={formData.subdistrict}
        onChange={(e) => handleSelectChange(e, 'subdistrict')}
        type="select"
        options={subDistricts}
        required
        disabled={!subDistricts.length}
      />

      <FormInput
        label="Village *"
        id="village"
        name="village"
        value={formData.village}
        onChange={(e) => handleSelectChange(e, 'village')}
        type="select"
        options={villages}
        required
        disabled={!villages.length}
      />
    </>
  );
};

export default AddressSelection;