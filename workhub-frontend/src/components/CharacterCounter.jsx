import React from 'react';

/**
 * CharacterCounter Component
 * Displays character count with visual warning when approaching limit
 */
export const CharacterCounter = ({ 
  current, 
  max, 
  warningThreshold = 0.9,
  showBar = false 
}) => {
  const percentage = (current / max) * 100;
  const isWarning = current / max >= warningThreshold;
  const isOver = current > max;
  
  const getColor = () => {
    if (isOver) return '#ef4444'; // red
    if (isWarning) return '#f59e0b'; // orange
    return '#6b7280'; // gray
  };
  
  return (
    <div className="character-counter">
      {showBar && (
        <div className="counter-bar-container">
          <div 
            className="counter-bar" 
            style={{ 
              width: `${Math.min(percentage, 100)}%`,
              backgroundColor: getColor(),
              height: '2px',
              transition: 'all 0.2s ease'
            }} 
          />
        </div>
      )}
      <div className="counter-text" style={{ color: getColor() }}>
        {current} / {max}
        {isOver && <span className="counter-warning"> (exceeds limit)</span>}
        {isWarning && !isOver && <span className="counter-warning"> (approaching limit)</span>}
      </div>
      
      <style jsx>{`
        .character-counter {
          margin-top: 4px;
          font-size: 0.875rem;
        }
        .counter-bar-container {
          width: 100%;
          height: 2px;
          background-color: #e5e7eb;
          border-radius: 1px;
          overflow: hidden;
          margin-bottom: 4px;
        }
        .counter-text {
          font-weight: 500;
          display: flex;
          align-items: center;
          gap: 4px;
        }
        .counter-warning {
          font-weight: 400;
          font-size: 0.8125rem;
        }
      `}</style>
    </div>
  );
};

export default CharacterCounter;


