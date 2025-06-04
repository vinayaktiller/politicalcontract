import React from 'react';
import { useSelector } from 'react-redux';
import { Navigate, Outlet } from 'react-router-dom';
import { RootState } from '../store'; // Adjust the import path based on your project structure

const ProtectedRoute: React.FC = () => {
  // Correctly type the `useSelector` to reference the Redux state
  const isAuthenticated = useSelector((state: RootState) => state.user.isLoggedIn);

  console.log('isAuthenticated:', isAuthenticated);

  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />;
};

export default ProtectedRoute;
