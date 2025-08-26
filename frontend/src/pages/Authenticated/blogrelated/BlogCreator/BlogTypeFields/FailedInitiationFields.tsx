import React, { useState, useRef, useEffect, MutableRefObject } from 'react';
import { BlogFormData } from '../types';
import { useAddressSelection } from '../../../../Unauthenticated/Registration/hooks/useAddressSelection';
import './FailedInitiationFields.css';

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

const FailedInitiationFields: React.FC<Props> = ({
  formData,
  handleChange,
  getMaxLength,
  isSubmitting,
}) => {
  const {
    countries,
    states,
    districts,
    subDistricts,
    villages,
    fetchCountries,
    fetchStates,
    fetchDistricts,
    fetchSubdistricts,
    fetchVillages,
    setStates,
    setDistricts,
    setSubDistricts,
    setVillages,
  } = useAddressSelection();

  // UI state
  const [sizeMenuOpen, setSizeMenuOpen] = useState(false);
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [pendingUpgradeKey, setPendingUpgradeKey] = useState<string | null>(null);
  const [showPasteModal, setShowPasteModal] = useState(false);
  const [pasteNewText, setPasteNewText] = useState<string | null>(null);
  const [pasteCandidateLen, setPasteCandidateLen] = useState<number>(0);
  const [pasteBestPreset, setPasteBestPreset] = useState<string | null>(null);

  // Textarea ref
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  // derive selectedSizeKey from formData.content_type (fallback to short_essay)
  const selectedSizeKey = formData.content_type || 'short_essay';
  const selectedSizeLabel = SIZE_MAP[selectedSizeKey]?.label ?? 'Short Essay';
  const computedMaxLength = SIZE_MAP[selectedSizeKey]?.chars ?? getMaxLength();

  // Content length handling
  const contentLen = formData.content ? formData.content.length : 0;
  const exceedsPreset = contentLen > computedMaxLength;

  // Track whether we've prompted for size upgrade
  const modalShownForSizeRef = useRef<string | null>(null);

  // Fetch countries on mount
  useEffect(() => {
    fetchCountries();
  }, [fetchCountries]);

  // Handle address changes
  const handleAddressChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const { name, value } = e.target;
    const numericValue = value ? Number(value) : null;
    
    // Update form data using the provided handleChange
    handleChange(e);
    
    // Fetch next level of addresses
    if (name === 'country_id' && numericValue) {
      setStates([]);
      setDistricts([]);
      setSubDistricts([]);
      setVillages([]);
      await fetchStates(numericValue);
    } else if (name === 'state_id' && numericValue) {
      setDistricts([]);
      setSubDistricts([]);
      setVillages([]);
      await fetchDistricts(numericValue);
    } else if (name === 'district_id' && numericValue) {
      setSubDistricts([]);
      setVillages([]);
      await fetchSubdistricts(numericValue);
    } else if (name === 'subdistrict_id' && numericValue) {
      setVillages([]);
      await fetchVillages(numericValue);
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

  // Find appropriate preset for content length
  const findPresetForLength = (len: number): string | null => {
    for (const key of SIZE_ORDER) {
      if (SIZE_MAP[key].chars >= len) return key;
    }
    return 'article';
  };

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
    <div className="failed-initiation-card">
      <h3 className="failed-initiation-top-title">Share your failed initiation experience</h3>

      {/* Location Section */}
      <div className="failed-initiation-location-section">
        <h4>Location Information (Optional)</h4>
        <p className="failed-initiation-form-hint">Add location context for better insights</p>
        <div className="failed-initiation-location-grid">
          <div className="failed-initiation-form-group">
            <label>Country:</label>
            <select
              name="country_id"
              value={formData.country_id || ''}
              onChange={handleAddressChange}
            >
              <option value="">Select Country</option>
              {countries.map((country) => (
                <option key={country.id} value={country.id}>
                  {country.name}
                </option>
              ))}
            </select>
          </div>
          
          <div className="failed-initiation-form-group">
            <label>State:</label>
            <select
              name="state_id"
              value={formData.state_id || ''}
              onChange={handleAddressChange}
              disabled={!states.length}
            >
              <option value="">Select State</option>
              {states.map((state) => (
                <option key={state.id} value={state.id}>
                  {state.name}
                </option>
              ))}
            </select>
          </div>
          
          <div className="failed-initiation-form-group">
            <label>District:</label>
            <select
              name="district_id"
              value={formData.district_id || ''}
              onChange={handleAddressChange}
              disabled={!districts.length}
            >
              <option value="">Select District</option>
              {districts.map((district) => (
                <option key={district.id} value={district.id}>
                  {district.name}
                </option>
              ))}
            </select>
          </div>
          
          <div className="failed-initiation-form-group">
            <label>Subdistrict:</label>
            <select
              name="subdistrict_id"
              value={formData.subdistrict_id || ''}
              onChange={handleAddressChange}
              disabled={!subDistricts.length}
            >
              <option value="">Select Subdistrict</option>
              {subDistricts.map((subdistrict) => (
                <option key={subdistrict.id} value={subdistrict.id}>
                  {subdistrict.name}
                </option>
              ))}
            </select>
          </div>
          
          <div className="failed-initiation-form-group">
            <label>Village:</label>
            <select
              name="village_id"
              value={formData.village_id || ''}
              onChange={handleAddressChange}
              disabled={!villages.length}
            >
              <option value="">Select Village</option>
              {villages.map((village) => (
                <option key={village.id} value={village.id}>
                  {village.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>
      
      {/* Target Details and Failure Reason */}
      <div className="failed-initiation-form-row">
        <div className="failed-initiation-form-group">
          <label>
            <span>Other Details</span>
            <span className="failed-initiation-required">*</span>
          </label>
          <input
            type="text"
            name="target_details"
            value={formData.target_details || ''}
            onChange={handleChange}
            placeholder="Person/group details"
          />
          <p className="failed-initiation-form-hint">Describe who you were trying to initiate contact with</p>
        </div>
        
        <div className="failed-initiation-form-group">
          <label>
            <span>Failure Reason</span>
            <span className="failed-initiation-required">*</span>
          </label>
          <input
            type="text"
            name="failure_reason"
            value={formData.failure_reason || ''}
            onChange={handleChange}
            placeholder="Reason for failure"
          />
          <p className="form-hint">Explain why the initiation failed</p>
        </div>
      </div>
      
      
      
      {/* Content Section */}
      <div className="failed-initiation-panel-body">
        <div className="failed-initiation-write-layout">
          <textarea
            ref={textareaRef}
            name="content"
            value={formData.content || ''}
            onChange={handleInput}
            onInput={(e) => adjustHeight(e.currentTarget)}
            onFocus={() => handleFocusScroll(textareaRef)}
            onPaste={handlePaste}
            placeholder="Share your learnings from this experience..."
            rows={4}
            className="journey-textarea full auto-expand-textarea"
          />
        </div>

        <div className="failed-initiation-panel-footer">
          <div className="failed-initiation-footer-left">
            <div
              role="button"
              tabIndex={0}
              onClick={() => setSizeMenuOpen((s) => !s)}
              onKeyDown={(e) => e.key === 'Enter' && setSizeMenuOpen((s) => !s)}
              className={`failed-initiation-char-counter clickable ${exceedsPreset ? 'exceeded' : ''}`}
              title="Click to change size"
            >
              {contentLen}/{computedMaxLength} · {selectedSizeLabel}
            </div>

            {sizeMenuOpen && (
              <div className="failed-initiation-size-popup footer-popup">
                {Object.entries(SIZE_MAP).map(([key, info]) => (
                  <button
                    key={key}
                    type="button"
                    className={`size-option ${key === selectedSizeKey ? 'selected' : ''}`}
                    onClick={() => applySize(key)}
                  >
                    <div className="failed-initiation-size-option-left">
                      <strong>{info.label}</strong>
                      <div className="failed-initiation-size-option-sub">{info.chars} chars</div>
                    </div>
                    {key === selectedSizeKey && <div className="size-option-check">✓</div>}
                  </button>
                ))}
              </div>
            )}

            {exceedsPreset && (
              <div className="failed-initiation-size-warning">
                Your content exceeds the {selectedSizeLabel} limit. Consider shortening.
              </div>
            )}
          </div>

          <div className="failed-initiation-footer-right">
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
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="18" height="18">
                  <path d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
                  Create Post
                </>
              )}
            </button>
          </div>
        </div>

        <p className="failed-initiation-form-note">
          Your blog will be published after review. Please ensure all information is accurate.
        </p>
      </div>

      {/* Paste modal */}
      {showPasteModal && pasteNewText && (
        <div className="failed-initiation-upgrade-modal-overlay" onClick={cancelPaste}>
          <div className="failed-initiation-upgrade-modal" onClick={(e) => e.stopPropagation()}>
            <h4>Paste is larger than current size</h4>
            <p>
              The text you pasted is <strong>{pasteCandidateLen}</strong> characters.
              It exceeds the current <strong>{SIZE_MAP[selectedSizeKey].label}</strong> limit ({computedMaxLength} chars).
            </p>

            <p style={{ marginTop: 8 }}>
              Choose what should happen:
            </p>

            <div className="failed-initiation-upgrade-actions" style={{ marginTop: 12 }}>
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

      {/* Upgrade modal */}
      {showUpgradeModal && pendingUpgradeKey && (
        <div className="failed-initiation-upgrade-modal-overlay" onClick={() => setShowUpgradeModal(false)}>
          <div className="failed-initiation-upgrade-modal" onClick={(e) => e.stopPropagation()}>
            <h4>Upgrade size?</h4>
            <p>
              You've reached the {SIZE_MAP[selectedSizeKey].label} limit ({computedMaxLength} chars).
              Would you like to upgrade to <strong>{SIZE_MAP[pendingUpgradeKey].label}</strong> ({SIZE_MAP[pendingUpgradeKey].chars} chars) to continue typing?
            </p>
            <div className="failed-initiation-upgrade-actions">
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

export default FailedInitiationFields;