import React from 'react';

interface FormInputProps {
  label: string;
  id: string;
  name: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => void;
  type?: 'text' | 'select';
  options?: { id: number; name: string }[];
  required?: boolean;
  disabled?: boolean;
  placeholder?: string;
  helpText?: string;
}

const FormInput: React.FC<FormInputProps> = ({
  label,
  id,
  name,
  value,
  onChange,
  type = 'text',
  options = [],
  required = false,
  disabled = false,
  placeholder = '',
  helpText = ''
}) => {
  return (
    <div className="gr-form-group">
      <label htmlFor={id} className="gr-form-label">
        {label}
      </label>
      
      {type === 'select' ? (
        <select
          id={id}
          name={name}
          value={value}
          onChange={onChange}
          required={required}
          disabled={disabled}
          className={`gr-form-select ${disabled ? 'disabled' : ''}`}
        >
          <option value="">Select {label.replace(' *', '')}</option>
          {options.map((option) => (
            <option key={option.id} value={String(option.id)}>
              {option.name}
            </option>
          ))}
        </select>
      ) : (
        <input
          type="text"
          id={id}
          name={name}
          value={value}
          onChange={onChange}
          required={required}
          placeholder={placeholder}
          className="gr-form-input"
        />
      )}
      
      {helpText && <p className="gr-form-help">{helpText}</p>}
    </div>
  );
};

export default FormInput;