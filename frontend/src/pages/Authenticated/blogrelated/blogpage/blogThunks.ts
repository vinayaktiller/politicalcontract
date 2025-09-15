// blogThunks.ts
import { createAsyncThunk } from "@reduxjs/toolkit";
import api from "../../../../api"; // adjust if your api path differs
import {
  Blog,
  LikeActionResponse,
  ShareActionResponse,
  CommentActionResponse,
  Comment,
} from "./blogTypes";
import {
  setLoading,
  setBlogs,
  setError,
  updateBlog,
  addComment,
  // incrementCommentCount,
  updateComment,
  addReplyToComment,
  removeTempComment, // Add this import
} from "./blogSlice";
import { RootState } from "../../../../store";

/**
 * Helper: normalize many common shapes of responses into Blog[]
 */
const extractBlogsArray = (data: any): Blog[] => {
  if (!data) return [];
  if (Array.isArray(data)) return data;
  if (data.blogs && Array.isArray(data.blogs)) return data.blogs;
  if (data.results && Array.isArray(data.results)) return data.results;
  if (data.data && Array.isArray(data.data)) return data.data;

  // If backend returned an object mapping ids to blog objects
  if (typeof data === "object") {
    const values = Object.values(data).filter(
      (v: any) => v && typeof v === "object" && ("id" in v || "header" in v)
    );
    if (values.length) return values as Blog[];
  }

  console.warn("extractBlogsArray: unexpected response shape", data);
  return [];
};

/**
 * fetchBlogs
 * - returns early if we already have blogs for blogType
 * - normalizes response before dispatching setBlogs
 */
export const fetchBlogs = createAsyncThunk<
  void,
  string,
  { state: RootState }
>("blogs/fetchBlogs", async (blogType: string, { dispatch, getState }) => {
  try {
    const state = getState() as RootState;
    const currentBlogs = state.blog.blogs[blogType]?.blogs || [];
    if (currentBlogs.length > 0) return;

    dispatch(setLoading({ blogType, loading: true }));

    const response = await api.get("/api/blog/circle-blogs/"); // adjust endpoint if required
    // Debug: log raw response if needed
    // console.log("fetchBlogs raw response:", response.data);

    const blogsArray = extractBlogsArray(response.data);
    console.log('fetchBlogs normalized blogsArray:', blogsArray);

    dispatch(setBlogs({ blogType, blogs: blogsArray }));
    dispatch(setLoading({ blogType, loading: false }));
  } catch (err: any) {
    console.error("fetchBlogs error:", err);
    dispatch(setError({ blogType, error: err?.message || "Unknown error" }));
    dispatch(setLoading({ blogType, loading: false }));
  }
});

/**
 * fetchBlog (single blog)
 * - fetch a single blog and either add it to the list or update existing
 */
export const fetchBlog = createAsyncThunk<
  Blog | void,
  string,
  { state: RootState }
>("blogs/fetchBlog", async (blogId: string, { dispatch, getState }) => {
  try {
    const response = await api.get(`/api/blog/blogs/${blogId}/`);
    const blogData = (response.data as any).blog || response.data;
    if (!blogData) {
      console.warn("fetchBlog: no blog found in response", response.data);
      return;
    }

    const blogType = blogData.header?.type || "circle";
    const state = getState() as RootState;
    const currentBlogs = state.blog.blogs[blogType]?.blogs || [];
    const blogIndex = currentBlogs.findIndex((b) => b.id === blogId);

    if (blogIndex === -1) {
      // append (or you could unshift depending on desired ordering)
      dispatch(setBlogs({ blogType, blogs: [...currentBlogs, blogData] }));
    } else {
      dispatch(updateBlog({ blogType, id: blogId, updates: blogData }));
    }

    return blogData as Blog;
  } catch (err: any) {
    console.error("Error fetching blog:", err);
    throw err;
  }
});

/**
 * fetchComments (for a single blog)
 */
export const fetchComments = createAsyncThunk<
  Comment[] | void,
  string,
  { state: RootState }
>("blogs/fetchComments", async (blogId: string, { dispatch, getState }) => {
  try {
    const response = await api.get<any>(`/api/blog/blogs/${blogId}/comments/`);
    const commentsData = (response.data as any).comments || response.data;

    // find blogType by searching current state
    const state = getState() as RootState;
    let blogType = "";
    Object.entries(state.blog.blogs).forEach(([type, blogState]) => {
      if (blogState?.blogs?.find((b) => b.id === blogId)) {
        blogType = type;
      }
    });

    if (blogType) {
      dispatch(updateBlog({ blogType, id: blogId, updates: { comments: commentsData } }));
    } else {
      console.warn("fetchComments: couldn't locate blogType for blogId", blogId);
    }

    return commentsData;
  } catch (err: any) {
    console.error("Error fetching comments:", err);
    throw err;
  }
});

/**
 * likeBlog
 */
export const likeBlog = createAsyncThunk<
  void,
  { blogType: string; blogId: string },
  { state: RootState }
>("blogs/likeBlog", async ({ blogType, blogId }, { dispatch, getState }) => {
  try {
    const response = await api.post<LikeActionResponse>(`/api/blog/blogs/${blogId}/like/`);

    const state = getState() as RootState;
    const currentBlog =
      state.blog.blogs[blogType]?.blogs.find((blog) => blog.id === blogId) || null;

    if (currentBlog) {
      const added = response.data?.action === "added";
      dispatch(
        updateBlog({
          blogType,
          id: blogId,
          updates: {
            footer: {
              ...currentBlog.footer,
              likes: added ? [...currentBlog.footer.likes, 0] : currentBlog.footer.likes.slice(0, -1),
              has_liked: added,
            },
          },
        })
      );
    } else {
      console.warn("likeBlog: currentBlog not found in state", blogType, blogId);
    }
  } catch (err: any) {
    console.error("Error liking blog:", err);
  }
});

/**
 * shareBlog
 */
export const shareBlog = createAsyncThunk<
  void,
  { blogType: string; blogId: string },
  { state: RootState }
>("blogs/shareBlog", async ({ blogType, blogId }, { dispatch, getState }) => {
  try {
    const response = await api.post<ShareActionResponse>(`/api/blog/blogs/${blogId}/share/`);

    const state = getState() as RootState;
    const currentBlog =
      state.blog.blogs[blogType]?.blogs.find((blog) => blog.id === blogId) || null;

    if (currentBlog) {
      const added = response.data?.action === "added";
      dispatch(
        updateBlog({
          blogType,
          id: blogId,
          updates: {
            footer: {
              ...currentBlog.footer,
              shares: added ? [...currentBlog.footer.shares, 0] : currentBlog.footer.shares.slice(0, -1),
              has_shared: added,
            },
          },
        })
      );
    }

    if (response.data?.action === "added") {
      alert("Blog shared successfully!");
    } else {
      alert("Blog unshared successfully!");
    }
  } catch (err: any) {
    console.error("Error sharing blog:", err);
    alert("Error sharing blog. Please try again.");
  }
});

/**
 * addCommentToBlog
 * - No optimistic update to prevent duplicates
 */
export const addCommentToBlog = createAsyncThunk<
  Comment | void,
  { blogType: string; blogId: string; text: string },
  { state: RootState }
>(
  "blogs/addComment",
  async ({ blogType, blogId, text }, { dispatch, getState }) => {
    try {
      const response = await api.post<CommentActionResponse>(
        `/api/blog/blogs/${blogId}/comments/`,
        { text: text.trim() }
      );

      const commentData = (response.data as any).comment || response.data;
      if (commentData) {
        dispatch(addComment({ blogType, blogId, comment: commentData }));
        return commentData;
      }
    } catch (err: any) {
      console.error("Error posting comment:", err);
      throw err;
    }
  }
);

/**
 * addReplyToCommentThunk
 */
export const addReplyToCommentThunk = createAsyncThunk<
  Comment | void,
  { blogType: string; blogId: string; commentId: string; text: string },
  { state: RootState }
>(
  "blogs/addReplyToCommentThunk",
  async ({ blogType, blogId, commentId, text }, { dispatch }) => {
    try {
      const response = await api.post<CommentActionResponse>(
        `/api/blog/comments/${commentId}/reply/`,
        { text: text.trim() }
      );

      const replyData = (response.data as any).comment || response.data;
      if (replyData) {
        dispatch(addReplyToComment({ blogType, blogId, commentId, reply: replyData }));
        return replyData;
      }
    } catch (err: any) {
      console.error("Error posting reply:", err);
      throw err;
    }
  }
);

/**
 * likeComment (finds comment within blog tree and updates it)
 */
export const likeComment = createAsyncThunk<
  void,
  { blogType: string; blogId: string; commentId: string },
  { state: RootState }
>(
  "blogs/likeComment",
  async ({ blogType, blogId, commentId }, { dispatch, getState }) => {
    try {
      const response = await api.post<LikeActionResponse>(`/api/blog/comments/${commentId}/like/`);

      const state = getState() as RootState;
      const currentBlog = state.blog.blogs[blogType]?.blogs.find((b) => b.id === blogId);

      if (!currentBlog) return;

      const findComment = (comments: Comment[]): Comment | null => {
        for (const comment of comments) {
          if (comment.id === commentId) return comment;
          if (comment.replies?.length) {
            const found = findComment(comment.replies);
            if (found) return found;
          }
        }
        return null;
      };

      const comment = findComment(currentBlog.comments);
      if (comment) {
        const hasAdded = response.data?.action === "added";
        const newLikes = hasAdded ? [...comment.likes, 0] : comment.likes.slice(0, -1);
        dispatch(
          updateComment({
            blogType,
            blogId,
            commentId,
            updates: {
              likes: newLikes,
              has_liked: hasAdded,
            },
          })
        );
      } else {
        console.warn("likeComment: comment not found", { blogType, blogId, commentId });
      }
    } catch (err: any) {
      console.error("Error liking comment:", err);
    }
  }
);