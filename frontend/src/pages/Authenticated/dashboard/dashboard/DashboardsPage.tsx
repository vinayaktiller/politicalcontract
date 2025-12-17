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
import { 
  Users,
  UserCheck,
  FileText,
  BarChart2,
  Calendar,
  TrendingUp
} from 'lucide-react';

// Define proper interfaces
interface ReportItem {
  id: string;
  report_type: 'daily' | 'weekly' | 'monthly';
  formatted_date: string;
  new_users: number;
  country_id?: number;
  country_name?: string;
  date?: string;
}

interface ActivityReportItem {
  id: number;
  report_type: string;
  level?: string;
  formatted_date?: string;
  active_users?: number;
  total_activity?: number;
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

        // Fetch initiation reports
        const reportsResponse = await api.get('api/reports/reports/latest/');
        const reportsData = reportsResponse.data as ReportItem[];
        
        console.log("Latest reports data:", reportsData);
        
        // Format dates to single line format (DD MMM YYYY)
        const formattedReports = reportsData.map(report => {
          let formattedDate = report.formatted_date;
          
          // If the API returns a formatted date, ensure it's in single line format
          if (report.date) {
            try {
              const dateObj = new Date(report.date);
              // Format to "15 Dec 2023" style
              formattedDate = dateObj.toLocaleDateString('en-US', {
                day: 'numeric',
                month: 'short',
                year: 'numeric'
              });
            } catch (e) {
              console.error('Date formatting error:', e);
            }
          }
          
          return {
            ...report,
            formatted_date: formattedDate
          };
        });
        
        setLatestReports(formattedReports);
        
        // Fetch activity reports
        const activityResponse = await api.get('api/activity_reports/activity-reports/latest/');
        const activityData = activityResponse.data as ActivityReportItem[];
        
        console.log("Activity reports data:", activityData);
        
        // Format activity reports
        const formattedActivity = activityData.map(report => {
          let formattedDate = report.formatted_date;
          
          // Format to single line date
          if (report.date) {
            try {
              const dateObj = new Date(report.date);
              formattedDate = dateObj.toLocaleDateString('en-US', {
                day: 'numeric',
                month: 'short',
                year: 'numeric'
              });
            } catch (e) {
              console.error('Date formatting error:', e);
            }
          } else if (report.week_start_date && report.week_last_date) {
            // For weekly reports, format as "15 Dec - 22 Dec 2023"
            try {
              const startDate = new Date(report.week_start_date);
              const endDate = new Date(report.week_last_date);
              const startStr = startDate.toLocaleDateString('en-US', {
                day: 'numeric',
                month: 'short'
              });
              const endStr = endDate.toLocaleDateString('en-US', {
                day: 'numeric',
                month: 'short',
                year: 'numeric'
              });
              formattedDate = `${startStr} - ${endStr}`;
            } catch (e) {
              console.error('Date formatting error:', e);
            }
          }
          
          return {
            ...report,
            formatted_date: formattedDate,
            // Ensure active_users has a default value if not provided
            active_users: report.active_users || 0
          };
        });
        
        setActivityReports(formattedActivity.slice(0, 5));
        
      } catch (error) {
        console.error("Error fetching data:", error);
        setError("Failed to load reports data. Please try again.");
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

  const handleReportClick = (reportType: string, id: string) => {
    navigate(`/reports/${reportType}/${id}/country`);
  };

  const handleActivityReportClick = (reportType: string, level: string, id: number) => {
    navigate(`/activity-reports/${reportType}/${id}/country`);
  };

  const renderActiveUsers = () => {
    return (
      <div className="dashboard-stat-content">
        <UserCheck size={24} className="stat-icon" />
        <div className="stat-text">
          <div className="stat-value">{activeCount}</div>
          <div className="stat-label">Active Users Today</div>
        </div>
      </div>
    );
  };

  const renderOverallReport = () => {
    return (
      <div className="dashboard-stat-content">
        <BarChart2 size={24} className="stat-icon" />
        <div className="stat-text">
          <div className="stat-value">Overall</div>
          <div className="stat-label">Complete Report</div>
        </div>
      </div>
    );
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
    const countStr = count.toLocaleString(); // Format with commas
    
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

  const getReportIcon = (type: string) => {
    switch (type) {
      case 'daily': return <Calendar size={16} />;
      case 'weekly': return <TrendingUp size={16} />;
      case 'monthly': return <BarChart2 size={16} />;
      default: return <FileText size={16} />;
    }
  };

  return (
    <div className="dashboard-page">
      {/* Top banner with total petitioners */}
      <div className="dashboard-live-count">
        <div className="dashboard-stat-value-large">
          {totalLoading ? (
            <div className="loading-count">...</div>
          ) : totalError ? (
            <div className="error-count">Error</div>
          ) : (
            <div className="total-count-display">
              <Users size={32} className="total-count-icon" />
              <AnimatedCount count={displayedTotalCount} />
            </div>
          )}
        </div>
        <div className="dashboard-stat-tagline">
          <p>Petitioners have signed for Political contract</p>
          <small>Live count updates every minute</small>
        </div>
      </div>

      <div className="dashboard-container">
        {/* Stat cards */}
        <div className="stat-cards-container">
          <div className="dashboard-stat-card" onClick={overallReport}>
            {renderOverallReport()}
          </div>
          
          <div className="dashboard-stat-card">
            {activeLoading ? (
              <div className="dashboard-stat-content">
                <div className="loading-text">Loading...</div>
              </div>
            ) : activeError ? (
              <div className="dashboard-stat-content">
                <div className="error-text">Error loading active users</div>
              </div>
            ) : (
              renderActiveUsers()
            )}
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="dashboard-report-card">
            <div className="loader-container">
              <div className="loader-spinner"></div>
              <p>Loading reports data...</p>
            </div>
          </div>
        )}

        {/* Error State */}
        {error && !loading && (
          <div className="dashboard-report-card">
            <div className="error-message">
              <div className="error-icon">⚠️</div>
              <p>{error}</p>
              <button 
                className="retry-btn"
                onClick={() => window.location.reload()}
              >
                Retry
              </button>
            </div>
          </div>
        )}

        {/* Latest Reports Table - Only show if not loading and no error */}
        {!loading && !error && (
          <>
            {/* Latest Initiation Reports Table */}
            <div className="dashboard-report-card">
              <div className="dashboard-report-card-header">
                <div className="report-card-title">
                  <FileText size={20} className="report-card-icon" />
                  <h2>Latest Initiation Reports</h2>
                </div>
                <button 
                  className="all-reports-btn"
                  onClick={() => navigate('/reports-list')}
                >
                  View All Reports
                </button>
              </div>
              <div className="report-card-content">
                <table className="dashboard-report-table">
                  <thead>
                    <tr>
                      <th>Report Type</th>
                      <th>Date</th>
                      <th>New Users</th>
                      <th>View</th>
                    </tr>
                  </thead>
                  <tbody>
                    {latestReports.length > 0 ? (
                      latestReports.map(report => (
                        <tr 
                          key={report.id} 
                          className="dashboard-report-row"
                        >
                          <td>
                            <div className="report-type-cell">
                              {getReportIcon(report.report_type)}
                              <span>{getReportTypeLabel(report.report_type)} Report</span>
                            </div>
                          </td>
                          <td>
                            <div className="date-cell">
                              {report.formatted_date}
                            </div>
                          </td>
                          <td>
                            <div className="new-users-cell">
                              <Users size={14} className="users-icon" />
                              <span className="new-users-count">
                                {report.new_users.toLocaleString()}
                              </span>
                            </div>
                          </td>
                          <td>
                            <button 
                              className="view-report-btn"
                              onClick={() => handleReportClick(report.report_type, report.id)}
                            >
                              View Details
                            </button>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={4}>
                          <div className="no-data-message">
                            <FileText size={32} />
                            <p>No initiation reports available</p>
                          </div>
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Activity Reports */}
            <div className="dashboard-report-card">
              <div className="dashboard-report-card-header">
                <div className="report-card-title">
                  <TrendingUp size={20} className="report-card-icon" />
                  <h2>Recent Activity Reports</h2>
                </div>
                <button 
                  className="all-reports-btn"
                  onClick={() => navigate('/activity-reports-list')}
                >
                  View All Reports
                </button>
              </div>
              <div className="report-card-content">
                <table className="dashboard-report-table">
                  <thead>
                    <tr>
                      <th>Report Type</th>
                      <th>Date</th>
                      <th>Active Users</th>
                      <th>View</th>
                    </tr>
                  </thead>
                  <tbody>
                    {activityReports.length > 0 ? (
                      activityReports.map(report => (
                        <tr 
                          key={report.id} 
                          className="dashboard-report-row"
                        >
                          <td>
                            <div className="report-type-cell">
                              {getReportIcon(report.report_type)}
                              <span>{getReportTypeLabel(report.report_type)} Report</span>
                            </div>
                          </td>
                          <td>
                            <div className="date-cell">
                              {report.formatted_date || 'N/A'}
                            </div>
                          </td>
                          <td>
                            <div className="active-users-cell">
                              <UserCheck size={14} className="active-icon" />
                              <span className="active-users-count">
                                {(report.active_users || 0).toLocaleString()}
                              </span>
                            </div>
                          </td>
                          <td>
                            <button 
                              className="view-report-btn"
                              onClick={() => handleActivityReportClick(
                                report.report_type, 
                                report.level || 'country', 
                                report.id
                              )}
                            >
                              View Details
                            </button>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={4}>
                          <div className="no-data-message">
                            <TrendingUp size={32} />
                            <p>No activity reports available</p>
                          </div>
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default DashboardsPage;