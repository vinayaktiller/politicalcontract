import React, { useRef, useEffect } from 'react';
import './HeartbeatGraph.css';
import { format, parseISO, subDays, eachDayOfInterval } from 'date-fns';

interface ActivityHistoryItem {
  date: string;
  active: boolean;
}

interface HeartbeatGraphProps {
  activityHistory: ActivityHistoryItem[];
}

const HeartbeatGraph: React.FC<HeartbeatGraphProps> = ({ activityHistory }) => {
  const graphRef = useRef<HTMLDivElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  
  // Generate 30 days of history (including gaps)
  const generateFullHistory = () => {
    const today = new Date();
    const thirtyDaysAgo = subDays(today, 29);
    const fullDates = eachDayOfInterval({ start: thirtyDaysAgo, end: today });
    
    return fullDates.map(date => {
      const dateStr = format(date, 'yyyy-MM-dd');
      const activity = activityHistory.find(a => a.date === dateStr);
      return {
        date: dateStr,
        active: activity ? activity.active : false
      };
    });
  };

  const fullHistory = generateFullHistory();
  const dayWidth = 40; // Increased width per day for better date visibility
  const totalWidth = fullHistory.length * dayWidth;

  // Realistic ECG waveform generator
  const generateECGPath = (index: number, isActive: boolean) => {
    const x = index * dayWidth;
    const path = [];
    
    if (isActive) {
      // ECG pattern: P wave, QRS complex, T wave
      path.push(`M ${x} 50`);
      path.push(`L ${x + dayWidth * 0.1} 50`);
      path.push(`L ${x + dayWidth * 0.15} 40`); // P wave
      path.push(`L ${x + dayWidth * 0.2} 50`);
      path.push(`L ${x + dayWidth * 0.3} 50`);
      path.push(`L ${x + dayWidth * 0.35} 70`); // Q
      path.push(`L ${x + dayWidth * 0.4} 30`);  // R
      path.push(`L ${x + dayWidth * 0.45} 50`); // S
      path.push(`L ${x + dayWidth * 0.55} 50`);
      path.push(`L ${x + dayWidth * 0.6} 45`);  // T wave
      path.push(`L ${x + dayWidth * 0.65} 50`);
      path.push(`L ${x + dayWidth} 50`);
    } else {
      // Flatline
      path.push(`M ${x} 50`);
      path.push(`L ${x + dayWidth} 50`);
    }
    
    return path.join(' ');
  };

  // Scroll to end (most recent date) on mount
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollLeft = scrollRef.current.scrollWidth;
    }
  }, []);

  return (
    <div className="heartbeat-graph-container" ref={graphRef}>
      <h3>Activity History</h3>
      <div className="graph-scroll-container" ref={scrollRef}>
        <svg 
          className="ecg-graph"
          width={totalWidth}
          height="120"
          viewBox={`0 0 ${totalWidth} 120`}
          preserveAspectRatio="none"
        >
          {/* Grid lines */}
          <line x1="0" y1="20" x2={totalWidth} y2="20" stroke="#f0f0f0" />
          <line x1="0" y1="50" x2={totalWidth} y2="50" stroke="#f0f0f0" strokeDasharray="4,2" />
          <line x1="0" y1="80" x2={totalWidth} y2="80" stroke="#f0f0f0" />
          
          {/* ECG Paths */}
          {fullHistory.map((item, index) => (
            <path
              key={index}
              d={generateECGPath(index, item.active)}
              stroke={item.active ? "#e74c3c" : "#95a5a6"}
              strokeWidth={item.active ? 2.5 : 1.5}
              fill="none"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          ))}
          
          {/* Date Labels - showing all dates but with rotation for better fit */}
          {fullHistory.map((item, index) => (
            <g key={`label-${index}`}>
              <text
                x={index * dayWidth + dayWidth / 2}
                y="105"
                fontSize="10"
                textAnchor="middle"
                fill="#7f8c8d"
                className="date-label"
                transform={`rotate(45 ${index * dayWidth + dayWidth / 2} 105)`}
              >
                {format(parseISO(item.date), 'MMM dd')}
              </text>
              <line
                x1={index * dayWidth + dayWidth / 2}
                y1="80"
                x2={index * dayWidth + dayWidth / 2}
                y2="100"
                stroke="#e9ecef"
                strokeWidth="1"
              />
            </g>
          ))}
        </svg>
      </div>
    </div>
  );
};

export default HeartbeatGraph;