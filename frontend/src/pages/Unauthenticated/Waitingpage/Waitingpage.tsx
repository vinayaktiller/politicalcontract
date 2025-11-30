import React, { useEffect, useState, useRef } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useDispatch } from "react-redux";
import { login } from "../../../login/login_logoutSlice";
import PhoneNumberForm from "../phonenumber/PhoneNumberForm";
import "../Waitingpage/Waitingpage.css";
import { getWsUrl, getApiUrl } from "../config";

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
  const [pendingUserId, setPendingUserId] = useState<number | null>(null);
  const [generatedUserId, setGeneratedUserId] = useState<number | null>(null);
  const [noInitiator, setNoInitiator] = useState<boolean>(false);
  const [showPhoneForm, setShowPhoneForm] = useState<boolean>(false);
  const [rejectionReason, setRejectionReason] = useState<string>("");
  const [claimedByName, setClaimedByName] = useState<string>("");
  const [isDeleting, setIsDeleting] = useState<boolean>(false);
  const [showDeleteConfirmation, setShowDeleteConfirmation] = useState<boolean>(false);
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const ws: WebSocketRef = useRef(null);

  // Track if verification is done in no-initiator path
  const [initiatorOkDone, setInitiatorOkDone] = useState(false);

  // Check localStorage for existing no-initiator status on component mount
  useEffect(() => {
    const savedUserType = localStorage.getItem("user_type");
    const savedStatus = localStorage.getItem("no_initiator_status");
    
    if (savedUserType === "no_initiator" || (location.state && (location.state as any).noInitiator)) {
      setNoInitiator(true);
      
      // If we have a saved status, use it immediately
      if (savedStatus) {
        setStatus(savedStatus);
        
        // If status is verified/rejected, ensure buttons appear
        if (savedStatus === "verified" || savedStatus === "rejected") {
          setShowPhoneForm(false);
          if (savedStatus === "verified") {
            setInitiatorOkDone(true);
          }
        } else {
          setShowPhoneForm(true);
        }
      } else {
        setStatus("no_initiator");
        setShowPhoneForm(true);
      }
      
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
    unclaimed: { icon: "⏳", message: "Your application is awaiting review by our team." },
    claimed: { icon: "👀", message: "Your application is currently being reviewed by an admin." },
    default: { icon: "📩", message: "Your request has been submitted!" },
  };

  useEffect(() => {
    if (user_email) {
      const wsUrl = getWsUrl(`/ws/waitingpage/${user_email}/`);
      ws.current = new WebSocket(wsUrl);
      ws.current.onopen = () => {
        console.log(`✅ WebSocket connected: ${ws.current?.url}`);
        
        // If we're a no-initiator user but don't have current status, the backend
        // will automatically send it when we connect due to the consumer logic
      };

      ws.current.onmessage = (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data);
          console.log("📩 Message received:", data);

          // Handle no-initiator status updates (on connect and real-time)
          if (data.type === "no_initiator_status") {
            setNoInitiator(true);
            setStatus(data.status);
            setPendingUserId(data.pending_user_id);
            setRejectionReason(data.rejection_reason || "");
            setClaimedByName(data.claimed_by_name || "");
            
            // Save status to localStorage for persistence across refreshes
            localStorage.setItem("no_initiator_status", data.status);
            localStorage.setItem("user_type", "no_initiator");
            
            // Show phone form only for unclaimed/claimed statuses
            if (data.status === "unclaimed" || data.status === "claimed") {
              setShowPhoneForm(true);
              setInitiatorOkDone(false);
            } else {
              setShowPhoneForm(false);
              
              // If status is verified, mark that we're ready for OK button
              if (data.status === "verified") {
                setInitiatorOkDone(true);
              }
            }
            
            console.log(`🔹 No-initiator status: ${data.status}, pending_user_id: ${data.pending_user_id}`);
          }
          // Handle admin verification messages (both verification and rejection)
          else if (data.type === "admin_verification") {
            setStatus(data.status);
            
            if (data.status === "verified") {
              // Store pending user ID for later cleanup
              setPendingUserId(data.pending_user_id);
              console.log("🔹 Pending user ID for cleanup:", data.pending_user_id);
              
              // Hide phone form immediately when verified
              setShowPhoneForm(false);
              
              // Save to localStorage
              localStorage.setItem("no_initiator_status", "verified");
              
              // Mark that we're ready for OK button
              setInitiatorOkDone(true);
            } 
            else if (data.status === "rejected") {
              // Handle rejection
              setRejectionReason(data.rejection_reason || "No reason provided");
              setPendingUserId(data.pending_user_id);
              setShowPhoneForm(false);
              
              // Save to localStorage
              localStorage.setItem("no_initiator_status", "rejected");
              
              console.log("🔹 Received rejection with pending_user_id:", data.pending_user_id);
            }
          }
          // Handle verification success (when petitioner is created)
          else if (data.type === "verification_success") {
            // Store user data from the actual created petitioner
            localStorage.setItem("user_id", data.generated_user_id);
            localStorage.setItem("name", data.name || "");
            localStorage.setItem("profile_pic", data.profile_pic || "");
            localStorage.setItem("user_type", "olduser"); // 🔥 Set user type to olduser
            setGeneratedUserId(data.generated_user_id);
            console.log("🔹 Stored generated_user_id in local storage:", data.generated_user_id);
            dispatch(login({ user_email }));
          }
          // Handle cleanup success messages
          else if (data.type === "no_initiator_cleanup_success") {
            console.log("✅ No-initiator verification cleanup successful");
            // Clear localStorage
            localStorage.removeItem("no_initiator_status");
            localStorage.setItem("user_type", "olduser"); // 🔥 Set user type to olduser
            // Now navigate since cleanup is complete and petitioner is created
            navigate("/landing");
          }
          else if (data.type === "no_initiator_rejection_cleanup_success") {
            console.log("✅ No-initiator rejection cleanup successful");
            // Clear localStorage
            localStorage.removeItem("no_initiator_status");
            localStorage.removeItem("user_type");
            navigate("/login");
          }
          else if (data.type === "no_initiator_verification_failed") {
            console.error("❌ No-initiator verification failed");
            // Show error message to user
            setStatus("verification_failed");
          }
          else if (data.status) {
            setStatus(data.status);
          }
          
          if (data.notification_id) {
            setNotificationId(data.notification_id);
            console.log("🔹 Notification ID received:", data.notification_id);
            localStorage.setItem("notification_id", data.notification_id.toString());
          }

          // Handle verification success for regular flow
          if (data.type === "verification_success" && data.generated_user_id) {
            localStorage.setItem("user_id", data.generated_user_id);
            localStorage.setItem("name", data.name);
            localStorage.setItem("profile_pic", data.profile_pic || "");
            localStorage.setItem("user_type", "olduser"); // 🔥 Set user type to olduser
            console.log("🔹 Stored generated_user_id in local storage:", data.generated_user_id);
            dispatch(login({ user_email }));
            
            // Hide phone form when verified in normal flow too
            setShowPhoneForm(false);
            
            // For normal (non-noInitiator) flow, perform direct navigation
            if (!noInitiator) {
              navigate("/landing");
            }
            // For noInitiator case, we wait for cleanup success message
          }
        } catch (error) {
          console.error("❌ WebSocket message parsing error:", error);
        }
      };

      ws.current.onerror = (error: Event) => console.error("⚠️ WebSocket error:", error);
      ws.current.onclose = (event: CloseEvent) => {
        console.log(`🔻 WebSocket closed: ${event.reason}`);
        // Optionally attempt to reconnect here
      };

      return () => {
        if (ws.current) {
          ws.current.close();
        }
      };
    }
  }, [user_email, noInitiator, navigate, dispatch]);

  // Handle delete registration request
  const handleDeleteRegistration = async () => {
    if (!user_email) {
      console.error("❌ No user email found");
      return;
    }

    setIsDeleting(true);
    try {
      const response = await fetch(getApiUrl('/api/pendingusers/pending-users/delete/'), {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email: user_email }),
      });

      const data = await response.json();

      if (data.success) {
        console.log("✅ Registration deleted successfully");
        
        // Clear local storage
        localStorage.removeItem("user_email");
        localStorage.removeItem("notification_id");
        localStorage.removeItem("user_type");
        localStorage.removeItem("no_initiator_status");
        
        // Close WebSocket connection
        if (ws.current) {
          ws.current.close();
        }
        
        // Navigate to login page
        navigate("/login");
      } else {
        console.error("❌ Failed to delete registration:", data.error);
        alert("Failed to delete registration. Please try again.");
      }
    } catch (error) {
      console.error("❌ Error deleting registration:", error);
      alert("An error occurred while deleting registration. Please try again.");
    } finally {
      setIsDeleting(false);
      setShowDeleteConfirmation(false);
    }
  };

  // Handle no-initiator verification acceptance
  const handleNoInitiatorVerification = () => {
    if (ws.current?.readyState === WebSocket.OPEN && pendingUserId) {
      ws.current.send(JSON.stringify({ 
        type: "accept_no_initiator_verification", 
        user_email, 
        pending_user_id: pendingUserId
      }));
      console.log("📤 Sent accept_no_initiator_verification message");
    } else {
      console.warn("⚠️ WebSocket is not open or pending_user_id missing");
    }
  };

  // Handle no-initiator rejection acceptance
  const handleNoInitiatorRejection = () => {
    if (ws.current?.readyState === WebSocket.OPEN && pendingUserId) {
      ws.current.send(JSON.stringify({ 
        type: "accept_no_initiator_rejection", 
        user_email, 
        pending_user_id: pendingUserId 
      }));
      console.log("📤 Sent accept_no_initiator_rejection message");
    } else {
      console.warn("⚠️ WebSocket is not open or pending_user_id missing");
    }
  };

  // Normal OK click (used after verified in initiator scenario)
  const handleOkClick = () => {
    if (ws.current?.readyState === WebSocket.OPEN && notificationId) {
      ws.current.send(JSON.stringify({ type: "accept_verification", user_email, notificationId }));
      console.log("📤 Sent accept_verification message");
    } else {
      console.warn("⚠️ WebSocket is not open or notificationId missing");
    }

    if (user_email) {
      dispatch(login({ user_email }));
    }
    navigate("/landing");
  };

  // Handle rejection for regular users
  const handleAcceptRejection = () => {
    if (ws.current?.readyState === WebSocket.OPEN && notificationId) {
      ws.current.send(JSON.stringify({ type: "accept_rejection", user_email, notificationId }));
      console.log("📤 Sent accept_rejection message");
      navigate("/login");
    } else {
      console.warn("⚠️ WebSocket is not open or notificationId missing");
    }
  };

  const handlePhoneNumberUpdated = () => {
    console.log("Phone number updated successfully");
  };

  const getStatusMessage = () => {
    // For no-initiator with claimed status, show custom message with admin name
    if (noInitiator && status === "claimed" && claimedByName) {
      return {
        icon: "👀",
        message: `Your application is being reviewed by ${claimedByName}.`
      };
    }
    
    // For verification failed scenario
    if (status === "verification_failed") {
      return {
        icon: "❌",
        message: "Verification failed. Please contact support."
      };
    }
    
    return statusMessages[status] || statusMessages.default;
  };

  // Determine if delete button should be visible
  const shouldShowDeleteButton = () => {
    // Only show in initiator flow (not no-initiator)
    if (noInitiator) return false;
    
    // Only show when status is pending/waiting
    const pendingStatuses = [
      "sent", 
      "not_viewed", 
      "reacted_pending", 
      "initiator_offline",
      "default"
    ];
    
    return pendingStatuses.includes(status) && !isDeleting;
  };

  const { icon, message } = getStatusMessage();

  // Determine which buttons to show
  const showVerifiedButton = status === "verified";
  const showRejectedButton = status === "rejected";
  const showDeleteButton = shouldShowDeleteButton();

  return (
    <div className="waiting-page-container">
      <div className="waiting-page-content">
        {/* Main Status Card */}
        <div className="waiting-page-message-box">
          <span className="waiting-page-status-icon">{icon}</span>
          <p className="waiting-page-text">{message}</p>

          {/* Show rejection reason if available */}
          {status === "rejected" && rejectionReason && (
            <div className="rejection-reason">
              <p><strong>Reason:</strong> {rejectionReason}</p>
            </div>
          )}

          {/* Show phone form only when not verified/rejected and in no-initiator flow */}
          {showPhoneForm && noInitiator && status !== "verified" && status !== "rejected" && (
            <div className="phone-form-section">
              <PhoneNumberForm 
                userEmail={user_email} 
                onPhoneNumberUpdated={handlePhoneNumberUpdated}
              />
            </div>
          )}

          {/* OK Button for verified status in normal initiator workflow */}
          {showVerifiedButton && !noInitiator && (
            <button className="waiting-page-button" onClick={handleOkClick}>OK</button>
          )}

          {/* OK Button for verified status in noInitiator workflow */}
          {showVerifiedButton && noInitiator && (
            <button className="waiting-page-button" onClick={handleNoInitiatorVerification}>OK</button>
          )}

          {/* Rejection button for no-initiator users */}
          {showRejectedButton && noInitiator && (
            <button className="waiting-page-button" onClick={handleNoInitiatorRejection}>
              Accept Rejection
            </button>
          )}

          {/* Rejection button for regular users */}
          {showRejectedButton && !noInitiator && (
            <button className="waiting-page-button" onClick={handleAcceptRejection}>
              Accept Rejection
            </button>
          )}

          {/* Show loading state while connecting */}
          {!status && (
            <div className="loading-state">
              <p>Connecting...</p>
            </div>
          )}
        </div>

        {/* Delete Registration Section - Fixed at bottom */}
        {showDeleteButton && (
          <div className="delete-registration-section">
            <div className="delete-info-text">
              <h3>Having issues with your registration?</h3>
              <p>
                If your initiator didn't receive your registration notification, 
                or if there's any other issue with the initiation process, 
                you can delete your current registration and reapply.
              </p>
            </div>
            <button 
              className="delete-registration-button" 
              onClick={() => setShowDeleteConfirmation(true)}
              disabled={isDeleting}
            >
              Delete Registration Request
            </button>
          </div>
        )}
      </div>

      {/* Delete Confirmation Popup */}
      {showDeleteConfirmation && (
        <div className="confirmation-overlay">
          <div className="confirmation-popup">
            <h3>Confirm Deletion</h3>
            <p>Are you sure you want to delete your registration request?</p>
            <p className="warning-text">
              This action cannot be undone. You will need to register again.
            </p>
            <div className="confirmation-buttons">
              <button 
                className="confirm-button" 
                onClick={handleDeleteRegistration}
                disabled={isDeleting}
              >
                {isDeleting ? "Deleting..." : "Yes, Delete"}
              </button>
              <button 
                className="cancel-button" 
                onClick={() => setShowDeleteConfirmation(false)}
                disabled={isDeleting}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default WaitingPage;