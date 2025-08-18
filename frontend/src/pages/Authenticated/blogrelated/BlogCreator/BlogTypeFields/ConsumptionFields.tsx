import React from 'react';
import { BlogFormData } from '../types';

type Props = {
  formData: BlogFormData;
  handleChange: (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => void;
};

const ConsumptionFields: React.FC<Props> = ({ formData, handleChange }) => {
  return (
    <>
      <div className="form-group">
        <label>
          <span>Content URL</span>
          <span className="required">*</span>
        </label>
        <input
          type="url"
          name="url"
          value={formData.url || ''}
          onChange={handleChange}
          placeholder="https://example.com/content"
        />
        <p className="form-hint">Link to the content you consumed</p>
      </div>
      
      <div className="form-group">
        <label>
          <span>Contribution ID (UUID)</span>
          <span className="required">*</span>
        </label>
        <input
          type="text"
          name="contribution"
          value={formData.contribution || ''}
          onChange={handleChange}
          placeholder="Enter contribution UUID"
        />
        <p className="form-hint">The unique ID of the contribution</p>
      </div>
    </>
  );
};

export default ConsumptionFields;