import api from '../../../../../api'; // Import your Axios instance
import { useState } from 'react';

interface ConnexionDetails {
  profilepic: string | null;
  name: string;
  text: string;
}

export function useConnexionValidation() {
  const [connexionDetails, setConnexionDetails] = useState<ConnexionDetails | null>(null);
  const [error, setError] = useState<string>('');

  const email = localStorage.getItem('user_email') || '';

  const validateConnexionID = async (id: number): Promise<boolean> => {
    if (id === 0) {
      setConnexionDetails({
        profilepic: null,
        name: 'First Member',
        text: 'YOU ARE THE FIRST MEMBER',
      });
      setError('');
      
      return true;
    }
    
    try {
      const response = await api.post<{ profilepic: string | null; name: string }>('/api/pendingusers/pending-user/validate-initiator/', {
        initiator_id: id,
        email,
      });

      if (typeof response.data === 'object' && response.data !== null) {
        setConnexionDetails({
          ...response.data, // Spreading only if response.data is an object
          text: `Are you sure this is the correct ID for connexion?`,
        });
        setError('');
        return true;
      } else {
        throw new Error("Invalid response format.");
      }
      
    } catch (err) {
      setConnexionDetails(null);
      setError(err instanceof Error ? err.message : 'Invalid Connexion ID.');
      return false;
    }
  };

  return { connexionDetails, error, validateConnexionID, setConnexionDetails, setError };
}
