import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface UserState {
    isLoggedIn: boolean;
    user_email: string;
}

const initialState: UserState = {
    isLoggedIn: false,
    user_email: '',
};

const userSlice = createSlice({
    name: 'user',
    initialState,
    reducers: {
        login: (state, action: PayloadAction<{ user_email: string }>) => {
            state.isLoggedIn = true;
            state.user_email = action.payload.user_email;
        },
        logout: (state) => {
            state.isLoggedIn = false;
            state.user_email = '';
        },
    },
});


export const { login, logout } = userSlice.actions;
export default userSlice.reducer;
