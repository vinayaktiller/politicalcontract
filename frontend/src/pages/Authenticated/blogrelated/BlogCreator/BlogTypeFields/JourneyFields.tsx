// JourneyFields.tsx
import React, { useEffect, useState, useRef, MutableRefObject } from 'react';
import './JourneyFields.css'; 
import { BlogFormData } from '../types';
import CircleContactsModal from '../CircleContacts/CircleContactsModal';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch } from '../../../../../store';
import {
  fetchCircleContacts,
  selectCircleContacts,
  selectCircleStatus,
} from '../CircleContacts/circleContactsSlice';
import ProfileHeader from '../ProfileHeader';

type Props = {
  formData: BlogFormData;
  handleChange: (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => void;
  getMaxLength: () => number;
  isSubmitting: boolean;
};

// Map content_type to labels and lengths
const SIZE_MAP: Record<string, { label: string; chars: number }> = {
  micro: { label: 'Micro', chars: 280 },
  short_essay: { label: 'Short Essay', chars: 3200 },
  article: { label: 'Article', chars: 12000 },
};

const SIZE_ORDER = ['micro', 'short_essay', 'article'];

const JourneyFields: React.FC<Props> = ({
  formData,
  handleChange,
  getMaxLength,
  isSubmitting,
}) => {
  const dispatch = useDispatch<AppDispatch>();
  const contacts = useSelector(selectCircleContacts);
  const contactsStatus = useSelector(selectCircleStatus);

  // UI state
  const [showContactsModal, setShowContactsModal] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [sizeMenuOpen, setSizeMenuOpen] = useState(false);
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [pendingUpgradeKey, setPendingUpgradeKey] = useState<string | null>(null);
  const [showPasteModal, setShowPasteModal] = useState(false);
  const [pasteNewText, setPasteNewText] = useState<string | null>(null);
  const [pasteCandidateLen, setPasteCandidateLen] = useState<number>(0);
  const [pasteBestPreset, setPasteBestPreset] = useState<string | null>(null);

  // derive selectedSizeKey from formData.content_type (fallback to short_essay)
  const selectedSizeKey = formData.content_type || 'short_essay';
  const selectedSizeLabel = SIZE_MAP[selectedSizeKey]?.label ?? 'Short Essay';
  const computedMaxLength = SIZE_MAP[selectedSizeKey]?.chars ?? getMaxLength();

  // track whether we've already prompted for this size
  const modalShownForSizeRef = useRef<string | null>(null);

  // textarea ref
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  // current user info
  const currentUserName = localStorage.getItem('name') || 'User';
  const currentUserPic = localStorage.getItem('profile_pic') || '';
  const currentUserId = localStorage.getItem('user_id')
    ? Number(localStorage.getItem('user_id'))
    : null;

  // Fixed: Proper default journey setup
  useEffect(() => {
    // Only set if we have a current user ID and target_user is not set to it
    if (currentUserId && formData.target_user !== currentUserId) {
      handleSelfJourney();
    }
  }, [currentUserId]); // Only run when currentUserId changes

  // fetch contacts
  useEffect(() => {
    dispatch(fetchCircleContacts(false));
  }, [dispatch]);

  const handleContactSelect = (contactId: number) => {
    handleChange({
      target: {
        name: 'target_user',
        value: contactId,
      },
    } as unknown as React.ChangeEvent<HTMLInputElement>);
    setShowContactsModal(false);
  };

  const handleRefreshContacts = async () => {
    setIsRefreshing(true);
    await dispatch(fetchCircleContacts(true));
    setIsRefreshing(false);
  };

  const handleSelfJourney = () => {
    if (currentUserId !== null) {
      handleChange({
        target: {
          name: 'target_user',
          value: currentUserId,
        },
      } as unknown as React.ChangeEvent<HTMLInputElement>);
    }
  };

  // Fixed: Proper numeric comparisons
  const isSelfJourney = currentUserId !== null && formData.target_user === currentUserId;
  const isOtherJourney = formData.target_user !== null && formData.target_user !== currentUserId;

  const selectedContact = contacts.find(c => c.id === formData.target_user);
  const targetName = selectedContact ? selectedContact.name : 'Unknown User';

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
  const footerMenuRef = useRef<HTMLDivElement | null>(null);
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

  // Scroll handling
  const handleFocusScroll = (elRef: MutableRefObject<HTMLTextAreaElement | null>) => {
    const el = elRef.current;
    if (!el) return;
    setTimeout(() => {
      try {
        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        const top = el.getBoundingClientRect().top + window.scrollY - 8;
        window.scrollTo({ top, behavior: 'smooth' });
      } catch (e) {}
    }, 160);
  };

  // Input handling
  const handleInput = (e: React.FormEvent<HTMLTextAreaElement>) => {
    handleChange(e as unknown as React.ChangeEvent<HTMLTextAreaElement>);
    adjustHeight(e.currentTarget);
  };

  // Paste handling
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
    <div className="journey-composer card">
      {/* TOP SECTION */}
      <div className="top-section">
        <div className="top-left">
          <h3 className="top-title">Write along through your journey</h3>
        </div>
        <div className="top-controls">
          <button
            type="button"
            className={`journey-toggle ${isSelfJourney ? 'active' : ''}`}
            onClick={handleSelfJourney}
            aria-pressed={isSelfJourney}
          >
            On your journey
          </button>

          <button
            type="button"
            className={`journey-toggle ${isOtherJourney ? 'active' : ''}`}
            onClick={() => setShowContactsModal(true)}
            aria-pressed={isOtherJourney}
          >
            On other's journey
          </button>
        </div>
      </div>

      {/* BOTTOM PANEL */}
      <div className="bottom-panel">
        <div className="panel-header">
          {isSelfJourney ? (
            <ProfileHeader name={currentUserName} profilePic={currentUserPic} onUserJourney={true} />
          ) : (
            <ProfileHeader
              name={targetName}
              profilePic={selectedContact?.profile_pic || ''}
              onUserJourney={false}
              targetName={targetName}
            />
          )}
        </div>

        <div className="panel-body">
          {isOtherJourney ? (
            <div className="textarea-avatar-wrapper">
              <img
                src={currentUserPic || '/placeholder-avatar.png'}
                alt={`${currentUserName} avatar`}
                className="avatar-sm inside-textarea-avatar"
              />
              <textarea
                ref={textareaRef}
                name="content"
                value={formData.content || ''}
                onChange={handleInput}
                onInput={(e) => adjustHeight(e.currentTarget)}
                onFocus={() => handleFocusScroll(textareaRef)}
                onPaste={handlePaste}
                placeholder={`Write on ${targetName}'s journey...`}
                rows={1}
                className="journey-textarea with-avatar-padding auto-expand-textarea"
              />
            </div>
          ) : (
            <div className="write-layout">
              <textarea
                ref={textareaRef}
                name="content"
                value={formData.content || ''}
                onChange={handleInput}
                onInput={(e) => adjustHeight(e.currentTarget)}
                onFocus={() => handleFocusScroll(textareaRef)}
                onPaste={handlePaste}
                placeholder="Share your journey story..."
                rows={1}
                className="journey-textarea full auto-expand-textarea"
              />
            </div>
          )}

          <div className="panel-footer">
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
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                    Create Post
                  </>
                )}
              </button>
            </div>
          </div>

          <p className="form-note">
            Your blog will be published after review. Please ensure all information is accurate.
          </p>
        </div>
      </div>

      {/* Modals */}
      {showPasteModal && pasteNewText && (
        <div className="upgrade-modal-overlay" onClick={cancelPaste}>
          <div className="upgrade-modal" onClick={(e) => e.stopPropagation()}>
            <h4>Paste is larger than current size</h4>
            <p>
              The text you pasted is <strong>{pasteCandidateLen}</strong> characters.
              It exceeds the current <strong>{SIZE_MAP[selectedSizeKey].label}</strong> limit ({computedMaxLength} chars).
            </p>

            <p style={{ marginTop: 8 }}>
              Choose what should happen:
            </p>

            <div className="upgrade-actions" style={{ marginTop: 12 }}>
              <button className="btn btn-secondary" onClick={trimToCurrent}>
                Trim to {SIZE_MAP[selectedSizeKey].label} ({computedMaxLength} chars)
              </button>

              {pasteBestPreset && pasteBestPreset !== selectedSizeKey && (
                <button
                  className="btn btn-primary"
                  onClick={() => upgradeToPreset(pasteBestPreset)}
                >
                  Upgrade to {SIZE_MAP[pasteBestPreset].label} ({SIZE_MAP[pasteBestPreset].chars})
                </button>
              )}

              <button className="btn btn-secondary" onClick={cancelPaste} style={{ marginLeft: 8 }}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

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

      {showContactsModal && (
        <CircleContactsModal
          contacts={contacts}
          loading={contactsStatus === 'loading'}
          onClose={() => setShowContactsModal(false)}
          onSelect={handleContactSelect}
          onRefresh={handleRefreshContacts}
          isRefreshing={isRefreshing}
        />
      )}
    </div>
  );
};

export default JourneyFields;