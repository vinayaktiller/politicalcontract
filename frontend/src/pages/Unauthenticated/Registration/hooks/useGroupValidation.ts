// src/hooks/useGroupValidation.ts
import { useState } from 'react';
import { getApiUrl } from '../../config'; // Adjust import path as needed

interface GroupDetails {
  id: number;
  name: string;
  profile_pic: string | null;
  profile_source: 'group' | 'founder' | null;
}

export function useGroupValidation() {
  const [groupDetails, setGroupDetails] = useState<GroupDetails | null>(null);
  const [error, setError] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);

  const email = localStorage.getItem('user_email') || '';

  const validateGroupID = async (id: number): Promise<boolean> => {
    if (id === 0) {
      setError('Group ID cannot be zero');
      return false;
    }

    setIsLoading(true);
    setError('');
    
    try {
      const response = await fetch(getApiUrl('/api/event/validate/'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ group_id: id, email }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Failed to validate group');
      }

      // Handle successful validation
      setGroupDetails({
        id: data.id,
        name: data.name,
        profile_pic: data.profile_pic,
        profile_source: data.profile_source,
      });
      
      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? 
        err.message : 
        'Invalid Group ID. Please check and try again.';
        
      setError(errorMessage);
      setGroupDetails(null);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const getGroupMessage = (): string => {
    if (!groupDetails) return '';
    
    const { name, profile_source } = groupDetails;
    
    switch(profile_source) {
      case 'group':
        return `Are you sure you want to initiate to the group "${name}"?`;
      case 'founder':
        return `This group uses its founder's profile. Are you sure you want to initiate to "${name}"?`;
      default:
        return `Are you sure you want to initiate to the group "${name}"?`;
    }
  };

  const getGroupCardText = (): string => {
    if (!groupDetails) return '';
    
    const { profile_source } = groupDetails;
    
    switch(profile_source) {
      case 'group':
        return 'This is the group profile';
      case 'founder':
        return 'This group uses its founder\'s profile';
      default:
        return 'Group profile';
    }
  };

  return { 
    groupDetails, 
    error, 
    isLoading,
    validateGroupID,
    getGroupMessage,
    getGroupCardText,
    setGroupDetails,
    setError
  };
}