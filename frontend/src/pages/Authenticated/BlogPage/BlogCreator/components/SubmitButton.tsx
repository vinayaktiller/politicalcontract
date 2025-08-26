import React from 'react';

interface SubmitButtonProps {
  isSubmitting: boolean;
  disabled?: boolean;
  className?: string;
}

export const SubmitButton: React.FC<SubmitButtonProps> = ({
  isSubmitting,
  disabled = false,
  className = '',
}) => (
  <button
    type="submit"
    disabled={isSubmitting || disabled}
    className={`submit-btn ${isSubmitting ? 'submitting' : ''} ${className}`}
  >
    {isSubmitting ? (
      <>
        <svg className="spinner" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
        </svg>
        Creating...
      </>
    ) : (
      <>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="18" height="18">
          <path d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
        </svg>
        Create Post
      </>
    )}
  </button>
);