import React, { useEffect, useState, useRef, useCallback } from "react";
import { useDispatch } from "react-redux";
import { useNavigate } from "react-router-dom";
import { closeCelebration } from "./celebrationSlice";
import confetti from "canvas-confetti";
import { config } from "../../../Unauthenticated/config";
import "./CelebrationModal.css";

interface CelebrationModalProps {
  data: any;
}

const CelebrationModal: React.FC<CelebrationModalProps> = ({ data }) => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const [imageUrl, setImageUrl] = useState<string>("");
  const [isVisible, setIsVisible] = useState(true);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);
  const [isClosing, setIsClosing] = useState(false);
  const timeoutRefs = useRef<NodeJS.Timeout[]>([]);
  const animationFrameRef = useRef<number | null>(null);

  const FRONTEND_BASE_URL = config.FRONTEND_BASE_URL;

  // Cleanup function
  const cleanup = useCallback(() => {
    // Clear all timeouts
    timeoutRefs.current.forEach((timeout) => clearTimeout(timeout));
    timeoutRefs.current = [];
    
    // Cancel animation frame
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    
    // Clear canvas
    if (canvasRef.current) {
      const ctx = canvasRef.current.getContext('2d');
      if (ctx) {
        ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
      }
    }
  }, []);

  // Set image URL
  useEffect(() => {
    if (data?.photo_url) {
      setImageUrl(data.photo_url);
    } else if (data?.type && data?.photo_id) {
      setImageUrl(`${FRONTEND_BASE_URL}/${data.type}/${data.photo_id}.jpg`);
    } else {
      setImageUrl(`${FRONTEND_BASE_URL}/initiation/1.jpg`);
    }
  }, [data, FRONTEND_BASE_URL]);

  // Confetti effect
  useEffect(() => {
    if (!canvasRef.current || !isVisible) return;

    const confettiInstance = confetti.create(canvasRef.current, {
      resize: true,
      useWorker: false,
    });

    cleanup(); // Clear previous timers

    // Fire confetti in sequence
    const timers = [
      setTimeout(() => {
        confettiInstance({
          particleCount: 150,
          angle: 60,
          spread: 55,
          origin: { x: 0.1, y: 0.8 },
          colors: ["#ff0000", "#ff8c00", "#ffff00"],
        });
      }, 300),
      
      setTimeout(() => {
        confettiInstance({
          particleCount: 150,
          angle: 120,
          spread: 55,
          origin: { x: 0.9, y: 0.8 },
          colors: ["#00ff00", "#00ffff", "#0000ff"],
        });
      }, 600),
      
      setTimeout(() => {
        confettiInstance({
          particleCount: 200,
          spread: 100,
          origin: { x: 0.5, y: 0.1 },
          colors: ["#ff00ff", "#ffff00", "#ff8c00"],
        });
      }, 900),
      
      setTimeout(() => {
        confettiInstance({
          particleCount: 300,
          spread: 120,
          origin: { y: 0.6 },
          colors: [
            "#ff0000",
            "#ff8c00",
            "#ffff00",
            "#00ff00",
            "#00ffff",
            "#0000ff",
            "#ff00ff",
          ],
        });
      }, 1200),
    ];

    timeoutRefs.current = timers;

    // Start closing sequence after 5 seconds
    const closeTimer = setTimeout(() => {
      handleClose();
    }, 5000);

    timers.push(closeTimer);

    return cleanup;
  }, [cleanup, isVisible]);

  const handleClose = useCallback(() => {
    if (!isVisible) return;
    
    setIsClosing(true);
    setIsVisible(false);
    
    // Give time for fly-out animation
    setTimeout(() => {
      cleanup();
      dispatch(closeCelebration());
      
      // Navigate to milestones page with highlight
      if (data?.id) {
        navigate(`/milestones?highlight=${data.id}`, {
          state: {
            fromCelebration: true,
            celebrationData: data,
          },
          replace: true // Use replace to prevent going back to modal
        });
      } else {
        // Fallback navigation if no data
        navigate('/milestones', { replace: true });
      }
    }, 500);
  }, [cleanup, dispatch, navigate, data, isVisible]);

  // Handle image error
  const handleImageError = useCallback(() => {
    setImageUrl(`${FRONTEND_BASE_URL}/initiation/1.jpg`);
  }, [FRONTEND_BASE_URL]);

  // Force close after max time (safety net)
  useEffect(() => {
    const forceCloseTimer = setTimeout(() => {
      if (isVisible) {
        console.warn('Force closing celebration modal after timeout');
        handleClose();
      }
    }, 10000); // 10 seconds max

    return () => clearTimeout(forceCloseTimer);
  }, [isVisible, handleClose]);

  if (!isVisible) return null;

  return (
    <div className="celebration-modal">
      <div className="celebration-backdrop" onClick={handleClose} />
      <div className="celebration-content">
        <h2 className="celebration-title">{data?.title || "Milestone Achieved!"}</h2>
        <div className="milestone-image-container">
          <img
            ref={imgRef}
            src={imageUrl}
            alt={data?.title || "Milestone"}
            className={`milestone-photo ${isClosing ? "fly-out" : ""}`}
            onError={handleImageError}
            draggable={false}
          />
        </div>
        <button 
          className="celebration-close-button"
          onClick={handleClose}
          aria-label="Close celebration"
        >
          ✕
        </button>
      </div>
      <canvas ref={canvasRef} className="celebration-canvas" />
    </div>
  );
};

export default CelebrationModal;