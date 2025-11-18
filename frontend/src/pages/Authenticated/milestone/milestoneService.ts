// src/services/milestoneService.ts
import api from '../../../api';

export interface Milestone {
  id: number; // CHANGED: from string to number to match backend
  user_id: number;
  title: string;
  text: string;
  created_at: string;
  delivered: boolean;
  photo_id: number;
  photo_url: string;
  type: string;
}

export const fetchUserMilestones = async (userId: number): Promise<Milestone[]> => {
    console.log("Fetching milestones for user ID:", userId);
    
    // Validate userId
    if (!userId || isNaN(userId)) {
        throw new Error(`Invalid user ID: ${userId}`);
    }

    try {
        const response = await api.get<Milestone[]>(
            '/api/users/milestones/', 
            { 
                params: { user_id: userId },
                timeout: 10000 // Add timeout to prevent hanging requests
            }
        );
        
        console.log("Milestones API response:", response.data);
        
        if (!response.data) {
            console.warn("No data received from milestones API");
            return [];
        }
        
        // Ensure we return an array even if the response is not properly formatted
        return Array.isArray(response.data) ? response.data : [];
    } catch (error: any) {
        console.error("Error fetching milestones:", error);
        
        // Provide more specific error messages
        if (error.response) {
            // Server responded with error status
            throw new Error(`Server error: ${error.response.status} - ${error.response.data?.message || 'Failed to fetch milestones'}`);
        } else if (error.request) {
            // Request was made but no response received
            throw new Error('Network error: Unable to reach the server. Please check your connection.');
        } else {
            // Something else happened
            throw new Error(`Failed to fetch milestones: ${error.message}`);
        }
    }
};