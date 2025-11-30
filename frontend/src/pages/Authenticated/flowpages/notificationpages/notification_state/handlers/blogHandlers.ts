import { Dispatch } from '@reduxjs/toolkit';
import { RootState } from '../../../../../../store';
import { updateBlog, addBlog, addSharedBlog, removeSharedBlog, removeBlog } from '../../../../blogrelated/blogpage/blogSlice';

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
  const { 
    blog_id, 
    action, 
    shared_by_user_id, 
    original_author_id, 
    user_id, 
    shares_count 
  } = data;
  
  const currentUserId = parseInt(localStorage.getItem('user_id') || '0', 10);

  console.log('Handle blog unshare called:', { 
    blog_id, 
    currentUserId, 
    user_id, 
    shared_by_user_id,
    action
  });

  // Don't process if this is our own action
  if (parseInt(user_id) === currentUserId) {
    console.log('Ignoring own blog unshare action');
    return;
  }

  if (action === 'unshared' && shared_by_user_id && original_author_id) {
    console.log('Processing blog unshare:', blog_id, 'shared by:', shared_by_user_id);
    
    // Convert IDs to strings for consistency
    const blogIdStr = blog_id.toString();
    const sharedByUserIdStr = shared_by_user_id.toString();
    
    // First try to remove as shared blog
    dispatch(removeSharedBlog({
      blogType: 'circle',
      blogId: blogIdStr,
      sharedByUserId: sharedByUserIdStr
    }));

    // Check if we need to completely remove the blog
    const state = getState();
    const circleBlogs = state.blog.blogs['circle']?.blogs || [];
    
    // Find the specific blog to check its properties
    const targetBlog = circleBlogs.find((blog: any) => blog.id === blogIdStr);
    
    // Only remove completely if:
    // 1. The blog doesn't exist in our store anymore, OR
    // 2. The blog exists but we're not the author and we're not sharing it
    const currentUserIdStr = currentUserId.toString();
    const shouldRemoveCompletely = !targetBlog || 
      (targetBlog && 
       (targetBlog as any).author_id !== currentUserIdStr && 
       !(targetBlog as any).is_shared);

    if (shouldRemoveCompletely) {
      dispatch(removeBlog({
        blogType: 'circle',
        blogId: blogIdStr
      }));
      console.log('Completely removed blog from store:', blogIdStr);
    } else {
      // Update share count for remaining blogs
      if (targetBlog) {
        dispatch(updateBlog({
          blogType: 'circle',
          id: blogIdStr,
          updates: {
            footer: {
              ...targetBlog.footer,
              shares: Array.from({ length: shares_count || 0 }, (_, i) => i + 1)
            }
          }
        }));
        console.log('Updated shares count for blog:', blogIdStr, 'count:', shares_count);
      }
    }
  } else {
    console.log('Invalid unshare data:', data);
  }
};

// Blog deletion handler
export const handleBlogDeleted: MessageHandler = (data, dispatch, getState) => {
  const { blog_id, action } = data;

  if (action === 'blog_deleted') {
    const blogIdStr = blog_id.toString();
    
    // Remove from all blog types
    const state = getState();
    const blogTypes = Object.keys(state.blog.blogs);
    
    blogTypes.forEach(blogType => {
      dispatch(removeBlog({
        blogType,
        blogId: blogIdStr
      }));
    });
    
    console.log('Blog deleted from all stores:', blogIdStr);
  }
};

// Blog modification handler (FIXED - This was the main issue)
export const handleBlogModified: MessageHandler = (data, dispatch, getState) => {
  const { blog_id, blog, user_id, blog_type = 'circle' } = data; // Added default blog_type
  const currentUserId = parseInt(localStorage.getItem('user_id') || '0', 10);

  console.log('Blog modification handler called:', { blog_id, user_id, currentUserId, blog });

  // Don't process if this is our own action
  if (parseInt(user_id) === currentUserId) {
    console.log('Ignoring own blog modification action');
    return;
  }

  if (blog && blog_id) {
    const state = getState();
    const blogIdStr = blog_id.toString();
    
    console.log('Updating blog in store:', blogIdStr, 'with data:', blog);
    
    // Update in circle blog type (main feed)
    if (state.blog.blogs['circle']) {
      dispatch(updateBlog({ 
        blogType: 'circle', 
        id: blogIdStr, 
        updates: blog 
      }));
      console.log('Blog updated in circle store');
    }
    
    // Update in specific blog type if different from circle
    if (blog_type && blog_type !== 'circle' && state.blog.blogs[blog_type]) {
      dispatch(updateBlog({ 
        blogType: blog_type, 
        id: blogIdStr, 
        updates: blog 
      }));
      console.log('Blog updated in', blog_type, 'store');
    }
  } else {
    console.log('Invalid blog modification data:', data);
  }
};