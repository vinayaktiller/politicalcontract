import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../../../api';
import './ActivityReportListPage.css';

interface ReportItem {
  id: number;
  report_type: 'daily' | 'weekly' | 'monthly';
  formatted_date: string;
  active_users: number;
  country_id: number;
  country_name: string;
}

interface ApiResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: ReportItem[];
}

const ActivityReportListPage: React.FC = () => {
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState({
    count: 0,
    next: null as string | null,
    previous: null as string | null,
    page: 1,
    pageSize: 20
  });
  const [filterType, setFilterType] = useState<string>('all');
  const [showFilterDropdown, setShowFilterDropdown] = useState(false);
  const navigate = useNavigate();
  const topRef = useRef<HTMLDivElement>(null);

  const fetchReports = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: pagination.page.toString(),
        page_size: pagination.pageSize.toString(),
        report_type: filterType
      });
      
      const response = await api.get<ApiResponse>('/api/activity_reports/activity-reports/list/', { params });

      
      setReports(response.data.results);
      setPagination(prev => ({
        ...prev,
        count: response.data.count,
        next: response.data.next,
        previous: response.data.previous
      }));
      setError(null);
    } catch (err) {
      setError('Failed to load activity reports. Please try again later.');
      console.error('Error fetching activity reports:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, [filterType, pagination.page, pagination.pageSize]);

  // Scroll to top when page or filter changes
  useEffect(() => {
    if (topRef.current) {
      topRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [pagination.page, filterType]);

  const handlePageChange = (newPage: number) => {
    setPagination(prev => ({ ...prev, page: newPage }));
  };

  const handlePageSizeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newSize = parseInt(e.target.value);
    setPagination(prev => ({ ...prev, pageSize: newSize, page: 1 }));
  };

  const handleReportClick = (reportType: string, id: number) => {
    navigate(`/activity-reports/${reportType}/${id}/country`);
  };

  const toggleFilterDropdown = () => {
    setShowFilterDropdown(!showFilterDropdown);
  };

  const handleFilterChange = (type: string) => {
    setFilterType(type);
    setShowFilterDropdown(false);
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  const getReportTypeLabel = (type: 'daily' | 'weekly' | 'monthly') => {
    return type.charAt(0).toUpperCase() + type.slice(1) + ' Activity Report';
  };

  const getIconForReportType = (type: 'daily' | 'weekly' | 'monthly') => {
    switch (type) {
      case 'daily':
        return (
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#3498db" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
            <line x1="16" y1="2" x2="16" y2="6"></line>
            <line x1="8" y1="2" x2="8" y2="6"></line>
            <line x1="3" y1="10" x2="21" y2="10"></line>
          </svg>
        );
      case 'weekly':
        return (
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#388e3c" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
            <line x1="16" y1="2" x2="16" y2="6"></line>
            <line x1="8" y1="2" x2="8" y2="6"></line>
            <line x1="3" y1="10" x2="21" y2="10"></line>
            <line x1="8" y1="14" x2="8" y2="14.01"></line>
            <line x1="12" y1="14" x2="12" y2="14.01"></line>
            <line x1="16" y1="14" x2="16" y2="14.01"></line>
            <line x1="8" y1="17" x2="8" y2="17.01"></line>
            <line x1="12" y1="17" x2="12" y2="17.01"></line>
            <line x1="16" y1="17" x2="16" y2="17.01"></line>
          </svg>
        );
      case 'monthly':
        return (
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#7b1fa2" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
            <line x1="16" y1="2" x2="16" y2="6"></line>
            <line x1="8" y1="2" x2="8" y2="6"></line>
            <line x1="3" y1="10" x2="21" y2="10"></line>
            <path d="M8 14h.01"></path>
            <path d="M12 14h.01"></path>
            <path d="M16 14h.01"></path>
            <path d="M8 18h.01"></path>
            <path d="M12 18h.01"></path>
            <path d="M16 18h.01"></path>
          </svg>
        );
      default:
        return (
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#3498db" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
            <line x1="16" y1="2" x2="16" y2="6"></line>
            <line x1="8" y1="2" x2="8" y2="6"></line>
            <line x1="3" y1="10" x2="21" y2="10"></line>
          </svg>
        );
    }
  };

  return (
    <div className="dashboard-page">
      <div className="dashboard-container" ref={topRef}>
        {/* Top Bar */}
        <div className="top-bar">
          <h2>Activity Reports</h2>
          <div className="controls">
            <div className="filter-container">
              <button className="filter-btn" onClick={toggleFilterDropdown}>
                Filter <span>▼</span>
              </button>
              {showFilterDropdown && (
                <div className="filter-dropdown">
                  <button 
                    className={filterType === 'all' ? 'active' : ''}
                    onClick={() => handleFilterChange('all')}
                  >
                    All Reports
                  </button>
                  <button 
                    className={filterType === 'daily' ? 'active' : ''}
                    onClick={() => handleFilterChange('daily')}
                  >
                    Daily
                  </button>
                  <button 
                    className={filterType === 'weekly' ? 'active' : ''}
                    onClick={() => handleFilterChange('weekly')}
                  >
                    Weekly
                  </button>
                  <button 
                    className={filterType === 'monthly' ? 'active' : ''}
                    onClick={() => handleFilterChange('monthly')}
                  >
                    Monthly
                  </button>
                </div>
              )}
            </div>
            
            <div className="page-size-selector">
              <label htmlFor="pageSize">Reports per page:</label>
              <select 
                id="pageSize"
                value={pagination.pageSize}
                onChange={handlePageSizeChange}
                disabled={loading}
              >
                <option value="10">10</option>
                <option value="20">20</option>
                <option value="50">50</option>
                <option value="100">100</option>
              </select>
            </div>
          </div>
        </div>

        {/* Reports Grid */}
        <div className="reports-grid">
          {loading ? (
            <div className="loader">Loading activity reports...</div>
          ) : error ? (
            <div className="error-message">{error}</div>
          ) : reports.length > 0 ? (
            reports.map(report => (
              <div 
                key={report.id}
                className={`report-card ${report.report_type}`}
                onClick={() => handleReportClick(report.report_type, report.id)}
              >
                <div className="report-content">
                  <div className="report-left">
                    <div className="report-date">{report.formatted_date}</div>
                    <div className="report-type">{getReportTypeLabel(report.report_type)}</div>
                    <div className="report-id">Report number: {report.id}</div>
                    <div className="report-country">Country: {report.country_name}</div>
                  </div>
                  <div className="report-right">
                    <div className="report-icon">
                      {getIconForReportType(report.report_type)}
                    </div>
                    <div className="report-users">
                      {report.active_users} active {report.active_users === 1 ? 'user' : 'users'}
                    </div>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="no-reports">No activity reports available for this filter</div>
          )}
        </div>

        {/* Pagination */}
        <div className="dashboard-pagination-controls">
          <button 
            onClick={() => handlePageChange(pagination.page - 1)}
            disabled={pagination.page === 1 || loading}
          >
            Previous
          </button>
          
          <span>Page {pagination.page} of {Math.ceil(pagination.count / pagination.pageSize)}</span>
          
          <button 
            onClick={() => handlePageChange(pagination.page + 1)}
            disabled={!pagination.next || loading}
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
};

export default ActivityReportListPage;