// StatusMessage.tsx
import React from 'react';

interface StatusMessageProps {
    message: string;
}

const StatusMessage: React.FC<StatusMessageProps> = ({ message }) => {
    return (
        <div className="cs-message-container">
            <p className="cs-message">
                {message || "No status message available"}
            </p>
        </div>
    );
};

export default StatusMessage;