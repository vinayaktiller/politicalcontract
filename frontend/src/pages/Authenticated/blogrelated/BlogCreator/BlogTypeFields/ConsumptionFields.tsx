import React, { useEffect, useRef, useState } from 'react';
import { BlogFormData, ContentType } from '../types';
import api from '../../../../../api';
import './ConsumptionFields.css';

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
  handleChange: (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => void;
  getMaxLength: () => number;
  isSubmitting: boolean;
};

const ConsumptionFields: React.FC<Props> = ({
  formData,
  setFormData,
  handleChange,
  getMaxLength,
  isSubmitting,
}) => {
  const [pendingUrl, setPendingUrl] = useState(formData.url || '');
  const [linkError, setLinkError] = useState<string | null>(null);
  const [isFetchingContribution, setIsFetchingContribution] = useState(false);
  const [contributionDetails, setContributionDetails] = useState<{
    title: string;
    description: string;
    image?: string;
    is_temporary?: boolean;
  } | null>(null);
  const [sizeMenuOpen, setSizeMenuOpen] = useState(false);
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [pendingUpgradeKey, setPendingUpgradeKey] = useState<string | null>(null);
  const [showPasteModal, setShowPasteModal] = useState(false);
  const [pasteNewText, setPasteNewText] = useState<string | null>(null);
  const [pasteCandidateLen, setPasteCandidateLen] = useState<number>(0);
  const [pasteBestPreset, setPasteBestPreset] = useState<string | null>(null);
  const [temporaryContributions, setTemporaryContributions] = useState<string[]>([]);

  // Current user info
  const currentUserName = localStorage.getItem('name') || 'User';
  const currentUserPic = localStorage.getItem('profile_pic') || '';

  // Textarea and menu refs
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const footerMenuRef = useRef<HTMLDivElement | null>(null);

  const selectedSizeKey = formData.content_type || 'short_essay';
  const selectedSizeLabel = SIZE_MAP[selectedSizeKey]?.label ?? 'Short Essay';
  const computedMaxLength = SIZE_MAP[selectedSizeKey]?.chars ?? getMaxLength();

  const modalShownForSizeRef = useRef<string | null>(null);
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

  // Clean up temporary contributions when component unmounts
  useEffect(() => {
    return () => {
      if (temporaryContributions.length > 0) {
        temporaryContributions.forEach(contributionId => {
          api.delete(`/api/blog_related/contributions/${contributionId}/`)
            .catch(error => console.error('Failed to clean up contribution:', error));
        });
      }
    };
  }, [temporaryContributions]);

  // Handle URL check and contribution lookup (OK button)
  const handleCheckContribution = async () => {
    setIsFetchingContribution(true);
    setLinkError(null);

    if (!pendingUrl) {
      setContributionDetails(null);
      setIsFetchingContribution(false);
      setLinkError('Please enter a URL.');
      setFormData(prev => ({ ...prev, url: '', contribution: '' }));
      return;
    }

    try {
      const response = await api.get(`/api/blog_related/get-contribution/?link=${encodeURIComponent(pendingUrl)}`);
      const contribution = response.data as {
        id: string;
        title: string;
        description: string;
        image?: string;
        is_temporary?: boolean;
      };

      setFormData(prev => ({
        ...prev,
        url: pendingUrl,
        contribution: contribution.id,
      }));

      setContributionDetails({
        title: contribution.title,
        description: contribution.description,
        image: contribution.image,
        is_temporary: contribution.title === 'orphan contribution' && contribution.description === 'not claimed yet',
      });

      if (
        contribution.title === 'orphan contribution' &&
        contribution.description === 'not claimed yet'
      ) {
        setTemporaryContributions(prev => [...prev, contribution.id]);
      }
    } catch (error: any) {
      if (error.response?.status === 404) {
        setLinkError('Contribution not found. Please check the URL or claim this contribution first.');
      } else {
        setLinkError('Failed to fetch contribution details.');
      }

      setFormData(prev => ({
        ...prev,
        url: pendingUrl,
        contribution: '',
      }));
      setContributionDetails(null);
    } finally {
      setIsFetchingContribution(false);
    }
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

  // Input handling
  const handleInput = (e: React.FormEvent<HTMLTextAreaElement>) => {
    handleChange(e as unknown as React.ChangeEvent<HTMLTextAreaElement>);
    adjustHeight(e.currentTarget);
  };

  // Handle paste logic
  const handlePaste = (e: React.ClipboardEvent<HTMLTextAreaElement>) => {
    e.preventDefault();
    const paste = e.clipboardData.getData('text') || '';
    const textarea = textareaRef.current;
    if (!textarea) return;

    const start = textarea.selectionStart ?? textarea.value.length;
    const end = textarea.selectionEnd ?? textarea.value.length;

    const before = textarea.value.slice(0, start);
    const after = textarea.value.slice(end);
    const candidate = before + paste + after;
    const candidateLen = candidate.length;

    if (candidateLen <= computedMaxLength) {
      handleChange({
        target: {
          name: 'content',
          value: candidate,
        },
      } as React.ChangeEvent<HTMLTextAreaElement>);
      setTimeout(() => {
        if (textareaRef.current) {
          const newPos = before.length + paste.length;
          textareaRef.current.selectionStart = textareaRef.current.selectionEnd = newPos;
        }
        adjustHeight(textareaRef.current);
      }, 0);
      return;
    }

    const bestPreset = findPresetForLength(candidateLen) || 'article';
    setPasteNewText(candidate);
    setPasteCandidateLen(candidateLen);
    setPasteBestPreset(bestPreset);
    setShowPasteModal(true);
  };

  // Paste actions
  const trimToCurrent = () => {
    if (pasteNewText === null) return;
    const trimmed = pasteNewText.slice(0, computedMaxLength);
    handleChange({
      target: { name: 'content', value: trimmed },
    } as React.ChangeEvent<HTMLTextAreaElement>);
    setShowPasteModal(false);
    setPasteNewText(null);
    setPasteCandidateLen(0);
    setPasteBestPreset(null);
    setTimeout(() => adjustHeight(textareaRef.current), 0);
  };

  const upgradeToPreset = (presetKey: string) => {
    if (pasteNewText === null) return;
    handleChange({
      target: { name: 'content_type', value: presetKey },
    } as React.ChangeEvent<HTMLInputElement>);
    handleChange({
      target: { name: 'content', value: pasteNewText },
    } as React.ChangeEvent<HTMLTextAreaElement>);
    setShowPasteModal(false);
    setPasteNewText(null);
    setPasteCandidateLen(0);
    setPasteBestPreset(null);
    setTimeout(() => adjustHeight(textareaRef.current), 0);
  };

  const cancelPaste = () => {
    setShowPasteModal(false);
    setPasteNewText(null);
    setPasteCandidateLen(0);
    setPasteBestPreset(null);
  };

  return (
    <div className="consumption-composer card">
      {/* TOP SECTION */}
      <div className="consumption-top-section">
        <div className="consumption-top-left">
          <h3 className="consumption-top-title">Share your content consumption experience</h3>
        </div>
      </div>

      {/* CONTENT URL FIELD */}
      <div className="consumption-url-input-section">
        <div className="consumption-form-group">
          <label>
            <span>Content URL</span>
            <span className="consumption-required">*</span>
          </label>
          <div style={{ display: 'flex', gap: '8px' }}>
            <input
              type="url"
              name="url"
              value={pendingUrl}
              onChange={(e) => setPendingUrl(e.target.value)}
              placeholder="https://example.com/content"
              disabled={isSubmitting}
              className="consumption-url-input"
            />
            <button
              type="button"
              onClick={handleCheckContribution}
              disabled={isSubmitting || !pendingUrl}
              className="consumption-btn consumption-btn-primary"
            >
              OK
            </button>
          </div>
          <p className="consumption-form-hint">
            Enter a link and click OK to fetch contribution details
          </p>

          {isFetchingContribution && (
            <div className="consumption-loading-indicator">
              <span className="consumption-spinner"></span> Looking up contribution...
            </div>
          )}
          {linkError && <div className="consumption-error-message">{linkError}</div>}
          {contributionDetails?.is_temporary && (
            <div className="consumption-temporary-notice">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" width="16" height="16">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
              This is a temporary contribution. It will be deleted if not used within 24 hours.
            </div>
          )}
        </div>
      </div>

      {/* CONTRIBUTION PREVIEW */}
      {contributionDetails && (
        <div className="consumption-contribution-preview">
          <h4>Content Preview</h4>
          <div className="consumption-contribution-card">
            {contributionDetails.image && (
              <img
                src={contributionDetails.image}
                alt={contributionDetails.title || 'Content preview'}
                className="consumption-contribution-image"
              />
            )}
            <div className="consumption-contribution-content">
              <h5>{contributionDetails.title && contributionDetails.title.trim() !== '' ? contributionDetails.title : 'Not yet claimed'}</h5>
              <p>{contributionDetails.description && contributionDetails.description.trim() !== '' ? contributionDetails.description : 'Not yet claimed'}</p>
            </div>
          </div>
        </div>
      )}

      {/* BOTTOM PANEL */}
      <div className="consumption-bottom-panel">
        <div className="consumption-panel-body">
          <div className="consumption-textarea-avatar-wrapper">
            <img
              src={currentUserPic || '/placeholder-avatar.png'}
              alt={`${currentUserName} avatar`}
              className="consumption-avatar-sm consumption-inside-textarea-avatar"
            />
            <textarea
              ref={textareaRef}
              name="content"
              value={formData.content || ''}
              onChange={handleInput}
              onPaste={handlePaste}
              placeholder="Share your thoughts about this content..."
              rows={1}
              className="consumption-textarea consumption-with-avatar-padding consumption-auto-expand-textarea"
            />
          </div>

          <div className="consumption-panel-footer">
            <div className="footer-left" ref={footerMenuRef}>
              <div
                role="button"
                tabIndex={0}
                onClick={() => setSizeMenuOpen((s) => !s)}
                onKeyDown={(e) => e.key === 'Enter' && setSizeMenuOpen((s) => !s)}
                className={`consumption-char-counter consumption-clickable ${exceedsPreset ? 'exceeded' : ''} ${sizeMenuOpen ? 'active' : ''}`}
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
                      className={`consumption-size-option ${key === selectedSizeKey ? 'selected' : ''}`}
                      onClick={() => applySize(key)}
                    >
                      <div className="consumption-size-option-left">
                        <strong>{info.label}</strong>
                        <div className="consumption-size-option-sub">{info.chars} chars</div>
                      </div>
                      {key === selectedSizeKey && <div className="consumption-size-option-check">✓</div>}
                    </button>
                  ))}
                </div>
              )}
              {exceedsPreset && (
                <div className="consumption-size-warning">
                  Your content exceeds the {selectedSizeLabel} limit.
                  {nextLargerPresetKey ? (
                    <>
                      {' '}
                      <button type="button" className="consumption-link-btn" onClick={expandToNext}>
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
                disabled={isSubmitting || !formData.url || !formData.content}
                className={`submit-btn ${isSubmitting ? 'submitting' : ''}`}
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
          <p className="consumption-form-note">
            Your blog will be published after review. Please ensure all information is accurate.
          </p>
        </div>
      </div>

      {/* Modals */}
      {showPasteModal && pasteNewText && (
        <div className="consumption-upgrade-modal-overlay" onClick={cancelPaste}>
          <div className="consumption-upgrade-modal" onClick={(e) => e.stopPropagation()}>
            <h4>Paste is larger than current size</h4>
            <p>
              The text you pasted is <strong>{pasteCandidateLen}</strong> characters.
              It exceeds the current <strong>{SIZE_MAP[selectedSizeKey].label}</strong> limit ({computedMaxLength} chars).
            </p>
            <p style={{ marginTop: 8 }}>
              Choose what should happen:
            </p>
            <div className="consumption-upgrade-actions" style={{ marginTop: 12 }}>
              <button className="consumption-btn consumption-btn-secondary" onClick={trimToCurrent}>
                Trim to {SIZE_MAP[selectedSizeKey].label} ({computedMaxLength} chars)
              </button>
              {pasteBestPreset && pasteBestPreset !== selectedSizeKey && (
                <button
                  className="consumption-btn consumption-btn-primary"
                  onClick={() => upgradeToPreset(pasteBestPreset)}
                >
                  Upgrade to {SIZE_MAP[pasteBestPreset].label} ({SIZE_MAP[pasteBestPreset].chars})
                </button>
              )}
              <button className="consumption-btn consumption-btn-secondary" onClick={cancelPaste} style={{ marginLeft: 8 }}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
      {showUpgradeModal && pendingUpgradeKey && (
        <div className="consumption-upgrade-modal-overlay" onClick={() => setShowUpgradeModal(false)}>
          <div className="consumption-upgrade-modal" onClick={(e) => e.stopPropagation()}>
            <h4>Upgrade size?</h4>
            <p>
              You've reached the {SIZE_MAP[selectedSizeKey].label} limit ({computedMaxLength} chars).
              Would you like to upgrade to <strong>{SIZE_MAP[pendingUpgradeKey].label}</strong> ({SIZE_MAP[pendingUpgradeKey].chars} chars) to continue typing?
            </p>
            <div className="consumption-upgrade-actions">
              <button className="consumption-btn consumption-btn-secondary" onClick={() => setShowUpgradeModal(false)}>
                Keep {SIZE_MAP[selectedSizeKey].label}
              </button>
              <button className="consumption-btn consumption-btn-primary" onClick={() => applySize(pendingUpgradeKey)}>
                Upgrade to {SIZE_MAP[pendingUpgradeKey].label}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ConsumptionFields;
