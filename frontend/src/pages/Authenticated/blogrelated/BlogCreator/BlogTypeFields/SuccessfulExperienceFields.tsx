// SuccessfulExperienceFields.tsx
import React, { useEffect, useState, useRef } from 'react';
import { BlogFormData } from '../types';
import './SuccessfulExperienceFields.css';
import './BlogTypeCommon.css';

// Map content_type to labels and lengths
const SIZE_MAP: Record<string, { label: string; chars: number }> = {
  micro: { label: 'Micro', chars: 280 },
  short_essay: { label: 'Short Essay', chars: 3200 },
  article: { label: 'Article', chars: 12000 },
};

const SIZE_ORDER = ['micro', 'short_essay', 'article'];

type Props = {
  formData: BlogFormData;
  handleChange: (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => void;
  getMaxLength: () => number;
  isSubmitting: boolean;
  name?: string;
  profile_picture?: string;
};

const SuccessfulExperienceFields: React.FC<Props> = ({
  formData,
  handleChange,
  getMaxLength,
  isSubmitting,
  name,
  profile_picture,
}) => {
  // UI state
  const [sizeMenuOpen, setSizeMenuOpen] = useState(false);
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [pendingUpgradeKey, setPendingUpgradeKey] = useState<string | null>(null);
  
  // track whether we've already prompted for this size
  const modalShownForSizeRef = useRef<string | null>(null);

  // textarea ref
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const footerMenuRef = useRef<HTMLDivElement | null>(null);

  // derive selectedSizeKey from formData.content_type (fallback to micro)
  const selectedSizeKey = formData.content_type || 'micro';
  const selectedSizeLabel = SIZE_MAP[selectedSizeKey]?.label ?? 'Micro';
  const computedMaxLength = SIZE_MAP[selectedSizeKey]?.chars ?? getMaxLength();

  // current user info
  const currentUserPic = localStorage.getItem('profile_pic') || '/placeholder-avatar.png';

  // Content length handling
  const contentLen = formData.content ? formData.content.length : 0;
  const exceedsPreset = contentLen > computedMaxLength;

  // Find next larger preset
  const nextLargerPresetKey = (() => {
    const idx = SIZE_ORDER.indexOf(selectedSizeKey);
    return idx >= 0 && idx < SIZE_ORDER.length - 1 ? SIZE_ORDER[idx + 1] : null;
  })();

  // Find appropriate preset for content length
  const findPresetForLength = (len: number): string | null => {
    for (const key of SIZE_ORDER) {
      if (SIZE_MAP[key].chars >= len) return key;
    }
    return 'article';
  };

  // Footer menu outside-click handling
  useEffect(() => {
    const onDocClick = (e: MouseEvent) => {
      if (footerMenuRef.current && !footerMenuRef.current.contains(e.target as Node)) {
        setSizeMenuOpen(false);
      }
    };
    document.addEventListener('click', onDocClick);
    return () => document.removeEventListener('click', onDocClick);
  }, []);

  // Content length exceed handling
  useEffect(() => {
    if (exceedsPreset) {
      const target = findPresetForLength(contentLen);
      if (target && target !== selectedSizeKey) {
        if (modalShownForSizeRef.current !== selectedSizeKey) {
          modalShownForSizeRef.current = selectedSizeKey;
          setPendingUpgradeKey(target);
          setShowUpgradeModal(true);
        }
      }
    } else {
      modalShownForSizeRef.current = null;
    }
  }, [exceedsPreset, contentLen, selectedSizeKey]);

  // Apply size update
  const applySize = (sizeKey: string) => {
    handleChange({
      target: {
        name: 'content_type',
        value: sizeKey,
      },
    } as React.ChangeEvent<HTMLInputElement>);
    setSizeMenuOpen(false);
    modalShownForSizeRef.current = null;
    setShowUpgradeModal(false);
    setPendingUpgradeKey(null);
  };

  const expandToNext = () => {
    if (nextLargerPresetKey) applySize(nextLargerPresetKey);
  };

  // Auto-expand textarea logic
  const adjustHeight = (el: HTMLTextAreaElement | null) => {
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${el.scrollHeight + 2}px`;
  };

  useEffect(() => {
    adjustHeight(textareaRef.current);
    Promise.resolve().then(() => adjustHeight(textareaRef.current));
  }, [formData.content, selectedSizeKey]);

  // Input handling
  const handleInput = (e: React.FormEvent<HTMLTextAreaElement>) => {
    handleChange(e as unknown as React.ChangeEvent<HTMLTextAreaElement>);
    adjustHeight(e.currentTarget);
  };

  const initiatorImgUrl = profile_picture || '/placeholder-avatar.png';

  return (
    <div className="successful-experience-composer card">
      {/* HEADER - Text on left, photo on right */}
      <div className="successful-experience-header" role="region" aria-label="Successful Experience header">
        <div className="header-text">
          <h2 className="successful-experience-title">
            Share your experience on initiating {name}
          </h2>
          <p className="successful-experience-subtitle">
            and also your expectations from {name} in terms of contributing to the movement
          </p>
        </div>
        
        <div className="header-image">
          <img
            src={initiatorImgUrl}
            alt={`${name}`}
            className="successful-experience-profile-pic"
            onError={(e) => {
              (e.target as HTMLImageElement).src = '/placeholder-avatar.png';
            }}
          />
        </div>
      </div>

      {/* BODY - Textarea with user avatar */}
      <div className="successful-experience-body">
        <div className="textarea-avatar-wrapper">
          <img 
            src={currentUserPic} 
            alt="Your avatar" 
            className="avatar-sm inside-textarea-avatar" 
          />
          <textarea
            ref={textareaRef}
            name="content"
            value={formData.content || ''}
            onChange={handleInput}
            placeholder="Share your thoughts and experiences..."
            rows={1}
            className="successful-experience-textarea with-avatar-padding auto-expand-textarea"
            maxLength={computedMaxLength}
          />
        </div>
      </div>

      {/* FOOTER - Character counter and submit button */}
      <div className="successful-experience-footer">
        <div className="footer-left" ref={footerMenuRef}>
          <div
            role="button"
            tabIndex={0}
            onClick={() => setSizeMenuOpen((s) => !s)}
            onKeyDown={(e) => e.key === 'Enter' && setSizeMenuOpen((s) => !s)}
            className={`char-counter clickable ${exceedsPreset ? 'exceeded' : ''}`}
            title="Click to change size"
          >
            {contentLen}/{computedMaxLength} · {selectedSizeLabel}
          </div>

          {sizeMenuOpen && (
            <div className="size-popup footer-popup">
              {Object.entries(SIZE_MAP).map(([key, info]) => (
                <button
                  key={key}
                  type="button"
                  className={`size-option ${key === selectedSizeKey ? 'selected' : ''}`}
                  onClick={() => applySize(key)}
                >
                  <div className="size-option-left">
                    <strong>{info.label}</strong>
                    <div className="size-option-sub">{info.chars} chars</div>
                  </div>
                  {key === selectedSizeKey && <div className="size-option-check">✓</div>}
                </button>
              ))}
            </div>
          )}

          {exceedsPreset && (
            <div className="size-warning">
              Your content exceeds the {selectedSizeLabel} limit.
              {nextLargerPresetKey ? (
                <>
                  {' '}
                  <button type="button" className="link-btn" onClick={expandToNext}>
                    Upgrade to {SIZE_MAP[nextLargerPresetKey].label}
                  </button>
                </>
              ) : (
                ' Consider shortening or choosing Article.'
              )}
            </div>
          )}
        </div>

        <div className="footer-right">
          <button
            type="submit"
            disabled={isSubmitting}
            className={`submit-btn ${isSubmitting ? 'submitting' : ''}`}
            aria-label="Create Post Button"
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
        </div>
      </div>

      {/* Upgrade Modal */}
      {showUpgradeModal && pendingUpgradeKey && (
        <div className="upgrade-modal-overlay" onClick={() => setShowUpgradeModal(false)}>
          <div className="upgrade-modal" onClick={(e) => e.stopPropagation()}>
            <h4>Upgrade size?</h4>
            <p>
              You've reached the {SIZE_MAP[selectedSizeKey].label} limit ({computedMaxLength} chars).
              Would you like to upgrade to <strong>{SIZE_MAP[pendingUpgradeKey].label}</strong> ({SIZE_MAP[pendingUpgradeKey].chars} chars) to continue typing?
            </p>
            <div className="upgrade-actions">
              <button className="btn btn-secondary" onClick={() => setShowUpgradeModal(false)}>
                Keep {SIZE_MAP[selectedSizeKey].label}
              </button>
              <button className="btn btn-primary" onClick={() => applySize(pendingUpgradeKey)}>
                Upgrade to {SIZE_MAP[pendingUpgradeKey].label}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SuccessfulExperienceFields;