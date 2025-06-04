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
  initiator_id?: number;
  profile_picture: File | null;
  event_type?: 'no_event' | 'group' | 'public' | 'private';
  event_id?: number;
}

  export interface AddressEntity {
    id: number; // Change string to number
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