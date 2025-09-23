import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { Line } from '@ant-design/charts';
import api from '../../../../api';
import './OverallReportPage.css';

interface GeographicalEntity {
  id: number;
  name: string;
}

interface ParentInfo {
  level: string;
  id: number;
}

interface ChildEntity {
  id: number;
  level: string;
  total_users: number;
  geographical_entity: GeographicalEntity;
}

interface DataChild {
  id: number;
  name: string;
  report_id: number | null;
  total_users: number;
}

interface Report {
  id: number;
  level: string;
  total_users: number;
  last_updated: string;
  geographical_entity: GeographicalEntity;
  last30daysdata?: Record<string, number>;
  children: ChildEntity[]; // kept for type consistency, unused now
  data: Record<string, DataChild>;
  parent_info: ParentInfo | null;
}

const OverallReportPage: React.FC = () => {
  const { level = 'country', entityId } = useParams<{ level?: string; entityId?: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const [data, setData] = useState<Report | Report[] | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchReport = async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = { level: level || 'country' };
      if (entityId) params.entity_id = entityId;
      const res = await api.get('/api/reports/overall-report/', { params });
      setData(res.data as Report | Report[]);
      if (!Array.isArray(res.data)) {
        const rpt = res.data as Report;
        const newPath = `/reports/overall/${rpt.level}/${rpt.geographical_entity.id}`;
        if (location.pathname !== newPath) {
          navigate(newPath, { replace: true });
        }
      }
    } catch (err) {
      console.error(err);
      setError('Failed to load report data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReport();
  }, [level, entityId, navigate, location]);

  const handleDrillDown = (lvl: string, id: number) => {
    navigate(`/reports/overall/${lvl}/${id}`);
  };

  const handleBackClick = () => {
    navigate(-1);
  };

  const getChildLevel = (currentLevel: string): string => {
    const map: Record<string, string> = {
      country: 'state',
      state: 'district',
      district: 'subdistrict',
      subdistrict: 'village',
      village: 'village'
    };
    return map[currentLevel] || currentLevel;
  };

  const renderChart = (report: Report) => {
    if (!report.last30daysdata) return null;

    const entries = Object.entries(report.last30daysdata)
      .map(([d, u]) => ({ date: d, users: u }))
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

    if (entries.length < 2) {
      return null;
    }

    const config = {
      data: entries,
      xField: 'date',
      yField: 'users',
      height: 200,
      smooth: true,
      line: {
        size: 2,
        color: '#3498db',
      },
      point: {
        size: 3,
        shape: 'circle',
        style: {
          fill: '#3498db',
          stroke: '#fff',
          lineWidth: 1,
        },
      },
      xAxis: {
        tickCount: 5,
        label: {
          style: {
            fill: '#666',
            fontSize: 10,
          },
          formatter: (text: string) => {
            const date = new Date(text);
            return `${date.getDate()}/${date.getMonth() + 1}`;
          }
        },
        grid: {
          line: {
            style: {
              stroke: '#f0f0f0',
              lineDash: [2, 2],
            },
          },
        },
      },
      yAxis: {
        label: {
          style: {
            fill: '#666',
            fontSize: 10,
          },
        },
        grid: {
          line: {
            style: {
              stroke: '#f0f0f0',
              lineDash: [2, 2],
            },
          },
        },
      },
      tooltip: {
        showTitle: false,
        formatter: (datum: any) => {
          return {
            name: 'Users',
            value: datum.users,
          };
        },
        domStyles: {
          'g2-tooltip': {
            padding: '6px 10px',
            borderRadius: '4px',
            fontSize: '12px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
          },
          'g2-tooltip-value': {
            fontWeight: 'bold',
            marginLeft: '4px',
          }
        },
      },
      interactions: [{ type: 'element-active' }],
    };
    return <Line {...config} />;
  };

  if (loading) {
    return (
      <div className="overall-report-page">
        <div className="overall-report-container">
          <div className="overall-report-loading">Loading report...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="overall-report-page">
        <div className="overall-report-container">
          <div className="overall-report-error">{error}</div>
        </div>
      </div>
    );
  }

  if (Array.isArray(data)) {
    return (
      <div className="overall-report-page">
        <div className="overall-report-container">
          <div className="overall-report-top-bar">
            <button className="overall-report-back-button disabled" disabled>
              &larr; Back
            </button>
            <h2>All Countries</h2>
            <div></div>
          </div>

          <div className="overall-report-children-grid">
            {data.map(r => (
              <div
                key={r.geographical_entity.id}
                className={`overall-report-child-card ${r.total_users > 0 ? 'active' : 'inactive'} clickable`}
                onClick={() => handleDrillDown(r.level, r.geographical_entity.id)}
              >
                <div className="overall-report-child-name">{r.geographical_entity.name}</div>
                <div className="overall-report-child-count">{r.total_users}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  const report = data as Report;
  const showChart = report.total_users >= 10 && 
                   report.last30daysdata && 
                   Object.keys(report.last30daysdata).length >= 2;
  
  return (
    <div className="overall-report-page">
      <div className="overall-report-container">
        <div className="overall-report-top-bar">
          <button onClick={handleBackClick} className="overall-report-back-button">
            &larr; Back
          </button>
          <h2>Overall Report for {report.geographical_entity.name}</h2>
          <div className="overall-report-total-users">
            <span className="overall-report-users-icon">👤</span>
            {report.total_users} {report.total_users === 1 ? 'user' : 'users'}
          </div>
        </div>

        <div className="overall-report-level-indicator">
          {report.level.toUpperCase()} LEVEL
        </div>

        {showChart && (
          <div className="overall-report-chart-section">
            <h3>Recent Graph</h3>
            <div className="overall-report-chart-container">
              {renderChart(report)}
            </div>
          </div>
        )}

        <div className="overall-report-children-section">
          <h3>
            {report.level === 'village'
              ? 'Users'
              : `${getChildLevel(report.level).toUpperCase()}S`}
          </h3>
          <div className="overall-report-children-grid">
            {Object.values(report.data).map(child => {
              const isActive = child.total_users > 0;
              const isClickable = isActive && child.report_id !== null;
              return (
                <div
                  key={child.id}
                  className={[
                    "overall-report-child-card",
                    isActive ? "active" : "inactive",
                    isClickable ? "clickable" : "",
                  ].join(" ")}
                  onClick={() => isClickable && handleDrillDown(getChildLevel(report.level), child.id)}
                >
                  <div className="overall-report-child-name">{child.name}</div>
                  <div className="overall-report-child-count">{child.total_users}</div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>  
  );
};

export default OverallReportPage;
