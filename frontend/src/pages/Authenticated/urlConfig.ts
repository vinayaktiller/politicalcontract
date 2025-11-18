// Centralized URL configuration
export const URL_CONFIG = {
  // Base URL for milestone images
  IMAGE_BASE_URL: 'https://pfs-ui-f7bnfbg9agb4cwcu.canadacentral-01.azurewebsites.net',
  
  // Fallback URL for development/error cases
  FALLBACK_IMAGE_URL: 'https://pfs-ui-f7bnfbg9agb4cwcu.canadacentral-01.azurewebsites.net/initiation/1.jpg',
  
  // Helper function to build image URLs
  buildImageUrl: (type: string, photoId: string | number): string => {
    return `${URL_CONFIG.IMAGE_BASE_URL}/${type}/${photoId}.jpg`;
  },
  
  // Helper function to get milestone image URL with fallback
  getMilestoneImageUrl: (type?: string, photoId?: string | number): string => {
    if (type && photoId) {
      return URL_CONFIG.buildImageUrl(type, photoId);
    }
    return URL_CONFIG.FALLBACK_IMAGE_URL;
  }
};