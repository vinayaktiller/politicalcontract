// src/hooks/useSpeakerValidation.ts
import { useState } from 'react';
import { getApiUrl } from '../../config'; // Adjust import path as needed

interface SpeakerDetails {
  profilepic: string | null;
  name: string;
  text: string;
}

export function useSpeakerValidation() {
  const [speakerDetails, setSpeakerDetails] = useState<SpeakerDetails | null>(null);
  const [error, setError] = useState<string>('');

  const email = localStorage.getItem('user_email') || '';

  const validateSpeakerID = async (id: number): Promise<boolean> => {
    if (id === 0) {
      setError('Invalid Speaker ID');
      return false;
    }

    try {
      const response = await fetch(getApiUrl('/api/pendingusers/pending-user/validate-initiator/'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ initiator_id: id, email }),
      });

      if (!response.ok) throw new Error('Invalid Speaker ID');

      const data = await response.json();
      
      setSpeakerDetails({
        profilepic: data.profilepic,
        name: data.name,
        text: "Are you sure this is your Speaker ID?",
      });

      setError('');
      return true;
    } catch (err) {
      setSpeakerDetails(null);
      setError(err instanceof Error ? err.message : 'Invalid Speaker ID');
      return false;
    }
  };

  return { speakerDetails, error, validateSpeakerID, setSpeakerDetails, setError  };
}