import React, { useEffect, useRef, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useNavigate } from "react-router-dom";
import { fetchBlogs, likeBlog, shareBlog } from "./blogThunks";
import BlogCard from "./BlogCard";
import { Blog, BlogsState } from "./blogTypes";
import { AppDispatch, RootState } from "../../../../store";
import "./BlogListPage.css";
import { updateScrollPosition, clearScrollPosition } from "./blogSlice";

function normalizeBlogs(input: any): Blog[] {
  if (!input) return [];
  if (Array.isArray(input)) return input;
  // common API shapes
  if (input.blogs && Array.isArray(input.blogs)) return input.blogs;
  if (input.results && Array.isArray(input.results)) return input.results;
  if (input.data && Array.isArray(input.data)) return input.data;

  // maybe the server returned a map { id: blog, ... }
  if (typeof input === "object") {
    const values = Object.values(input).filter(
      (v) => v && typeof v === "object" && ("id" in v || "header" in v)
    );
    if (values.length) return values as Blog[];
  }

  // console.warn("normalizeBlogs: unexpected shape for blogs ->", input);
  return [];
}

export default function BlogListPage() {
  const dispatch = useDispatch<AppDispatch>();
  const navigate = useNavigate();
  
  // Refs for scroll management
  const containerRef = useRef<HTMLDivElement>(null);
  const blogType = "circle";

  const blogState = useSelector(
    (state: RootState) =>
      state.blog.blogs[blogType] || {
        blogs: [],
        loading: false,
        error: null,
      }
  );

  // Get scroll position from Redux store
  const scrollPosition = useSelector((state: RootState) => 
    state.blog.scrollPositions[blogType] || 0
  );

  // Get main fetch status from Redux store - this is our single source of truth
  const mainFetchDone = useSelector((state: RootState) => 
    state.blog.mainFetchDone[blogType] || false
  );

  // Properly type the blog state
  const typedBlogState = blogState as BlogsState;
  
  // Keep the original raw value for logging/debug if needed
  const rawBlogs = typedBlogState.blogs;
  const blogs: Blog[] = normalizeBlogs(rawBlogs);

  const loading = typedBlogState.loading;
  const error = typedBlogState.error;

  // State to track if we're restoring scroll position
  const [isRestoringScroll, setIsRestoringScroll] = useState(true);

  // NEW: Simplified fetch logic - only depends on mainFetchDone
  useEffect(() => {
    // Only fetch if main fetch hasn't been done
    if (!mainFetchDone) {
      console.log('🔄 Performing initial main fetch for blogs');
      
      dispatch(fetchBlogs(blogType))
        .unwrap()
        .then(() => {
          console.log('✅ Initial main fetch completed and persisted');
        })
        .catch((error) => {
          console.error('❌ Failed to fetch blogs:', error);
        });
    } else {
      console.log('⏩ Skipping fetch - main fetch already done');
    }
  }, [dispatch, blogType, mainFetchDone]); // Removed loading dependency

  // Save scroll position to Redux
  const saveScrollPosition = () => {
    if (!containerRef.current) return;
    
    const position = containerRef.current.scrollTop;
    dispatch(updateScrollPosition({ blogType, position }));
  };

  // Restore scroll position from Redux
  const restoreScrollPosition = () => {
    if (!containerRef.current || scrollPosition === 0) return false;
    
    containerRef.current.scrollTop = scrollPosition;
    return true;
  };

  // Save scroll position before unload
  useEffect(() => {
    const handleBeforeUnload = () => {
      saveScrollPosition();
    };

    window.addEventListener("beforeunload", handleBeforeUnload);
    
    return () => {
      saveScrollPosition();
      window.removeEventListener("beforeunload", handleBeforeUnload);
    };
  }, []);

  // Save scroll position on navigation
  useEffect(() => {
    return () => {
      // This runs when component unmounts (navigation away)
      saveScrollPosition();
    };
  }, []);

  // Restore scroll position after blogs are loaded and container is rendered
  useEffect(() => {
    if (!loading && blogs.length > 0 && containerRef.current && isRestoringScroll) {
      // Small timeout to ensure DOM is fully updated
      const timer = setTimeout(() => {
        const restored = restoreScrollPosition();
        setIsRestoringScroll(false);
        
        if (!restored) {
          // If no saved position, scroll to top
          containerRef.current!.scrollTop = 0;
        }
      }, 100);
      
      return () => clearTimeout(timer);
    }
  }, [loading, blogs.length, isRestoringScroll, scrollPosition]);

  // Handle scroll events to save position periodically
  useEffect(() => {
    const handleScroll = () => {
      // Throttle scroll saving to improve performance
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

  // Clear scroll position when component mounts initially for fresh load
  useEffect(() => {
    // Only clear if we're doing a fresh load (check if we have any blogs)
    if (blogs.length === 0 && !loading) {
      dispatch(clearScrollPosition({ blogType }));
    }
  }, [dispatch, blogType, blogs.length, loading]);

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
    // Save position before navigating
    saveScrollPosition();
    navigate(`/profile/${userId}`);
  };

  const handleCommentClick = (blogId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    // Save position before navigating
    saveScrollPosition();
    navigate(`/blog/${blogId}`, { state: { focusComment: true } });
  };

  const handleBlogClick = (blogId: string) => {
    // Save position before navigating
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

    // Save position before navigating
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

  if (loading && !mainFetchDone) {
    return <div className="blog-list-page-loading">Loading blogs...</div>;
  }
  
  if (error) {
    return <div className="blog-list-page-error">Error loading blogs: {error}</div>;
  }

  return (
    <div 
      ref={containerRef} 
      className="blog-list-page-container blog-list-scroll-container"
    >
      <h1 className="blog-list-page-title">Blogs</h1>
      {blogs.length === 0 ? (
        <p className="blog-list-page-empty">No blogs found.</p>
      ) : (
        <ul className="blog-list-page-list">
          {blogs.map((blog: Blog) => (
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

      {/* Fixed button in bottom right corner */}
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