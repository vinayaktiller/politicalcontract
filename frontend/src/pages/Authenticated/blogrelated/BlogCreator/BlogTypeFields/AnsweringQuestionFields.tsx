import React from 'react';
import { BlogFormData } from '../types';

type Props = {
  formData: BlogFormData;
  handleChange: (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => void;
};

const AnsweringQuestionFields: React.FC<Props> = ({ formData, handleChange }) => {
  return (
    <div className="form-group">
      <label>
        <span>Question ID</span>
        <span className="required">*</span>
      </label>
      <input
        type="number"
        name="questionid"
        value={formData.questionid || ''}
        onChange={handleChange}
        placeholder="Enter question ID"
      />
      <p className="form-hint">The ID of the question you're answering</p>
    </div>
  );
};

export default AnsweringQuestionFields;