// import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
// import api from '../../../api';

// interface Blog {
//   id: string;
//   content: string;
//   base_blog: {
//     id: string;
//     userid: number;
//     likes: number[];
//     dislikes: number[];
//     relevant_count: number[];
//     irrelevant_count: number[];
//     shares: number[];
//     type: string;
//     created_at: string;
//     updated_at: string;
//   };
//   userid_details: {
//     id: number;
//     name: string;
//     profilepic_url: string | null;
//   } | null;
//   target_user_details: any;
//   my_journey: boolean;
//   blog_type: string;
// }

// interface JourneyBlogState {
//   blogs: Blog[];
//   status: 'idle' | 'loading' | 'succeeded' | 'failed';
//   error: string | null;
// }

// const initialState: JourneyBlogState = {
//   blogs: [],
//   status: 'idle',
//   error: null
// };

// export const fetchAllJourneyBlogs = createAsyncThunk(
//   'journeyBlogs/fetchAll',
//   async (_, { rejectWithValue }) => {
//     try {
//       const response = await api.get('/journey-blogs/');
//       return response.data;
//     } catch (err: any) {
//       return rejectWithValue(err.response?.data || 'Failed to fetch blogs');
//     }
//   }
// );

// export const createJourneyBlog = createAsyncThunk(
//   'journeyBlogs/create',
//   async (blogData: { content: string; type: string; target_user: number }, { rejectWithValue }) => {
//     try {
//       const response = await api.post('/journey-blogs/', {
//         content: blogData.content,
//         type: blogData.type,
//         target_user: blogData.target_user
//       });
//       return response.data;
//     } catch (err: any) {
//       return rejectWithValue(err.response?.data || 'Failed to create blog');
//     }
//   }
// );

// const journeyBlogSlice = createSlice({
//   name: 'journeyBlogs',
//   initialState,
//   reducers: {},
//   extraReducers: (builder) => {
//     builder
//       .addCase(fetchAllJourneyBlogs.pending, (state) => {
//         state.status = 'loading';
//       })
//       .addCase(fetchAllJourneyBlogs.fulfilled, (state, action) => {
//         state.status = 'succeeded';
//         state.blogs = action.payload;
//       })
//       .addCase(fetchAllJourneyBlogs.rejected, (state, action) => {
//         state.status = 'failed';
//         state.error = action.payload as string;
//       })
//       .addCase(createJourneyBlog.fulfilled, (state, action) => {
//         state.blogs.unshift(action.payload);
//       })
//       .addCase(createJourneyBlog.rejected, (state, action) => {
//         state.error = action.payload as string;
//       });
//   }
// });

// export default journeyBlogSlice.reducer;

export {}