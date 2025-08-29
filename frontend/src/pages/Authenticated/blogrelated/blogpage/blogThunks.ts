import { createAsyncThunk } from '@reduxjs/toolkit';
import api from '../../../../api';
import { Blog, LikeActionResponse, ShareActionResponse } from './blogTypes';
import { setLoading, setBlogs, setError, updateBlog } from './blogSlice';

export const fetchBlogs = createAsyncThunk(
  'blogs/fetchBlogs',
  async (blogType: string, { dispatch }) => {
    try {
      dispatch(setLoading({ blogType, loading: true }));
      const response = await api.get<Blog[]>(`/api/blog/${blogType}-blogs/`);
      dispatch(setBlogs({ blogType, blogs: response.data }));
    } catch (err: any) {
      dispatch(setError({ blogType, error: err.message || 'Unknown error' }));
    }
  }
);

export const likeBlog = createAsyncThunk(
  'blogs/likeBlog',
  async ({ blogType, blogId }: { blogType: string; blogId: string }, { dispatch }) => {
    try {
      const response = await api.post<LikeActionResponse>(`/api/blog/blogs/${blogId}/like/`);
      dispatch(updateBlog({
        blogType,
        id: blogId,
        updates: {
          footer: {
            shares: response.data.action === 'added' ? [1] : [],
            has_shared: response.data.action === 'added',
            likes: [], // You may want to preserve previous likes if available
            relevant_count: [0], // Or preserve previous value
            irrelevant_count: [0], // Or preserve previous value
            comments: [], // Or preserve previous value
            has_liked: false // Or preserve previous value
          }
        }
      }));
    } catch (err: any) {
      console.error('Error liking blog:', err);
    }
  }
);

export const shareBlog = createAsyncThunk(
  'blogs/shareBlog',
  async ({ blogType, blogId }: { blogType: string; blogId: string }, { dispatch }) => {
    try {
      const response = await api.post<ShareActionResponse>(`/api/blog/blogs/${blogId}/share/`);
      dispatch(updateBlog({
        blogType,
        id: blogId,
        updates: {
          footer: {
            shares: response.data.action === 'added' ? [1] : [],
            has_shared: response.data.action === 'added',
            likes: [], // You may want to preserve previous likes if available
            relevant_count: [0], // Or preserve previous value
            irrelevant_count: [0], // Or preserve previous value
            comments: [], // Or preserve previous value
            has_liked: false // Or preserve previous value
          }
        }
      }));
      
      if (response.data.action === 'added') {
        alert('Blog shared successfully!');
      } else {
        alert('Blog unshared successfully!');
      }
    } catch (err: any) {
      console.error('Error sharing blog:', err);
      alert('Error sharing blog. Please try again.');
    }
  }
);