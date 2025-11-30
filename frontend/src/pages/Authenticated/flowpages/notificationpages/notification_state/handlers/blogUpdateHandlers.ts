// handlers/blogUpdateHandlers.ts
import { Dispatch } from '@reduxjs/toolkit';
import { RootState } from '../../../../../../store';
import { updateBlog } from '../../../../blogrelated/blogpage/blogSlice';
import { MessageHandler } from './handlerRegistry';

// Blog update handler (for likes/shares) - FIXED
export const handleBlogUpdateMessage: MessageHandler = (data, dispatch, getState) => {
  const { blog_id, update_type, action, user_id, shares_count } = data;
  
  const currentUserId = parseInt(localStorage.getItem('user_id') || '0', 10);
  
  // Don't process if this is our own action
  if (parseInt(user_id) === currentUserId) {
    console.log('Ignoring own blog update action');
    return;
  }
  
  const blogType = 'circle';
  const state = getState();
  const blogsState = state.blog?.blogs?.[blogType];
  
  if (!blogsState || !Array.isArray(blogsState.blogs)) {
    console.log('Blogs state not found or invalid for type:', blogType);
    return;
  }
  
  const blog = blogsState.blogs.find((b: any) => String(b.id) === String(blog_id));
  if (!blog) {
    console.log('Blog not found for update:', blog_id);
    return;
  }
  
  console.log('Updating blog:', blog_id, 'update_type:', update_type, 'action:', action);
  
  const prevFooter = blog.footer || {
    likes: [] as number[],
    shares: [] as number[],
    relevant_count: [] as number[],
    irrelevant_count: [] as number[],
    comments: [] as string[],
    has_liked: false,
    has_shared: false,
  };
  
  // Handle different update types
  if (update_type === 'like') {
    const updatedLikes = Array.isArray(prevFooter.likes) ? [...prevFooter.likes] : [];
    const actingUserId = typeof user_id === 'string' ? parseInt(user_id, 10) || user_id : user_id;
    
    if (action === 'added') {
      if (!updatedLikes.some((id) => String(id) === String(actingUserId))) {
        updatedLikes.push(actingUserId as any);
      }
    } else if (action === 'removed') {
      const idx = updatedLikes.findIndex((id) => String(id) === String(actingUserId));
      if (idx !== -1) {
        updatedLikes.splice(idx, 1);
      }
    }
    
    const footerUpdates = {
      ...prevFooter,
      likes: updatedLikes,
    };
    
    dispatch(updateBlog({
      blogType,
      id: String(blog_id),
      updates: {
        footer: footerUpdates,
      },
    }));
    
    console.log('Updated likes for blog:', blog_id, 'new likes:', updatedLikes);
    
  } else if (update_type === 'share') {
    // Handle share updates
    const updatedShares = Array.isArray(prevFooter.shares) ? [...prevFooter.shares] : [];
    const actingUserId = typeof user_id === 'string' ? parseInt(user_id, 10) || user_id : user_id;
    
    if (action === 'added') {
      if (!updatedShares.some((id) => String(id) === String(actingUserId))) {
        updatedShares.push(actingUserId as any);
      }
    } else if (action === 'removed') {
      const idx = updatedShares.findIndex((id) => String(id) === String(actingUserId));
      if (idx !== -1) {
        updatedShares.splice(idx, 1);
      }
    }
    
    const footerUpdates = {
      ...prevFooter,
      shares: updatedShares,
    };
    
    // If shares_count is provided, use it (more reliable)
    if (shares_count !== undefined) {
      footerUpdates.shares = Array.from({ length: shares_count }, (_, i) => i + 1);
    }
    
    dispatch(updateBlog({
      blogType,
      id: String(blog_id),
      updates: {
        footer: footerUpdates,
      },
    }));
    
    console.log('Updated shares for blog:', blog_id, 'new shares:', updatedShares, 'shares_count:', shares_count);
  }
};