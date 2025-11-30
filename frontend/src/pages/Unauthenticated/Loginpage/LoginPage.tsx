import React, { useEffect } from "react";
import GoogleButton from "react-google-button";
import { useNavigate } from "react-router-dom";
import { useGoogleLogin } from "@react-oauth/google";
import { useDispatch } from "react-redux";
import { login } from "../../../login/login_logoutSlice";
import { connectWebSocket } from "../../Authenticated/flowpages/notificationpages/notification_state/notificationsThunk";
import api from "../../../api";
import axios from "axios";
import handleLogout from "../../../login/logout";
import { config, getApiUrl } from "../config";

import "./login.css";

interface CodeResponse {
  code: string;
}

const LoginPage: React.FC = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();

  // Auto-redirect pending users
  useEffect(() => {
    const userType = localStorage.getItem("user_type");
    if (userType === "pendinguser") navigate("/waiting");
    else if (userType === "no_initiator")
      navigate("/waiting", { state: { noInitiator: true } });
  }, [navigate]);

  // Trigger login notification
  const triggerLoginNotification = async (userId: string) => {
    try {
      const response = await axios.post(
        getApiUrl(config.endpoints.pushNotification),
        { user_id: userId },
        {
          withCredentials: true,
          headers: { "Content-Type": "application/json" },
        }
      );
      navigate("/app");
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 401) {
        handleLogout();
        window.location.reload();
      }
      throw error;
    }
  };

  // Handle Google OAuth
  const handleSuccess = async (codeResponse: CodeResponse) => {
    try {
      const response = await fetch(getApiUrl(config.endpoints.googleAuth), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ code: codeResponse.code }),
      });

      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

      const data = await response.json();
      const { user_type, user_email, user_id, name, profile_pic, no_initiator } = data;

      localStorage.setItem("user_email", user_email);

      if (user_type === "olduser") {
        localStorage.setItem("user_id", user_id);
        localStorage.setItem("name", name || "");
        localStorage.setItem("profile_pic", profile_pic || "");

        dispatch(login({ user_email, name, profile_pic }));
        if (user_id) dispatch(connectWebSocket(user_id) as any);

        await triggerLoginNotification(user_id);
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
    }
  };

  const googleLogin = useGoogleLogin({
    flow: "auth-code",
    onSuccess: handleSuccess,
    onError: (error) => console.error("Google login error:", error),
  });

  // TEMP: Check backend
  const checkBackend = async () => {
    try {
      const response = await fetch(getApiUrl("/"), { method: "GET" });
      const text = await response.text();
      alert(`Backend response: ${text}`);
    } catch (error) {
      alert("Error checking backend");
    }
  };

  return (
    <div className="login-page">
      <div className="login-content">
        
        <p className="welcome-text">Welcome to the petition website of</p>

        <h1 className="main-title">PUBLIC FUNDING SYSTEM</h1>

        <p className="signin-text">Sign in with your Google account</p>

        <div className="google-wrapper">
          <GoogleButton onClick={() => googleLogin()} label="Sign in with Google" />
        </div>

        {/* TEMP */}
        <button onClick={checkBackend} className="backend-btn">
          Check Backend
        </button>
      </div>

      {/* LOGO + FOOTER */}
      <div className="footer-section">
        <img
          src="https://pfs-ui-f7bnfbg9agb4cwcu.canadacentral-01.azurewebsites.net/logo100.png"
          alt="PFS Logo"
          className="footer-logo"
        />
        <div className="footer-text">
          for equal ownership on political parties and democracy
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
