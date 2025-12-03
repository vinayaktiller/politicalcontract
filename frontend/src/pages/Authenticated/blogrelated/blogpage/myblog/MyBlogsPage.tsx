// MyBlogsPage.tsx
import React, { useEffect, useRef, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useNavigate } from "react-router-dom";
import { fetchBlogs, likeBlog, shareBlog } from "../blogThunks";
import BlogCard from "../BlogCard";
import { Blog } from "../blogTypes";
import { AppDispatch, RootState } from "../../../../../store";
import "../BlogListPage.css";
import { 
  updateMyBlogsScrollPosition, 
  clearMyBlogsScrollPosition 
} from "../blogSlice";

export default function MyBlogsPage() {
  const dispatch = useDispatch<AppDispatch>();
  const navigate = useNavigate();
  const containerRef = useRef<HTMLDivElement>(null);
  
  const blogType = "circle";
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);

  useEffect(() => {
    const userId = localStorage.getItem("user_id");
    setCurrentUserId(userId);
  }, []);

  const blogState = useSelector((state: RootState) => 
    state.blog.blogs[blogType] || { blogs: [], loading: false, error: null }
  );
  const mainFetchDone = useSelector((state: RootState) => 
    state.blog.mainFetchDone[blogType] || false
  );
  
  // Get MyBlogsPage scroll position for current user from Redux
  const myBlogsScrollPosition = useSelector((state: RootState) => 
    currentUserId ? state.blog.myblogscrollPositions[currentUserId] || 0 : 0
  );

  const [isRestoringScroll, setIsRestoringScroll] = useState(true);

  const rawBlogs = blogState.blogs;
  const allBlogs: Blog[] = Array.isArray(rawBlogs) ? rawBlogs : 
    rawBlogs?.blogs ? rawBlogs.blogs :
    rawBlogs?.results ? rawBlogs.results :
    rawBlogs?.data ? rawBlogs.data : [];

  const myBlogs = currentUserId 
    ? allBlogs.filter(blog => {
        const blogUserId = blog.user?.id?.toString() || 
                          blog.header?.user?.id?.toString() ||
                          blog.original_author_id;
        return blogUserId === currentUserId;
      })
    : [];

  useEffect(() => {
    if (!mainFetchDone) {
      console.log('🔄 Fetching blogs (first time)');
      dispatch(fetchBlogs(blogType));
    }
  }, [dispatch, blogType, mainFetchDone]);

  // Save scroll position for MyBlogsPage (using currentUserId)
  const saveScrollPosition = () => {
    if (!containerRef.current || !currentUserId) return;
    
    const position = containerRef.current.scrollTop;
    dispatch(updateMyBlogsScrollPosition({ 
      userId: currentUserId, 
      position 
    }));
  };

  // Restore scroll position for MyBlogsPage
  const restoreScrollPosition = () => {
    if (!containerRef.current || !currentUserId || myBlogsScrollPosition === 0) return false;
    
    containerRef.current.scrollTop = myBlogsScrollPosition;
    return true;
  };

  // Save scroll on unmount/navigation
  useEffect(() => {
    return () => {
      saveScrollPosition();
    };
  }, []);

  // Save scroll before unload
  useEffect(() => {
    const handleBeforeUnload = () => {
      saveScrollPosition();
    };

    window.addEventListener("beforeunload", handleBeforeUnload);
    
    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload);
    };
  }, []);

  // Restore scroll after blogs load
  useEffect(() => {
    if (!blogState.loading && myBlogs.length > 0 && containerRef.current && currentUserId && isRestoringScroll) {
      const timer = setTimeout(() => {
        const restored = restoreScrollPosition();
        setIsRestoringScroll(false);
        
        if (!restored && containerRef.current) {
          containerRef.current.scrollTop = 0;
        }
      }, 100);
      
      return () => clearTimeout(timer);
    }
  }, [blogState.loading, myBlogs.length, isRestoringScroll, myBlogsScrollPosition, currentUserId]);

  // Handle scroll events
  useEffect(() => {
    const handleScroll = () => {
      saveScrollPosition();
    };

    const container = containerRef.current;
    if (container) {
      container.addEventListener('scroll', handleScroll);
      return () => {
        container.removeEventListener('scroll', handleScroll);
      };
    }
  }, []);

  // Clear scroll on initial empty load
  useEffect(() => {
    if (myBlogs.length === 0 && !blogState.loading && currentUserId) {
      dispatch(clearMyBlogsScrollPosition({ userId: currentUserId }));
    }
  }, [dispatch, myBlogs.length, blogState.loading, currentUserId]);

  // Event handlers (unchanged from your original)
  const handleLike = (blogId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    dispatch(likeBlog({ blogType, blogId }));
  };

  const handleShare = (blogId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    dispatch(shareBlog({ blogType, blogId }));
  };

  const handleUserClick = (userId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    saveScrollPosition();
    navigate(`/profile/${userId}`);
  };

  const handleCommentClick = (blogId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    saveScrollPosition();
    navigate(`/blog/${blogId}`, { state: { focusComment: true } });
  };

  const handleBlogClick = (blogId: string) => {
    saveScrollPosition();
    navigate(`/blog/${blogId}`);
  };

  const handleReportClick = (
    report_kind?: string,
    time_type?: string,
    id?: string,
    level?: string,
    e?: React.MouseEvent
  ) => {
    if (e) e.stopPropagation();
    if (!report_kind || !time_type || !id || !level) return;

    saveScrollPosition();

    if (report_kind === "activity_report") {
      navigate(`/activity-reports/${time_type}/${id}/${level}`);
    } else {
      navigate(`/reports/${time_type}/${id}/${level}`);
    }
  };

  const formatReportTitle = (report_kind: string, time_type: string): string => {
    const kind = report_kind === "activity_report" ? "Activity" : "Initiation";
    const time = time_type.charAt(0).toUpperCase() + time_type.slice(1);
    return `${time} ${kind} Report`;
  };

  // Render states
  if (!currentUserId) {
    return (
      <div className="blog-list-page-container">
        <h1 className="blog-list-page-title">My Blogs</h1>
        <div className="blog-list-page-error">
          Please log in to view your blogs.
        </div>
      </div>
    );
  }

  if (blogState.loading && !mainFetchDone) {
    return <div className="blog-list-page-loading">Loading blogs...</div>;
  }
  
  if (blogState.error) {
    return <div className="blog-list-page-error">Error: {blogState.error}</div>;
  }

  return (
    <div 
      ref={containerRef} 
      className="blog-list-page-container blog-list-scroll-container"
    >
      <h1 className="blog-list-page-title">My Blogs</h1>
      
      <div className="my-blogs-info-section">
        <p className="my-blogs-count">Your blogs ({myBlogs.length})</p>
        <div className="my-blogs-user-id-display">
          <span>User ID: {currentUserId}</span>
        </div>
      </div>
      
      {myBlogs.length === 0 ? (
        <div className="blog-list-page-empty">
          <p>No blogs created yet.</p>
          <button 
            onClick={() => navigate('/blog-creator')} 
            className="my-blogs-create-btn"
          >
            Create First Blog
          </button>
        </div>
      ) : (
        <ul className="blog-list-page-list">
          {myBlogs.map((blog: Blog) => (
            <BlogCard
              key={blog.id}
              blog={blog}
              onBlogClick={handleBlogClick}
              onUserClick={handleUserClick}
              onLikeClick={handleLike}
              onShareClick={handleShare}
              onCommentClick={handleCommentClick}
              onReportClick={handleReportClick}
              formatReportTitle={formatReportTitle}
            />
          ))}
        </ul>
      )}

      <button 
        onClick={() => {
          saveScrollPosition();
          navigate('/blog-creator');
        }} 
        className="blog-creator-fixed-btn"
      >
        Create Blog
      </button>
    </div>
  );
}