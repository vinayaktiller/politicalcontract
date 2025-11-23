// handlers/blogHandlers.ts
import { Dispatch } from '@reduxjs/toolkit';
import { RootState } from '../../../../../../store';
import { updateBlog, addBlog, addSharedBlog, removeSharedBlog } from '../../../../blogrelated/blogpage/blogSlice';

type MessageHandler = (data: any, dispatch: Dispatch, getState: () => RootState) => void;

// Blog creation handler
export const handleBlogUpload: MessageHandler = (data, dispatch, getState) => {
  const { blog_id, action, blog, user_id, blog_type } = data;
  const currentUserId = parseInt(localStorage.getItem('user_id') || '0', 10);

  if (user_id === currentUserId) return;

  if (action === 'blog_created' && blog && blog_type) {
    console.log('New blog received via WebSocket:', blog, blog_type);
    
    dispatch(addBlog({ blogType: 'circle', blog }));
    
    const state = getState();
    if (state.blog.blogs[blog_type]) {
      dispatch(addBlog({ blogType: blog_type, blog }));
    }
  }
};

// Blog share handler
export const handleBlogShared: MessageHandler = (data, dispatch, getState) => {
  const { blog_id, action, blog, shared_by_user_id, original_author_id, user_id } = data;
  const currentUserId = parseInt(localStorage.getItem('user_id') || '0', 10);

  if (user_id === currentUserId) {
    console.log('Ignoring own blog share action');
    return;
  }

  if (action === 'shared' && blog && shared_by_user_id && original_author_id) {
    dispatch(addSharedBlog({
      blogType: 'circle',
      blog: blog,
      sharedByUserId: shared_by_user_id,
      originalAuthorId: original_author_id
    }));
  }
};

// Blog unshare handler
export const handleBlogUnshared: MessageHandler = (data, dispatch, getState) => {
  const { blog_id, action, shared_by_user_id, original_author_id, user_id } = data;
  const currentUserId = parseInt(localStorage.getItem('user_id') || '0', 10);

  if (user_id === currentUserId) return;

  if (action === 'unshared' && shared_by_user_id && original_author_id) {
    dispatch(removeSharedBlog({
      blogType: 'circle',
      blogId: blog_id,
      sharedByUserId: shared_by_user_id
    }));
  }
};

// Blog modification handler
export const handleBlogModified: MessageHandler = (data, dispatch, getState) => {
  const { blog_id, blog, user_id, blog_type } = data;
  const currentUserId = parseInt(localStorage.getItem('user_id') || '0', 10);

  if (user_id === currentUserId) return;

  if (blog && blog_type) {
    const state = getState();
    
    if (state.blog.blogs['circle']) {
      dispatch(updateBlog({ blogType: 'circle', id: blog_id, updates: blog }));
    }
    
    if (state.blog.blogs[blog_type]) {
      dispatch(updateBlog({ blogType: blog_type, id: blog_id, updates: blog }));
    }
  }
};