import React, { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useNavigate } from "react-router-dom";
import { fetchBlogs, likeBlog, shareBlog } from "./blogThunks";
import BlogCard from "./BlogCard";
import { Blog } from "./blogTypes";
import { AppDispatch, RootState } from "../../../../store";
import "./BlogListPage.css";

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

  console.warn("normalizeBlogs: unexpected shape for blogs ->", input);
  return [];
}

export default function BlogListPage() {
  const dispatch = useDispatch<AppDispatch>();
  const navigate = useNavigate();

  const blogType = "circle";

  const blogState = useSelector(
    (state: RootState) =>
      state.blog.blogs[blogType] || {
        blogs: [],
        loading: false,
        error: null,
      }
  );

  // Keep the original raw value for logging/debug if needed
  const rawBlogs = (blogState as any).blogs;
  const blogs: Blog[] = normalizeBlogs(rawBlogs);

  const loading = (blogState as any).loading;
  const error = (blogState as any).error;

  useEffect(() => {
    dispatch(fetchBlogs(blogType));
  }, [dispatch, blogType]);

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
    navigate(`/profile/${userId}`);
  };

  const handleCommentClick = (blogId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    navigate(`/blog/${blogId}`, { state: { focusComment: true } });
  };

  const handleBlogClick = (blogId: string) => {
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

  if (loading) return <div className="blog-list-page-loading">Loading blogs...</div>;
  if (error) return <div className="blog-list-page-error">Error loading blogs: {error}</div>;

  return (
    <div className="blog-list-page-container">
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
        onClick={() => navigate('/blog-creator')} 
        className="blog-creator-fixed-btn"
      >
        Create Blog
      </button>
    </div>
  );
}
