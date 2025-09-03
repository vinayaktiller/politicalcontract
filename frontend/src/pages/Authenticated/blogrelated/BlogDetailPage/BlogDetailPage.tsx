import React, { useEffect, useState } from "react";
import { useParams, useNavigate, useLocation } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import {
  fetchBlog,
  fetchComments,
  likeBlog,
  shareBlog,
  addCommentToBlog,
  likeComment,
  addReplyToCommentThunk,
} from "../blogpage/blogThunks";
import { setReplyingState, setReplyText } from "../blogpage/blogSlice";
import { AppDispatch, RootState } from "../../../../store";
import "./BlogDetailPage.css";

const BlogDetailPage: React.FC = () => {
  const { blogId } = useParams<{ blogId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useDispatch<AppDispatch>();

  const [newComment, setNewComment] = useState("");
  const [commentLoading, setCommentLoading] = useState<boolean>(false);
  const [expandedComments, setExpandedComments] = useState<Set<string>>(new Set());

  // Fetch blog and type from Redux state
  const { blog, blogType } = useSelector((state: RootState) => {
    if (!blogId) return { blog: null, blogType: null };
    for (const type of Object.keys(state.blog.blogs)) {
      const foundBlog = state.blog.blogs[type].blogs.find(b => b.id === blogId);
      if (foundBlog) return { blog: foundBlog, blogType: type };
    }
    return { blog: null, blogType: null };
  });

  const loading = useSelector((state: RootState) => state.blog.status === "loading");
  const error = useSelector((state: RootState) => state.blog.error);

  // Scroll to comments if coming from a location with focusComment
  useEffect(() => {
    if ((location.state as any)?.focusComment) {
      setTimeout(() => {
        const commentsSection = document.getElementById("BlogDetailPage-comments-section");
        if (commentsSection) {
          commentsSection.scrollIntoView({ behavior: "smooth" });
          commentsSection.focus();
        }
      }, 100);
    }
  }, [location.state]);

  // Toggle expanded state for comments
  const toggleExpandedComment = (commentId: string) => {
    setExpandedComments(prev => {
      const newSet = new Set(prev);
      if (newSet.has(commentId)) {
        newSet.delete(commentId);
      } else {
        newSet.add(commentId);
      }
      return newSet;
    });
  };

  // Actions
  const handleLike = async () => {
    if (!blog || !blogType) return;
    try {
      dispatch(likeBlog({ blogType, blogId: blog.id }));
    } catch (err) {
      console.error("Error liking blog:", err);
    }
  };

  const handleShare = async () => {
    if (!blog || !blogType) return;
    try {
      dispatch(shareBlog({ blogType, blogId: blog.id }));
    } catch (err) {
      console.error("Error sharing blog:", err);
      alert("Error sharing blog. Please try again.");
    }
  };

  const handleSubmitComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!blog || !blogType || !newComment.trim()) return;
    try {
      setCommentLoading(true);
      await dispatch(
        addCommentToBlog({
          blogType,
          blogId: blog.id,
          text: newComment,
        })
      ).unwrap();
      setNewComment("");
    } catch (err) {
      console.error("Error posting comment:", err);
      alert("Error posting comment. Please try again.");
    } finally {
      setCommentLoading(false);
    }
  };

  const handleUserClick = (userId: number) => {
    navigate(`/profile/${userId}`);
  };

  const handleLikeComment = async (commentId: string) => {
    if (!blog || !blogType) return;
    try {
      dispatch(likeComment({ blogType, blogId: blog.id, commentId }));
    } catch (err) {
      console.error("Error liking comment:", err);
    }
  };

  const handleReplyToComment = async (commentId: string, text: string) => {
    if (!blog || !blogType || !text.trim()) return;
    try {
      await dispatch(
        addReplyToCommentThunk({
          blogType,
          blogId: blog.id,
          commentId,
          text,
        })
      ).unwrap();
      dispatch(
        setReplyingState({
          blogType,
          blogId: blog.id,
          commentId,
          isReplying: false,
        })
      );
      dispatch(
        setReplyText({
          blogType,
          blogId: blog.id,
          commentId,
          text: "",
        })
      );
    } catch (err) {
      console.error("Error posting reply:", err);
      alert("Error posting reply. Please try again.");
    }
  };

  const toggleReplying = (commentId: string, isReplying: boolean) => {
    if (!blog || !blogType) return;
    dispatch(
      setReplyingState({
        blogType,
        blogId: blog.id,
        commentId,
        isReplying,
      })
    );
    if (!isReplying) {
      dispatch(
        setReplyText({
          blogType,
          blogId: blog.id,
          commentId,
          text: "",
        })
      );
    }
  };

  // Recursively render comments/replies
  const CommentItem = ({ comment, depth = 0 }: { comment: any; depth?: number }) => {
    const [localReplyText, setLocalReplyText] = useState("");
    const isReplying = comment.is_replying || false;
    const hasReplies = comment.replies && comment.replies.length > 0;
    const isExpanded = expandedComments.has(comment.id);
    
    return (
      <div
        className={`BlogDetailPage-comment ${depth > 0 ? "BlogDetailPage-comment-reply" : ""}`}
        style={{ 
          marginLeft: depth > 0 ? `${Math.min(depth, 3) * 12}px` : '0',
          maxWidth: depth > 3 ? `calc(100% - ${3 * 12}px)` : '100%'
        }}
      >
        <div className="BlogDetailPage-comment-header">
          <img
            src={comment.user?.profile_pic || "/default-profile.png"}
            alt={comment.user?.name || "User"}
            className="BlogDetailPage-comment-user-image"
            onClick={() => comment.user && handleUserClick(comment.user.id)}
          />
          <div className="BlogDetailPage-comment-user-info">
            <strong
              className="BlogDetailPage-comment-user-name"
              onClick={() => comment.user && handleUserClick(comment.user.id)}
            >
              {comment.user?.name}
            </strong>
            <p className="BlogDetailPage-comment-date">{new Date(comment.created_at).toLocaleString()}</p>
          </div>
        </div>
        <p className="BlogDetailPage-comment-text">{comment.text}</p>
        <div className="BlogDetailPage-comment-actions">
          <button
            type="button"
            className={`BlogDetailPage-comment-action ${comment.has_liked ? "BlogDetailPage-active" : ""}`}
            onClick={() => handleLikeComment(comment.id)}
          >
            ❤️ ({comment.likes ? comment.likes.length : 0})
          </button>
          <button
            type="button"
            className="BlogDetailPage-comment-action"
            onClick={() => toggleReplying(comment.id, !isReplying)}
          >
            💬 Reply
          </button>
          {hasReplies && (
            <button
              type="button"
              className="BlogDetailPage-comment-action"
              onClick={() => toggleExpandedComment(comment.id)}
            >
              {isExpanded ? '▲ Hide Replies' : `▼ View Replies (${comment.replies.length})`}
            </button>
          )}
        </div>
        {isReplying && (
          <div className="BlogDetailPage-reply-form">
            <textarea
              className="BlogDetailPage-reply-input"
              placeholder="Write a reply..."
              value={localReplyText}
              onChange={(e) => setLocalReplyText(e.target.value)}
              autoFocus
            />
            <div className="BlogDetailPage-reply-actions">
              <button
                type="button"
                className="BlogDetailPage-reply-cancel"
                onClick={() => {
                  toggleReplying(comment.id, false);
                  setLocalReplyText("");
                }}
              >
                Cancel
              </button>
              <button
                type="button"
                className="BlogDetailPage-reply-submit"
                onClick={async () => {
                  await handleReplyToComment(comment.id, localReplyText);
                  setLocalReplyText("");
                  // Auto-expand to show the new reply
                  if (!isExpanded) {
                    toggleExpandedComment(comment.id);
                  }
                }}
                disabled={!localReplyText.trim()}
              >
                Post Reply
              </button>
            </div>
          </div>
        )}
        {hasReplies && isExpanded && (
          <div className="BlogDetailPage-comment-replies">
            {comment.replies.map((reply: any) => (
              <CommentItem key={reply.id} comment={reply} depth={depth + 1} />
            ))}
          </div>
        )}
      </div>
    );
  };

  // Calculate displayed comment count
  const actualCommentCount =
    blog?.footer.comments.filter((id: string) => !id.startsWith("temp-")).length || 0;

  if (loading) return <div className="BlogDetailPage-loading">Loading blog...</div>;
  if (error) return <div className="BlogDetailPage-error">Error loading blog: {error}</div>;
  if (!blog) return <div className="BlogDetailPage-not-found">Blog not found</div>;

  // Helper for report titles
  const formatReportTitle = (report_kind: string, time_type: string): string => {
    const kind = report_kind === "activity_report" ? "Activity" : "Initiation";
    const time = time_type.charAt(0).toUpperCase() + time_type.slice(1);
    return `${time} ${kind} Report`;
  };

  // Helper for clicking on report
  const handleReportClick = (
    report_kind?: string,
    time_type?: string,
    id?: string,
    level?: string
  ) => {
    if (!report_kind || !time_type || !id || !level) return;
    if (report_kind === "activity_report") {
      navigate(`/activity-reports/${time_type}/${id}/${level}`);
    } else {
      navigate(`/reports/${time_type}/${id}/${level}`);
    }
  };

  return (
    <div className="BlogDetailPage-container">
      <button onClick={() => navigate(-1)} className="BlogDetailPage-back-button">
        ← Back
      </button>
      <div className="BlogDetailPage-content">
        {/* Blog Header */}
        {blog.header && blog.header.user && (
          <div className="BlogDetailPage-header">
            <img
              src={blog.header.user.profile_pic || "/default-profile.png"}
              alt={blog.header.user.name}
              className="BlogDetailPage-user-image"
              onClick={() => handleUserClick(blog.header.user.id)}
            />
            <div className="BlogDetailPage-user-info">
              <h3
                className="BlogDetailPage-user-name"
                onClick={() => handleUserClick(blog.header.user.id)}
              >
                {blog.header.user.name}
              </h3>
              <p className="BlogDetailPage-user-relation">
                {blog.header.user.relation}
              </p>
              <p className="BlogDetailPage-meta">
                {new Date(blog.header.created_at).toLocaleString()} •{" "}
                {blog.header.type}
              </p>
              {blog.header.narrative && (
                <p className="BlogDetailPage-narrative">
                  {blog.header.narrative}
                </p>
              )}
            </div>
          </div>
        )}
        {/* Blog Body */}
        <div className="BlogDetailPage-body">
          {/* Target User */}
          {blog.body.body_type_fields?.target_user && (
            <div
              className="BlogDetailPage-target-user"
              onClick={() =>
                handleUserClick(blog.body.body_type_fields.target_user!.id)
              }
            >
              <img
                src={
                  blog.body.body_type_fields.target_user.profile_pic ||
                  "/default-profile.png"
                }
                alt={blog.body.body_type_fields.target_user.name}
                className="BlogDetailPage-target-user-image"
              />
              <div className="BlogDetailPage-target-user-info">
                <span className="BlogDetailPage-target-user-name">
                  {blog.body.body_type_fields.target_user.name}
                </span>
                <span className="BlogDetailPage-target-user-relation">
                  ({blog.body.body_type_fields.target_user.relation})
                </span>
              </div>
            </div>
          )}
          {/* Milestone */}
          {blog.body.body_type_fields?.milestone && (
            <div className="BlogDetailPage-milestone">
              <div className="BlogDetailPage-milestone-content">
                <h4 className="BlogDetailPage-milestone-title">
                  {blog.body.body_type_fields.milestone.title}
                </h4>
                {blog.body.body_type_fields.milestone.text && (
                  <p className="BlogDetailPage-milestone-text">
                    {blog.body.body_type_fields.milestone.text}
                  </p>
                )}
              </div>
              {blog.body.body_type_fields.milestone.photo_url && (
                <div className="BlogDetailPage-milestone-image-container">
                  <img
                    src={blog.body.body_type_fields.milestone.photo_url}
                    alt={blog.body.body_type_fields.milestone.title}
                    className="BlogDetailPage-milestone-image"
                    onError={(e) => {
                      const target = e.target as HTMLImageElement;
                      target.src = "http://localhost:3000/initiation/1.jpg";
                    }}
                  />
                </div>
              )}
            </div>
          )}
          {/* Report insight */}
          {blog.header.type === "report_insight" &&
            blog.body.body_type_fields?.report_kind && (
              <div
                className="BlogDetailPage-report BlogDetailPage-report-insight"
                tabIndex={0}
                role="button"
                onClick={() =>
                  handleReportClick(
                    blog.body.body_type_fields.report_kind,
                    blog.body.body_type_fields.time_type,
                    blog.body.body_type_fields.id,
                    blog.body.body_type_fields.level
                  )
                }
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    handleReportClick(
                      blog.body.body_type_fields.report_kind,
                      blog.body.body_type_fields.time_type,
                      blog.body.body_type_fields.id,
                      blog.body.body_type_fields.level
                    );
                  }
                }}
              >
                <h4 className="BlogDetailPage-report-title">
                  {formatReportTitle(
                    blog.body.body_type_fields.report_kind,
                    blog.body.body_type_fields.time_type || ""
                  )}
                </h4>
                {blog.body.body_type_fields.date && (
                  <p className="BlogDetailPage-report-date">
                    {blog.body.body_type_fields.date}
                  </p>
                )}
                {blog.body.body_type_fields.location && (
                  <p className="BlogDetailPage-report-location">
                    <strong>📍</strong>{" "}
                    {blog.body.body_type_fields.location}
                  </p>
                )}
                {typeof blog.body.body_type_fields.new_users !==
                  "undefined" && (
                  <p className="BlogDetailPage-report-users">
                    <strong>New Users:</strong>{" "}
                    {blog.body.body_type_fields.new_users}
                  </p>
                )}
              </div>
            )}
          {/* Other type-specific cases */}
          {blog.header.type === "consumption" && (
            <>
              {blog.body.body_type_fields?.title && (
                <p className="BlogDetailPage-consumption-title">
                  <strong>Title:</strong> {blog.body.body_type_fields.title}
                </p>
              )}
              {blog.body.body_type_fields?.url && (
                <p className="BlogDetailPage-consumption-url">
                  <strong>URL:</strong>{" "}
                  <a
                    href={blog.body.body_type_fields.url}
                    target="_blank"
                    rel="noreferrer"
                    className="BlogDetailPage-link"
                  >
                    {blog.body.body_type_fields.url}
                  </a>
                </p>
              )}
            </>
          )}
          {blog.header.type === "answering_question" &&
            blog.body.body_type_fields?.question?.text && (
              <p className="BlogDetailPage-question">
                {blog.body.body_type_fields.question.text}
              </p>
            )}
          {blog.header.type === "failed_initiation" && (
            <>
              {blog.body.body_type_fields?.location && (
                <p className="BlogDetailPage-failed-location">
                  <strong>📍</strong>{" "}
                  {blog.body.body_type_fields.location}
                </p>
              )}
              {blog.body.body_type_fields?.target_details && (
                <p className="BlogDetailPage-target-details">
                  <strong>Other Details:</strong>{" "}
                  {blog.body.body_type_fields.target_details}
                </p>
              )}
              {blog.body.body_type_fields?.failure_reason && (
                <p className="BlogDetailPage-failure-reason">
                  <strong>Failure Reason:</strong>{" "}
                  {blog.body.body_type_fields.failure_reason}
                </p>
              )}
            </>
          )}
          {/* Main Blog Body text */}
          <div className="BlogDetailPage-body-text">
            <p>{blog.body.body_text ?? "No content available"}</p>
          </div>
        </div>
        {/* Footer actions */}
        <div className="BlogDetailPage-actions">
          <button
            type="button"
            className={`BlogDetailPage-action-btn BlogDetailPage-like-btn ${
              blog.footer.has_liked ? "BlogDetailPage-active" : ""
            }`}
            onClick={handleLike}
          >
            ❤️ Like ({blog.footer.likes.length})
          </button>
          <button
            type="button"
            className={`BlogDetailPage-action-btn BlogDetailPage-share-btn ${
              blog.footer.has_shared ? "BlogDetailPage-active" : ""
            }`}
            onClick={handleShare}
          >
            🔄 {blog.footer.has_shared ? "Unshare" : "Share"} ({blog.footer.shares.length})
          </button>
        </div>
      </div>
      {/* Comments Section */}
      <div id="BlogDetailPage-comments-section" className="BlogDetailPage-comments" tabIndex={-1}>
        <h3 className="BlogDetailPage-comments-title">Comments ({actualCommentCount})</h3>
        {/* New Comment Form */}
        <form onSubmit={handleSubmitComment} className="BlogDetailPage-comment-form">
          <textarea
            className="BlogDetailPage-comment-input"
            placeholder="Write a comment..."
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
          />
          <button
            type="submit"
            className="BlogDetailPage-comment-submit"
            disabled={commentLoading || !newComment.trim()}
          >
            {commentLoading ? "Posting..." : "Post Comment"}
          </button>
        </form>
        {/* Comment List */}
        <div className="BlogDetailPage-comment-list">
          {blog.comments.length === 0 ? (
            <p className="BlogDetailPage-no-comments">No comments yet.</p>
          ) : (
            blog.comments.map((comment: any) => (
              <CommentItem key={comment.id} comment={comment} />
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default BlogDetailPage;