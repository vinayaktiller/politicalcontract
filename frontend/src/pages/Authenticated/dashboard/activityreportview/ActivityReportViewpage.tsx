import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "../../../../api";
import "./ActivityReportViewPage.css";

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
  active_users: number;
  report_id?: number;
}

interface ParentInfo {
  level: ReportLevel;
  report_id: number;
}

interface ActivityDistribution {
  [key: string]: number;
}

interface ReportData {
  id: number;
  geographical_entity: GeographicalEntity;
  active_users: number;
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
  additional_info?: {
    activity_distribution?: ActivityDistribution;
  };
}

const ActivityReportViewPage: React.FC = () => {
  const { period, reportId, level } = useParams<{
    period: ReportType;
    reportId: string;
    level: ReportLevel;
  }>();

  const [report, setReport] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showDistribution, setShowDistribution] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchReportData = async () => {
      try {
        setLoading(true);
        setError("");
        console.log("🔍 Fetching Activity Report Data...", { period, reportId, level });

        const response = await api.get<ReportData>(`/api/activity_reports/activity-report/`, {
          params: {
            type: period,
            report_id: reportId,
            level: level,
          },
        });

        console.log("✅ Activity API Response:", response.data);
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
      console.warn("⚠️ Missing required parameters in URL", { period, reportId, level });
      setError("Missing required parameters in URL");
      setLoading(false);
    }
  }, [period, reportId, level]);

  const handleChildClick = (child: ChildData) => {
    if (child.active_users > 0 && child.report_id) {
      const nextLevel = getChildLevel(level as ReportLevel);
      console.log(`➡️ Navigating to child activity report: /activity-reports/${period}/${child.report_id}/${nextLevel}`);
      navigate(`/activity-reports/${period}/${child.report_id}/${nextLevel}`);
    }
  };

  const handleBackClick = () => {
    console.log("🔙 Back button clicked. Parent Info:", report?.parent_info);
    if (level === "country") {
      // Navigate to the reports list page when at country level
      console.log("➡️ At country level, navigating to /activity-reports-list");
      navigate("/activity-reports-list");
    } else if (report?.parent_info) {
      navigate(`/activity-reports/${period}/${report.parent_info.report_id}/${report.parent_info.level}`);
    } else {
      // fallback to list if no parent info for safety
      navigate("/activity-reports-list");
    }
  };

  // Write Insight button handler
  const handleWriteInsight = () => {
    if (!report) return;
    const insightData = {
      geographical_entity: report.geographical_entity,
      id: report.id,
      level: report.level,
      active_users: report.active_users,
      date: report.date,
      period: period,
      report_kind: "activity", // indicate activity report
    };
    console.log("📝 Navigating to BlogCreator with activity insight data:", insightData);
    navigate("/blog-creator", { state: insightData });
  };

  const getChildLevel = (currentLevel: ReportLevel): ReportLevel => {
    const levelMap: Record<ReportLevel, ReportLevel> = {
      country: "state",
      state: "district",
      district: "subdistrict",
      subdistrict: "village",
      village: "village",
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
      const monthName = new Date(report.year, report.month - 1).toLocaleString("default", { month: "long" });
      return `${entity.name} Report - ${monthName} ${report.year}`;
    }
    return `${entity.name} Report`;
  };

  const renderDistribution = () => {
    if (!report?.additional_info?.activity_distribution) return null;

    const distribution = report.additional_info.activity_distribution;
    const buckets = Object.keys(distribution)
      .map(Number)
      .sort((a, b) => a - b);

    return (
      <div className="activity-report-distribution">
        <h3>Activity Distribution</h3>
        <div className="activity-distribution-bars">
          {buckets.map((bucket) => (
            <div key={bucket} className="activity-distribution-bar">
              <div className="activity-bar-label">
                {bucket}+ {bucket === 1 ? "day" : "days"}
              </div>
              <div className="activity-bar-container">
                <div
                  className="activity-bar-fill"
                  style={{ width: `${report.active_users ? (distribution[bucket] / report.active_users) * 100 : 0}%` }}
                >
                  {distribution[bucket]}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  if (loading) return <div className="activity-report-loading">Loading report...</div>;
  if (error) return <div className="activity-report-error">{error}</div>;

  return (
    <div className="activity-report-page">
      <div className="activity-report-container">
        {report && (
          <>
            <div className="activity-report-top-bar">
              <div className="activity-report-header-actions">
                <button
                  onClick={handleBackClick}
                  disabled={!report.parent_info && level !== "country"}
                  className={`activity-report-back-button ${!report.parent_info && level !== "country" ? "disabled" : ""}`}
                >
                  &larr; Back
                </button>
                <button onClick={handleWriteInsight} className="activity-report-write-insight-button">
                  Write Insight
                </button>
              </div>
              <h2>{formatTitle()}</h2>
              <div className="activity-report-total-users">
                <span className="activity-report-users-icon">👤</span>
                {report.active_users} {report.active_users === 1 ? "user" : "users"}
              </div>
            </div>

            <div className="activity-report-level-indicator">{report.level.toUpperCase()} LEVEL</div>

            {(period === "weekly" || period === "monthly") && (
              <div className="activity-report-distribution-toggle">
                <button onClick={() => setShowDistribution(!showDistribution)}>
                  {showDistribution ? "Hide Activity Distribution" : "Show Activity Distribution"}
                </button>
              </div>
            )}

            {showDistribution && renderDistribution()}

            <div className="activity-report-children-grid">
              {Object.entries(report.children_data).map(([id, child]) => (
                <div
                  key={id}
                  className={`activity-report-child-card ${child.active_users > 0 ? "active" : "inactive"} ${
                    child.active_users > 0 && child.report_id ? "clickable" : ""
                  }`}
                  onClick={() => child.active_users > 0 && child.report_id && handleChildClick(child)}
                >
                  <div className="activity-report-child-name">{child.name}</div>
                  <div className="activity-report-child-count">{child.active_users}</div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default ActivityReportViewPage;
