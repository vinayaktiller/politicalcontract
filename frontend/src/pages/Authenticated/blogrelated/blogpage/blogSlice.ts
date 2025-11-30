import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { Blog, BlogsSliceState, Comment } from "./blogTypes";

const initialState: BlogsSliceState = {
  blogs: {},
  status: "idle",
  error: null,
  needsRefresh: {},
  scrollPositions: {},
  mainFetchDone: {},
};

const blogSlice = createSlice({
  name: "blogs",
  initialState,
  reducers: {
    // Enhanced clearBlogs action to ensure complete cleanup
    clearBlogs: (state) => {
      console.log('🧹 Clearing all blog data from store...');
      state.blogs = {};
      state.status = "idle";
      state.error = null;
      state.needsRefresh = {};
      state.scrollPositions = {};
      state.mainFetchDone = {};
    },
    
    // Clear specific blog type data
    clearBlogsByType: (state, action: PayloadAction<{ blogType: string }>) => {
      const { blogType } = action.payload;
      if (state.blogs[blogType]) {
        console.log(`🧹 Clearing blog data for type: ${blogType}`);
        delete state.blogs[blogType];
      }
      if (state.needsRefresh[blogType]) {
        delete state.needsRefresh[blogType];
      }
      if (state.scrollPositions[blogType]) {
        delete state.scrollPositions[blogType];
      }
      if (state.mainFetchDone[blogType]) {
        delete state.mainFetchDone[blogType];
      }
    },

    // NEW: Mark main fetch as done for a blog type
    setMainFetchDone: (state, action: PayloadAction<{ blogType: string }>) => {
      state.mainFetchDone[action.payload.blogType] = true;
    },
    
    // NEW: Clear main fetch flag for a blog type
    clearMainFetchDone: (state, action: PayloadAction<{ blogType: string }>) => {
      state.mainFetchDone[action.payload.blogType] = false;
    },
    
    // NEW: Update scroll position for a blog type
    updateScrollPosition: (state, action: PayloadAction<{ blogType: string; position: number }>) => {
      const { blogType, position } = action.payload;
      state.scrollPositions[blogType] = position;
    },
    
    // NEW: Clear scroll position for a blog type
    clearScrollPosition: (state, action: PayloadAction<{ blogType: string }>) => {
      const { blogType } = action.payload;
      if (state.scrollPositions[blogType]) {
        delete state.scrollPositions[blogType];
      }
    },
    
    // NEW: Mark a blog type as needing refresh
    markNeedsRefresh: (state, action: PayloadAction<{ blogType: string }>) => {
      state.needsRefresh[action.payload.blogType] = true;
    },
    
    // NEW: Clear refresh flag for a blog type
    clearRefreshFlag: (state, action: PayloadAction<{ blogType: string }>) => {
      state.needsRefresh[action.payload.blogType] = false;
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
      // Clear refresh flag when blogs are successfully fetched
      state.needsRefresh[action.payload.blogType] = false;
      // Mark main fetch as done when blogs are successfully set
      state.mainFetchDone[action.payload.blogType] = true;
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
          (blog: Blog) => blog.id === id
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
        (b: Blog) => b.id === blog.id
      );
      
      if (existingIndex === -1) {
        // Add new blog at the beginning of the list
        state.blogs[blogType].blogs.unshift(blog);
        // Mark as needing refresh when new blog is added
        state.needsRefresh[blogType] = true;
      } else {
        // Update existing blog
        state.blogs[blogType].blogs[existingIndex] = blog;
      }
      
      console.log('Added blog to store:', blogType, blog.id);
    },
    
    // ✅ Add shared blog handler
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
      const sharedBlog: Blog = {
        ...blog,
        is_shared: true,
        shared_by_user_id: sharedByUserId,
        original_author_id: originalAuthorId,
        // You can also modify the relation/header to show "X shared Y's post"
        header: {
          ...blog.header,
          relation: `shared by ${sharedByUserId}`,
        }
      };
      
      // Check if blog already exists to avoid duplicates
      const existingIndex = state.blogs[blogType].blogs.findIndex(
        (b: Blog) => b.id === blog.id
      );
      
      if (existingIndex === -1) {
        // Add shared blog at the beginning of the list
        state.blogs[blogType].blogs.unshift(sharedBlog);
        // Mark as needing refresh when shared blog is added
        state.needsRefresh[blogType] = true;
      } else {
        // Update existing blog with share info
        state.blogs[blogType].blogs[existingIndex] = sharedBlog;
      }
      
      console.log('Added shared blog to store:', blogType, blog.id, 'shared by:', sharedByUserId);
    },
    
    // ✅ Remove shared blog handler
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
        (b: Blog) => b.id === blogId
      );
      
      if (blogIndex !== -1) {
        const blog = state.blogs[blogType].blogs[blogIndex];
        
        // Check if this is the same shared blog (same sharer)
        if (blog.is_shared && blog.shared_by_user_id === sharedByUserId) {
          // Remove the blog from the list
          state.blogs[blogType].blogs.splice(blogIndex, 1);
          // Mark as needing refresh when shared blog is removed
          state.needsRefresh[blogType] = true;
          console.log('Removed shared blog from store:', blogType, blogId, 'unshared by:', sharedByUserId);
        } else {
          console.log('Blog found but not matching share criteria:', blogId);
        }
      } else {
        console.log('Blog not found in store for removal:', blogId);
      }
    },
    
    // ✅ Remove blog completely (for deleted_blogs)
    removeBlog: (
      state,
      action: PayloadAction<{ 
        blogType: string; 
        blogId: string;
      }>
    ) => {
      const { blogType, blogId } = action.payload;
      if (!state.blogs[blogType]) {
        return;
      }
      
      // Find and remove the blog from the list
      const blogIndex = state.blogs[blogType].blogs.findIndex(
        (b: Blog) => b.id === blogId
      );
      
      if (blogIndex !== -1) {
        state.blogs[blogType].blogs.splice(blogIndex, 1);
        // Mark as needing refresh when blog is removed
        state.needsRefresh[blogType] = true;
        console.log('Removed blog from store:', blogType, blogId);
      } else {
        console.log('Blog not found in store for deletion:', blogId);
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
          (blog: Blog) => blog.id === blogId
        );
        if (index !== -1) {
          // Check if comment already exists to avoid duplicates
          const existingCommentIndex = state.blogs[blogType].blogs[index].comments.findIndex(
            (c: Comment) => c.id === comment.id
          );
          if (existingCommentIndex === -1) {
            state.blogs[blogType].blogs[index].comments.push(comment);
          } else {
            // If comment already exists, update it
            state.blogs[blogType].blogs[index].comments[existingCommentIndex] = comment;
          }
          state.blogs[blogType].blogs[index].footer.comments = 
            state.blogs[blogType].blogs[index].comments.map((c: Comment) => c.id);
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
          (blog: Blog) => blog.id === blogId
        );
        if (blogIndex !== -1) {
          const updateCommentInTree = (comments: Comment[]): Comment[] => {
            return comments.map((comment: Comment) => {
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
          (blog: Blog) => blog.id === blogId
        );
        if (blogIndex !== -1) {
          const addReplyToCommentInTree = (comments: Comment[]): Comment[] => {
            return comments.map((comment: Comment) => {
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
          (blog: Blog) => blog.id === blogId
        );
        if (blogIndex !== -1) {
          const setReplyingInTree = (comments: Comment[]): Comment[] => {
            return comments.map((comment: Comment) => {
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
          (blog: Blog) => blog.id === blogId
        );
        if (blogIndex !== -1) {
          const setReplyTextInTree = (comments: Comment[]): Comment[] => {
            return comments.map((comment: Comment) => {
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
          (blog: Blog) => blog.id === blogId
        );
        if (index !== -1) {
          state.blogs[blogType].blogs[index].comments = 
            state.blogs[blogType].blogs[index].comments.filter(
              (comment: Comment) => comment.id !== tempCommentId
            );
        }
      }
    },
  },
});

export const {
  clearBlogs,
  clearBlogsByType,
  setMainFetchDone,
  clearMainFetchDone,
  updateScrollPosition,
  clearScrollPosition,
  markNeedsRefresh,
  clearRefreshFlag,
  setLoading,
  setBlogs,
  setError,
  updateBlog,
  addBlog,
  addSharedBlog,
  removeSharedBlog,
  removeBlog,
  addComment,
  updateComment,
  removeTempComment,
  addReplyToComment,
  setReplyingState,
  setReplyText,
} = blogSlice.actions;

export default blogSlice.reducer;