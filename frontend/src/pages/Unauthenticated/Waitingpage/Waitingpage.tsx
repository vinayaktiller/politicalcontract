// WaitingPage.tsx
import React, { useEffect, useState, useRef } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useDispatch } from "react-redux";
import { login } from "../../../login/login_logoutSlice";
import PhoneNumberForm from "../phonenumber/PhoneNumberForm";
import "../Waitingpage/Waitingpage.css";

interface StatusMessage {
  icon: string;
  message: string;
}

type WebSocketRef = React.MutableRefObject<WebSocket | null>;

const WaitingPage: React.FC = () => {
  const user_email = localStorage.getItem("user_email") || '';
  const location = useLocation();
  const [status, setStatus] = useState<string>("");
  const [notificationId, setNotificationId] = useState<number | null>(null);
  const [noInitiator, setNoInitiator] = useState<boolean>(false);
  const [showPhoneForm, setShowPhoneForm] = useState<boolean>(false);
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const ws: WebSocketRef = useRef(null);

  // Check if user registered without an initiator
  useEffect(() => {
    if (location.state && (location.state as any).noInitiator) {
      setNoInitiator(true);
      setStatus("no_initiator");
      setShowPhoneForm(true);
    }
  }, [location]);

  const statusMessages: Record<string, StatusMessage> = {
    initiator_offline: { icon: "⚠️", message: "Your initiator is offline. Ask them to come online." },
    sent: { icon: "✅", message: "Your request has been sent. Waiting for review." },
    not_viewed: { icon: "👀", message: "Your initiator hasn't viewed your request yet." },
    reacted_pending: { icon: "⏳", message: "Your initiator has seen your request but hasn't responded." },
    verified: { icon: "🎉", message: "Your request has been verified! Proceed to profile setup." },
    rejected: { icon: "🚫", message: "Your request was rejected. Try another initiator." },
    no_initiator: { icon: "⏳", message: "Waiting for initiator assignment. Our team will review your application shortly." },
    admin_review: { icon: "📋", message: "Your application is under review by our team." },
    initiator_assigned: { icon: "✅", message: "An initiator has been assigned to you. Please wait for their verification." },
    default: { icon: "📩", message: "Your request has been submitted!" },
  };
  
   useEffect(() => {
        if ((location.state && (location.state as any).noInitiator) || 
            localStorage.getItem("user_type") === "no_initiator") {
            setNoInitiator(true);
            setStatus("no_initiator");
            setShowPhoneForm(true);
        }
    }, [location]);

  useEffect(() => {
    if (user_email) {
      ws.current = new WebSocket(`ws://localhost:8000/ws/waitingpage/${user_email}/`);

      ws.current.onopen = () => console.log(`✅ WebSocket connected: ${ws.current?.url}`);

      ws.current.onmessage = (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data);
          console.log("📩 Message received:", data);

          if (data.status) setStatus(data.status);
          if (data.notification_id) {
            setNotificationId(data.notification_id);
            console.log("🔹 Notification ID received:", data.notification_id);
            localStorage.setItem("notification_id", data.notification_id.toString());
          }

          // Handle no-initiator specific statuses
          if (data.type === "admin_review") {
            setStatus("admin_review");
          } else if (data.type === "initiator_assigned") {
            setStatus("initiator_assigned");
            setNoInitiator(false); // No longer in no-initiator state
          }

          // Store generated_user_id when verification is successful
          if (data.type === "verification_success" && data.generated_user_id) {
            localStorage.setItem("user_id", data.generated_user_id);
            localStorage.setItem("name", data.name);
            localStorage.setItem("profile_pic", data.profile_pic || "");
            console.log("🔹 Stored generated_user_id in local storage:", data.generated_user_id);
            dispatch(login({ user_email })); // Dispatch login action with user_email
            navigate("/heartbeat");
          }
        } catch (error) {
          console.error("❌ WebSocket message parsing error:", error);
        }
      };

      ws.current.onerror = (error: Event) => console.error("⚠️ WebSocket error:", error);
      ws.current.onclose = (event: CloseEvent) => console.log(`🔻 WebSocket closed: ${event.reason}`);

      return () => ws.current?.close();
    }
  }, [user_email, noInitiator]);

  const handleOkClick = () => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type: "accept_verification", user_email, notificationId }));
      console.log("📤 Sent accept_verification message");
    } else {
      console.warn("⚠️ WebSocket is not open");
    }
    
    if (user_email) {
      dispatch(login({ user_email }));
    }
  };

  const handleAcceptRejection = () => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type: "accept_rejection", user_email, notificationId }));
      console.log("📤 Sent accept_rejection message");
    } else {
      console.warn("⚠️ WebSocket is not open");
    }
    navigate("/login");
  };

  const handlePhoneNumberUpdated = () => {
    // Optional: You can add any logic to run after phone number is updated
    console.log("Phone number updated successfully");
  };

  const { icon, message } = statusMessages[status] || statusMessages.default;

  return (
    <div className="waiting-page-container">
      <div className="waiting-page-message-box">
        <span className="waiting-page-status-icon">{icon}</span>
        <p className="waiting-page-text">{message}</p>
        
        {noInitiator && status === "no_initiator" && (
          <div className="no-initiator-info">
            <p>We'll notify you once an initiator has been assigned to you.</p>
          </div>
        )}
        
        {showPhoneForm && noInitiator && (
          <div className="phone-form-section">
            <PhoneNumberForm 
              userEmail={user_email} 
              onPhoneNumberUpdated={handlePhoneNumberUpdated}
            />
          </div>
        )}
        
        {status === "verified" ? (
          <button className="waiting-page-button" onClick={handleOkClick}>OK</button>
        ) : status === "rejected" ? (
          <button className="waiting-page-button" onClick={handleAcceptRejection}>Accept Rejection</button>
        ) : null}
      </div>
    </div>
  );
};

export default WaitingPage;