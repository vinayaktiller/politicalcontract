import React, { useEffect, useState, useRef } from "react";
import { useDispatch } from "react-redux";
import { useNavigate } from "react-router-dom";
import { closeCelebration } from "./celebrationSlice";
import confetti from "canvas-confetti";
import "./CelebrationModal.css";

interface CelebrationModalProps {
  data: any; // Define proper interface if possible
}

const CelebrationModal: React.FC<CelebrationModalProps> = ({ data }) => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const [imageUrl, setImageUrl] = useState<string>("");
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);
  const [isClosing, setIsClosing] = useState(false);
  const timeoutRefs = useRef<NodeJS.Timeout[]>([]);

  useEffect(() => {
    if (data.photo_url) {
      setImageUrl(data.photo_url);
    } else if (data.type) {
      // setImageUrl(`http://localhost:3000/${data.type}/${data.photo_id}.jpg`);
      setImageUrl(`https://pfs-ui-f7bnfbg9agb4cwcu.canadacentral-01.azurewebsites.net/${data.type}/${data.photo_id}.jpg`);
    } else {
      setImageUrl("http://localhost:3000/initiation/1.jpg");
    }

    const fireConfetti = () => {
      if (!canvasRef.current) return;

      const confettiInstance = confetti.create(canvasRef.current, {
        resize: true,
        useWorker: false,
      });

      timeoutRefs.current.forEach((timeout) => clearTimeout(timeout));
      timeoutRefs.current = [];

      timeoutRefs.current.push(
        setTimeout(() => {
          confettiInstance({
            particleCount: 150,
            angle: 60,
            spread: 55,
            origin: { x: 0.1, y: 0.8 },
            colors: ["#ff0000", "#ff8c00", "#ffff00"],
          });
        }, 300)
      );

      timeoutRefs.current.push(
        setTimeout(() => {
          confettiInstance({
            particleCount: 150,
            angle: 120,
            spread: 55,
            origin: { x: 0.9, y: 0.8 },
            colors: ["#00ff00", "#00ffff", "#0000ff"],
          });
        }, 600)
      );

      timeoutRefs.current.push(
        setTimeout(() => {
          confettiInstance({
            particleCount: 200,
            spread: 100,
            origin: { x: 0.5, y: 0.1 },
            colors: ["#ff00ff", "#ffff00", "#ff8c00"],
          });
        }, 900)
      );

      timeoutRefs.current.push(
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
        }, 1200)
      );
    };

    fireConfetti();

    const timer = setTimeout(() => {
      setIsClosing(true);
      const currentImg = imgRef.current;
      if (currentImg) {
        const imgRect = currentImg.getBoundingClientRect();
        const targetElement = document.getElementById(`milestone-${data.id}`);
        const targetRect = targetElement?.getBoundingClientRect();
        const defaultRect = {
          top: window.innerHeight / 2,
          left: window.innerWidth / 2,
          width: 300,
          height: 300,
        };

        setTimeout(() => {
          dispatch(closeCelebration());
          navigate(`/milestones?highlight=${data.id}`, {
            state: {
              fromCelebration: true, // <-- Added flag here
              celebrationData: {
                ...data,
                startRect: imgRect,
                targetRect: targetRect || defaultRect,
                imageUrl,
              },
            },
          });
        }, 500);
      }
    }, 5000);

    return () => {
      clearTimeout(timer);
      timeoutRefs.current.forEach((timeout) => clearTimeout(timeout));
      if (canvasRef.current) {
        canvasRef.current.width = canvasRef.current.width;
      }
    };
  }, [dispatch, navigate, data, imageUrl]);

  const handleImageError = () => {
    setImageUrl("http://localhost:3000/initiation/1.jpg");
  };

  return (
    <div className="celebration-modal">
      <div className="celebration-backdrop" />
      <div className="celebration-content">
        <h2 className="celebration-title">{data.title}</h2>
        <div className="milestone-image-container">
          <img
            ref={imgRef}
            src={imageUrl}
            alt={data.title}
            className={`milestone-photo ${isClosing ? "fly-out" : ""}`}
            onError={handleImageError}
            draggable={false}
          />
        </div>
      </div>
      <canvas ref={canvasRef} className="celebration-canvas" />
    </div>
  );
};

export default CelebrationModal;
