import React, { useEffect, useRef, useState } from 'react';
import { BlogFormData, ContentType } from '../types';
import './ReportInsightFields.css';

type Props = {
  formData: BlogFormData;
  setFormData: React.Dispatch<React.SetStateAction<BlogFormData>>;
  getMaxLength: () => number;
  isSubmitting: boolean;
  geographical_entity?: { id: number; name: string; type: string };
  new_users?: number;
  active_users?: number;
  date?: string;
  period?: string;
  report_kind?: string;
  level?: string;
};

const contentTypeOptions: ContentType[] = ['micro', 'short_essay', 'article'];

function formatDate(dateStr?: string) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
}

const ReportInsightFields: React.FC<Props> = ({
  formData,
  setFormData,
  getMaxLength,
  isSubmitting,
  geographical_entity,
  new_users,
  active_users,
  date,
  period,
  report_kind,
  level,
}) => {
  useEffect(() => {
    console.log('📊 ReportInsightFields Extra Props:', { date, period, report_kind, geographical_entity, new_users, active_users, level });
  }, [date, period, report_kind, geographical_entity, new_users, active_users, level]);

  const contentLen = formData.content?.length || 0;
  const maxLength = getMaxLength();
  const currentUserPic = localStorage.getItem('profile_pic') || '/placeholder-avatar.png';

  // Prefer new_users if provided, otherwise use active_users
  const usersCount = typeof new_users === 'number' ? new_users : typeof active_users === 'number' ? active_users : null;
  const usersLabel = typeof new_users === 'number' ? 'New Users' : typeof active_users === 'number' ? 'Active Users' : 'Users';

  const secondLineText = (() => {
    if (!period && !report_kind) return '';
    let kindText = '';
    if (report_kind === 'report') kindText = 'Initiation';
    else if (report_kind && report_kind.toLowerCase().includes('activity')) kindText = 'Activity';
    return [period, kindText, report_kind].filter(Boolean).join(' ');
  })();

  const rightTop = level ? `Level: ${level}` : '';
  const rightBottom = geographical_entity ? `${geographical_entity.type || 'Country'}: ${geographical_entity.name || ''}` : '';

  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const [dropdownOpen, setDropdownOpen] = useState(false);

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

  const handleContentChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setFormData(prev => ({ ...prev, target_user: null, content: e.target.value }));
    adjustHeight(e.currentTarget);
  };

  return (
    <div className="report-insight-composer card">
      <div className="report-insight-header" role="region" aria-label="Report header">
        <div className="header-grid">
          {/* LEFT: date (top), second line (below) */}
          <div className="header-left">
            <div className="date-line" aria-label="Report Date">{formatDate(date)}</div>
            <div className="second-line truncate" aria-label="Report Period and Kind" title={secondLineText}>
              {secondLineText}
            </div>
          </div>

          {/* RIGHT: level (top), country/type (below) */}
          <div className="header-right">
            {/* If you want rightTop shown, re-enable the line below */}
            {/* <div className="right-top truncate" aria-label="Level">{rightTop}</div> */}
            <div className="right-bottom truncate" aria-label="Country">{rightBottom}</div>
          </div>

          {/* CENTER: people icon + users (small, centered, spans both columns) */}
          <div className="header-center-users" aria-label="Users summary">
            <svg className="people-icon" viewBox="0 0 24 24" width="18" height="18" aria-hidden>
              <path fill="currentColor" d="M16 11c1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3 1.34 3 3 3zM8 11c1.66 0 3-1.34 3-3S9.66 5 8 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h9v-2.5C10 14.17 8.33 13 6 13zM16 13c-.29 0-.62.02-.98.05 1.16.84 1.98 1.97 1.98 3.45V19h6v-2.5C23 14.17 18.33 13 16 13z"/>
            </svg>
            <span className="new-users-text">{usersCount !== null ? `${usersLabel}: ${usersCount}` : 'No users data'}</span>
          </div>
        </div>
      </div>

      <div className="report-insight-body">
        <div className="textarea-avatar-wrapper">
          <img src={currentUserPic} alt="Current user avatar" className="avatar-sm inside-textarea-avatar" />
          <textarea
            ref={textareaRef}
            name="content"
            value={formData.content || ''}
            onChange={handleContentChange}
            placeholder="Share your report insight story..."
            rows={1}
            className="report-insight-textarea with-avatar-padding auto-expand-textarea"
            maxLength={maxLength}
          />
        </div>
      </div>

      <div className="report-insight-footer">
        <div
          className="char-counter-wrapper"
          ref={dropdownRef}
          style={{ position: 'relative', display: 'inline-block', cursor: 'pointer' }}
          onClick={toggleDropdown}
          aria-haspopup="listbox"
          aria-expanded={dropdownOpen}
          tabIndex={0}
          onKeyDown={e => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              toggleDropdown();
            }
          }}
          aria-label="Select content type"
        >
          <div className="char-counter" aria-live="polite">
            {contentLen}/{maxLength} {String(formData.content_type || '').replace('_', ' ')}
          </div>

          {dropdownOpen && (
            <ul
              className="content-type-dropdown"
              role="listbox"
              aria-activedescendant={`content-type-option-${formData.content_type}`}
              style={{
                position: 'absolute',
                top: '100%',
                left: 0,
                backgroundColor: 'white',
                border: '1px solid #ddd',
                boxShadow: '0 2px 6px rgba(0,0,0,0.15)',
                zIndex: 1000,
                marginTop: 4,
                width: 'max-content',
                padding: '4px 0',
                listStyle: 'none',
              }}
            >
              {contentTypeOptions.map(type => (
                <li
                  id={`content-type-option-${type}`}
                  key={type}
                  role="option"
                  aria-selected={formData.content_type === type}
                  onClick={() => handleContentTypeSelect(type)}
                  onKeyDown={e => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      handleContentTypeSelect(type);
                    }
                  }}
                  tabIndex={0}
                  style={{
                    padding: '6px 12px',
                    backgroundColor: formData.content_type === type ? '#f0f0f0' : 'white',
                    cursor: 'pointer',
                  }}
                >
                  {type.replace('_', ' ')}
                </li>
              ))}
            </ul>
          )}
        </div>

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
  );
};

export default ReportInsightFields;
