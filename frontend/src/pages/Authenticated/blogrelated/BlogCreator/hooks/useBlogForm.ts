// import { useState, useEffect } from 'react';
// import { BlogFormData, BlogType, ContentType } from '../types';
// import api from '../../../../../api'; // Ensure this path points to your Axios instance

// export default function useBlogForm() {
//   const userIdFromStorage = localStorage.getItem("user_id");
//   const initialUserId = userIdFromStorage ? parseInt(userIdFromStorage, 10) : null;
  
//   const initialFormData: BlogFormData = {
//     type: 'journey',
//     content_type: 'micro',
//     content: '',
//     userid: initialUserId,
//   };

//   const [formData, setFormData] = useState<BlogFormData>(initialFormData);
//   const [isSubmitting, setIsSubmitting] = useState(false);
//   const [error, setError] = useState<string | null>(null);
//   const [success, setSuccess] = useState(false);

//   // Auto-switch content type based on length
//   useEffect(() => {
//     const length = formData.content.length;
//     let newType: ContentType = formData.content_type;
    
//     if (length > 3200 && formData.content_type !== 'article') {
//       newType = 'article';
//     } else if (length > 280 && formData.content_type === 'micro') {
//       newType = 'short_essay';
//     }
    
//     if (newType !== formData.content_type) {
//       setFormData(prev => ({ ...prev, content_type: newType }));
//     }
//   }, [formData.content, formData.content_type]);

//   const handleChange = (
//     e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
//   ) => {
//     const { name, value } = e.target;

//     const finalValue = [
//       'target_user',
//       'report_id',
//       'questionid',
//       'country_id',
//       'state_id',
//       'district_id',
//       'subdistrict_id',
//       'village_id',
//     ].includes(name)
//       ? value === ''
//         ? null
//         : Number(value)
//       : value;

//     setFormData((prev) => ({
//       ...prev,
//       [name]: finalValue,
//     }));
//   };

//   const handleSubmit = async (e: React.FormEvent) => {
//     e.preventDefault();
//     setIsSubmitting(true);
//     setError(null);
//     setSuccess(false);

//     try {
//       const response = await api.post('/api/blog/create-blog/', formData);
//       setSuccess(true);
//       // Reset form after successful submission
//       setFormData(initialFormData);
//     } catch (err: any) {
//       console.error('Error creating blog:', err.response?.data || err.message);
//       setError(err.response?.data?.message || 'Failed to create blog');
//     } finally {
//       setIsSubmitting(false);
//     }
//   };

//   const getMaxLength = () => {
//     switch (formData.content_type) {
//       case 'micro': return 280;
//       case 'short_essay': return 3200;
//       case 'article': return 12000;
//       default: return 280;
//     }
//   };

//   return {
//     formData,
//     setFormData,
//     isSubmitting,
//     error,
//     success,
//     handleChange,
//     handleSubmit,
//     getMaxLength
//   };
// }

import { useState, useEffect } from 'react';
import { BlogFormData, BlogType, ContentType } from '../types';
import api from '../../../../../api'; // your Axios instance

export default function useBlogForm() {
  const userIdFromStorage = localStorage.getItem("user_id");
  const initialUserId = userIdFromStorage ? parseInt(userIdFromStorage, 10) : null;

  const initialFormData: BlogFormData = {
    type: 'journey',
    content_type: 'micro',
    content: '',
    userid: initialUserId, // must match backend model
  };

  const [formData, setFormData] = useState<BlogFormData>(initialFormData);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Auto-switch content type based on length
  useEffect(() => {
    const length = formData.content.length;
    let newType: ContentType = formData.content_type;

    if (length > 3200 && formData.content_type !== 'article') {
      newType = 'article';
    } else if (length > 280 && formData.content_type === 'micro') {
      newType = 'short_essay';
    }

    if (newType !== formData.content_type) {
      setFormData(prev => ({ ...prev, content_type: newType }));
    }
  }, [formData.content, formData.content_type]);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    const finalValue = [
      'target_user', 'report_id', 'questionid',
      'country_id', 'state_id', 'district_id',
      'subdistrict_id', 'village_id',
    ].includes(name)
      ? value === '' ? null : Number(value)
      : value;

    setFormData((prev) => ({
      ...prev,
      [name]: finalValue,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);
    setSuccess(false);

    try {
      console.log("Submitting blog payload:", formData); // debug
      await api.post('/api/blog/create-blog/', formData);

      setSuccess(true);
      // Reset but keep userid
      setFormData(prev => ({
        ...initialFormData,
        userid: prev.userid,
      }));
    } catch (err: any) {
      console.error('Error creating blog:', err.response?.data || err.message);
      setError(err.response?.data?.message || 'Failed to create blog');
    } finally {
      setIsSubmitting(false);
    }
  };

  const getMaxLength = () => {
    switch (formData.content_type) {
      case 'micro': return 280;
      case 'short_essay': return 3200;
      case 'article': return 12000;
      default: return 280;
    }
  };

  return {
    formData,
    setFormData,
    isSubmitting,
    error,
    success,
    handleChange,
    handleSubmit,
    getMaxLength,
  };
}
