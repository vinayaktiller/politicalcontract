import { useState, useEffect, FormEvent } from 'react';
import { useAddressSelection } from '../../../Unauthenticated/Registration/hooks/useAddressSelection';
import api from '../../../../api';

interface GroupFormData {
  name: string;
  institution: string;
  country: string;
  state: string;
  district: string;
  subdistrict: string;
  village: string;
}

const useGroupRegistrationForm = () => {
  const founderId = localStorage.getItem("user_id") || "";
  
  const [formData, setFormData] = useState<GroupFormData>({
    name: '',
    institution: '',
    country: '',
    state: '',
    district: '',
    subdistrict: '',
    village: ''
  });
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitMessage, setSubmitMessage] = useState('');
  const [isError, setIsError] = useState(false);
  
  const {
    countries,
    states,
    districts,
    subDistricts,
    villages,
    fetchCountries,
    fetchStates,
    fetchDistricts,
    fetchSubdistricts,
    fetchVillages,
    setStates,
    setDistricts,
    setSubDistricts,
    setVillages
  } = useAddressSelection();

  useEffect(() => {
    fetchCountries();
  }, [fetchCountries]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleAddressChange = async (type: string, value: string) => {
    const updateFormData = (updates: Partial<GroupFormData>) => {
      setFormData(prev => ({ ...prev, ...updates }));
    };

    switch (type) {
      case 'country':
        updateFormData({ 
          country: value, 
          state: '', 
          district: '', 
          subdistrict: '', 
          village: '' 
        });
        setStates([]);
        setDistricts([]);
        setSubDistricts([]);
        setVillages([]);
        await fetchStates(Number(value));
        break;
      case 'state':
        updateFormData({ 
          state: value, 
          district: '', 
          subdistrict: '', 
          village: '' 
        });
        setDistricts([]);
        setSubDistricts([]);
        setVillages([]);
        await fetchDistricts(Number(value));
        break;
      case 'district':
        updateFormData({ 
          district: value, 
          subdistrict: '', 
          village: '' 
        });
        setSubDistricts([]);
        setVillages([]);
        await fetchSubdistricts(Number(value));
        break;
      case 'subdistrict':
        updateFormData({ 
          subdistrict: value, 
          village: '' 
        });
        setVillages([]);
        await fetchVillages(Number(value));
        break;
      case 'village':
        updateFormData({ 
          village: value 
        });
        break;
      default:
        break;
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setIsError(false);
    
    try {
      const response = await api.post('/api/event/register/', {
        ...formData,
        founder: founderId,
        speakers: []
      });

      if (response.status === 201 || response.status === 200) {
        setSubmitMessage('Group created successfully!');
        setFormData({ 
          name: '', 
          institution: '', 
          country: '', 
          state: '', 
          district: '', 
          subdistrict: '', 
          village: '' 
        });
      } else {
        setIsError(true);
        const errorMsg = (response.data && (response.data as any).errors) || 'Failed to create group';
        setSubmitMessage(errorMsg);
      }
    } catch (error) {
      setIsError(true);
      setSubmitMessage('Network error. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return {
    formData,
    isSubmitting,
    submitMessage,
    isError,
    handleChange,
    handleAddressChange,
    handleSubmit,
    countries,
    states,
    districts,
    subDistricts,
    villages
  };
};

export default useGroupRegistrationForm;