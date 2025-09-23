import { config, getApiUrl } from '../../config';

export const registrationService = {
  
  getCookie: (name: string): string | null => {
    let cookieValue: string | null = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === `${name}=`) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    console.log(`Extracted cookie ${name}:`, cookieValue);
    return cookieValue;
  },

  submitRegistration: async (formData: Record<string, any>): Promise<any> => {
    console.log("🚀 submitRegistration started...");

    const formDataToSend = new FormData();
    Object.entries(formData).forEach(([key, value]) => {
      formDataToSend.append(key, value);
    });

    console.log("📦 Form data prepared:", Object.fromEntries(formDataToSend.entries()));
    const csrfToken = registrationService.getCookie('csrftoken') ?? '';
    console.log("🔑 CSRF Token:", csrfToken);

    try {
      const response = await fetch(getApiUrl(config.endpoints.createPendingUser), {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken },
        body: formDataToSend,
      });

      console.log("📡 Server response received, status:", response.status);

      if (response.ok) {
        const result = await response.json();
        console.log("✅ Registration successful, response data:", result);
        return result;
      } else {
        const errorData = await response.text();
        console.error("❌ Error creating user, response:", errorData);
        throw new Error(`Server error: ${errorData}`);
      }
    } catch (error) {
      console.error("🔥 Error submitting form:", error);
      throw error;
    }
  },
};