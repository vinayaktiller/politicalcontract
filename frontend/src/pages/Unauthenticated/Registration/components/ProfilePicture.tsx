import React, { useRef, useState } from 'react';
import ReactCrop, { Crop } from 'react-image-crop';
import { FormStepProps } from '../types/registrationTypes';
import 'react-image-crop/dist/ReactCrop.css';

const ProfilePicture: React.FC<FormStepProps> = ({
  setFormData,
  nextStep,
  prevStep,
}) => {
  const [src, setSrc] = useState<string | null>(null);
  const [crop, setCrop] = useState<Crop>({
    unit: '%',
    width: 30,
    height: 33,
    x: 10,
    y: 10
  });
  const [croppedImage, setCroppedImage] = useState<string | null>(null);
  const imgRef = useRef<HTMLImageElement | null>(null);

  const onSelectFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.length) {
      const reader = new FileReader();
      reader.addEventListener('load', () => setSrc(reader.result as string));
      reader.readAsDataURL(e.target.files[0]);
    }
  };

  const getCroppedImg = () => {
    if (!imgRef.current) return;

    const image = imgRef.current;
    const canvas = document.createElement('canvas');
    const scaleX = image.naturalWidth / image.width;
    const scaleY = image.naturalHeight / image.height;
    canvas.width = crop.width || 0;
    canvas.height = crop.height || 0;
    const ctx = canvas.getContext('2d');

    if (ctx && crop.width && crop.height) {
      ctx.drawImage(
        image,
        (crop.x || 0) * scaleX,
        (crop.y || 0) * scaleY,
        crop.width * scaleX,
        crop.height * scaleY,
        0,
        0,
        crop.width,
        crop.height
      );

      setCroppedImage(canvas.toDataURL('image/jpeg'));
    }
  };

  const handleUpload = async () => {
    if (croppedImage) {
      const blob = await fetch(croppedImage).then(res => res.blob());
      const file = new File([blob], 'profile.jpg', { type: 'image/jpeg' });
      setFormData(prev => ({ ...prev, profile_picture: file }));
      nextStep();
    }
  };

  return (
    <div className="form-step">
      <h2>Profile Picture</h2>

      {/* Cropped Image Preview on Top */}
      {croppedImage && (
        <div className="preview" style={{ textAlign: 'center', marginBottom: '1rem' }}>
          <h3>Cropped Preview</h3>
          <img src={croppedImage} alt="Cropped preview" style={{ maxWidth: '100%', borderRadius: '5px', border: '2px solid #ccc' }} />
        </div>
      )}

      <div className="form-group">
        <label>Upload Profile Picture</label>
        <input type="file" accept="image/*" onChange={onSelectFile} />

        {src && (
          <div className="image-editor">
            <ReactCrop crop={crop} onChange={c => setCrop(c)} onComplete={getCroppedImg}>
              <img ref={imgRef} src={src} alt="Crop me" style={{ maxWidth: '100%' }} />
            </ReactCrop>
          </div>
        )}
      </div>

      <div className="form-navigation">
        <button type="button" onClick={prevStep} className="btn-secondary">
          Previous
        </button>
        <button type="button" onClick={handleUpload} className="btn-primary" disabled={!croppedImage}>
          Save & Continue
        </button>
      </div>
    </div>
  );

};

export default ProfilePicture;
