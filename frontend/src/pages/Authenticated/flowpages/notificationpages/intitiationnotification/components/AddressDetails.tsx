import React from 'react';
import '../styles.css';

interface AddressDetailsProps {
  country: number;
  state: number;
  district: number;
  subdistrict: number;
  village: number;
}

const AddressDetails: React.FC<AddressDetailsProps> = ({ 
  country, 
  state, 
  district, 
  subdistrict, 
  village 
}) => {
  return (
    <div className="profile-address">
      Address 
      <br />
      Country ID: {country}
      <br />
      State ID: {state}
      <br />
      District ID: {district}
      <br />
      Subdistrict ID: {subdistrict} 
      <br />
      Village ID: {village}
    </div>
  );
};

export default AddressDetails;