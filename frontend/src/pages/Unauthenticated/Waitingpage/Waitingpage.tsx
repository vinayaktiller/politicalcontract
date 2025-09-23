// WaitingPage.tsx
import React, { useEffect, useState, useRef } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useDispatch } from "react-redux";
import { login } from "../../../login/login_logoutSlice";
import PhoneNumberForm from "../phonenumber/PhoneNumberForm";
import "../Waitingpage/Waitingpage.css";
import { getWsUrl } from "../config";

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

  // Track if verification is done in no-initiator path
  const [initiatorOkDone, setInitiatorOkDone] = useState(false);

  useEffect(() => {
    if (location.state && (location.state as any).noInitiator) {
      setNoInitiator(true);
      setStatus("no_initiator");
      setShowPhoneForm(true);
      localStorage.setItem("user_type", "no_initiator");
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
      const wsUrl = getWsUrl(`/ws/waitingpage/${user_email}/`);
      ws.current = new WebSocket(wsUrl);
      ws.current.onopen = () => console.log(`✅ WebSocket connected: ${ws.current?.url}`);

      ws.current.onmessage = (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data);
          console.log("📩 Message received:", data);

          // Handle different message types
          if (data.type === "no_initiator_status") {
            setStatus(data.status);
          } else if (data.type === "admin_verification") {
                setStatus(data.status);
                if (data.status === "verified") {
                    // Store user data and await OK click for navigation
                    localStorage.setItem("user_id", data.generated_user_id);
                    localStorage.setItem("name", data.name || "");
                    localStorage.setItem("profile_pic", data.profile_pic || "");
                    console.log("🔹 Stored generated_user_id in local storage:", data.generated_user_id);
                    dispatch(login({ user_email }));
                    // Do NOT navigate yet—wait for user OK click (handled below)
                    setInitiatorOkDone(true);
                }
            }
           else if (data.status) {
            setStatus(data.status);
          }
          
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
            setNoInitiator(false);
          }

          // Store generated_user_id when verification is successful
          if (data.type === "verification_success" && data.generated_user_id) {
            localStorage.setItem("user_id", data.generated_user_id);
            localStorage.setItem("name", data.name);
            localStorage.setItem("profile_pic", data.profile_pic || "");
            console.log("🔹 Stored generated_user_id in local storage:", data.generated_user_id);
            dispatch(login({ user_email }));
            // For normal (non-noInitiator) flow, perform direct navigation
            if (!noInitiator) {
              navigate("/heartbeat");
            } else {
              // For noInitiator case, wait for user OK click
              setInitiatorOkDone(true);
            }
          }
        } catch (error) {
          console.error("❌ WebSocket message parsing error:", error);
        }
      };

      ws.current.onerror = (error: Event) => console.error("⚠️ WebSocket error:", error);
      ws.current.onclose = (event: CloseEvent) => console.log(`🔻 WebSocket closed: ${event.reason}`);

      return () => ws.current?.close();
    }
  }, [user_email, noInitiator, navigate, dispatch]);

  // Normal OK click (used after verified in initiator scenario)
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
    navigate("/heartbeat");
  };

  // Special OK click for "no initiator" scenario after verification
  const handleNoInitiatorOkClick = () => {
    // Mark user_type old_user
    localStorage.setItem("user_type", "old_user");
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type: "accept_verification", user_email, notificationId }));
      console.log("📤 Sent accept_verification message (no_initiator)");
    } else {
      console.warn("⚠️ WebSocket is not open");
    }
    dispatch(login({ user_email }));
    navigate("/heartbeat");
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

        {/* OK Button for verified status in normal initiator workflow */}
        {status === "verified" && !noInitiator ? (
          <button className="waiting-page-button" onClick={handleOkClick}>OK</button>
        ) : null}

        {/* OK Button for verified status in noInitiator workflow: user must click before proceeding */}
        {status === "verified" && noInitiator && initiatorOkDone ? (
          <button className="waiting-page-button" onClick={handleNoInitiatorOkClick}>OK</button>
        ) : null}

        {status === "rejected" ? (
          <button className="waiting-page-button" onClick={handleAcceptRejection}>Accept Rejection</button>
        ) : null}
      </div>
    </div>
  );
};

export default WaitingPage;