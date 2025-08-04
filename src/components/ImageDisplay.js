import React, { useState } from 'react';

function ImageDisplay({ src, alt, className = "", containerHeight = "h-48" }) {
  const [showModal, setShowModal] = useState(false);

  const handleImageClick = () => {
    setShowModal(true);
  };

  const handleModalClose = () => {
    setShowModal(false);
  };

  const handleModalClick = (e) => {
    if (e.target === e.currentTarget) {
      setShowModal(false);
    }
  };

  return (
    <>
      <div 
        className={`${containerHeight} bg-gray-100 flex items-center justify-center cursor-pointer ${className}`}
        onClick={handleImageClick}
      >
        <img
          src={src}
          alt={alt}
          className="max-w-full max-h-full object-contain"
        />
      </div>

      {showModal && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4"
          onClick={handleModalClick}
        >
          <div className="relative max-w-full max-h-full">
            <button
              onClick={handleModalClose}
              className="absolute top-4 right-4 text-white bg-black bg-opacity-50 rounded-full w-8 h-8 flex items-center justify-center hover:bg-opacity-75 z-10"
            >
              ×
            </button>
            <img
              src={src}
              alt={alt}
              className="max-w-full max-h-full object-contain"
            />
          </div>
        </div>
      )}
    </>
  );
}

export default ImageDisplay;