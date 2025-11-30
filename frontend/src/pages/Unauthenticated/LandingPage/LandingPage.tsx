import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useDispatch } from "react-redux";
import { useGoogleLogin } from "@react-oauth/google";
import GoogleButton from "react-google-button";
import { login } from "../../../login/login_logoutSlice";
import { connectWebSocket } from "../../Authenticated/flowpages/notificationpages/notification_state/notificationsThunk";
import axios from "axios";
import { config, getApiUrl } from "../config";
import "./LandingPage.css";

interface CodeResponse {
  code: string;
}

const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const [isLoading, setIsLoading] = useState(false);

  // Trigger login notification - returns a Promise
  const triggerLoginNotification = async (userId: string) => {
    console.log("Triggering login notification for user ID:", userId);
    try {
      const response = await axios.post(
        getApiUrl(config.endpoints.pushNotification),
        { user_id: userId },
        {
          withCredentials: true,
          headers: {
            "Content-Type": "application/json",
          },
        }
      );
      console.log("Login notification response:", response.data);
      return response.data;
    } catch (error: any) {
      console.error("Error triggering login notification:", error);
      throw error;
    }
  };

  // Handle Google OAuth success - same as LoginPage
  const handleSuccess = async (codeResponse: CodeResponse) => {
    setIsLoading(true);
    
    try {
      console.log("Google OAuth success, exchanging code for tokens");
      
      const response = await fetch(getApiUrl(config.endpoints.googleAuth), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({ code: codeResponse.code }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      const { user_type, user_email, user_id, name, profile_pic, no_initiator } = data;

      console.log("Auth response:", data);

      // Store commonly needed info
      localStorage.setItem("user_email", user_email);

      if (user_type === "olduser") {
        localStorage.setItem("user_id", user_id);
        localStorage.setItem("name", name || "");
        localStorage.setItem("profile_pic", profile_pic || "");
        localStorage.setItem("user_type", "olduser");
        
        dispatch(login({ user_email, name, profile_pic }));

        if (user_id) {
          dispatch(connectWebSocket(user_id) as any);
        }
        
        await triggerLoginNotification(user_id);
        
        // Navigate to heartbeat after successful authentication
        console.log("Landing auth successful, navigating to heartbeat");
        navigate("/app");
        
      } else if (user_type === "pendinguser") {
        localStorage.setItem("user_type", user_type);
        navigate("/waiting");
      } else if (user_type === "no_initiator" || no_initiator) {
        localStorage.setItem("user_type", "no_initiator");
        navigate("/waiting", { state: { noInitiator: true } });
      } else if (user_type === "newuser") {
        navigate("/register");
      }
    } catch (error) {
      console.error("Error exchanging authorization code:", error);
      setIsLoading(false);
    }
  };

  const googleLogin = useGoogleLogin({
    flow: "auth-code",
    onSuccess: handleSuccess,
    onError: (error) => {
      console.error("Google login error:", error);
      setIsLoading(false);
    },
  });

  return (
    <div className="landing-page-container">
      <div className="landing-page-content">
        {/* Header Section */}
        <div className="landing-page-header">
          <div className="logo-section">
            <h1 className="system-title">Public Funding System</h1>
          </div>
          <div className="welcome-section">
            <h2 className="welcome-title">Welcome!</h2>
            <p className="welcome-subtitle">
              Thank you for signing in and showing your support. 
              You are now part of a community dedicated to creating 
              a more equitable political landscape.
            </p>
          </div>
        </div>

        {/* Core Values Section */}
        <div className="values-section">
          <h3 className="values-title">Our Core Principles</h3>
          <div className="values-grid">
            <div className="value-card">
              <div className="value-icon">⚖️</div>
              <h4 className="value-name">Equal Representation</h4>
              <p className="value-description">
                Every voice matters equally in our democratic process
              </p>
            </div>
            
            <div className="value-card">
              <div className="value-icon">🗳️</div>
              <h4 className="value-name">Equal Political Participation</h4>
              <p className="value-description">
                Ensuring everyone has the opportunity to engage in politics
              </p>
            </div>
            
            <div className="value-card">
              <div className="value-icon">📢</div>
              <h4 className="value-name">Equal Influence</h4>
              <p className="value-description">
                Balancing political power across all segments of society
              </p>
            </div>
            
            <div className="value-card">
              <div className="value-icon">🏛️</div>
              <h4 className="value-name">Equal Political Status</h4>
              <p className="value-description">
                Creating a level playing field in political representation
              </p>
            </div>
          </div>
        </div>

        {/* Action Section */}
        <div className="action-section">
          <div className="action-content">
            <p className="action-text">
              Join us in building a system where democracy works for everyone, 
              not just the privileged few.
            </p>
            
            <div className="google-button-section">
              <p className="google-button-text">
                Sign in with your Google account to continue
              </p>
              <div className="google-button-wrapper">
                <GoogleButton 
                  onClick={() => googleLogin()} 
                  label="Sign in with Google"
                  disabled={isLoading}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Loading state */}
        {isLoading && (
          <div className="landing-page-loading">
            <p>Setting up your account...</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default LandingPage;