// import React, { useEffect, useRef, useState } from 'react';
// import { useLocation } from 'react-router-dom';
// import { useBlogForm } from './hooks/useBlogForm';
// import { BlogType, ReportType, InsightData } from './types';
// import { determineReportType } from './utils/helpers';
// import { BLOG_TYPE_COMPONENTS } from './utils/constants';
// import { JourneyFields } from './BlogTypeFields/JourneyFields';
// import { MilestoneFields } from './BlogTypeFields/MilestoneFields';
// import { ReportInsightFields } from './BlogTypeFields/ReportInsightFields';
// import { FailedInitiationFields } from './BlogTypeFields/FailedInitiationFields';
// import { ConsumptionFields } from './BlogTypeFields/ConsumptionFields';
// import { AnsweringQuestionFields } from './BlogTypeFields/AnsweringQuestionFields';
// import './BlogCreator.css';

// interface BlogTypeSelectorProps {
//   formData: any;
//   isTypeLocked: boolean;
//   insightData: InsightData | undefined;
//   onChange: (e: React.ChangeEvent<HTMLSelectElement>) => void;
// }

// const BlogTypeSelector: React.FC<BlogTypeSelectorProps> = ({
//   formData,
//   isTypeLocked,
//   insightData,
//   onChange,
// }) => (
//   <div className="form-row">
//     <div className="form-group">
//       <label htmlFor="blog-type-select">Blog Type</label>
//       <select
//         id="blog-type-select"
//         name="type"
//         value={formData.type}
//         onChange={onChange}
//         disabled={isTypeLocked}
//         aria-label="Select blog type"
//         aria-disabled={isTypeLocked}
//         className={isTypeLocked ? 'disabled-select' : ''}
//       >
//         <option value="journey">Journey</option>
//         <option value="successful_experience">Successful Experience</option>
//         <option value="milestone">Milestone</option>
//         <option value="report_insight">Report Insight</option>
//         <option value="failed_initiation">Failed Initiation</option>
//         <option value="consumption">Content Consumption</option>
//         <option value="answering_question">Answering Question</option>
//       </select>
//       {isTypeLocked && (
//         <p className="input-hint" aria-live="polite">
//           Blog type is locked because you're creating from a {insightData?.milestone_kind ? 'milestone' : 'report'}
//         </p>
//       )}
//     </div>
//   </div>
// );

// interface StatusIndicatorsProps {
//   error: string | null;
//   success: boolean;
// }

// const StatusIndicators: React.FC<StatusIndicatorsProps> = ({ error, success }) => (
//   <>
//     {error && (
//       <div className="alert error" role="alert" aria-live="assertive">
//         <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
//           <path
//             fillRule="evenodd"
//             d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
//             clipRule="evenodd"
//           />
//         </svg>
//         {error}
//       </div>
//     )}

//     {success && (
//       <div className="alert success" role="alert" aria-live="polite">
//         <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
//           <path
//             fillRule="evenodd"
//             d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
//             clipRule="evenodd"
//           />
//         </svg>
//         Blog created successfully!
//       </div>
//     )}
//   </>
// );

// const BlogCreator: React.FC = () => {
//   const location = useLocation();
//   const [isTypeLocked, setIsTypeLocked] = useState(false);
//   const isInitializedFromReport = useRef(false);
//   const prevTypeRef = useRef('');

//   const {
//     formData,
//     setFormData,
//     isSubmitting,
//     error,
//     success,
//     handleChange,
//     handleSubmit,
//     getMaxLength,
//   } = useBlogForm();

//   const insightData = location.state as InsightData | undefined;

//   // Lock the form type and prefill when opened from a report or milestone insight
//   useEffect(() => {
//     if (insightData?.report_kind) {
//       setIsTypeLocked(true);
//       isInitializedFromReport.current = true;
//       setFormData(prev => ({
//         ...prev,
//         type: 'report_insight',
//         report_id: insightData.id ? String(insightData.id) : null,
//         report_type: determineReportType(insightData.period, insightData.level, insightData.report_kind),
//         content_type: 'micro',
//       }));
//     } else if (insightData?.milestone_kind) {
//       setIsTypeLocked(true);
//       isInitializedFromReport.current = true;
//       setFormData(prev => ({
//         ...prev,
//         type: 'milestone',
//         milestone_id: insightData.milestone_id,
//         content_type: 'micro',
//       }));
//     } else {
//       setIsTypeLocked(false);
//     }
//   }, [insightData, setFormData]);

//   // Reset form when blog type changes (preserve content when switching between journey types)
//   useEffect(() => {
//     const prevType = prevTypeRef.current;
//     const JOURNEY_TYPES: BlogType[] = ['journey', 'successful_experience'];
//     const isSwitchingJourneyTypes = JOURNEY_TYPES.includes(formData.type) && JOURNEY_TYPES.includes(prevType as BlogType);

//     if (!isSwitchingJourneyTypes && formData.type !== prevType && !isInitializedFromReport.current) {
//       setFormData(prev => ({
//         ...prev,
//         content: '',
//         content_type: 'short_essay',
//       }));
//     }

//     prevTypeRef.current = formData.type;
//     isInitializedFromReport.current = false;
//   }, [formData.type, setFormData]);

//   const handleTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
//     if (isTypeLocked) return;
//     handleChange(e);
//   };

//   const TypeSpecificFields = BLOG_TYPE_COMPONENTS[formData.type];
  
//   // Prepare extra props for different field types
//   const getTypeSpecificProps = () => {
//     if (formData.type === 'report_insight') {
//       return {
//         geographical_entity: insightData?.geographical_entity,
//         new_users: insightData?.new_users,
//         active_users: insightData?.active_users,
//         date: insightData?.date,
//         period: insightData?.period,
//         report_kind: insightData?.report_kind,
//         level: insightData?.level,
//       };
//     } else if (formData.type === 'milestone') {
//       return {
//         milestone_id: insightData?.milestone_id ? String(insightData.milestone_id) : null,
//         title: insightData?.title,
//         text: insightData?.text,
//         photo_id: insightData?.photo_id,
//         type: insightData?.type,
//         milestone_kind: insightData?.milestone_kind,
//       };
//     }
//     return {};
//   };

//   return (
//     <div className="blog-creator">
//       <StatusIndicators error={error} success={success} />

//       <form onSubmit={handleSubmit} className="blog-form" noValidate>
//         <BlogTypeSelector
//           formData={formData}
//           isTypeLocked={isTypeLocked}
//           insightData={insightData}
//           onChange={handleTypeChange}
//         />

//         <TypeSpecificFields
//           formData={formData}
//           setFormData={setFormData}
//           handleChange={handleChange}
//           getMaxLength={getMaxLength}
//           isSubmitting={isSubmitting}
//           {...getTypeSpecificProps()}
//         />
//       </form>
//     </div>
//   );
// };

// export default BlogCreator;