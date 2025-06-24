// LoadingSpinner.jsx - Loading component
import React from 'react';

const LoadingSpinner = () => {
  return (
    <div className="min-h-screen bg-black flex items-center justify-center"> {/* Changed background to black */}
      <div className="text-center">
        <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-yellow-400 mx-auto mb-6"></div> {/* Yellow spinner, thicker border, slightly larger */}
        <p className="text-white text-lg font-semibold tracking-wide">Loading Canary...</p> {/* White text, slightly larger, bolder, spaced out */}
      </div>
    </div>
  );
};

export default LoadingSpinner;