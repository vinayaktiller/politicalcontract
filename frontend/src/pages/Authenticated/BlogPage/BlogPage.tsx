// import React, { useState, useEffect } from 'react';
// import { useDispatch, useSelector } from 'react-redux';
// import type { AppDispatch, RootState } from "../../../store";
// import { fetchAllJourneyBlogs, createJourneyBlog } from './BlogSlice';
// import { format } from 'date-fns';
// import './JourneyBlogPage.css';

// interface NewBlogForm {
//   content: string;
//   type: 'micro' | 'short_essay' | 'article';
//   target_user: number | null;
// }

// const JourneyBlogPage: React.FC = () => {
//   const dispatch = useDispatch<AppDispatch>();
//   const { blogs, status, error } = useSelector((state: RootState) => state.journeyBlogs);
//   const currentUser = useSelector((state: RootState) => state.auth.user);
  
//   const [newBlog, setNewBlog] = useState<NewBlogForm>({
//     content: '',
//     type: 'micro',
//     target_user: currentUser?.id || null
//   });
//   const [isCreating, setIsCreating] = useState(false);
//   const [showForm, setShowForm] = useState(false);
//   const [characterCount, setCharacterCount] = useState(0);
  
//   const maxLengths = {
//     micro: 280,
//     short_essay: 3200,
//     article: 12000
//   };

//   useEffect(() => {
//     if (status === 'idle') {
//       dispatch(fetchAllJourneyBlogs());
//     }
//   }, [dispatch, status]);

//   const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
//     const { value } = e.target;
//     setNewBlog({ ...newBlog, content: value });
//     setCharacterCount(value.length);
//   };

//   const handleTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
//     setNewBlog({ 
//       ...newBlog, 
//       type: e.target.value as 'micro' | 'short_essay' | 'article',
//       content: ''
//     });
//     setCharacterCount(0);
//   };

//   const handleSubmit = async (e: React.FormEvent) => {
//     e.preventDefault();
//     setIsCreating(true);
    
//     try {
//       await dispatch(createJourneyBlog({
//         ...newBlog,
//         target_user: newBlog.target_user || currentUser?.id || 0
//       }));
      
//       setNewBlog({ 
//         content: '', 
//         type: 'micro',
//         target_user: currentUser?.id || null
//       });
//       setShowForm(false);
//       setCharacterCount(0);
//     } catch (err) {
//       console.error('Failed to create blog:', err);
//     } finally {
//       setIsCreating(false);
//     }
//   };

//   const getTypeLabel = (type: string) => {
//     switch(type) {
//       case 'micro': return 'Thought';
//       case 'short_essay': return 'Story';
//       case 'article': return 'Article';
//       default: return 'Blog';
//     }
//   };

//   const formatDate = (dateString: string) => {
//     return format(new Date(dateString), 'MMM d, yyyy · h:mm a');
//   };

//   const renderContent = (content: string, type: string) => {
//     if (type === 'micro') {
//       return (
//         <div className="blog-content micro">
//           <p>{content}</p>
//         </div>
//       );
//     }
//     return (
//       <div className={`blog-content ${type}`}>
//         <p>{content}</p>
//       </div>
//     );
//   };

//   return (
//     <div className="journey-blog-page">
//       <div className="blog-header">
//         <h1>Journey Blogs</h1>
//         <p>Share your journey with the community</p>
//       </div>

//       <div className="blog-controls">
//         <button 
//           className="create-blog-btn"
//           onClick={() => setShowForm(!showForm)}
//         >
//           {showForm ? 'Cancel' : 'Write a Blog'}
//         </button>
//       </div>

//       {showForm && (
//         <div className="blog-form-container">
//           <form onSubmit={handleSubmit} className="blog-form">
//             <div className="form-header">
//               <h2>Create New Blog</h2>
//               <select 
//                 value={newBlog.type} 
//                 onChange={handleTypeChange}
//                 className="blog-type-selector"
//               >
//                 <option value="micro">Thought (280 chars)</option>
//                 <option value="short_essay">Story (3200 chars)</option>
//                 <option value="article">Article (12000 chars)</option>
//               </select>
//             </div>
            
//             <div className="form-group">
//               <textarea
//                 value={newBlog.content}
//                 onChange={handleInputChange}
//                 placeholder={`Share your ${getTypeLabel(newBlog.type).toLowerCase()}...`}
//                 maxLength={maxLengths[newBlog.type]}
//                 className="blog-content-input"
//                 rows={newBlog.type === 'micro' ? 3 : 6}
//               />
//               <div className="character-counter">
//                 {characterCount}/{maxLengths[newBlog.type]}
//               </div>
//             </div>
            
//             <div className="form-actions">
//               <button
//                 type="submit"
//                 disabled={newBlog.content.length < 5 || isCreating}
//                 className="submit-blog-btn"
//               >
//                 {isCreating ? 'Posting...' : 'Publish'}
//               </button>
//             </div>
//           </form>
//         </div>
//       )}

//       <div className="blogs-container">
//         {status === 'loading' ? (
//           <div className="loading-indicator">
//             <div className="spinner"></div>
//             <p>Loading blogs...</p>
//           </div>
//         ) : error ? (
//           <div className="error-message">
//             <p>Error loading blogs: {error}</p>
//           </div>
//         ) : blogs.length === 0 ? (
//           <div className="empty-state">
//             <div className="empty-icon">📝</div>
//             <h3>No Blogs Yet</h3>
//             <p>Be the first to share your journey!</p>
//           </div>
//         ) : (
//           blogs.map(blog => (
//             <div key={blog.id} className={`blog-card ${blog.base_blog.type}`}>
//               <div className="blog-header-info">
//                 {blog.userid_details?.profilepic_url ? (
//                   <img 
//                     src={blog.userid_details.profilepic_url} 
//                     alt={blog.userid_details.name} 
//                     className="author-avatar"
//                   />
//                 ) : (
//                   <div className="avatar-placeholder">
//                     {blog.userid_details?.name.charAt(0) || 'U'}
//                   </div>
//                 )}
//                 <div className="author-info">
//                   <h4 className="author-name">{blog.userid_details?.name || 'Unknown User'}</h4>
//                   <p className="blog-date">{formatDate(blog.base_blog.created_at)}</p>
//                 </div>
//                 <div className="blog-type-tag">
//                   {getTypeLabel(blog.base_blog.type)}
//                 </div>
//               </div>
              
//               {renderContent(blog.content, blog.base_blog.type)}
              
//               <div className="blog-meta">
//                 <div className="meta-item">
//                   <span className="meta-icon">❤️</span>
//                   <span>{blog.base_blog.likes.length}</span>
//                 </div>
//                 <div className="meta-item">
//                   <span className="meta-icon">💬</span>
//                   <span>0</span>
//                 </div>
//                 <div className="meta-item">
//                   <span className="meta-icon">↗️</span>
//                   <span>{blog.base_blog.shares.length}</span>
//                 </div>
//               </div>
//             </div>
//           ))
//         )}
//       </div>
//     </div>
//   );
// };

// export default JourneyBlogPage;

export {}