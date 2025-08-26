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
      Country : {country}
      <br />
      State : {state}
      <br />
      District : {district}
      <br />
      Subdistrict : {subdistrict} 
      <br />
      Village : {village}
    </div>
  );
};

export default AddressDetails;