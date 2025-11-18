// // ReportGenerationPage.tsx
// import React, { useState, useEffect } from 'react';
// import { useNavigate } from 'react-router-dom';
// import api from '../../../../../api';
// import './ReportGenerationPage.css';

// interface PendingReports {
//   daily: {
//     count: number;
//     periods: string[];
//   };
//   weekly: {
//     count: number;
//     periods: Array<{
//       week_start: string;
//       week_end: string;
//       week_number: number;
//       year: number;
//     }>;
//   };
//   monthly: {
//     count: number;
//     periods: Array<{
//       month_start: string;
//       month_end: string;
//       month: number;
//       year: number;
//     }>;
//   };
// }

// interface GenerationResult {
//   summary: {
//     total_processed: number;
//     successful: number;
//     errors: number;
//   };
//   details: {
//     daily?: Array<{
//       date: string;
//       status: 'success' | 'error';
//       message: string;
//     }>;
//     weekly?: Array<{
//       period: string;
//       status: 'success' | 'error';
//       message: string;
//     }>;
//     monthly?: Array<{
//       period: string;
//       status: 'success' | 'error';
//       message: string;
//     }>;
//   };
// }

// const ReportGenerationPage: React.FC = () => {
//   const navigate = useNavigate();
//   const [pendingReports, setPendingReports] = useState<PendingReports | null>(null);
//   const [loading, setLoading] = useState(true);
//   const [generating, setGenerating] = useState(false);
//   const [error, setError] = useState<string | null>(null);
//   const [generationResult, setGenerationResult] = useState<GenerationResult | null>(null);
//   const [activeTab, setActiveTab] = useState<'pending' | 'custom' | 'quick'>('pending');
  
//   // Custom range form state
//   const [customRange, setCustomRange] = useState({
//     startDate: '',
//     endDate: '',
//     reportTypes: ['daily', 'weekly', 'monthly'] as ('daily' | 'weekly' | 'monthly')[]
//   });

//   // Quick actions state
//   const [lastNDays, setLastNDays] = useState(7);

//   // Fetch pending reports on component mount
//   useEffect(() => {
//     fetchPendingReports();
//   }, []);

//   const fetchPendingReports = async () => {
//     try {
//       setLoading(true);
//       const response = await api.get('/api/reports/pending/');
//       setPendingReports(response.data as PendingReports);
//       setError(null);
//     } catch (err) {
//       setError('Failed to fetch pending reports');
//       console.error('Error fetching pending reports:', err);
//     } finally {
//       setLoading(false);
//     }
//   };

//   const generateAllPending = async () => {
//     try {
//       setGenerating(true);
//       const response = await api.post('/api/reports/generate-all-pending/');
//       setGenerationResult(response.data as GenerationResult);
//       // Refresh pending reports after generation
//       await fetchPendingReports();
//     } catch (err) {
//       setError('Failed to generate reports');
//       console.error('Error generating reports:', err);
//     } finally {
//       setGenerating(false);
//     }
//   };

//   const generateCustomRange = async () => {
//     if (!customRange.startDate || !customRange.endDate) {
//       setError('Please select both start and end dates');
//       return;
//     }

//     try {
//       setGenerating(true);
//       const response = await api.post('/api/reports/generate-custom/', customRange);
//       setGenerationResult(response.data as GenerationResult);
//     } catch (err) {
//       setError('Failed to generate custom reports');
//       console.error('Error generating custom reports:', err);
//     } finally {
//       setGenerating(false);
//     }
//   };

//   const generateLastNDays = async () => {
//     try {
//       setGenerating(true);
//       const response = await api.post('/api/reports/generate-last-n-days/', {
//         days: lastNDays,
//         report_types: ['daily']
//       });
//       setGenerationResult(response.data as GenerationResult);
//     } catch (err) {
//       setError('Failed to generate reports for last N days');
//       console.error('Error generating last N days reports:', err);
//     } finally {
//       setGenerating(false);
//     }
//   };

//   const handleReportTypeToggle = (type: 'daily' | 'weekly' | 'monthly') => {
//     setCustomRange(prev => ({
//       ...prev,
//       reportTypes: prev.reportTypes.includes(type)
//         ? prev.reportTypes.filter(t => t !== type)
//         : [...prev.reportTypes, type]
//     }));
//   };

//   const formatDate = (dateString: string) => {
//     return new Date(dateString).toLocaleDateString('en-US', {
//       year: 'numeric',
//       month: 'short',
//       day: 'numeric'
//     });
//   };

//   const getWeekRangeString = (week: any) => {
//     return `${formatDate(week.week_start)} - ${formatDate(week.week_end)} (Week ${week.week_number})`;
//   };

//   const getMonthString = (month: any) => {
//     const date = new Date(month.year, month.month - 1);
//     return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long' });
//   };

//   return (
//     <div className="dashboard-page">
//       <div className="dashboard-container">
//         {/* Top Bar */}
//         <div className="top-bar">
//           <h2>Report Generation</h2>
//           <div className="controls">
//             <button 
//               className="refresh-btn"
//               onClick={fetchPendingReports}
//               disabled={loading}
//             >
//               Refresh
//             </button>
//           </div>
//         </div>

//         {/* Navigation Tabs */}
//         <div className="generation-tabs">
//           <button
//             className={`tab-button ${activeTab === 'pending' ? 'active' : ''}`}
//             onClick={() => setActiveTab('pending')}
//           >
//             Pending Reports
//           </button>
//           <button
//             className={`tab-button ${activeTab === 'custom' ? 'active' : ''}`}
//             onClick={() => setActiveTab('custom')}
//           >
//             Custom Range
//           </button>
//           <button
//             className={`tab-button ${activeTab === 'quick' ? 'active' : ''}`}
//             onClick={() => setActiveTab('quick')}
//           >
//             Quick Actions
//           </button>
//         </div>

//         {/* Error Display */}
//         {error && (
//           <div className="error-message generation-error">
//             {error}
//             <button onClick={() => setError(null)} className="close-error">×</button>
//           </div>
//         )}

//         {/* Generation Results */}
//         {generationResult && (
//           <div className="generation-results">
//             <h3>Generation Results</h3>
//             <div className="results-summary">
//               <div className="summary-item total">
//                 <span className="label">Total Processed:</span>
//                 <span className="value">{generationResult.summary.total_processed}</span>
//               </div>
//               <div className="summary-item success">
//                 <span className="label">Successful:</span>
//                 <span className="value">{generationResult.summary.successful}</span>
//               </div>
//               <div className="summary-item errors">
//                 <span className="label">Errors:</span>
//                 <span className="value">{generationResult.summary.errors}</span>
//               </div>
//             </div>

//             {/* Detailed Results */}
//             <div className="detailed-results">
//               {generationResult.details.daily && generationResult.details.daily.length > 0 && (
//                 <div className="result-section">
//                   <h4>Daily Reports</h4>
//                   {generationResult.details.daily.map((result, index) => (
//                     <div key={index} className={`result-item ${result.status}`}>
//                       <span className="date">{result.date}</span>
//                       <span className="message">{result.message}</span>
//                       <span className={`status ${result.status}`}>
//                         {result.status === 'success' ? '✓' : '✗'}
//                       </span>
//                     </div>
//                   ))}
//                 </div>
//               )}

//               {generationResult.details.weekly && generationResult.details.weekly.length > 0 && (
//                 <div className="result-section">
//                   <h4>Weekly Reports</h4>
//                   {generationResult.details.weekly.map((result, index) => (
//                     <div key={index} className={`result-item ${result.status}`}>
//                       <span className="period">{result.period}</span>
//                       <span className="message">{result.message}</span>
//                       <span className={`status ${result.status}`}>
//                         {result.status === 'success' ? '✓' : '✗'}
//                       </span>
//                     </div>
//                   ))}
//                 </div>
//               )}

//               {generationResult.details.monthly && generationResult.details.monthly.length > 0 && (
//                 <div className="result-section">
//                   <h4>Monthly Reports</h4>
//                   {generationResult.details.monthly.map((result, index) => (
//                     <div key={index} className={`result-item ${result.status}`}>
//                       <span className="period">{result.period}</span>
//                       <span className="message">{result.message}</span>
//                       <span className={`status ${result.status}`}>
//                         {result.status === 'success' ? '✓' : '✗'}
//                       </span>
//                     </div>
//                   ))}
//                 </div>
//               )}
//             </div>

//             <button 
//               className="clear-results-btn"
//               onClick={() => setGenerationResult(null)}
//             >
//               Clear Results
//             </button>
//           </div>
//         )}

//         {/* Main Content based on Active Tab */}
//         <div className="generation-content">
//           {activeTab === 'pending' && (
//             <div className="pending-reports-section">
//               <div className="section-header">
//                 <h3>Pending Reports</h3>
//                 <button
//                   className="generate-all-btn"
//                   onClick={generateAllPending}
//                   disabled={generating || !pendingReports || (
//                     pendingReports.daily.count === 0 &&
//                     pendingReports.weekly.count === 0 &&
//                     pendingReports.monthly.count === 0
//                   )}
//                 >
//                   {generating ? 'Generating...' : 'Generate All Pending'}
//                 </button>
//               </div>

//               {loading ? (
//                 <div className="loader">Loading pending reports...</div>
//               ) : pendingReports ? (
//                 <div className="pending-cards">
//                   {/* Daily Pending Card */}
//                   <div className="pending-card daily">
//                     <div className="card-header">
//                       <h4>Daily Reports</h4>
//                       <span className="count-badge">{pendingReports.daily.count}</span>
//                     </div>
//                     <div className="card-content">
//                       {pendingReports.daily.count > 0 ? (
//                         <div className="pending-list">
//                           {pendingReports.daily.periods.slice(0, 5).map((date, index) => (
//                             <div key={index} className="pending-item">
//                               {formatDate(date)}
//                             </div>
//                           ))}
//                           {pendingReports.daily.count > 5 && (
//                             <div className="more-items">
//                               +{pendingReports.daily.count - 5} more dates
//                             </div>
//                           )}
//                         </div>
//                       ) : (
//                         <div className="no-pending">No pending daily reports</div>
//                       )}
//                     </div>
//                   </div>

//                   {/* Weekly Pending Card */}
//                   <div className="pending-card weekly">
//                     <div className="card-header">
//                       <h4>Weekly Reports</h4>
//                       <span className="count-badge">{pendingReports.weekly.count}</span>
//                     </div>
//                     <div className="card-content">
//                       {pendingReports.weekly.count > 0 ? (
//                         <div className="pending-list">
//                           {pendingReports.weekly.periods.slice(0, 3).map((week, index) => (
//                             <div key={index} className="pending-item">
//                               {getWeekRangeString(week)}
//                             </div>
//                           ))}
//                           {pendingReports.weekly.count > 3 && (
//                             <div className="more-items">
//                               +{pendingReports.weekly.count - 3} more weeks
//                             </div>
//                           )}
//                         </div>
//                       ) : (
//                         <div className="no-pending">No pending weekly reports</div>
//                       )}
//                     </div>
//                   </div>

//                   {/* Monthly Pending Card */}
//                   <div className="pending-card monthly">
//                     <div className="card-header">
//                       <h4>Monthly Reports</h4>
//                       <span className="count-badge">{pendingReports.monthly.count}</span>
//                     </div>
//                     <div className="card-content">
//                       {pendingReports.monthly.count > 0 ? (
//                         <div className="pending-list">
//                           {pendingReports.monthly.periods.slice(0, 3).map((month, index) => (
//                             <div key={index} className="pending-item">
//                               {getMonthString(month)}
//                             </div>
//                           ))}
//                           {pendingReports.monthly.count > 3 && (
//                             <div className="more-items">
//                               +{pendingReports.monthly.count - 3} more months
//                             </div>
//                           )}
//                         </div>
//                       ) : (
//                         <div className="no-pending">No pending monthly reports</div>
//                       )}
//                     </div>
//                   </div>
//                 </div>
//               ) : (
//                 <div className="error-message">Failed to load pending reports</div>
//               )}
//             </div>
//           )}

//           {activeTab === 'custom' && (
//             <div className="custom-range-section">
//               <h3>Generate Custom Range Reports</h3>
//               <div className="custom-form">
//                 <div className="form-group">
//                   <label htmlFor="startDate">Start Date</label>
//                   <input
//                     type="date"
//                     id="startDate"
//                     value={customRange.startDate}
//                     onChange={(e) => setCustomRange(prev => ({ ...prev, startDate: e.target.value }))}
//                   />
//                 </div>

//                 <div className="form-group">
//                   <label htmlFor="endDate">End Date</label>
//                   <input
//                     type="date"
//                     id="endDate"
//                     value={customRange.endDate}
//                     onChange={(e) => setCustomRange(prev => ({ ...prev, endDate: e.target.value }))}
//                   />
//                 </div>

//                 <div className="form-group">
//                   <label>Report Types</label>
//                   <div className="report-type-checkboxes">
//                     <label className="checkbox-label">
//                       <input
//                         type="checkbox"
//                         checked={customRange.reportTypes.includes('daily')}
//                         onChange={() => handleReportTypeToggle('daily')}
//                       />
//                       Daily Reports
//                     </label>
//                     <label className="checkbox-label">
//                       <input
//                         type="checkbox"
//                         checked={customRange.reportTypes.includes('weekly')}
//                         onChange={() => handleReportTypeToggle('weekly')}
//                       />
//                       Weekly Reports
//                     </label>
//                     <label className="checkbox-label">
//                       <input
//                         type="checkbox"
//                         checked={customRange.reportTypes.includes('monthly')}
//                         onChange={() => handleReportTypeToggle('monthly')}
//                       />
//                       Monthly Reports
//                     </label>
//                   </div>
//                 </div>

//                 <button
//                   className="generate-custom-btn"
//                   onClick={generateCustomRange}
//                   disabled={generating || !customRange.startDate || !customRange.endDate}
//                 >
//                   {generating ? 'Generating...' : 'Generate Custom Reports'}
//                 </button>
//               </div>
//             </div>
//           )}

//           {activeTab === 'quick' && (
//             <div className="quick-actions-section">
//               <h3>Quick Actions</h3>
              
//               <div className="quick-action-cards">
//                 {/* Last N Days Card */}
//                 <div className="quick-action-card">
//                   <div className="action-header">
//                     <h4>Generate Last N Days</h4>
//                     <div className="days-input">
//                       <input
//                         type="number"
//                         min="1"
//                         max="365"
//                         value={lastNDays}
//                         onChange={(e) => setLastNDays(parseInt(e.target.value) || 1)}
//                       />
//                       <span>days</span>
//                     </div>
//                   </div>
//                   <p>Generate daily reports for the last specified number of days.</p>
//                   <button
//                     className="action-btn"
//                     onClick={generateLastNDays}
//                     disabled={generating}
//                   >
//                     {generating ? 'Generating...' : `Generate Last ${lastNDays} Days`}
//                   </button>
//                 </div>

//                 {/* Yesterday Card */}
//                 <div className="quick-action-card">
//                   <div className="action-header">
//                     <h4>Generate Yesterday's Report</h4>
//                   </div>
//                   <p>Generate daily report for yesterday only.</p>
//                   <button
//                     className="action-btn"
//                     onClick={() => {
//                       const yesterday = new Date();
//                       yesterday.setDate(yesterday.getDate() - 1);
//                       setCustomRange({
//                         startDate: yesterday.toISOString().split('T')[0],
//                         endDate: yesterday.toISOString().split('T')[0],
//                         reportTypes: ['daily']
//                       });
//                       setActiveTab('custom');
//                     }}
//                   >
//                     Go to Custom Range
//                   </button>
//                 </div>

//                 {/* Last Week Card */}
//                 <div className="quick-action-card">
//                   <div className="action-header">
//                     <h4>Generate Last Week</h4>
//                   </div>
//                   <p>Generate reports for the previous complete week.</p>
//                   <button
//                     className="action-btn"
//                     onClick={() => {
//                       const today = new Date();
//                       const lastWeekStart = new Date(today);
//                       lastWeekStart.setDate(today.getDate() - today.getDay() - 7);
//                       const lastWeekEnd = new Date(lastWeekStart);
//                       lastWeekEnd.setDate(lastWeekStart.getDate() + 6);
                      
//                       setCustomRange({
//                         startDate: lastWeekStart.toISOString().split('T')[0],
//                         endDate: lastWeekEnd.toISOString().split('T')[0],
//                         reportTypes: ['daily', 'weekly']
//                       });
//                       setActiveTab('custom');
//                     }}
//                   >
//                     Go to Custom Range
//                   </button>
//                 </div>

//                 {/* Last Month Card */}
//                 <div className="quick-action-card">
//                   <div className="action-header">
//                     <h4>Generate Last Month</h4>
//                   </div>
//                   <p>Generate reports for the previous complete month.</p>
//                   <button
//                     className="action-btn"
//                     onClick={() => {
//                       const today = new Date();
//                       const lastMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1);
//                       const lastMonthEnd = new Date(today.getFullYear(), today.getMonth(), 0);
                      
//                       setCustomRange({
//                         startDate: lastMonth.toISOString().split('T')[0],
//                         endDate: lastMonthEnd.toISOString().split('T')[0],
//                         reportTypes: ['daily', 'weekly', 'monthly']
//                       });
//                       setActiveTab('custom');
//                     }}
//                   >
//                     Go to Custom Range
//                   </button>
//                 </div>
//               </div>
//             </div>
//           )}
//         </div>

//         {/* Navigation to Reports List */}
//         <div className="navigation-footer">
//           <button 
//             className="view-reports-btn"
//             onClick={() => navigate('/reports/list')}
//           >
//             View Generated Reports
//           </button>
//         </div>
//       </div>
//     </div>
//   );
// };

// export default ReportGenerationPage;


// ReportGenerationPage.tsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../../../../api';
import './ReportGenerationPage.css';

interface YesterdayStatus {
  date: string;
  exists: boolean;
  message: string;
}

interface GenerationResult {
  status: 'success' | 'error' | 'already_exists';
  message: string;
  date: string;
}

const ReportGenerationPage: React.FC = () => {
  const navigate = useNavigate();
  const [yesterdayStatus, setYesterdayStatus] = useState<YesterdayStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generationResult, setGenerationResult] = useState<GenerationResult | null>(null);

  // Fetch yesterday's status on component mount
  useEffect(() => {
    fetchYesterdayStatus();
  }, []);

  const fetchYesterdayStatus = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/reports/yesterday-status/');
      setYesterdayStatus(response.data as YesterdayStatus);
      setError(null);
    } catch (err) {
      setError('Failed to fetch report status');
      console.error('Error fetching yesterday status:', err);
    } finally {
      setLoading(false);
    }
  };

  const generateYesterdayReport = async () => {
    try {
      setGenerating(true);
      setError(null);
      const response = await api.post('/api/reports/generate-yesterday/');
      setGenerationResult(response.data as GenerationResult);
      
      // Refresh status after generation
      await fetchYesterdayStatus();
    } catch (err) {
      setError('Failed to generate report');
      console.error('Error generating yesterday report:', err);
    } finally {
      setGenerating(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const getStatusColor = () => {
    if (!yesterdayStatus) return '#666';
    return yesterdayStatus.exists ? '#27ae60' : '#e74c3c';
  };

  const getStatusText = () => {
    if (!yesterdayStatus) return 'Checking...';
    return yesterdayStatus.exists ? 'Report Generated' : 'Report Pending';
  };

  return (
    <div className="dashboard-page">
      <div className="dashboard-container">
        {/* Top Bar */}
        <div className="top-bar">
          <h2>Report Generation</h2>
          <div className="controls">
            <button 
              className="refresh-btn"
              onClick={fetchYesterdayStatus}
              disabled={loading}
            >
              Refresh
            </button>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="error-message">
            {error}
            <button onClick={() => setError(null)} className="close-error">×</button>
          </div>
        )}

        {/* Generation Results */}
        {generationResult && (
          <div className={`generation-result ${generationResult.status}`}>
            <div className="result-icon">
              {generationResult.status === 'success' && '✓'}
              {generationResult.status === 'error' && '✗'}
              {generationResult.status === 'already_exists' && 'ℹ'}
            </div>
            <div className="result-content">
              <h3>
                {generationResult.status === 'success' && 'Report Generated Successfully'}
                {generationResult.status === 'error' && 'Generation Failed'}
                {generationResult.status === 'already_exists' && 'Report Already Exists'}
              </h3>
              <p>{generationResult.message}</p>
              <span className="result-date">{formatDate(generationResult.date)}</span>
            </div>
            <button 
              className="close-result-btn"
              onClick={() => setGenerationResult(null)}
            >
              ×
            </button>
          </div>
        )}

        {/* Main Content */}
        <div className="generation-content">
          <div className="yesterday-report-section">
            <h3>Yesterday's Report</h3>
            
            {loading ? (
              <div className="loader">Checking report status...</div>
            ) : yesterdayStatus ? (
              <div className="status-card">
                <div className="status-header">
                  <h4>Report for {formatDate(yesterdayStatus.date)}</h4>
                  <div 
                    className="status-indicator"
                    style={{ backgroundColor: getStatusColor() }}
                  >
                    {getStatusText()}
                  </div>
                </div>
                
                <div className="status-message">
                  {yesterdayStatus.message}
                </div>

                <button
                  className="generate-btn"
                  onClick={generateYesterdayReport}
                  disabled={generating || yesterdayStatus.exists}
                >
                  {generating ? 'Generating...' : 
                   yesterdayStatus.exists ? 'Already Generated' : 'Generate Yesterday\'s Report'}
                </button>

                {yesterdayStatus.exists && (
                  <div className="view-report-link">
                    <button 
                      className="view-report-btn"
                      onClick={() => navigate('/reports/list')}
                    >
                      View All Reports
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <div className="error-message">Failed to load report status</div>
            )}
          </div>

          {/* Quick Info Section */}
          <div className="info-section">
            <h4>How it works:</h4>
            <ul>
              <li>Click "Generate Yesterday's Report" to create the daily report for yesterday</li>
              <li>The system will automatically check if the report already exists</li>
              <li>If the report exists, the button will be disabled</li>
              <li>You can view all generated reports by clicking "View All Reports"</li>
            </ul>
          </div>
        </div>

        {/* Navigation */}
        <div className="navigation-footer">
          <button 
            className="view-reports-btn"
            onClick={() => navigate('/reports/list')}
          >
            View All Generated Reports
          </button>
        </div>
      </div>
    </div>
  );
};

export default ReportGenerationPage;