// src/services/idBreakdownService.ts
import api from '../../../api';

export interface IDBreakdown {
  id: string;
  state: {
    id: string;
    name: string;
  };
  district: {
    id: string;
    name: string;
  };
  subdistrict: {
    id: string;
    name: string;
  };
  village: {
    id: string;
    name: string;
  };
  person_code: string;
}

export const fetchIDBreakdown = async (id: string): Promise<IDBreakdown> => {
  try {
    const response = await api.get<IDBreakdown>(
      `/api/geographies/id-breakdown/${id}/` // <-- Use path param, not query
    );
    return response.data;
  } catch (error) {
    throw new Error(`Failed to fetch ID breakdown: ${(error as Error).message}`);
  }
};
