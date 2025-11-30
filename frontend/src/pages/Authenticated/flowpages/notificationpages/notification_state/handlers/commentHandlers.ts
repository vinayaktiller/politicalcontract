// handlers/commentHandlers.ts
import { Dispatch } from '@reduxjs/toolkit';
import { RootState } from '../../../../../../store';
import { updateBlog, addComment } from '../../../../blogrelated/blogpage/blogSlice';
import { MessageHandler } from './handlerRegistry';
import { Blog, Comment } from '../../../../blogrelated/blogpage/blogTypes'; // Import types

// Define types for comment operations
interface CommentTreeUtils {
  findCommentInTree: (comments: Comment[], commentId: string) => Comment | null;
  updateCommentInTree: (comments: Comment[], commentId: string, updates: Partial<Comment>) => Comment[];
  addReplyToCommentInTree: (comments: Comment[], commentId: string, reply: Comment) => Comment[];
}

// Helper functions for comment tree operations
const commentTreeUtils: CommentTreeUtils = {
  findCommentInTree: (comments: Comment[], commentId: string): Comment | null => {
    for (const comment of comments) {
      if (comment.id === commentId) return comment;
      if (comment.replies?.length > 0) {
        const found = commentTreeUtils.findCommentInTree(comment.replies, commentId);
        if (found) return found;
      }
    }
    return null;
  },

  updateCommentInTree: (comments: Comment[], commentId: string, updates: Partial<Comment>): Comment[] => {
    return comments.map((comment: Comment) => {
      if (comment.id === commentId) {
        return { ...comment, ...updates };
      }
      if (comment.replies?.length > 0) {
        return {
          ...comment,
          replies: commentTreeUtils.updateCommentInTree(comment.replies, commentId, updates)
        };
      }
      return comment;
    });
  },

  addReplyToCommentInTree: (comments: Comment[], commentId: string, reply: Comment): Comment[] => {
    return comments.map((comment: Comment) => {
      if (comment.id === commentId) {
        return {
          ...comment,
          replies: [...(comment.replies || []), reply]
        };
      }
      if (comment.replies?.length > 0) {
        return {
          ...comment,
          replies: commentTreeUtils.addReplyToCommentInTree(comment.replies, commentId, reply)
        };
      }
      return comment;
    });
  }
};

// Blog utility functions
const blogUtils = {
  findBlogById: (state: RootState, blogId: string): { blogType: string | null; blog: Blog | null } => {
    for (const blogType of Object.keys(state.blog.blogs)) {
      const blog = state.blog.blogs[blogType].blogs.find((b: Blog) => b.id === blogId);
      if (blog) return { blogType, blog };
    }
    return { blogType: null, blog: null };
  },

  getCurrentUserId: (): number => {
    return parseInt(localStorage.getItem('user_id') || '0', 10);
  }
};

// Define message data types
interface CommentUpdateData {
  blog_id: string;
  action: string;
  comment: Comment;
  user_id: number;
}

interface CommentLikeUpdateData {
  blog_id: string;
  comment_id: string;
  action: string;
  likes_count: number;
  user_id: number;
}

interface ReplyUpdateData {
  blog_id: string;
  comment_id: string;
  reply: Comment;
  user_id: number;
}

// Comment update handler
export const handleCommentUpdateMessage: MessageHandler = (data, dispatch, getState) => {
  const { blog_id, action, comment, user_id } = data as CommentUpdateData;
  const blogType = 'circle';
  const state = getState();
  const blogsState = state.blog?.blogs?.[blogType];
  
  if (!blogsState || !Array.isArray(blogsState.blogs)) return;
  
  const blog = blogsState.blogs.find((b: Blog) => String(b.id) === String(blog_id));
  if (!blog) return;

  if (action === 'comment_added') {
    dispatch(addComment({
      blogType,
      blogId: String(blog_id),
      comment: comment,
    }));
  } else if (action === 'comment_deleted') {
    const updatedComments = blog.comments.filter((c: Comment) => c.id !== comment.id);
    dispatch(updateBlog({
      blogType,
      id: String(blog_id),
      updates: {
        comments: updatedComments,
        footer: {
          ...blog.footer,
          comments: blog.footer.comments.filter((id: string) => id !== comment.id),
        },
      },
    }));
  }
};

// Comment like update handler
export const handleCommentLikeUpdateMessage: MessageHandler = (data, dispatch, getState) => {
  const { blog_id, comment_id, action, likes_count, user_id } = data as CommentLikeUpdateData;
  
  if (user_id === blogUtils.getCurrentUserId()) return;
  
  const { blogType, blog } = blogUtils.findBlogById(getState(), blog_id);
  if (!blogType || !blog) return;
  
  const updatedComments = commentTreeUtils.updateCommentInTree(
    blog.comments, 
    comment_id, 
    { 
      likes: Array(likes_count).fill(0),
      has_liked: action === 'added'
    }
  );
  
  dispatch(updateBlog({
    blogType,
    id: blog_id,
    updates: { comments: updatedComments }
  }));
};

// Reply update handler
export const handleReplyUpdateMessage: MessageHandler = (data, dispatch, getState) => {
  const { blog_id, comment_id, reply, user_id } = data as ReplyUpdateData;
  
  if (user_id === blogUtils.getCurrentUserId()) return;
  
  const { blogType, blog } = blogUtils.findBlogById(getState(), blog_id);
  if (!blogType || !blog) return;
  
  const updatedComments = commentTreeUtils.addReplyToCommentInTree(
    blog.comments,
    comment_id,
    reply
  );
  
  dispatch(updateBlog({
    blogType,
    id: blog_id,
    updates: {
      comments: updatedComments,
      footer: {
        ...blog.footer,
        comments: [...blog.footer.comments, reply.id]
      }
    }
  }));
};