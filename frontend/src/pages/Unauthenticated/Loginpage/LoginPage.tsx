// LoginPage.tsx
import React from "react";
import GoogleButton from "react-google-button";
import { useNavigate } from "react-router-dom";
import { useGoogleLogin } from "@react-oauth/google";
import { useDispatch } from "react-redux";
import { login } from "../../../login/login_logoutSlice";
import { connectWebSocket } from "../../Authenticated/flowpages/notificationpages/notification_state/notificationsThunk";
import api from "../../../api";
import "./login.css";
import axios from "axios";
import handleLogout from "../../../login/logout";

interface CodeResponse {
  code: string;
}

const BASE_URL = "http://127.0.0.1:8000";

const LoginPage: React.FC = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();

  // Trigger login notification - returns a Promise
  const triggerLoginNotification = async (userId: string) => {
    console.log("Triggering login notification for user ID:", userId);
    try {
      const response = await axios.post(
        `${BASE_URL}/api/users/push-notification/login/`,
        { user_id: userId },
        {
          withCredentials: true,
          headers: {
            "Content-Type": "application/json",
          },
        }
      );
      console.log("Login notification response:", response.data);
      navigate("/heartbeat");
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 401) {
        handleLogout();
        window.location.reload();
      } else {
        console.error("Error triggering login notification:", error);
      }
      throw error;
    }
  };

  // Handle Google OAuth success, logic for each user type
  const handleSuccess = async (codeResponse: CodeResponse) => {
    try {
      const response = await fetch(`${BASE_URL}/api/users/auth/google/`, {
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

      // Store commonly needed info
      localStorage.setItem("user_email", user_email);

      if (user_type === "olduser") {
        localStorage.setItem("user_id", user_id);
        localStorage.setItem("name", name || "");
        localStorage.setItem("profile_pic", profile_pic || "");
        dispatch(login({ user_email, name, profile_pic }));

        if (user_id) {
          dispatch(connectWebSocket(user_id) as any);
        }
        await triggerLoginNotification(user_id);
        navigate("/heartbeat");
      } else if (user_type === "pendinguser") {
        localStorage.setItem("user_type", user_type);
        navigate("/waiting");
      } else if (user_type === "no_initiator" || no_initiator) {
        // Set extra flag and go to waiting page (pass state for phone form)
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
    onError: (error) => {
      console.error("Google login error:", error);
    },
  });

  const testCookieAuth = async () => {
    try {
      const response = await api.get("/api/users/test-cookie/");
      console.log("Cookie test response:", response.data);
    } catch (error) {
      console.error("Cookie test failed:", error);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <h1>
          Welcome to <span className="highlight">Political Contract</span>
        </h1>
        <p className="subtext">Login using your Google account</p>
        <div className="google-button-wrapper">
          <GoogleButton onClick={() => googleLogin()} label="Sign in with Google" />
        </div>
      </div>
      <button onClick={testCookieAuth} style={{ marginTop: "20px" }}>
        Test Cookie Authentication
      </button>
    </div>
  );
};

export default LoginPage;
