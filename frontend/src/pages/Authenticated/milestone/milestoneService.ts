// src/services/milestoneService.ts
import api from '../../../api';

export interface Milestone {
  id: string;
  user_id: number;
  title: string;
  text: string;
  created_at: string;
  delivered: boolean;
  photo_id: number;
  photo_url: string;
  type: string;
}

export const fetchUserMilestones = async (userId: string): Promise<Milestone[]> => {
    console.log("Fetching milestones for user ID:", userId);
  try {
    const response = await api.get<Milestone[]>(
      '/api/users/milestones/', 
      { params: { user_id: userId } }
    );
    return response.data;
  } catch (error) {
    throw new Error(`Failed to fetch milestones: ${(error as Error).message}`);
  }
};