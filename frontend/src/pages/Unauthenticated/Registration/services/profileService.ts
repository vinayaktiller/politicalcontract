import { FormDataTypes } from '../types/registrationTypes';
import { FormDataInitialState } from '../constants/initialState'; // Define initial state separately

export const profileService = {
  uploadProfilePicture: async (croppedImage: string): Promise<File | undefined> => {
    if (croppedImage) {
      try {
        // Convert croppedImage URL to a Blob
        const blob: Blob = await fetch(croppedImage).then(res => res.blob());

        // Create a File object from the Blob
        const file: File = new File([blob], 'profile_picture.jpg', { type: 'image/jpeg' });

        // Update the initial state while ensuring type safety
        const updatedState: FormDataTypes = {
          ...FormDataInitialState, // Use actual initial state object, not the type
          profile_picture: file,
        };

        // Log the updated states for debugging
        console.log('FormDataInitialState:', FormDataInitialState);
        console.log('Updated State:', updatedState);

        // Return the File object
        return file;
      } catch (error) {
        console.error('Error processing cropped image:', error);
        return undefined;
      }
    }
    return undefined;
  },
};
