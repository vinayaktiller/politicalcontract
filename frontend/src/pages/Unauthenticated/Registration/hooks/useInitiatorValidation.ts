import { useState, useEffect } from 'react';

interface InitiatorDetails {
  profilepic: string | null;
  name: string;
  text: string;
}

export function useInitiatorValidation() {
  const [initiatorDetails, setInitiatorDetails] = useState<InitiatorDetails | null>(null);
  const [error, setError] = useState<string>('');

  const email = localStorage.getItem('user_email') || '';

  const validateInitiatorID = async (id: number): Promise<boolean> => {
    if (id === 0) {
      setInitiatorDetails({
        profilepic: null,
        name: 'First Member',
        text: 'YOU ARE THE FIRST MEMBER',
      });
      setError('');
     
      return true;
    }

    try {
      const response = await fetch(`https://pfs-be-01-buf0fwgnfgbechdu.centralus-01.azurewebsites.net/api/pendingusers/pending-user/validate-initiator/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ initiator_id: id, email }),
      });

      if (!response.ok) throw new Error('Invalid Initiator ID');

      const data = await response.json();

      // **Log response to inspect the structure**
      console.log("Backend Response:", data);

      const hasEvent = false; // Define hasEvent with a default value
      setInitiatorDetails({
        ...data,
        text: `Are you sure this is your ${hasEvent ? 'Agent' : 'Initiator'} ID?`,
      });

      setError('');
      return true;
    } catch (err) {
      setInitiatorDetails(null);
      setError(err instanceof Error ? err.message : 'Invalid Initiator ID.');
      return false;
    }
  };

  return { initiatorDetails, error, validateInitiatorID, setInitiatorDetails, setError};
}
