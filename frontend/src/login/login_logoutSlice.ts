import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface UserState {
    isLoggedIn: boolean;
    user_email: string;
    name?: string;
    profile_pic?: string;
}

interface LoginPayload {
    user_email: string;
    name?: string;
    profile_pic?: string;
}

const initialState: UserState = {
    isLoggedIn: false,
    user_email: '',
    name: '',
    profile_pic: undefined
};

const userSlice = createSlice({
    name: 'user',
    initialState,
    reducers: {
        login: (state, action: PayloadAction<LoginPayload>) => {
            state.isLoggedIn = true;
            state.user_email = action.payload.user_email;
            state.name = action.payload.name;
            state.profile_pic = action.payload.profile_pic;
        },
        logout: (state) => {
            state.isLoggedIn = false;
            state.user_email = '';
            state.name = undefined;
            state.profile_pic = undefined;
        },
    },
});

export const { login, logout } = userSlice.actions;
export default userSlice.reducer;