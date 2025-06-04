import React from 'react';


interface StatusMessageProps {
    message: string;
}

const StatusMessage: React.FC<StatusMessageProps> = ({ message }) => {
    return (
        <div className="status-message-container">
            <p className="status-message">
                {message || "No status message available"}
            </p>
        </div>
    );
};

export default StatusMessage;
