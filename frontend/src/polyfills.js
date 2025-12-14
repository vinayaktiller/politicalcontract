// src/polyfills.js
import 'core-js/stable';
import 'regenerator-runtime/runtime';

// Mobile Safari in Private Browsing Mode
if (typeof window.sessionStorage === 'undefined') {
  Object.defineProperty(window, 'sessionStorage', {
    value: (function() {
      var data = {};
      return {
        setItem: function(key, val) {
          data[key] = String(val);
        },
        getItem: function(key) {
          return data[key];
        },
        removeItem: function(key) {
          delete data[key];
        },
        clear: function() {
          data = {};
        },
        key: function(i) {
          var keys = Object.keys(data);
          return keys[i] || null;
        },
        get length() {
          return Object.keys(data).length;
        }
      };
    })()
  });
}

// Mobile cookie fallback
if (!document.cookie && window.localStorage) {
  Object.defineProperty(document, 'cookie', {
    get: function() {
      return window.localStorage.getItem('cookieFallback') || '';
    },
    set: function(val) {
      window.localStorage.setItem('cookieFallback', val);
    }
  });
}