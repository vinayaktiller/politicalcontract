import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';
import { Provider } from 'react-redux';
import { PersistGate } from 'redux-persist/integration/react';
import { store, persistor } from './store'; // Import your Redux store
import './polyfills';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  
    <Provider store={store}> {/* Wrap App with Redux Provider */}
      <PersistGate loading={null} persistor={persistor}> {/* Ensures persisted state loads */}
        <App />
      </PersistGate>
    </Provider>
  
);

// Measure performance if needed
reportWebVitals();
