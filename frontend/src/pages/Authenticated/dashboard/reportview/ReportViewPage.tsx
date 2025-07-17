import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "../../../../api";
import "./ReportViewPage.css";

type ReportType = "daily" | "weekly" | "monthly";
type ReportLevel = "country" | "state" | "district" | "subdistrict" | "village";

interface GeographicalEntity {
  id: number;
  name: string;
  type: string;
}

interface ChildData {
  id: number;
  name: string;
  new_users: number;
  report_id?: number;
}

interface ParentInfo {
  level: ReportLevel;
  report_id: number;
}

interface ReportData {
  id: number;
  geographical_entity: GeographicalEntity;
  new_users: number;
  level: ReportLevel;
  parent_info: ParentInfo | null;
  children_data: Record<string, ChildData>;
  date?: string;
  week_number?: number;
  year?: number;
  month?: number;
  week_start_date?: string;
  week_last_date?: string;
  last_date?: string;
}

const ReportViewPage = () => {
  const { period, reportId, level } = useParams<{
    period: ReportType;
    reportId: string;
    level: ReportLevel;
  }>();
  
  const [report, setReport] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    const fetchReportData = async () => {
      try {
        setLoading(true);
        setError("");
        
        const response = await api.get<ReportData>(
          `/api/reports/reports/view/`, 
          {
            params: {
              type: period,
              report_id: reportId,
              level: level
            }
          }
        );
        
        setReport(response.data);
      } catch (err) {
        setError("Failed to load report. Please try again later.");
        console.error("API Error:", err);
      } finally {
        setLoading(false);
      }
    };

    if (period && reportId && level) {
      fetchReportData();
    } else {
      setError("Missing required parameters in URL");
      setLoading(false);
    }
  }, [period, reportId, level]);

  const handleChildClick = (child: ChildData) => {
    if (child.new_users > 0 && child.report_id) {
      const nextLevel = getChildLevel(level as ReportLevel);
      navigate(`/reports/${period}/${child.report_id}/${nextLevel}`);
    }
  };

  const handleBackClick = () => {
    if (report?.parent_info) {
      navigate(
        `/reports/${period}/${report.parent_info.report_id}/${report.parent_info.level}`
      );
    }
  };

  const getChildLevel = (currentLevel: ReportLevel): ReportLevel => {
    const levelMap: Record<ReportLevel, ReportLevel> = {
      country: "state",
      state: "district",
      district: "subdistrict",
      subdistrict: "village",
      village: "village"
    };
    return levelMap[currentLevel];
  };

  const formatTitle = () => {
    if (!report) return "";
    
    const entity = report.geographical_entity;
    if (period === "daily" && report.date) {
      return `${entity.name} Report - ${new Date(report.date).toLocaleDateString()}`;
    }
    if (period === "weekly" && report.week_number && report.year) {
      return `${entity.name} Report - Week ${report.week_number}, ${report.year}`;
    }
    if (period === "monthly" && report.month && report.year) {
      const monthName = new Date(report.year, report.month - 1).toLocaleString(
        "default",
        { month: "long" }
      );
      return `${entity.name} Report - ${monthName} ${report.year}`;
    }
    return `${entity.name} Report`;
  };

  if (loading) {
    return (
      <div className="report-view-page">
        <div className="report-view-container">
          <div className="report-view-loading">Loading report...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="report-view-page">
        <div className="report-view-container">
          <div className="report-view-error">{error}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="report-view-page">
      <div className="report-view-container">
        {report && (
          <>
            <div className="report-view-top-bar">
              <button
                onClick={handleBackClick}
                disabled={!report.parent_info}
                className={`report-view-back-button ${!report.parent_info ? 'disabled' : ''}`}
              >
                &larr; Back
              </button>
              <h2>{formatTitle()}</h2>
              <div className="report-view-total-users">
                <span className="report-view-users-icon">👤</span>
                {report.new_users} {report.new_users === 1 ? 'person' : 'people'}
              </div>
            </div>

            <div className="report-view-level-indicator">
              {report.level.toUpperCase()} LEVEL
            </div>

            <div className="report-view-children-grid">
              {Object.entries(report.children_data).map(([id, child]) => (
                <div
                  key={id}
                  className={`report-view-child-card ${
                    child.new_users > 0 ? "active" : "inactive"
                  } ${child.new_users > 0 && child.report_id ? 'clickable' : ''}`}
                  onClick={() => child.new_users > 0 && child.report_id && handleChildClick(child)}
                >
                  <div className="report-view-child-name">{child.name}</div>
                  <div className="report-view-child-count">{child.new_users}</div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default ReportViewPage;