import React, { useState } from 'react';
import api from '../../../api';
import './ClaimContributionForm.css';

const ClaimContributionForm = () => {
  const [formData, setFormData] = useState({
    link: '',
    title: '',
    discription: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setSuccess(false);
    setError(null);

    try {
      const userId = localStorage.getItem("user_id");
      if (!userId) {
        setError("User not logged in. Please log in to claim your contribution.");
        setIsSubmitting(false);
        return;
      }

      // Build request payload INCLUDING owner
      const payload = {
        ...formData,
        owner: parseInt(userId, 10), // Ensure it’s a number
      };

      console.log("Submitting contribution payload:", payload);

      await api.post('/api/blog_related/contributions/create/', payload);

      setSuccess(true);
      setFormData({ link: '', title: '', discription: '' });
    } catch (err: any) {
      console.error('Error claiming contribution:', err.response?.data || err.message);
      const errorMsg =
        err.response?.data?.detail ||
        err.response?.data?.link?.[0] || 
        'Failed to claim contribution';
      setError(errorMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="contribution-page-container">
      <div className="contribution-page-card">
        <div className="contribution-page-header">
          <h1>Claim Your Contribution</h1>
          <p>Share your published work and get recognition</p>
        </div>

        {success && (
          <div className="contribution-success-message">
            <svg className="contribution-success-icon" viewBox="0 0 24 24">
              <path fill="currentColor" d="M12,2A10,10 0 0,1 22,12A10,10 0 0,1 12,22A10,10 0 0,1 2,12A10,10 0 0,1 12,2M11,16.5L18,9.5L16.59,8.09L11,13.67L7.91,10.59L6.5,12L11,16.5Z" />
            </svg>
            <p>Contribution claimed successfully!</p>
          </div>
        )}

        {error && (
          <div className="contribution-error-message">
            <svg className="contribution-error-icon" viewBox="0 0 24 24">
              <path fill="currentColor" d="M13,13H11V7H13M13,17H11V15H13M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2Z" />
            </svg>
            <p>{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="contribution-page-form">
          <div className="contribution-form-group">
            <label htmlFor="link">Content URL *</label>
            <input
              type="url"
              id="link"
              name="link"
              value={formData.link}
              onChange={handleChange}
              placeholder="https://example.com/your-content"
              required
              className={error?.includes('URL') ? 'contribution-input-error' : ''}
            />
            <div className="contribution-input-hint">
              Paste the direct link to your published content
            </div>
          </div>

          <div className="contribution-form-group">
            <label htmlFor="title">Title</label>
            <input
              type="text"
              id="title"
              name="title"
              value={formData.title}
              onChange={handleChange}
              placeholder="My Amazing Article/Video"
            />
            <div className="contribution-input-hint">
              A descriptive title for your contribution
            </div>
          </div>

          <div className="contribution-form-group">
            <label htmlFor="discription">Description</label>
            <textarea
              id="discription"
              name="discription"
              value={formData.discription}
              onChange={handleChange}
              placeholder="Briefly describe your contribution..."
              rows={4}
            />
            <div className="contribution-input-hint">
              Optional details about your work
            </div>
          </div>

          <button
            type="submit"
            className="contribution-submit-btn"
            disabled={isSubmitting || !formData.link}
          >
            {isSubmitting ? (
              <>
                <span className="contribution-spinner"></span> Processing...
              </>
            ) : (
              'Claim Contribution'
            )}
          </button>

          <div className="contribution-form-footer">
            <p>By claiming, you verify this is your original content</p>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ClaimContributionForm;
