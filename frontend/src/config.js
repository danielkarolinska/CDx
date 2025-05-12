// Environment-specific configuration
export const config = {
  apiUrl: import.meta.env.VITE_API_URL || (
    import.meta.env.PROD 
      ? 'https://cdx-backend.onrender.com'
      : 'http://127.0.0.1:8000'
  ),
  
  // Add other configuration values here
  appTitle: 'CDx - Companion Diagnostics',
  version: '1.0.0',
};

// Helper function to get API endpoint URLs
export const getApiUrl = (endpoint) => {
  const baseUrl = config.apiUrl;
  return `${baseUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
};

export default config; 