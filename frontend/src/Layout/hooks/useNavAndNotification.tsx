import { useReducer, useEffect, useCallback } from 'react';

type State = {
  isNavVisible: boolean;
  butIsNavVisible: boolean;
  isNotificationsVisible: boolean;
  butIsNotificationsVisible: boolean;
};

type Action = 
  | { type: 'SHOW_NAV'; butIsNotificationsVisible?: boolean }
  | { type: 'HIDE_NAV'; butIsNotificationsVisible?: boolean }
  | { type: 'TOGGLE_NAV' }
  | { type: 'SHOW_NOTIFICATIONS'; butIsNavVisible?: boolean }
  | { type: 'HIDE_NOTIFICATIONS'; butIsNavVisible?: boolean }
  | { type: 'TOGGLE_NOTIFICATIONS' };

const initialState: State = {
  isNavVisible: false,
  butIsNavVisible: false,
  isNotificationsVisible: false,
  butIsNotificationsVisible: false,
};

const reducer = (state: State, action: Action): State => {
  switch (action.type) {
    case 'SHOW_NAV':
      return {
        ...state,
        isNavVisible: true,
        butIsNotificationsVisible: action.butIsNotificationsVisible ?? state.butIsNotificationsVisible,
      };
    case 'HIDE_NAV':
      return {
        ...state,
        isNavVisible: false,
        butIsNotificationsVisible: action.butIsNotificationsVisible ?? state.butIsNotificationsVisible,
      };
    case 'TOGGLE_NAV':
      return {
        ...state,
        isNavVisible: !state.isNavVisible,
        butIsNavVisible: !state.butIsNavVisible,
      };
    case 'SHOW_NOTIFICATIONS':
      return {
        ...state,
        isNotificationsVisible: true,
        butIsNavVisible: action.butIsNavVisible ?? state.butIsNavVisible,
      };
    case 'HIDE_NOTIFICATIONS':
      return {
        ...state,
        isNotificationsVisible: false,
        butIsNavVisible: action.butIsNavVisible ?? state.butIsNavVisible,
      };
    case 'TOGGLE_NOTIFICATIONS':
      return {
        ...state,
        isNotificationsVisible: !state.isNotificationsVisible,
        butIsNotificationsVisible: !state.butIsNotificationsVisible,
      };
    default:
      return state;
  }
};

export const useNavAndNotification = () => {
  const [state, dispatch] = useReducer(reducer, initialState);

  const handleResize = useCallback(() => {
    const width = window.innerWidth;
    if (width >= 1200) {
      dispatch({ type: 'SHOW_NAV' });
      dispatch({ type: 'SHOW_NOTIFICATIONS' });
    } else if (width >= 600) {
      dispatch({ type: 'SHOW_NAV' });
      dispatch({ type: 'HIDE_NOTIFICATIONS' });
    } else {
      dispatch({ type: 'HIDE_NAV' });
      dispatch({ type: 'HIDE_NOTIFICATIONS' });
    }
  }, []);

  useEffect(() => {
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [handleResize]);

  const toggleNav = () => dispatch({ type: 'TOGGLE_NAV' });
  const toggleNotifications = () => dispatch({ type: 'TOGGLE_NOTIFICATIONS' });

  return { state, toggleNav, toggleNotifications };
};