import React, { useState, useEffect } from 'react';
import api from '../../../../api'; // Your configured axios instance

import './BlogCreator.css';

// Type definitions
type BlogType =
  | 'journey'
  | 'successful_experience'
  | 'milestone'
  | 'report_insight'
  | 'failed_initiation'
  | 'consumption'
  | 'answering_question';

type ContentType = 'micro' | 'short_essay' | 'article';

type ReportType =
  | 'activity_reports.DailyVillageActivityReport'
  | 'activity_reports.WeeklyVillageActivityReport'
  | 'activity_reports.MonthlyVillageActivityReport'
  | 'activity_reports.DailySubdistrictActivityReport'
  | 'activity_reports.WeeklySubdistrictActivityReport'
  | 'activity_reports.MonthlySubdistrictActivityReport'
  | 'activity_reports.DailyDistrictActivityReport'
  | 'activity_reports.WeeklyDistrictActivityReport'
  | 'activity_reports.MonthlyDistrictActivityReport'
  | 'activity_reports.DailyStateActivityReport'
  | 'activity_reports.WeeklyStateActivityReport'
  | 'activity_reports.MonthlyStateActivityReport'
  | 'activity_reports.DailyCountryActivityReport'
  | 'activity_reports.WeeklyCountryActivityReport'
  | 'activity_reports.MonthlyCountryActivityReport'
  | 'report.VillageDailyReport'
  | 'report.VillageWeeklyReport'
  | 'report.VillageMonthlyReport'
  | 'report.SubdistrictDailyReport'
  | 'report.SubdistrictWeeklyReport'
  | 'report.SubdistrictMonthlyReport'
  | 'report.DistrictDailyReport'
  | 'report.DistrictWeeklyReport'
  | 'report.DistrictMonthlyReport'
  | 'report.StateDailyReport'
  | 'report.StateWeeklyReport'
  | 'report.StateMonthlyReport'
  | 'report.CountryDailyReport'
  | 'report.CountryWeeklyReport'
  | 'report.CountryMonthlyReport'
  | 'report.CumulativeReport'
  | 'report.OverallReport';

interface BlogFormData {
  type: BlogType;
  content_type: ContentType;
  content: string;
  target_user?: number | null;
  milestone_id?: string | null;
  report_type?: ReportType | null;
  report_id?: number | null;
  url?: string | null;
  contribution?: string | null;
  questionid?: number | null;
  country_id?: number | null;
  state_id?: number | null;
  district_id?: number | null;
  subdistrict_id?: number | null;
  village_id?: number | null;
  target_details?: string | null;
  failure_reason?: string | null;
  userid: number | null;
}

const BlogCreatorr: React.FC = () => {
  const userIdFromStorage = localStorage.getItem("user_id");
  const initialUserId = userIdFromStorage ? parseInt(userIdFromStorage, 10) : null;
  
  const initialFormData: BlogFormData = {
    type: 'journey',
    content_type: 'micro',
    content: '',
    userid: initialUserId,
  };

  const [formData, setFormData] = useState<BlogFormData>(initialFormData);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    setFormData((prev) => ({
      ...initialFormData,
      type: prev.type,
      content_type: prev.content_type,
      content: prev.content,
    }));
  }, [formData.type]);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;

    const finalValue = [
      'target_user',
      'report_id',
      'questionid',
      'country_id',
      'state_id',
      'district_id',
      'subdistrict_id',
      'village_id',
    ].includes(name)
      ? value === ''
        ? null
        : Number(value)
      : value;

    setFormData((prev) => ({
      ...prev,
      [name]: finalValue,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);
    setSuccess(false);

    try {
      const response = await api.post('/api/blog/create-blog/', formData);
      console.log('Blog created:', response.data);
      setSuccess(true);
      // Reset form after successful submission
      setFormData(initialFormData);
    } catch (err: any) {
      console.error('Error creating blog:', err.response?.data || err.message);
      setError(err.response?.data?.message || 'Failed to create blog');
    } finally {
      setIsSubmitting(false);
    }
  };

  const getMaxLength = () => {
    switch (formData.content_type) {
      case 'micro': return 280;
      case 'short_essay': return 3200;
      case 'article': return 12000;
      default: return 280;
    }
  };

  const reportTypeOptions: { value: ReportType; label: string }[] = [
    { value: 'activity_reports.DailyVillageActivityReport', label: 'Daily Village Activity Report' },
    { value: 'activity_reports.WeeklyVillageActivityReport', label: 'Weekly Village Activity Report' },
    { value: 'activity_reports.MonthlyVillageActivityReport', label: 'Monthly Village Activity Report' },
    { value: 'activity_reports.DailySubdistrictActivityReport', label: 'Daily Subdistrict Activity Report' },
    { value: 'activity_reports.WeeklySubdistrictActivityReport', label: 'Weekly Subdistrict Activity Report' },
    { value: 'activity_reports.MonthlySubdistrictActivityReport', label: 'Monthly Subdistrict Activity Report' },
    { value: 'activity_reports.DailyDistrictActivityReport', label: 'Daily District Activity Report' },
    { value: 'activity_reports.WeeklyDistrictActivityReport', label: 'Weekly District Activity Report' },
    { value: 'activity_reports.MonthlyDistrictActivityReport', label: 'Monthly District Activity Report' },
    { value: 'activity_reports.DailyStateActivityReport', label: 'Daily State Activity Report' },
    { value: 'activity_reports.WeeklyStateActivityReport', label: 'Weekly State Activity Report' },
    { value: 'activity_reports.MonthlyStateActivityReport', label: 'Monthly State Activity Report' },
    { value: 'activity_reports.DailyCountryActivityReport', label: 'Daily Country Activity Report' },
    { value: 'activity_reports.WeeklyCountryActivityReport', label: 'Weekly Country Activity Report' },
    { value: 'activity_reports.MonthlyCountryActivityReport', label: 'Monthly Country Activity Report' },

    { value: 'report.VillageDailyReport', label: 'Village Daily Report' },
    { value: 'report.VillageWeeklyReport', label: 'Village Weekly Report' },
    { value: 'report.VillageMonthlyReport', label: 'Village Monthly Report' },
    { value: 'report.SubdistrictDailyReport', label: 'Subdistrict Daily Report' },
    { value: 'report.SubdistrictWeeklyReport', label: 'Subdistrict Weekly Report' },
    { value: 'report.SubdistrictMonthlyReport', label: 'Subdistrict Monthly Report' },
    { value: 'report.DistrictDailyReport', label: 'District Daily Report' },
    { value: 'report.DistrictWeeklyReport', label: 'District Weekly Report' },
    { value: 'report.DistrictMonthlyReport', label: 'District Monthly Report' },
    { value: 'report.StateDailyReport', label: 'State Daily Report' },
    { value: 'report.StateWeeklyReport', label: 'State Weekly Report' },
    { value: 'report.StateMonthlyReport', label: 'State Monthly Report' },
    { value: 'report.CountryDailyReport', label: 'Country Daily Report' },
    { value: 'report.CountryWeeklyReport', label: 'Country Weekly Report' },
    { value: 'report.CountryMonthlyReport', label: 'Country Monthly Report' },
    { value: 'report.CumulativeReport', label: 'Cumulative Report' },
    { value: 'report.OverallReport', label: 'Overall Report' },
  ];

  return (
    <div className="blog-creator">
      <div className="blog-creator-card">
        <div className="blog-creator-header">
          <h2>Create Your Blog Post</h2>
          <p>Share your experiences, insights, and stories with our community</p>
          <div className="header-divider"></div>
        </div>

        {error && (
          <div className="alert error">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            {error}
          </div>
        )}

        {success && (
          <div className="alert success">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            Blog created successfully!
          </div>
        )}

        <form onSubmit={handleSubmit} className="blog-form">
          <div className="form-row">
            <div className="form-group">
              <label>Blog Type</label>
              <select
                name="type"
                value={formData.type}
                onChange={handleChange}
              >
                <option value="journey">Journey</option>
                <option value="successful_experience">Successful Experience</option>
                <option value="milestone">Milestone</option>
                <option value="report_insight">Report Insight</option>
                <option value="failed_initiation">Failed Initiation</option>
                <option value="consumption">Content Consumption</option>
                <option value="answering_question">Answering Question</option>
              </select>
              <p className="form-hint">Select the category for your blog post</p>
            </div>

            <div className="form-group">
              <label>Content Format</label>
              <select
                name="content_type"
                value={formData.content_type}
                onChange={handleChange}
              >
                <option value="micro">Micro (280 chars)</option>
                <option value="short_essay">Short Essay (3200 chars)</option>
                <option value="article">Article (12000 chars)</option>
              </select>
              <p className="form-hint">Choose the length of your content</p>
            </div>
          </div>

          <div className="form-group content-group">
            <div className="content-header">
              <label>
                Content
                {formData.type !== 'failed_initiation' && <span className="required">*</span>}
              </label>
              <div className="char-counter">
                {formData.content.length}/{getMaxLength()}
              </div>
            </div>
            
            <textarea
              name="content"
              value={formData.content}
              onChange={handleChange}
              placeholder="Share your story..."
              rows={formData.content_type === 'micro' ? 4 : 8}
              maxLength={getMaxLength()}
              className={formData.type === 'failed_initiation' ? 'disabled' : ''}
              disabled={formData.type === 'failed_initiation'}
            />
            
            {formData.type === 'failed_initiation' && (
              <p className="form-hint">
                Content field is not needed for Failed Initiation posts
              </p>
            )}
          </div>

          <div className="additional-info">
            <h3>Additional Information</h3>
            
            <div className="form-row">
              {/* Target User */}
              {['journey', 'successful_experience', 'milestone'].includes(formData.type) && (
                <div className="form-group">
                  <label>
                    <span>Target User ID</span>
                    <span className="required">*</span>
                  </label>
                  <input
                    type="number"
                    name="target_user"
                    value={formData.target_user || ''}
                    onChange={handleChange}
                    placeholder="Enter user ID"
                  />
                </div>
              )}

              {/* Milestone ID */}
              {formData.type === 'milestone' && (
                <div className="form-group">
                  <label>
                    <span>Milestone ID (UUID)</span>
                    <span className="required">*</span>
                  </label>
                  <input
                    type="text"
                    name="milestone_id"
                    value={formData.milestone_id || ''}
                    onChange={handleChange}
                    placeholder="Enter milestone UUID"
                  />
                </div>
              )}

              {/* Report Fields */}
              {formData.type === 'report_insight' && (
                <>
                  <div className="form-group">
                    <label>
                      <span>Report Type</span>
                      <span className="required">*</span>
                    </label>
                    <select
                      name="report_type"
                      value={formData.report_type || ''}
                      onChange={handleChange}
                    >
                      <option value="">Select a report type</option>
                      {reportTypeOptions.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="form-group">
                    <label>
                      <span>Report ID</span>
                      <span className="required">*</span>
                    </label>
                    <input
                      type="number"
                      name="report_id"
                      value={formData.report_id || ''}
                      onChange={handleChange}
                      placeholder="Enter report ID"
                    />
                  </div>
                </>
              )}

              {/* Consumption Fields */}
              {formData.type === 'consumption' && (
                <>
                  <div className="form-group">
                    <label>
                      <span>Content URL</span>
                      <span className="required">*</span>
                    </label>
                    <input
                      type="url"
                      name="url"
                      value={formData.url || ''}
                      onChange={handleChange}
                      placeholder="https://example.com/content"
                    />
                  </div>
                  <div className="form-group">
                    <label>
                      <span>Contribution ID (UUID)</span>
                      <span className="required">*</span>
                    </label>
                    <input
                      type="text"
                      name="contribution"
                      value={formData.contribution || ''}
                      onChange={handleChange}
                      placeholder="Enter contribution UUID"
                    />
                  </div>
                </>
              )}

              {/* Question ID */}
              {formData.type === 'answering_question' && (
                <div className="form-group">
                  <label>
                    <span>Question ID</span>
                    <span className="required">*</span>
                  </label>
                  <input
                    type="number"
                    name="questionid"
                    value={formData.questionid || ''}
                    onChange={handleChange}
                    placeholder="Enter question ID"
                  />
                </div>
              )}

              {/* Failed Initiation Fields */}
              {formData.type === 'failed_initiation' && (
                <>
                  <div className="form-group">
                    <label>
                      <span>Target Details</span>
                      <span className="required">*</span>
                    </label>
                    <input
                      type="text"
                      name="target_details"
                      value={formData.target_details || ''}
                      onChange={handleChange}
                      placeholder="Person/group details"
                    />
                  </div>
                  <div className="form-group">
                    <label>
                      <span>Failure Reason</span>
                      <span className="required">*</span>
                    </label>
                    <input
                      type="text"
                      name="failure_reason"
                      value={formData.failure_reason || ''}
                      onChange={handleChange}
                      placeholder="Reason for failure"
                    />
                  </div>
                  
                  <div className="location-section">
                    <h4>Location Information (Optional)</h4>
                    <div className="location-grid">
                      <div className="form-group">
                        <label>Country ID</label>
                        <input
                          type="number"
                          name="country_id"
                          value={formData.country_id || ''}
                          onChange={handleChange}
                          placeholder="Country ID"
                        />
                      </div>
                      <div className="form-group">
                        <label>State ID</label>
                        <input
                          type="number"
                          name="state_id"
                          value={formData.state_id || ''}
                          onChange={handleChange}
                          placeholder="State ID"
                        />
                      </div>
                      <div className="form-group">
                        <label>District ID</label>
                        <input
                          type="number"
                          name="district_id"
                          value={formData.district_id || ''}
                          onChange={handleChange}
                          placeholder="District ID"
                        />
                      </div>
                      <div className="form-group">
                        <label>Subdistrict ID</label>
                        <input
                          type="number"
                          name="subdistrict_id"
                          value={formData.subdistrict_id || ''}
                          onChange={handleChange}
                          placeholder="Subdistrict ID"
                        />
                      </div>
                      <div className="form-group">
                        <label>Village ID</label>
                        <input
                          type="number"
                          name="village_id"
                          value={formData.village_id || ''}
                          onChange={handleChange}
                          placeholder="Village ID"
                        />
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>

          <div className="submit-section">
            <button
              type="submit"
              disabled={isSubmitting}
              className={isSubmitting ? 'submitting' : ''}
            >
              {isSubmitting ? (
                <>
                  <svg className="spinner" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"></circle>
                  </svg>
                  Creating Blog...
                </>
              ) : (
                <>
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                  Create Blog Post
                </>
              )}
            </button>
            <p className="form-note">
              Your blog will be published after review. Please ensure all information is accurate.
            </p>
          </div>
        </form>
      </div>
    </div>
  );
};

export default BlogCreatorr;