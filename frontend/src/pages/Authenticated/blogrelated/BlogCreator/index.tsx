import React, { useEffect, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import useBlogForm from './hooks/useBlogForm';
import { BlogType, ReportType } from './types';

import JourneyFields from './BlogTypeFields/JourneyFields';
import SuccessfulExperienceFields from './BlogTypeFields/SuccessfulExperienceFields';
import MilestoneFields from './BlogTypeFields/MilestoneFields';
import ReportInsightFields from './BlogTypeFields/ReportInsightFields';
import FailedInitiationFields from './BlogTypeFields/FailedInitiationFields';
import ConsumptionFields from './BlogTypeFields/ConsumptionFields';
import AnsweringQuestionFields from './BlogTypeFields/AnsweringQuestionFields';

import './BlogCreator.css';
import api from '../../../../api';

const BLOG_TYPE_COMPONENTS: Record<BlogType, React.FC<any>> = {
  journey: JourneyFields,
  successful_experience: SuccessfulExperienceFields,
  milestone: MilestoneFields,
  report_insight: ReportInsightFields,
  failed_initiation: FailedInitiationFields,
  consumption: ConsumptionFields,
  answering_question: AnsweringQuestionFields,
};

const BlogCreator: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [isTypeLocked, setIsTypeLocked] = useState(false);
  const [sourceType, setSourceType] = useState<string>('');
  const isInitializedFromReport = useRef(false);
  const [previousBlogType, setPreviousBlogType] = useState<BlogType | null>(null);

  // Extract insight data from navigation state
  const insightData = location.state as
    | {
        geographical_entity?: { id: number; name: string; type: string };
        id?: string | number;
        level?: string;
        new_users?: number;
        active_users?: number;
        date?: string;
        period?: string;
        report_kind?: string; 
        milestone_kind?: string;
        title?: string;
        text?: string;
        photo_id?: string | number;
        milestone_id?: string | null;
        type?: string | null;
        question_kind?: string;
        question_id?: string | null;
        question_text?: string;
        question_rank?: number;
        target_user?: number | null;
        name?: string;
        profile_picture?: string;
      }
    | undefined;

  const {
    formData,
    setFormData,
    isSubmitting,
    error,
    success,
    handleChange,
    handleSubmit,
    getMaxLength,
  } = useBlogForm();

  // Track blog type changes for cleanup
  useEffect(() => {
    if (previousBlogType === 'consumption' && formData.type !== 'consumption') {
      
      // User switched away from consumption type - clean up any temporary contributions
      if (formData.contribution) {
        api.delete(`/api/blog_related/contributions/${formData.contribution}/`)
          .then(() => {
            console.log('Cleaned up temporary contribution:', formData.contribution);
          })
          .catch(error => {
            console.error('Failed to clean up contribution:', error);
          });
      }
    }
    
    setPreviousBlogType(formData.type);
  }, [formData.type, previousBlogType, formData.contribution]);

  // Clean up on component unmount
  useEffect(() => {
    return () => {
      if (formData.type === 'consumption' && formData.contribution) {
        console.log('Component unmounting, cleaning up contribution:', formData.contribution);
        // Clean up any temporary contributions when leaving the page
        api.delete(`/api/blog_related/contributions/${formData.contribution}/`)
          .then(() => {
            console.log('Cleaned up temporary contribution on unmount:', formData.contribution);
          })
          .catch(error => {
            console.error('Failed to clean up contribution on unmount:', error);
          });
      }
    };
  }, [formData.type, formData.contribution]);

  // Extra props for different blog types
  const reportInsightExtraProps = {
    geographical_entity: insightData?.geographical_entity,
    new_users: insightData?.new_users,
    active_users: insightData?.active_users,
    date: insightData?.date,
    period: insightData?.period,
    report_kind: insightData?.report_kind,
    level: insightData?.level,
  };

  const milestoneExtraProps = {
    milestone_id: insightData?.milestone_id ? String(insightData.milestone_id) : null,
    title: insightData?.title,
    text: insightData?.text,
    photo_id: insightData?.photo_id,
    type: insightData?.type,
    milestone_kind: insightData?.milestone_kind,
  };

  const questionExtraProps = {
    question_id: insightData?.question_id,
    question_text: insightData?.question_text,
    question_rank: insightData?.question_rank,
    question_kind: insightData?.question_kind,
  };

  const successfulExperienceExtraProps = {
    target_user: insightData?.target_user,
    name: insightData?.name,
    profile_picture: insightData?.profile_picture,
  };

  const TypeSpecificFields = BLOG_TYPE_COMPONENTS[formData.type];
  const prevTypeRef = useRef(formData.type);

  // Prefill & lock type depending on source
  useEffect(() => {
    if (insightData?.report_kind) {
      setIsTypeLocked(true);
      setSourceType('report');
      isInitializedFromReport.current = true;
      setFormData(prev => ({
        ...prev,
        type: 'report_insight',
        report_id: insightData.id ? String(insightData.id) : null,
        report_type: determineReportType(insightData.period, insightData.level, insightData.report_kind),
        content_type: 'micro',
      }));
    } else if (insightData?.milestone_kind) {
      setIsTypeLocked(true);
      setSourceType('milestone');
      isInitializedFromReport.current = true;
      setFormData(prev => ({
        ...prev,
        type: 'milestone',
        milestone_id: insightData.milestone_id,
        content_type: 'micro',
      }));
    } else if (insightData?.question_kind) {
      setIsTypeLocked(true);
      setSourceType('question');
      isInitializedFromReport.current = true;
      setFormData(prev => ({
        ...prev,
        type: 'answering_question',
        questionid: insightData.question_id ? parseInt(insightData.question_id) : null,
        content_type: 'micro',
      }));
    } else if (insightData?.type === 'successful_experience') {
      setIsTypeLocked(true);
      setSourceType('successful_experience');
      isInitializedFromReport.current = true;
      setFormData(prev => ({
        ...prev,
        type: 'successful_experience',
        target_user: insightData.target_user,
        content_type: 'micro',
      }));
    } else {
      setIsTypeLocked(false);
      setSourceType('');
    }
  }, [insightData, setFormData]);

  // Reset form on blog type change
  useEffect(() => {
    const prevType = prevTypeRef.current;
    const JOURNEY_TYPES: BlogType[] = ['journey', 'successful_experience'];
    const isSwitchingJourneyTypes =
      JOURNEY_TYPES.includes(formData.type) && JOURNEY_TYPES.includes(prevType);

    if (!isSwitchingJourneyTypes && formData.type !== prevType && !isInitializedFromReport.current) {
      setFormData(prev => ({
        ...prev,
        content: '',
        content_type: 'short_essay',
      }));
    }

    prevTypeRef.current = formData.type;
    isInitializedFromReport.current = false;
  }, [formData.type, setFormData]);

  const handleTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    if (isTypeLocked) return;
    handleChange(e);
  };

  return (
    <div className="blog-creator">
      {/* Status indicators */}
      {error && (
        <div className="alert error" role="alert" aria-live="assertive">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
            <path
              fillRule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
              clipRule="evenodd"
            />
          </svg>
          {error}
        </div>
      )}

      {success && (
        <div className="alert success" role="alert" aria-live="polite">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
              clipRule="evenodd"
            />
          </svg>
          Blog created successfully!
        </div>
      )}

      <form onSubmit={handleSubmit} className="blog-form" noValidate>
        {/* Only show blog type selection when not locked */}
        {!isTypeLocked && (
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="blog-type-select">Blog Type</label>
              <select
                id="blog-type-select"
                name="type"
                value={formData.type}
                onChange={handleTypeChange}
                aria-label="Select blog type"
              >
                <option value="journey">Journey</option>
                <option value="failed_initiation">Failed Initiation</option>
                <option value="consumption">Content Consumption</option>
              </select>
            </div>
          </div>
        )}

        {TypeSpecificFields && (
          <TypeSpecificFields
            formData={formData}
            setFormData={setFormData}
            handleChange={handleChange}
            getMaxLength={getMaxLength}
            isSubmitting={isSubmitting}
            {...(formData.type === 'report_insight' ? reportInsightExtraProps : {})}
            {...(formData.type === 'milestone' ? milestoneExtraProps : {})}
            {...(formData.type === 'answering_question' ? questionExtraProps : {})}
            {...(formData.type === 'successful_experience' ? successfulExperienceExtraProps : {})}
          />
        )}
      </form>
    </div>
  );
};

// Helper to determine report type
function determineReportType(period?: string, level?: string, kind?: string): ReportType | null {
  if (!period || !level) return null;

  const periodCapitalized = period.charAt(0).toUpperCase() + period.slice(1).toLowerCase();
  const levelCapitalized = level.charAt(0).toUpperCase() + level.slice(1).toLowerCase();

  if (kind && kind.toLowerCase().includes('activity')) {
    return `activity_reports.${periodCapitalized}${levelCapitalized}ActivityReport` as ReportType;
  }

  return `report.${levelCapitalized}${periodCapitalized}Report` as ReportType;
}

export default BlogCreator;