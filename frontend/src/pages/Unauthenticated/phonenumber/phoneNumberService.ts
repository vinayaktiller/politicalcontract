import api from '../../../api';

export interface PhoneNumberResponse {
  phone_number?: string;
  // Add any other returned fields below as needed
}

export const phoneNumberService = {
  getPhoneNumber: async (email: string): Promise<PhoneNumberResponse> => {
    const response = await api.get<PhoneNumberResponse>(`api/pendingusers/api/phone-number/?email=${encodeURIComponent(email)}`);
    return response.data;
  },

  updatePhoneNumber: async (email: string, phoneNumber: string): Promise<PhoneNumberResponse> => {
    const response = await api.post<PhoneNumberResponse>('api/pendingusers/api/phone-number/', {
      email,
      phone_number: phoneNumber
    });
    return response.data;
  }
};
