// types/registrationTypes.ts
export interface FormDataTypes {
  gmail: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  gender: string;
  country: string;
  state: string;
  district: string;
  subdistrict: string;
  village: string;
  initiator_id?: number | null; // Allow null for no-initiator case
  profile_picture: File | null;
  event_type?: 'no_event' | 'group' | 'public' | 'private';
  event_id?: number;
  has_no_initiator?: boolean; // New field to track no-initiator choice
}

export interface AddressEntity {
  id: number;
  name: string;
}

export interface FormStepProps {
  formData: FormDataTypes;
  setFormData: React.Dispatch<React.SetStateAction<FormDataTypes>>;
  nextStep: () => void;
  prevStep: () => void;
  currentStep: number;
  totalSteps: number;
}

export interface CropType {
  aspect?: number;
  width?: number;
  height?: number;
  x?: number;
  y?: number;
}