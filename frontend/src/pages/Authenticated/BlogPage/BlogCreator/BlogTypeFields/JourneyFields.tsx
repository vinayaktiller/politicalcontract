import React, { useEffect, useRef, useState } from 'react';
import { BlogFormData } from '../types';
import { SizeSelector } from '../components/SizeSelector';
import { SubmitButton } from '../components/SubmitButton';
import { adjustTextareaHeight, handleFocusScroll } from '../utils/helpers';
import './JourneyFields.css';

interface Props {
  formData: BlogFormData;
  handleChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => void;
  getMaxLength: () => number;
  isSubmitting: boolean;
}

export const JourneyFields: React.FC<Props> = ({
  formData,
  handleChange,
  getMaxLength,
  isSubmitting,
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const contentLen = formData.content?.length || 0;

  useEffect(() => {
    adjustTextareaHeight(textareaRef.current);
  }, [formData.content]);

  const handleInput = (e: React.FormEvent<HTMLTextAreaElement>) => {
    handleChange(e as unknown as React.ChangeEvent<HTMLTextAreaElement>);
    adjustTextareaHeight(e.currentTarget);
  };

  const handleSizeChange = (size: string) => {
    handleChange({
      target: {
        name: 'content_type',
        value: size,
      },
    } as React.ChangeEvent<HTMLInputElement>);
  };

  return (
    <div className="journey-composer card">
      <div className="top-section">
        <h3 className="top-title">Write along through your journey</h3>
      </div>

      <div className="bottom-panel">
        <div className="panel-body">
          <textarea
            ref={textareaRef}
            name="content"
            value={formData.content || ''}
            onChange={handleInput}
            onFocus={() => handleFocusScroll(textareaRef.current)}
            placeholder="Share your journey story..."
            rows={1}
            className="journey-textarea full auto-expand-textarea"
          />

          <div className="panel-footer">
            <div className="footer-left">
              <SizeSelector
                selectedSize={formData.content_type || 'short_essay'}
                contentLength={contentLen}
                onSizeChange={handleSizeChange}
              />
            </div>

            <div className="footer-right">
              <SubmitButton isSubmitting={isSubmitting} />
            </div>
          </div>

          <p className="form-note">
            Your blog will be published after review. Please ensure all information is accurate.
          </p>
        </div>
      </div>
    </div>
  );
};