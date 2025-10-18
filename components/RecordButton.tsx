
import React from 'react';
import { Icons } from '../constants';

interface RecordButtonProps {
  isRecording: boolean;
  isLoading: boolean;
  onStart: () => void;
  onStop: () => void;
}

const RecordButton: React.FC<RecordButtonProps> = ({ isRecording, isLoading, onStart, onStop }) => {
  const isDisabled = isLoading;

  const handleClick = () => {
    if (isRecording) {
      onStop();
    } else {
      onStart();
    }
  };

  const getButtonContent = () => {
    if (isLoading) {
      return <Icons.Spinner className="w-8 h-8 animate-spin" />;
    }
    if (isRecording) {
      return <Icons.Stop className="w-8 h-8" />;
    }
    return <Icons.Mic className="w-8 h-8" />;
  };
  
  const getButtonClass = () => {
      let baseClass = "w-20 h-20 rounded-full flex items-center justify-center text-white transition-all duration-300 ease-in-out shadow-lg focus:outline-none focus:ring-4";
      if (isDisabled) return `${baseClass} bg-gray-400 cursor-not-allowed`;
      if (isRecording) return `${baseClass} bg-red-500 hover:bg-red-600 focus:ring-red-300`;
      return `${baseClass} bg-blue-500 hover:bg-blue-600 focus:ring-blue-300`;
  }

  return (
    <button
      onClick={handleClick}
      disabled={isDisabled}
      className={getButtonClass()}
      aria-label={isRecording ? 'Stop recording' : 'Start recording'}
    >
      {getButtonContent()}
    </button>
  );
};

export default RecordButton;
