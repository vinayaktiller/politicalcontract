import React, { useEffect, useState } from "react";
import "./DashboardsPage.css";
import api from "../../../../api";
import { useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from "../../../../store";
import { 
  connectWebSocket, 
  disconnectWebSocket
} from "./activeusers/activeUsersThunks";
import { motion, AnimatePresence } from "framer-motion";

// Define proper interfaces
interface ReportItem {
  id: string; // Changed from number to string (UUID)
  report_type: 'daily' | 'weekly' | 'monthly';
  formatted_date: string;
  new_users: number;
  country_id?: number;
  country_name?: string;
  date?: string; // Added optional date field for potential fallback
}

interface ActivityReportItem {
  id: number;
  report_type: string;
  level?: string;
  formatted_date?: string;
  date?: string;
  week_start_date?: string;
  week_last_date?: string;
}

const DashboardsPage = () => {
  console.log("[DashboardsPage] Component rendering");
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const [latestReports, setLatestReports] = useState<ReportItem[]>([]);
  const [activityReports, setActivityReports] = useState<ActivityReportItem[]>([]);
  const [prevTotalCount, setPrevTotalCount] = useState(0);
  const [displayedTotalCount, setDisplayedTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Get active users state
  const activeUsersState = useSelector((state: RootState) => state.activeUsers);
  
  const activeCount = activeUsersState?.activeCount ?? 0;
  const totalCount = activeUsersState?.totalCount ?? 0;
  const activeLoading = activeUsersState?.activeLoading ?? true;
  const totalLoading = activeUsersState?.totalLoading ?? true;
  const activeError = activeUsersState?.activeError ?? null;
  const totalError = activeUsersState?.totalError ?? null;
  
  console.log(`[DashboardsPage] Active users state:`, { 
    activeCount, 
    totalCount, 
    activeLoading, 
    totalLoading,
    activeError,
    totalError
  });

  // Animation effect for total count
  useEffect(() => {
    if (totalCount !== prevTotalCount) {
      setPrevTotalCount(totalCount);
      setDisplayedTotalCount(totalCount);
    }
  }, [totalCount, prevTotalCount]);

  useEffect(() => {
    console.log("[DashboardsPage] useEffect - Initializing WebSocket connection");
    dispatch(connectWebSocket() as any);
    
    return () => {
      console.log("[DashboardsPage] Cleanup - Closing WebSocket connection");
      dispatch(disconnectWebSocket() as any);
    };
  }, [dispatch]);

  useEffect(() => {
    console.log("[DashboardsPage] useEffect - Fetching reports data");
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch initiation reports - Use the same endpoint as ReportsListPage
        const reportsResponse = await api.get('api/reports/reports/latest/');
        const reportsData = reportsResponse.data as ReportItem[];
        
        console.log("Latest reports data:", reportsData);
        
        // The API already provides formatted_date, so use it directly
        setLatestReports(reportsData);
        
        // Fetch activity reports
        const activityResponse = await api.get('api/activity_reports/activity-reports/latest/');
        const activityData = activityResponse.data as ActivityReportItem[];
        
        console.log("Activity reports data:", activityData);
        
        // Format activity reports similarly
        const normalizedActivity = activityData.map((report: ActivityReportItem) => {
          // If API already provides formatted_date, use it
          if (report.formatted_date) {
            return report;
          }
          
          // Otherwise format it
          if (report.report_type === 'monthly' && report.date) {
            return { 
              ...report, 
              formatted_date: new Date(report.date).toLocaleString('default', { month: 'long', year: 'numeric' })
            };
          } else if (report.report_type === 'weekly' && report.week_start_date && report.week_last_date) {
            const start = new Date(report.week_start_date).toLocaleDateString('en-US', { day: 'numeric', month: 'short' });
            const end = new Date(report.week_last_date).toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' });
            return { ...report, formatted_date: `${start} – ${end}` };
          } else if (report.date) {
            return { 
              ...report, 
              formatted_date: new Date(report.date).toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' })
            };
          }
          return report;
        });
        
        setActivityReports(normalizedActivity.slice(0, 5));
        
      } catch (error) {
        console.error("Error fetching data:", error);
        setError("Failed to load reports data");
        setLatestReports([]);
        setActivityReports([]);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const overallReport = () => {
    navigate("/reports/overall/country/1");
  };

  const handleReportClick = (reportType: string, id: string) => { // ✅ id is string
    navigate(`/reports/${reportType}/${id}/country`);
  };

  const handleActivityReportClick = (reportType: string, level: string, id: number) => {
    navigate(`/activity-reports/${reportType}/${id}/country`);
  };

  const renderActiveUsers = () => {
    if (activeLoading) {
      return <p className="dashboard-stat-label">Loading active users...</p>;
    }
    if (activeError) {
      return <p className="dashboard-stat-label error">Error: {activeError}</p>;
    }
    return <p className="dashboard-stat-label">{activeCount} Active users Today</p>;
  };

  const renderTotalPetitioners = () => {
    if (totalLoading) {
      return <p className="dashboard-stat-label">Loading total petitioners...</p>;
    }
    if (totalError) {
      return <p className="dashboard-stat-label error">Error: {totalError}</p>;
    }
    return <p className="dashboard-stat-label">Petitioners have signed for Political contract</p>;
  };

  // Create a rolling digit component
  const RollingDigit = ({ digit, key }: { digit: string; key: number }) => {
    return (
      <div className="digit-container" key={key}>
        <AnimatePresence mode="wait">
          <motion.div
            key={digit}
            initial={{ y: "100%", opacity: 0 }}
            animate={{ y: "0%", opacity: 1 }}
            exit={{ y: "-100%", opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="digit"
          >
            {digit}
          </motion.div>
        </AnimatePresence>
      </div>
    );
  };

  // Create the animated count display
  const AnimatedCount = ({ count }: { count: number }) => {
    const countStr = count.toString();
    
    return (
      <div className="animated-count">
        {countStr.split('').map((digit, index) => (
          <RollingDigit digit={digit} key={index} />
        ))}
      </div>
    );
  };

  const getReportTypeLabel = (type: string) => {
    return type.charAt(0).toUpperCase() + type.slice(1);
  };

  return (
    <div className="dashboard-page">
      {/* Top banner with total petitioners */}
      <div className="dashboard-live-count">
        <div className="dashboard-stat-value">
          {totalLoading ? (
            '...'
          ) : totalError ? (
            'Error'
          ) : (
            <AnimatedCount count={displayedTotalCount} />
          )}
        </div>
        <div className="dashboard-stat-tagline">
          {renderTotalPetitioners()}
        </div>
      </div>

      <div className="dashboard-container">
        {/* Stat card for active users */}
        <div className="dashboard-stat-card">
          {renderActiveUsers()}
        </div>

        {/* Overall report button */}
        <div className="dashboard-stat-card" onClick={overallReport}>
          <p className="dashboard-stat-label">Overall Report</p>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="dashboard-report-card">
            <div className="loader">Loading reports...</div>
          </div>
        )}

        {/* Error State */}
        {error && !loading && (
          <div className="dashboard-report-card">
            <div className="error-message">{error}</div>
          </div>
        )}

        {/* Latest Reports Table - Only show if not loading and no error */}
        {!loading && !error && (
          <>
            {/* Latest Reports Table */}
            <div className="dashboard-report-card">
              <div className="dashboard-report-card-header">
                <h2>Latest Initiation Reports</h2>
                <button 
                  className="all-reports-btn"
                  onClick={() => navigate('/reports-list')}
                >
                  All Reports
                </button>
              </div>
              <table className="dashboard-report-table">
                <thead>
                  <tr>
                    <th>Report Type</th>
                    <th>Date</th>
                    <th>ID</th>
                  </tr>
                </thead>
                <tbody>
                  {latestReports.length > 0 ? (
                    latestReports.map(report => (
                      <tr 
                        key={report.id} 
                        onClick={() => handleReportClick(report.report_type, report.id)}
                        className="dashboard-report-row"
                      >
                        <td>{getReportTypeLabel(report.report_type)} Report</td>
                        <td>{report.formatted_date}</td> {/* Use formatted_date from API */}
                        <td>{report.id}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={3}>No data available</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Activity Reports */}
            <div className="dashboard-report-card">
              <div className="dashboard-report-card-header">
                <h2>Recent Activity Reports</h2>
                <button 
                  className="all-reports-btn"
                  onClick={() => navigate('/activity-reports-list')}
                >
                  All Reports
                </button>
              </div>
              <table className="dashboard-report-table">
                <thead>
                  <tr>
                    <th>Report Type</th>
                    <th>Date</th>
                    <th>ID</th>
                  </tr>
                </thead>
                <tbody>
                  {activityReports.length > 0 ? (
                    activityReports.map(report => (
                      <tr 
                        key={report.id} 
                        onClick={() => handleActivityReportClick(
                          report.report_type, 
                          report.level || 'country', 
                          report.id
                        )}
                        className="dashboard-report-row"
                      >
                        <td>{getReportTypeLabel(report.report_type)} Report</td>
                        <td>{report.formatted_date || 'N/A'}</td>
                        <td>{report.id}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={3}>No data available</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default DashboardsPage;