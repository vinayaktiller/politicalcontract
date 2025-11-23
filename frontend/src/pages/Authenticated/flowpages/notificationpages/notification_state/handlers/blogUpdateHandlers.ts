// handlers/blogUpdateHandlers.ts
import { Dispatch } from '@reduxjs/toolkit';
import { RootState } from '../../../../../../store';
import { updateBlog } from '../../../../blogrelated/blogpage/blogSlice';
import { MessageHandler } from './handlerRegistry';

// Blog update handler (for likes/shares)
export const handleBlogUpdateMessage: MessageHandler = (data, dispatch, getState) => {
  const { blog_id, update_type, action, user_id } = data;
  
  const currentUserId = parseInt(localStorage.getItem('user_id') || '0', 10);
  
  if (user_id === currentUserId) return;
  
  const blogType = 'circle';
  const state = getState();
  const blogsState = state.blog?.blogs?.[blogType];
  if (!blogsState || !Array.isArray(blogsState.blogs)) return;
  
  const blog = blogsState.blogs.find((b: any) => String(b.id) === String(blog_id));
  if (!blog) return;
  
  const prevFooter = blog.footer || {
    likes: [] as number[],
    shares: [] as number[],
    relevant_count: [] as number[],
    irrelevant_count: [] as number[],
    comments: [] as string[],
    has_liked: false,
    has_shared: false,
  };
  
  const isLike = update_type === 'like';
  const targetKey: 'likes' | 'shares' = isLike ? 'likes' : 'shares';
  const actingUserId = typeof user_id === 'string' ? parseInt(user_id, 10) || user_id : user_id;
  const updatedArray = Array.isArray(prevFooter[targetKey])
    ? [...prevFooter[targetKey]]
    : [];
    
  if (action === 'added') {
    if (!updatedArray.some((id) => String(id) === String(actingUserId))) {
      updatedArray.push(actingUserId as any);
    }
  } else {
    const idx = updatedArray.findIndex((id) => String(id) === String(actingUserId));
    if (idx !== -1) {
      updatedArray.splice(idx, 1);
    }
  }
  
  const footerUpdates = {
    ...prevFooter,
    [targetKey]: updatedArray,
  };
  
  dispatch(updateBlog({
    blogType,
    id: String(blog_id),
    updates: {
      footer: footerUpdates,
    },
  }));
};