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
  report_id?: string;
}

interface ParentInfo {
  level: ReportLevel;
  report_id: string;
}

interface ReportData {
  id: string;
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
        console.log("🔍 Fetching Report Data...");
        console.log("👉 URL Params:", { period, reportId, level });

        const response = await api.get<ReportData>(
          `/api/reports/reports/view/`,
          {
            params: {
              type: period,
              report_id: reportId,
              level: level,
            },
          }
        );

        console.log("✅ API Response Data:", response.data);
        setReport(response.data);
      } catch (err) {
        console.error("❌ API Error:", err);
        setError("Failed to load report. Please try again later.");
      } finally {
        setLoading(false);
      }
    };

    if (period && reportId && level) {
      fetchReportData();
    } else {
      console.warn("⚠️ Missing required parameters in URL", {
        period,
        reportId,
        level,
      });
      setError("Missing required parameters in URL");
      setLoading(false);
    }
  }, [period, reportId, level]);

  const handleChildClick = (child: ChildData) => {
    console.log("👶 Child Clicked:", child);
    if (child.new_users > 0 && child.report_id) {
      const nextLevel = getChildLevel(level as ReportLevel);
      console.log(
        `➡️ Navigating to child report: /reports/${period}/${child.report_id}/${nextLevel}`
      );
      navigate(`/reports/${period}/${child.report_id}/${nextLevel}`);
    }
  };

  const handleBackClick = () => {
    console.log("🔙 Back button clicked. Parent Info:", report?.parent_info);

    if (report?.level === "country") {
      // If at country level, go to reports list page
      console.log("➡️ At country level, navigating to /reports-list");
      navigate("/reports-list");
    } else if (report?.parent_info) {
      // Otherwise, navigate to parent report
      console.log(
        `➡️ Navigating back to parent report: /reports/${period}/${report.parent_info.report_id}/${report.parent_info.level}`
      );
      navigate(
        `/reports/${period}/${report.parent_info.report_id}/${report.parent_info.level}`
      );
    }
  };

  const handleWriteInsight = () => {
    if (!report) return;
    const insightData = {
      geographical_entity: report.geographical_entity,
      id: report.id,
      level: report.level,
      new_users: report.new_users,
      date: getFormattedDateText(),

      period: period,
      report_kind: "report",
    };
    console.log("📝 Navigating to BlogCreator with insight data:", insightData);
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
      const monthName = new Date(report.year, report.month - 1).toLocaleString(
        "default",
        { month: "long" }
      );
      return `${entity.name} Report - ${monthName} ${report.year}`;
    }
    return `${entity.name} Report`;
  };

  const getFormattedDateText = () => {
    if (!report) return "";
    if (period === "daily" && report.date) {
      return new Date(report.date).toLocaleDateString(); // e.g. "8/27/2025"
    }
    if (period === "weekly" && report.week_number && report.year && report.week_start_date) {
      // Extract month number from week_start_date string
      const startDate = new Date(report.week_start_date);
      const monthAbbr = startDate.toLocaleString("default", { month: "short" });
      return `Week ${report.week_number}, ${monthAbbr} ${report.year}`;
    }
    if (period === "monthly" && report.month && report.year) {
      const monthName = new Date(report.year, report.month - 1).toLocaleString(
        "default",
        { month: "long" }
      );
      return `${monthName} ${report.year}`; // e.g. "August 2025"
    }
    return ""; // fallback
  };


  if (loading) {
    console.log("⏳ Loading state active...");
    return (
      <div className="report-view-page">
        <div className="report-view-container">
          <div className="report-view-loading">Loading report...</div>
        </div>
      </div>
    );
  }

  if (error) {
    console.warn("⚠️ Error State:", error);
    return (
      <div className="report-view-page">
        <div className="report-view-container">
          <div className="report-view-error">{error}</div>
        </div>
      </div>
    );
  }

  console.log("📊 Final Report Data (render):", report);

  return (
    <div className="report-view-page">
      <div className="report-view-container">
        {report && (
          <>
            <div className="report-view-top-bar">
              <div className="report-view-header-actions">
                <button
                  onClick={handleBackClick}
                  disabled={!report.parent_info && report.level !== "country"}
                  className={`report-view-back-button ${
                    (!report.parent_info && report.level !== "country")
                      ? "disabled"
                      : ""
                  }`}
                >
                  &larr; Back
                </button>
                <button
                  onClick={handleWriteInsight}
                  className="report-view-write-insight-button"
                >
                  Write Insight
                </button>
              </div>
              <h2>{formatTitle()}</h2>
              <div className="report-view-total-users">
                <span className="report-view-users-icon">👤</span>
                {report.new_users}{" "}
                {report.new_users === 1 ? "person" : "people"}
              </div>
            </div>

            <div className="report-view-level-indicator">
              {report.level.toUpperCase()} LEVEL
            </div>

            <div className="report-view-children-grid">
              {Object.entries(report.children_data).map(([id, child]) => {
                console.log(`📍 Child Rendered: ${child.name}`, child);
                return (
                  <div
                    key={id}
                    className={`report-view-child-card ${
                      child.new_users > 0 ? "active" : "inactive"
                    } ${
                      child.new_users > 0 && child.report_id ? "clickable" : ""
                    }`}
                    onClick={() =>
                      child.new_users > 0 &&
                      child.report_id &&
                      handleChildClick(child)
                    }
                  >
                    <div className="report-view-child-name">{child.name}</div>
                    <div className="report-view-child-count">
                      {child.new_users}
                    </div>
                  </div>
                );
              })}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default ReportViewPage;
