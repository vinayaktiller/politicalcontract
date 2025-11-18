import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { Blog, BlogsSliceState, Comment } from "./blogTypes";

const initialState: BlogsSliceState = {
  blogs: {},
  status: "idle",
  error: null,
};

const blogSlice = createSlice({
  name: "blogs",
  initialState,
  reducers: {
    // Add this new action to clear all blog data
    clearBlogs: (state) => {
      state.blogs = {};
      state.status = "idle";
      state.error = null;
    },
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
          
          // Handle nested updates properly
          const updatedBlog = {
            ...existing,
            ...updates,
            // Preserve nested structures if not provided in updates
            header: updates.header ? { ...existing.header, ...updates.header } : existing.header,
            body: updates.body ? { ...existing.body, ...updates.body } : existing.body,
            footer: updates.footer ? { ...existing.footer, ...updates.footer } : existing.footer,
            comments: updates.comments !== undefined ? updates.comments : existing.comments,
          };
          
          state.blogs[blogType].blogs[index] = updatedBlog;
        } else {
          // If blog doesn't exist in this type, add it
          state.blogs[blogType].blogs.push(updates as Blog);
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
      
      // Check if blog already exists to avoid duplicates
      const existingIndex = state.blogs[blogType].blogs.findIndex(
        b => b.id === blog.id
      );
      
      if (existingIndex === -1) {
        // Add new blog at the beginning of the list
        state.blogs[blogType].blogs.unshift(blog);
      } else {
        // Update existing blog
        state.blogs[blogType].blogs[existingIndex] = blog;
      }
      
      console.log('Added blog to store:', blogType, blog.id);
    },
    // ✅ NEW: Add shared blog handler
    addSharedBlog: (
      state,
      action: PayloadAction<{ 
        blogType: string; 
        blog: Blog;
        sharedByUserId: string;
        originalAuthorId: string;
      }>
    ) => {
      const { blogType, blog, sharedByUserId, originalAuthorId } = action.payload;
      if (!state.blogs[blogType]) {
        state.blogs[blogType] = {
          blogs: [],
          loading: false,
          error: null,
        };
      }
      
      // Mark the blog as shared and add metadata
      const sharedBlog = {
        ...blog,
        is_shared: true,
        shared_by_user_id: sharedByUserId,
        original_author_id: originalAuthorId,
        // You can also modify the relation/header to show "X shared Y's post"
        header: {
          ...blog.header,
          relation: `shared by ${sharedByUserId}`,
          // Or modify author info to show both original author and sharer
        }
      };
      
      // Check if blog already exists to avoid duplicates
      const existingIndex = state.blogs[blogType].blogs.findIndex(
        b => b.id === blog.id
      );
      
      if (existingIndex === -1) {
        // Add shared blog at the beginning of the list
        state.blogs[blogType].blogs.unshift(sharedBlog);
      } else {
        // Update existing blog with share info
        state.blogs[blogType].blogs[existingIndex] = sharedBlog;
      }
      
      console.log('Added shared blog to store:', blogType, blog.id, 'shared by:', sharedByUserId);
    },
    // ✅ NEW: Remove shared blog handler
    removeSharedBlog: (
      state,
      action: PayloadAction<{ 
        blogType: string; 
        blogId: string;
        sharedByUserId: string;
      }>
    ) => {
      const { blogType, blogId, sharedByUserId } = action.payload;
      if (!state.blogs[blogType]) {
        return;
      }
      
      // Find the blog in the store
      const blogIndex = state.blogs[blogType].blogs.findIndex(
        b => b.id === blogId
      );
      
      if (blogIndex !== -1) {
        const blog = state.blogs[blogType].blogs[blogIndex];
        
        // Check if this is the same shared blog (same sharer)
        const blogAny = blog as any;
        if (blogAny.is_shared && blogAny.shared_by_user_id === sharedByUserId) {
          // Remove the blog from the list
          state.blogs[blogType].blogs.splice(blogIndex, 1);
          console.log('Removed shared blog from store:', blogType, blogId, 'unshared by:', sharedByUserId);
        } else {
          console.log('Blog found but not matching share criteria:', blogId);
        }
      } else {
        console.log('Blog not found in store for removal:', blogId);
      }
    },
    addComment: (
      state,
      action: PayloadAction<{
        blogType: string;
        blogId: string;
        comment: Comment;
      }>
    ) => {
      const { blogType, blogId, comment } = action.payload;
      if (state.blogs[blogType]) {
        const index = state.blogs[blogType].blogs.findIndex(
          (blog) => blog.id === blogId
        );
        if (index !== -1) {
          // Check if comment already exists to avoid duplicates
          const existingCommentIndex = state.blogs[blogType].blogs[index].comments.findIndex(
            c => c.id === comment.id
          );
          if (existingCommentIndex === -1) {
            state.blogs[blogType].blogs[index].comments.push(comment);
          } else {
            // If comment already exists, update it
            state.blogs[blogType].blogs[index].comments[existingCommentIndex] = comment;
          }
          state.blogs[blogType].blogs[index].footer.comments = 
            state.blogs[blogType].blogs[index].comments.map(c => c.id);
        }
      }
    },
    updateComment: (
      state,
      action: PayloadAction<{
        blogType: string;
        blogId: string;
        commentId: string;
        updates: Partial<Comment>;
      }>
    ) => {
      const { blogType, blogId, commentId, updates } = action.payload;
      if (state.blogs[blogType]) {
        const blogIndex = state.blogs[blogType].blogs.findIndex(
          (blog) => blog.id === blogId
        );
        if (blogIndex !== -1) {
          const updateCommentInTree = (comments: Comment[]): Comment[] => {
            return comments.map((comment) => {
              if (comment.id === commentId) {
                return { ...comment, ...updates };
              }
              if (comment.replies && comment.replies.length > 0) {
                return {
                  ...comment,
                  replies: updateCommentInTree(comment.replies),
                };
              }
              return comment;
            });
          };

          state.blogs[blogType].blogs[blogIndex].comments =
            updateCommentInTree(state.blogs[blogType].blogs[blogIndex].comments);
        }
      }
    },
    addReplyToComment: (
      state,
      action: PayloadAction<{
        blogType: string;
        blogId: string;
        commentId: string;
        reply: Comment;
      }>
    ) => {
      const { blogType, blogId, commentId, reply } = action.payload;
      if (state.blogs[blogType]) {
        const blogIndex = state.blogs[blogType].blogs.findIndex(
          (blog) => blog.id === blogId
        );
        if (blogIndex !== -1) {
          const addReplyToCommentInTree = (comments: Comment[]): Comment[] => {
            return comments.map((comment) => {
              if (comment.id === commentId) {
                return {
                  ...comment,
                  replies: [...(comment.replies || []), reply],
                };
              }
              if (comment.replies && comment.replies.length > 0) {
                return {
                  ...comment,
                  replies: addReplyToCommentInTree(comment.replies),
                };
              }
              return comment;
            });
          };

          state.blogs[blogType].blogs[blogIndex].comments =
            addReplyToCommentInTree(state.blogs[blogType].blogs[blogIndex].comments);
        }
      }
    },
    setReplyingState: (
      state,
      action: PayloadAction<{
        blogType: string;
        blogId: string;
        commentId: string;
        isReplying: boolean;
      }>
    ) => {
      const { blogType, blogId, commentId, isReplying } = action.payload;
      if (state.blogs[blogType]) {
        const blogIndex = state.blogs[blogType].blogs.findIndex(
          (blog) => blog.id === blogId
        );
        if (blogIndex !== -1) {
          const setReplyingInTree = (comments: Comment[]): Comment[] => {
            return comments.map((comment) => {
              if (comment.id === commentId) {
                return { ...comment, is_replying: isReplying };
              }
              if (comment.replies && comment.replies.length > 0) {
                return {
                  ...comment,
                  replies: setReplyingInTree(comment.replies),
                };
              }
              return comment;
            });
          };

          state.blogs[blogType].blogs[blogIndex].comments =
            setReplyingInTree(state.blogs[blogType].blogs[blogIndex].comments);
        }
      }
    },
    setReplyText: (
      state,
      action: PayloadAction<{
        blogType: string;
        blogId: string;
        commentId: string;
        text: string;
      }>
    ) => {
      const { blogType, blogId, commentId, text } = action.payload;
      if (state.blogs[blogType]) {
        const blogIndex = state.blogs[blogType].blogs.findIndex(
          (blog) => blog.id === blogId
        );
        if (blogIndex !== -1) {
          const setReplyTextInTree = (comments: Comment[]): Comment[] => {
            return comments.map((comment) => {
              if (comment.id === commentId) {
                return { ...comment, reply_text: text };
              }
              if (comment.replies && comment.replies.length > 0) {
                return {
                  ...comment,
                  replies: setReplyTextInTree(comment.replies),
                };
              }
              return comment;
            });
          };

          state.blogs[blogType].blogs[blogIndex].comments =
            setReplyTextInTree(state.blogs[blogType].blogs[blogIndex].comments);
        }
      }
    },
    removeTempComment: (
      state,
      action: PayloadAction<{
        blogType: string;
        blogId: string;
        tempCommentId: string;
      }>
    ) => {
      const { blogType, blogId, tempCommentId } = action.payload;
      if (state.blogs[blogType]) {
        const index = state.blogs[blogType].blogs.findIndex(
          (blog) => blog.id === blogId
        );
        if (index !== -1) {
          state.blogs[blogType].blogs[index].comments = 
            state.blogs[blogType].blogs[index].comments.filter(
              comment => comment.id !== tempCommentId
            );
        }
      }
    },
  },
});

export const {
  clearBlogs,
  setLoading,
  setBlogs,
  setError,
  updateBlog,
  addBlog,
  addSharedBlog,
  removeSharedBlog, // Export the new action
  addComment,
  updateComment,
  removeTempComment,
  addReplyToComment,
  setReplyingState,
  setReplyText,
} = blogSlice.actions;

export default blogSlice.reducer;