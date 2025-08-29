// blogSlice.ts
import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { Blog, BlogsSliceState } from "./blogTypes";

const initialState: BlogsSliceState = {
  blogs: {},
  status: "idle",
  error: null,
};

const blogSlice = createSlice({
  name: "blogs",
  initialState,
  reducers: {
    setLoading: (
      state,
      action: PayloadAction<{ blogType: string; loading: boolean }>
    ) => {
      if (!state.blogs[action.payload.blogType]) {
        state.blogs[action.payload.blogType] = {
          blogs: [],
          loading: false,
          error: null,
        };
      }
      state.blogs[action.payload.blogType].loading = action.payload.loading;
    },
    setBlogs: (
      state,
      action: PayloadAction<{ blogType: string; blogs: Blog[] }>
    ) => {
      if (!state.blogs[action.payload.blogType]) {
        state.blogs[action.payload.blogType] = {
          blogs: [],
          loading: false,
          error: null,
        };
      }
      state.blogs[action.payload.blogType].blogs = action.payload.blogs;
      state.blogs[action.payload.blogType].error = null;
      state.status = "succeeded";
    },
    setError: (
      state,
      action: PayloadAction<{ blogType: string; error: string }>
    ) => {
      if (!state.blogs[action.payload.blogType]) {
        state.blogs[action.payload.blogType] = {
          blogs: [],
          loading: false,
          error: null,
        };
      }
      state.blogs[action.payload.blogType].error = action.payload.error;
      state.blogs[action.payload.blogType].blogs = [];
      state.status = "failed";
    },
    updateBlog: (
      state,
      action: PayloadAction<{
        blogType: string;
        id: string;
        updates: Partial<Blog>;
      }>
    ) => {
      const { blogType, id, updates } = action.payload;
      if (state.blogs[blogType]) {
        const index = state.blogs[blogType].blogs.findIndex(
          (blog) => blog.id === id
        );
        if (index !== -1) {
          const existing = state.blogs[blogType].blogs[index];
          state.blogs[blogType].blogs[index] = {
            ...existing,
            ...updates,
            footer: {
              ...existing.footer,
              ...updates.footer, // ✅ merge footer updates instead of replacing
            },
          };
        }
      }
    },
    addBlog: (
      state,
      action: PayloadAction<{ blogType: string; blog: Blog }>
    ) => {
      const { blogType, blog } = action.payload;
      if (!state.blogs[blogType]) {
        state.blogs[blogType] = {
          blogs: [],
          loading: false,
          error: null,
        };
      }
      state.blogs[blogType].blogs.unshift(blog);
    },
  },
});

export const { setLoading, setBlogs, setError, updateBlog, addBlog } =
  blogSlice.actions;
export default blogSlice.reducer;
