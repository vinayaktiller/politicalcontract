import React, { useEffect, useRef, useState } from 'react';
import { BlogFormData, ContentType } from '../types';
import { config } from '../../../../Unauthenticated/config';
import './MilestoneFields.css';

// Map content_type to labels and lengths
const SIZE_MAP: Record<string, { label: string; chars: number }> = {
  micro: { label: 'Micro', chars: 280 },
  short_essay: { label: 'Short Essay', chars: 3200 },
  article: { label: 'Article', chars: 12000 },
};

const SIZE_ORDER = ['micro', 'short_essay', 'article'];

type Props = {
  formData: BlogFormData;
  setFormData: React.Dispatch<React.SetStateAction<BlogFormData>>;
  getMaxLength: () => number;
  isSubmitting: boolean;
  milestone_id?: string | null;
  title?: string;
  text?: string;
  photo_id?: string | number;
  milestone_kind?: string;
  type?: string | null;
};

const contentTypeOptions: ContentType[] = ['micro', 'short_essay', 'article'];

const MilestoneFields: React.FC<Props> = ({
  formData,
  setFormData,
  getMaxLength,
  isSubmitting,
  milestone_id,
  title,
  text,
  photo_id,
  milestone_kind,
  type,
}) => {
  // Get frontend base URL from config
  const FRONTEND_BASE_URL = config.FRONTEND_BASE_URL;

  useEffect(() => {
    console.log('🏆 MilestoneFields Extra Props:', { 
      milestone_id, title, text, photo_id, milestone_kind, type 
    });
  }, [milestone_id, title, text, photo_id, milestone_kind]);

  const contentLen = formData.content?.length || 0;
  const maxLength = getMaxLength();
  const currentUserPic = localStorage.getItem('profile_pic') || '/placeholder-avatar.png';

  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const footerMenuRef = useRef<HTMLDivElement | null>(null);
  
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [pendingUpgradeKey, setPendingUpgradeKey] = useState<string | null>(null);
  const modalShownForSizeRef = useRef<string | null>(null);
  
  // derive selectedSizeKey from formData.content_type (fallback to short_essay)
  const selectedSizeKey = formData.content_type || 'short_essay';
  const selectedSizeLabel = SIZE_MAP[selectedSizeKey]?.label ?? 'Short Essay';
  const computedMaxLength = SIZE_MAP[selectedSizeKey]?.chars ?? getMaxLength();
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

  const adjustHeight = (el: HTMLTextAreaElement | null) => {
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${el.scrollHeight + 2}px`;
  };

  useEffect(() => {
    adjustHeight(textareaRef.current);
    Promise.resolve().then(() => adjustHeight(textareaRef.current));
  }, [formData.content]);

  const toggleDropdown = () => setDropdownOpen(prev => !prev);
  const closeDropdown = () => setDropdownOpen(false);

  const handleContentTypeSelect = (type: ContentType) => {
    setFormData(prev => ({ ...prev, content_type: type }));
    closeDropdown();
  };

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        closeDropdown();
      }
    };
    if (dropdownOpen) document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [dropdownOpen]);

  // Content length exceed handling
  useEffect(() => {
    if (exceedsPreset) {
      const target = findPresetForLength(contentLen);
      if (target && target !== selectedSizeKey) {
        if (modalShownForSizeRef.current !== selectedSizeKey) {
          setPendingUpgradeKey(target);
          setShowUpgradeModal(true);
        }
      }
    }
  }, [exceedsPreset, contentLen, selectedSizeKey]);

  // Apply size update
  const applySize = (sizeKey: string) => {
    setFormData(prev => ({
      ...prev,
      content_type: sizeKey as ContentType
    }));
    setDropdownOpen(false);
    setShowUpgradeModal(false);
    setPendingUpgradeKey(null);
  };

  const expandToNext = () => {
    if (nextLargerPresetKey) applySize(nextLargerPresetKey);
  };

  const handleContentChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setFormData(prev => ({ ...prev, content: e.target.value }));
    adjustHeight(e.currentTarget);
  };

  // Set initial values
  useEffect(() => {
    setFormData(prev => ({
      ...prev,
      milestone_id: milestone_id || prev.milestone_id
    }));
  }, [milestone_id, setFormData]);

  const milestoneImgUrl =
    type && photo_id
      ? `${FRONTEND_BASE_URL}/${type}/${photo_id}.jpg`
      : `${FRONTEND_BASE_URL}/initiation/1.jpg`;

  // Footer menu outside-click handling
  useEffect(() => {
    const onDocClick = (e: MouseEvent) => {
      if (footerMenuRef.current && !footerMenuRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('click', onDocClick);
    return () => document.removeEventListener('click', onDocClick);
  }, []);

  return (
    <div className="milestone-composer card">
      <div className="milestone-header" role="region" aria-label="Milestone header">
        <div className="header-top">
          <div className="milestone-title" aria-label="Milestone Title">
            On Achiving Title "{title || 'Milestone Achievement'}"
          </div>
          {/* <div className="milestone-type" aria-label="Milestone Type">
            {milestone_kind ? `${milestone_kind}` : 'User Milestone'}
          </div> */}
        </div>
        
        <div className="milestone-image-wrapper">
          <img
            src={milestoneImgUrl}
            alt={title || 'Milestone image'}
            className="milestone-header-image"
            onError={(e) => {
              (e.target as HTMLImageElement).src = `${FRONTEND_BASE_URL}/initiation/1.jpg`;
            }}
          />
        </div>
      </div>

      <div className="milestone-body">
        <div className="textarea-avatar-wrapper">
          <img 
            src={currentUserPic} 
            alt="Current user avatar" 
            className="avatar-sm inside-textarea-avatar" 
          />
          <textarea
            ref={textareaRef}
            name="content"
            value={formData.content || ''}
            onChange={handleContentChange}
            placeholder="Share the story behind this milestone..."
            rows={1}
            className="milestone-textarea with-avatar-padding auto-expand-textarea"
            maxLength={computedMaxLength}
          />
        </div>
      </div>

      <div className="milestone-footer">
        <div className="footer-left" ref={footerMenuRef}>
          <div
            role="button"
            tabIndex={0}
            onClick={() => setDropdownOpen((s) => !s)}
            onKeyDown={(e) => e.key === 'Enter' && setDropdownOpen((s) => !s)}
            className={`char-counter clickable ${exceedsPreset ? 'exceeded' : ''}`}
            title="Click to change size"
          >
            {contentLen}/{computedMaxLength} · {selectedSizeLabel}
          </div>

          {dropdownOpen && (
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

export default MilestoneFields;