import React, { useRef, useEffect, useState } from 'react';
import { SIZE_MAP, SIZE_ORDER } from '../utils/helpers';

interface SizeSelectorProps {
  selectedSize: string;
  contentLength: number;
  onSizeChange: (size: string) => void;
  className?: string;
}

export const SizeSelector: React.FC<SizeSelectorProps> = ({
  selectedSize,
  contentLength,
  onSizeChange,
  className = '',
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const computedMaxLength = SIZE_MAP[selectedSize]?.chars || 3200;
  const exceedsPreset = contentLength > computedMaxLength;

  // Find next larger preset
  const nextLargerPresetKey = (() => {
    const idx = SIZE_ORDER.indexOf(selectedSize);
    return idx >= 0 && idx < SIZE_ORDER.length - 1 ? SIZE_ORDER[idx + 1] : null;
  })();

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  return (
    <div className={`size-selector ${className}`} ref={dropdownRef}>
      <div
        className={`char-counter clickable ${exceedsPreset ? 'exceeded' : ''} ${isOpen ? 'active' : ''}`}
        onClick={() => setIsOpen(!isOpen)}
        title="Click to change size"
      >
        {contentLength}/{computedMaxLength} · {SIZE_MAP[selectedSize]?.label || 'Short Essay'}
      </div>

      {isOpen && (
        <div className="size-popup">
          {Object.entries(SIZE_MAP).map(([key, info]) => (
            <button
              key={key}
              type="button"
              className={`size-option ${key === selectedSize ? 'selected' : ''}`}
              onClick={() => {
                onSizeChange(key);
                setIsOpen(false);
              }}
            >
              <div className="size-option-left">
                <strong>{info.label}</strong>
                <div className="size-option-sub">{info.chars} chars</div>
              </div>
              {key === selectedSize && <div className="size-option-check">✓</div>}
            </button>
          ))}
        </div>
      )}

      {exceedsPreset && nextLargerPresetKey && (
        <div className="size-warning">
          Your content exceeds the {SIZE_MAP[selectedSize].label} limit.{' '}
          <button
            type="button"
            className="link-btn"
            onClick={() => onSizeChange(nextLargerPresetKey)}
          >
            Upgrade to {SIZE_MAP[nextLargerPresetKey].label}
          </button>
        </div>
      )}
    </div>
  );
};