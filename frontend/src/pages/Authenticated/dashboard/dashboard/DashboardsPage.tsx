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

const DashboardsPage = () => {
  console.log("[DashboardsPage] Component rendering");
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const [latestReports, setLatestReports] = useState<any[]>([]);
  const [activityReports, setActivityReports] = useState<any[]>([]);
  const [prevTotalCount, setPrevTotalCount] = useState(0);
  const [displayedTotalCount, setDisplayedTotalCount] = useState(0);

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
        // Fetch initiation reports
        const reportsResponse = await api.get('api/reports/reports/latest/');
        const reportsData = reportsResponse.data as any[];
        
        const normalizedReports = reportsData.map((report: any) => {
          let dateStr = report.date;
          
          if (report.report_type === 'monthly' && dateStr.length === 7) {
            dateStr = `${dateStr}-01`;
          }
          
          let formatted_date = '';
          try {
            if (report.report_type === 'monthly') {
              formatted_date = new Date(dateStr).toLocaleString('default', { month: 'long', year: 'numeric' });
            } else {
              formatted_date = new Date(dateStr).toLocaleDateString('en-US', { 
                day: 'numeric', 
                month: 'short', 
                year: 'numeric' 
              });
            }
          } catch (e) {
            console.error(`Date formatting error:`, e);
            formatted_date = 'Invalid Date';
          }
          
          return { ...report, formatted_date };
        });
        setLatestReports(normalizedReports);
        
        // Fetch activity reports
        const activityResponse = await api.get('api/activity_reports/activity-reports/latest/');
        const activityData = activityResponse.data as any[];
        
        const normalizedActivity = activityData.map((report: any) => {
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
        setLatestReports([]);
        setActivityReports([]);
      }
    };

    fetchData();
  }, []);

  const overallReport = () => {
    navigate("/reports/overall/country/1");
  };

  const handleReportClick = (reportType: string, id: number) => {
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
                    <td>{report.report_type.charAt(0).toUpperCase() + report.report_type.slice(1)}</td>
                    <td>{report.formatted_date}</td>
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
                    onClick={() => handleActivityReportClick(report.report_type, report.level, report.id)}
                    className="dashboard-report-row"
                  >
                    <td>{report.report_type.charAt(0).toUpperCase() + report.report_type.slice(1)}</td>
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
      </div>
    </div>
  );
};

export default DashboardsPage;