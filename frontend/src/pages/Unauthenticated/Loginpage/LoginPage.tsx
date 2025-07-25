import React from "react";
import GoogleButton from "react-google-button";
import { useNavigate } from "react-router-dom";
import { useGoogleLogin } from "@react-oauth/google";
import { useDispatch } from "react-redux";
import { login } from "../../../login/login_logoutSlice";
import { connectWebSocket } from "../../Authenticated/flowpages/notificationpages/notification_state/notificationsThunk";
import api from "../../../api"; // Your Axios instance
import "./login.css"; // Import your CSS file for styling

interface CodeResponse {
  code: string;
}

const LoginPage: React.FC = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();

  console.log("LoginPage component is mounted!");
  console.log("Current route:", window.location.pathname);

  const BASE_URL = "http://127.0.0.1:8000"; // Backend API URL

  const handleSuccess = async (codeResponse: CodeResponse) => {
    try {
      const authorizationCode = codeResponse.code;
      console.log("Authorization code received:", authorizationCode);

      // Exchange authorization code for user details & tokens
      const response = await fetch(`${BASE_URL}/api/users/auth/google/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ code: authorizationCode }),
      });

      const data = await response.json();
      const { user_type, user_email, tokens, user_id, name, profile_pic } = data;

      if (user_type === "olduser") {
        localStorage.setItem("access_token", tokens.access);
        localStorage.setItem("refresh_token", tokens.refresh);
        localStorage.setItem("user_id", user_id);
        localStorage.setItem("user_email", user_email);
        localStorage.setItem("name", name);
        localStorage.setItem("profile_pic", profile_pic || ""); // Store profile picture URL


        dispatch(login({ user_email, name, profile_pic }));
        const userId = localStorage.getItem("user_id");
        if (userId) {
          dispatch(connectWebSocket(userId) as any);
        }

        // 🔔 Make API call to trigger push notification
        await triggerLoginNotification(tokens.access, user_id);


        navigate("/heartbeat");
        // window.location.reload();
      } else if (user_type === "pendinguser") {
        localStorage.setItem("user_type", user_type);
        localStorage.setItem("user_email", user_email);
        navigate("/waiting");
      } else if (user_type === "newuser") {
        localStorage.setItem("user_email", user_email);
        navigate("/register");
      }
    } catch (error) {
      console.error("Error exchanging authorization code:", error);
    }
  };

  // Define googleLogin using useGoogleLogin
  const googleLogin = useGoogleLogin({
    flow: "auth-code",
    onSuccess: handleSuccess,
    onError: (error) => {
      console.error("Google login error:", error);
    },
  });

  // 📢 Function to trigger push notification API call
  const triggerLoginNotification = async (accessToken: string, userId: string) => {
  try {
    const response = await api.post("/api/users/push-notification/login/", {
      user_id: userId, // 🔥 Sending user ID in the request body
    }, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
      },
    });

    console.log("Login notification response:", response.data);
  } catch (error) {
    console.error("Error triggering login notification:", error);
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
          <GoogleButton onClick={googleLogin} label="Sign in with Google" />
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
