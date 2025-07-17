// src/components/BreakdownIdPage/BreakdownIdPage.tsx
import React, { useState, useEffect } from 'react';
import { fetchIDBreakdown } from './idBreakdownService';
import './BreakdownIdPage.css';

interface Breakdown {
  stateCode: string;
  stateName: string;
  districtCode: string;
  districtName: string;
  subDistrictCode: string;
  subDistrictName: string;
  villageCode: string;
  villageName: string;
  personCode: string;
}

const BreakdownIdPage: React.FC = () => {
  const [userId, setUserId] = useState<string>('');
  const [breakdown, setBreakdown] = useState<Breakdown | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    const fetchData = async () => {
      const storedId = localStorage.getItem("user_id");
      if (!storedId || storedId.length !== 14) {
        setError("Invalid user ID format. ID must be exactly 14 digits.");
        setLoading(false);
        return;
      }

      setUserId(storedId);
      
      try {
        // Fetch all data in a single API call
        const data = await fetchIDBreakdown(storedId);
        
        // Transform response to match our component structure
        const transformedData: Breakdown = {
          stateCode: storedId.substring(0, 2),
          stateName: data.state.name,
          districtCode: storedId.substring(2, 4),
          districtName: data.district.name,
          subDistrictCode: storedId.substring(4, 6),
          subDistrictName: data.subdistrict.name,
          villageCode: storedId.substring(6, 9),
          villageName: data.village.name,
          personCode: storedId.substring(9, 14)
        };
        
        setBreakdown(transformedData);
        setError(null);
      } catch (err) {
        setError(`Error loading location data: ${(err as Error).message}`);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="id-page-container">
        <div className="id-page-loader"></div>
        <p>Decoding your ID...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="id-page-container">
        <div className="id-page-error-alert">
          <h3>Error</h3>
          <p>{error}</p>
          <p>Your ID: <strong>{userId}</strong></p>
        </div>
      </div>
    );
  }

  return (
   
    <div className="id-page-container">
      <div className="id-page-header">
        <h1>Your ID Explained</h1>
        <p>Your unique identifier decrypted and explained</p>
        <div className="id-page-id-display">{userId}</div>
      </div>

    

      <div className="id-page-breakdown-container">
        <div className="id-page-segment">
          <div className="id-page-segment-header">
            <span className="id-page-segment-code">{breakdown?.stateCode}</span>
            <span className="id-page-segment-label">State</span>
          </div>
          <div className="id-page-segment-name">{breakdown?.stateName}</div>
          <div className="id-page-segment-description">First 2 digits represent your state</div>
        </div>

        <div className="id-page-segment">
          <div className="id-page-segment-header">
            <span className="id-page-segment-code">{breakdown?.districtCode}</span>
            <span className="id-page-segment-label">District</span>
          </div>
          <div className="id-page-segment-name">{breakdown?.districtName}</div>
          <div className="id-page-segment-description">Digits 3-4 represent your district within state {breakdown?.stateCode}</div>
        </div>

        <div className="id-page-segment">
          <div className="id-page-segment-header">
            <span className="id-page-segment-code">{breakdown?.subDistrictCode}</span>
            <span className="id-page-segment-label">Sub-District</span>
          </div>
          <div className="id-page-segment-name">{breakdown?.subDistrictName}</div>
          <div className="id-page-segment-description">Digits 5-6 represent your sub-district within district {breakdown?.stateCode}{breakdown?.districtCode}</div>
        </div>

        <div className="id-page-segment">
          <div className="id-page-segment-header">
            <span className="id-page-segment-code">{breakdown?.villageCode}</span>
            <span className="id-page-segment-label">Village</span>
          </div>
          <div className="id-page-segment-name">{breakdown?.villageName}</div>
          <div className="id-page-segment-description">Digits 7-9 represent your village within sub-district {breakdown?.stateCode}{breakdown?.districtCode}{breakdown?.subDistrictCode}</div>
        </div>

       <div className="id-page-segment id-page-segment-personal">
        <div className="id-page-segment-header">
            <span className="id-page-segment-code id-page-segment-code-personal">
            {breakdown?.personCode}
            </span>
            <span className="id-page-segment-label">Personal ID</span>
        </div>
        <div className="id-page-segment-name">Your unique identifier</div>
        <div className="id-page-segment-description">
            Digits 10-14 represent you in village {breakdown?.stateCode}{breakdown?.districtCode}{breakdown?.subDistrictCode}{breakdown?.villageCode}
        </div>
        </div>
      </div>

      <div className="id-page-summary">
        <h3>How Your ID is Structured</h3>
        <p>
          Your 14-digit ID follows a hierarchical structure where each segment builds upon the previous one:
        </p>
        <div className="id-page-id-structure">
          <span className="id-page-state">State<br/>{breakdown?.stateCode}</span>
          <span className="id-page-district">District<br/>{breakdown?.districtCode}</span>
          <span className="id-page-subdistrict">Sub-Dist<br/>{breakdown?.subDistrictCode}</span>
          <span className="id-page-village">Village<br/>{breakdown?.villageCode}</span>
          <span className="id-page-person">You<br/>{breakdown?.personCode}</span>
        </div>
        <div className="id-page-hierarchy">
          <div className="id-page-level">
            <div className="id-page-level-name">State</div>
            <div className="id-page-level-code">{breakdown?.stateCode}</div>
            <div className="id-page-level-desc">First 2 digits</div>
          </div>
          <div className="id-page-connector">↓</div>
          <div className="id-page-level">
            <div className="id-page-level-name">District</div>
            <div className="id-page-level-code">{breakdown?.districtCode}</div>
            <div className="id-page-level-desc">Next 2 digits (relative to state)</div>
          </div>
          <div className="id-page-connector">↓</div>
          <div className="id-page-level">
            <div className="id-page-level-name">Sub-District</div>
            <div className="id-page-level-code">{breakdown?.subDistrictCode}</div>
            <div className="id-page-level-desc">Next 2 digits (relative to district)</div>
          </div>
          <div className="id-page-connector">↓</div>
          <div className="id-page-level">
            <div className="id-page-level-name">Village</div>
            <div className="id-page-level-code">{breakdown?.villageCode}</div>
            <div className="id-page-level-desc">Next 3 digits (relative to sub-district)</div>
          </div>
          <div className="id-page-connector">↓</div>
          <div className="id-page-level">
            <div className="id-page-level-name">Personal ID</div>
            <div className="id-page-level-code id-page-level-code-personal">
                {breakdown?.personCode}
            </div>
            <div className="id-page-level-desc">Last 5 digits (unique to you)</div>
            </div>
          </div>
      </div>
    </div>
  );
};

export default BreakdownIdPage;