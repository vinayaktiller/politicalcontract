import React, { useEffect, useState } from "react";
import { useParams, useNavigate, useLocation } from "react-router-dom";
import api from "../../../../api";

// ------------------
// Types
// ------------------
interface User {
  id: number;
  name: string;
  profile_pic: string | null;
  relation: string;
}

interface Milestone {
  id: string;
  title: string;
  text: string;
  photo_url: string | null;
  type: string | null;
  photo_id: number | null;
}

interface BlogHeader {
  user: User;
  type: string;
  created_at: string;
  narrative?: string;
}

interface BlogBody {
  body_text: string | null;
  body_type_fields: {
    target_user?: User;
    milestone?: Milestone;
    report_type?: string | null;
    report_id?: string | null;
    report_kind?: string;
    time_type?: string;
    id?: string;
    level?: string;
    location?: string;
    new_users?: number;
    date?: string;
    url?: string | null;
    contribution?: string | null;
    questionid?: number | null;
    country_id?: number | null;
    state_id?: number | null;
    district_id?: number | null;
    subdistrict_id?: number | null;
    village_id?: number | null;
    target_details?: string | null;
    failure_reason?: string | null;
    title?: string | null;
    question?: {
      id: number | null;
      text: string | null;
      rank: number | null;
    };
  };
}

interface BlogFooter {
  likes: number[];
  relevant_count: number[];
  irrelevant_count: number[];
  shares: number[];
  comments: string[];
  has_liked: boolean;
  has_shared: boolean;
}

interface Blog {
  id: string;
  header: BlogHeader;
  body: BlogBody;
  footer: BlogFooter;
}

interface Comment {
  id: string;
  user: User;
  text: string;
  created_at: string;
  replies?: Comment[];
}

// API Response Types
interface ApiResponse<T> {
  data: T;
  status: number;
  statusText: string;
  headers: any;
  config: any;
}

interface BlogApiResponse {
  blog?: Blog;
}

interface CommentsApiResponse {
  comments?: Comment[];
}

interface LikeShareResponse {
  action: string;
}

interface CommentApiResponse {
  comment?: Comment;
}

// ------------------
// Component
// ------------------
const BlogDetailPage: React.FC = () => {
  const { blogId } = useParams<{ blogId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const [blog, setBlog] = useState<Blog | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [newComment, setNewComment] = useState("");
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [commentLoading, setCommentLoading] = useState<boolean>(false);

  // ------------------
  // Fetch Blog + Comments
  // ------------------
  useEffect(() => {
    const fetchBlog = async () => {
      if (!blogId) return;

      try {
        setLoading(true);
        const response = await api.get<BlogApiResponse>(`/api/blog/blogs/${blogId}/`);
        
        // Check if the response has a nested blog property
        const blogData = (response.data as BlogApiResponse).blog || response.data;
        setBlog(blogData as Blog);
        console.log("Blog fetched:", blogData);

        setError(null);

        const commentsResponse = await api.get<CommentsApiResponse>(
          `/api/blog/blogs/${blogId}/comments/`
        );
        
        // Check if comments are nested in a property
        const commentsData = (commentsResponse.data as CommentsApiResponse).comments || commentsResponse.data;
        setComments(commentsData as Comment[]);
      } catch (err: any) {
        setError(err.message || "Error loading blog");
        setBlog(null);
      } finally {
        setLoading(false);
      }
    };

    fetchBlog();
  }, [blogId]);

  // ------------------
  // Scroll to comments if asked
  // ------------------
  useEffect(() => {
    if ((location.state as any)?.focusComment) {
      setTimeout(() => {
        const commentsSection = document.getElementById("comments-section");
        if (commentsSection) {
          commentsSection.scrollIntoView({ behavior: "smooth" });
          commentsSection.focus();
        }
      }, 100);
    }
  }, [location.state]);

  // ------------------
  // Actions
  // ------------------
  const handleLike = async () => {
    if (!blog) return;

    try {
      const response = await api.post<LikeShareResponse>(`/api/blog/blogs/${blog.id}/like/`);
      const data = response.data;

      setBlog((prevBlog) => {
        if (!prevBlog) return null;
        return {
          ...prevBlog,
          footer: {
            ...prevBlog.footer,
            likes:
              data.action === "added"
                ? [...prevBlog.footer.likes, 0]
                : prevBlog.footer.likes.slice(0, -1),
            has_liked: data.action === "added",
          },
        };
      });
    } catch (err) {
      console.error("Error liking blog:", err);
    }
  };

  const handleShare = async () => {
    if (!blog) return;

    try {
      const response = await api.post<LikeShareResponse>(`/api/blog/blogs/${blog.id}/share/`);
      const data = response.data;

      setBlog((prevBlog) => {
        if (!prevBlog) return null;
        return {
          ...prevBlog,
          footer: {
            ...prevBlog.footer,
            shares:
              data.action === "added"
                ? [...prevBlog.footer.shares, 0]
                : prevBlog.footer.shares.slice(0, -1),
            has_shared: data.action === "added",
          },
        };
      });

      alert(
        data.action === "added"
          ? "Blog shared successfully!"
          : "Blog unshared successfully!"
      );
    } catch (err) {
      console.error("Error sharing blog:", err);
      alert("Error sharing blog. Please try again.");
    }
  };

  const handleSubmitComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!blog || !newComment.trim()) return;

    try {
      setCommentLoading(true);
      const response = await api.post<CommentApiResponse>(`/api/blog/blogs/${blog.id}/comments/`, {
        text: newComment.trim(),
      });

      const commentData = (response.data as CommentApiResponse).comment || response.data;
      setComments((prevComments) => [
        commentData as Comment,
        ...prevComments,
      ]);
      setNewComment("");

      setBlog((prevBlog) => {
        if (!prevBlog) return null;
        return {
          ...prevBlog,
          footer: {
            ...prevBlog.footer,
            comments: [...prevBlog.footer.comments, "new-comment-id"],
          },
        };
      });
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

  const formatReportTitle = (
    report_kind: string,
    time_type: string
  ): string => {
    const kind = report_kind === "activity_report" ? "Activity" : "Initiation";
    const time =
      time_type.charAt(0).toUpperCase() + time_type.slice(1);
    return `${time} ${kind} Report`;
  };

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

  // ------------------
  // Render
  // ------------------

  if (loading) return <div>Loading blog...</div>;
  if (error) return <div>Error loading blog: {error}</div>;
  if (!blog) return <div>Blog not found</div>;

  // Add safe access to nested properties
  const header = blog.header || {} as BlogHeader;
  const body = blog.body || {} as BlogBody;
  const footer = blog.footer || {} as BlogFooter;

  return (
    <div
      className="blog-detail-page"
      style={{
        padding: "2rem",
        maxWidth: "800px",
        margin: "0 auto",
        paddingTop: "50px",
      }}
    >
      <button
        onClick={() => navigate(-1)}
        style={{
          marginBottom: "1rem",
          padding: "0.5rem 1rem",
          background: "#f0f0f0",
          border: "none",
          borderRadius: "4px",
          cursor: "pointer",
        }}
      >
        ← Back
      </button>

      {/* Blog Content */}
      <div
        style={{
          marginBottom: "2rem",
          border: "1px solid #eee",
          borderRadius: "8px",
          padding: "1.5rem",
        }}
      >
        {/* Header */}
        {header && header.user && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              marginBottom: "1rem",
            }}
          >
            <img
              src={header.user.profile_pic || "/default-profile.png"}
              alt={header.user.name}
              style={{
                width: "50px",
                height: "50px",
                borderRadius: "50%",
                marginRight: "1rem",
                objectFit: "cover",
                cursor: "pointer",
              }}
              onClick={() => handleUserClick(header.user.id)}
            />
            <div style={{ flex: 1 }}>
              <h3
                style={{ margin: 0, cursor: "pointer" }}
                onClick={() => handleUserClick(header.user.id)}
                className="user-clickable"
              >
                {header.user.name}
              </h3>
              <p style={{ margin: 0, color: "#666" }}>
                {header.user.relation}
              </p>
              <p style={{ margin: 0, color: "#666" }}>
                {new Date(header.created_at).toLocaleString()} •{" "}
                {header.type}
              </p>
              {header.narrative && (
                <p
                  style={{
                    margin: "0.5rem 0 0 0",
                    fontStyle: "italic",
                    color: "#666",
                  }}
                >
                  {header.narrative}
                </p>
              )}
            </div>
          </div>
        )}

        {/* Body */}
        <div style={{ marginBottom: "1rem" }}>
          {/* Target User */}
          {body.body_type_fields &&
            body.body_type_fields.target_user && (
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  margin: "0.5rem 0",
                  cursor: "pointer",
                }}
                onClick={() =>
                  handleUserClick(
                    body.body_type_fields.target_user!.id
                  )
                }
                className="user-clickable"
              >
                <img
                  src={
                    body.body_type_fields.target_user.profile_pic ||
                    "/default-profile.png"
                  }
                  alt={body.body_type_fields.target_user.name}
                  style={{
                    width: "30px",
                    height: "30px",
                    borderRadius: "50%",
                    marginRight: "0.5rem",
                    objectFit: "cover",
                  }}
                />
                <div>
                  <span style={{ fontWeight: "bold" }}>
                    {body.body_type_fields.target_user.name}
                  </span>
                  <span
                    style={{ color: "#666", marginLeft: "0.5rem" }}
                  >
                    ({body.body_type_fields.target_user.relation})
                  </span>
                </div>
              </div>
            )}

          {/* Milestone */}
          {body.body_type_fields &&
            body.body_type_fields.milestone && (
              <div
                style={{
                  margin: "1rem 0",
                  border: "1px solid #e0e0e0",
                  borderRadius: "8px",
                  overflow: "hidden",
                }}
              >
                <div style={{ padding: "1rem" }}>
                  <h4 style={{ margin: "0 0 0.5rem 0" }}>
                    {body.body_type_fields.milestone.title}
                  </h4>
                  {body.body_type_fields.milestone.text && (
                    <p
                      style={{
                        margin: "0 0 1rem 0",
                        color: "#666",
                      }}
                    >
                      {body.body_type_fields.milestone.text}
                    </p>
                  )}
                </div>
                {body.body_type_fields.milestone.photo_url && (
                  <div
                    style={{
                      position: "relative",
                      width: "100%",
                      height: "300px",
                      overflow: "hidden",
                    }}
                  >
                    <img
                      src={
                        body.body_type_fields.milestone.photo_url
                      }
                      alt={body.body_type_fields.milestone.title}
                      style={{
                        width: "100%",
                        height: "100%",
                        objectFit: "cover",
                        display: "block",
                      }}
                      onError={(e) => {
                        const target = e.target as HTMLImageElement;
                        target.src =
                          "http://localhost:3000/initiation/1.jpg";
                      }}
                    />
                  </div>
                )}
              </div>
            )}

          {/* Report insight */}
          {header.type === "report_insight" &&
            body.body_type_fields &&
            body.body_type_fields.report_kind && (
              <div
                className="report-insight-nav"
                style={{
                  margin: "1rem 0",
                  padding: "1rem",
                  border: "1px solid #e0e0e0",
                  borderRadius: "8px",
                  cursor: "pointer",
                }}
                tabIndex={0}
                role="button"
                onClick={() =>
                  handleReportClick(
                    body.body_type_fields.report_kind,
                    body.body_type_fields.time_type,
                    body.body_type_fields.id,
                    body.body_type_fields.level
                  )
                }
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    handleReportClick(
                      body.body_type_fields.report_kind,
                      body.body_type_fields.time_type,
                      body.body_type_fields.id,
                      body.body_type_fields.level
                    );
                  }
                }}
              >
                <h4 style={{ margin: "0 0 0.5rem 0" }}>
                  {formatReportTitle(
                    body.body_type_fields.report_kind,
                    body.body_type_fields.time_type || ""
                  )}
                </h4>
                {body.body_type_fields.date && (
                  <p
                    style={{
                      margin: "0 0 0.5rem 0",
                      color: "#666",
                    }}
                  >
                    {body.body_type_fields.date}
                  </p>
                )}
                {body.body_type_fields.location && (
                  <p
                    style={{
                      margin: "0 0 0.5rem 0",
                      color: "#666",
                    }}
                  >
                    <strong>📍</strong>{" "}
                    {body.body_type_fields.location}
                  </p>
                )}
                {typeof body.body_type_fields.new_users !==
                  "undefined" && (
                  <p
                    style={{
                      margin: "0 0 0.5rem 0",
                      color: "#666",
                    }}
                  >
                    <strong>New Users:</strong>{" "}
                    {body.body_type_fields.new_users}
                  </p>
                )}
              </div>
            )}

          {/* Other type-specific cases */}
          {header.type === "consumption" && (
            <>
              {body.body_type_fields &&
                body.body_type_fields.title && (
                  <p>
                    <strong>Title:</strong>{" "}
                    {body.body_type_fields.title}
                  </p>
                )}
              {body.body_type_fields &&
                body.body_type_fields.url && (
                  <p style={{ marginTop: "0.5rem" }}>
                    <strong>URL:</strong>{" "}
                    <a
                      href={body.body_type_fields.url}
                      target="_blank"
                      rel="noreferrer"
                    >
                      {body.body_type_fields.url}
                    </a>
                  </p>
                )}
            </>
          )}

          {header.type === "answering_question" &&
            body.body_type_fields &&
            body.body_type_fields.question?.text && (
              <p>{body.body_type_fields.question?.text}</p>
            )}

          {header.type === "failed_initiation" && (
            <>
              {body.body_type_fields &&
                body.body_type_fields.location && (
                  <p
                    style={{
                      margin: "0 0 0.5rem 0",
                      color: "#666",
                    }}
                  >
                    <strong>📍</strong>{" "}
                    {body.body_type_fields.location}
                  </p>
                )}
              {body.body_type_fields &&
                body.body_type_fields.target_details && (
                  <p>
                    <strong>Other Details:</strong>{" "}
                    {body.body_type_fields.target_details}
                  </p>
                )}
              {body.body_type_fields &&
                body.body_type_fields.failure_reason && (
                  <p
                    style={{
                      paddingTop: "1rem",
                      borderRadius: "4px",
                    }}
                  >
                    <strong>Failure Reason:</strong>{" "}
                    {body.body_type_fields.failure_reason}
                  </p>
                )}
            </>
          )}

          {/* Body text */}
          <div
            style={{
              marginTop: "1rem",
              padding: "1rem",
              backgroundColor: "#f5f5f5",
              borderRadius: "4px",
            }}
          >
            <p style={{ margin: 0 }}>
              {body.body_text ?? "No content available"}
            </p>
          </div>
        </div>

        {/* Footer actions */}
        <div style={{ display: "flex", alignItems: "center" }}>
          <button
            className={`reaction-btn btn-like ${
              footer.has_liked ? "active" : ""
            }`}
            onClick={handleLike}
            style={{ backgroundColor: "transparent" }}
          >
            ❤️ Like ({footer.likes ? footer.likes.length : 0})
          </button>

          <button
            className={`reaction-btn btn-share ${
              footer.has_shared ? "active" : ""
            }`}
            onClick={handleShare}
            style={{ backgroundColor: "transparent" }}
          >
            🔄 {footer.has_shared ? "Unshare" : "Share"} (
            {footer.shares ? footer.shares.length : 0})
          </button>
        </div>
      </div>

      {/* Comments */}
      <div id="comments-section" tabIndex={-1}>
        <h3>
          Comments ({footer.comments ? footer.comments.length : 0})
        </h3>

        {/* Comment Form */}
        <form onSubmit={handleSubmitComment} className="comment-form">
          <textarea
            className="comment-input"
            placeholder="Write a comment..."
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
          />
          <button
            type="submit"
            className="comment-submit-btn"
            disabled={commentLoading || !newComment.trim()}
          >
            {commentLoading ? "Posting..." : "Post Comment"}
          </button>
        </form>

        {/* Comment List */}
        <div className="comment-list">
          {comments.length === 0 ? (
            <p>No comments yet.</p>
          ) : (
            comments.map((comment) => (
              <div
                key={comment.id}
                style={{
                  marginBottom: "1rem",
                  padding: "1rem",
                  border: "1px solid #e0e0e0",
                  borderRadius: "6px",
                }}
              >
                <div style={{ display: "flex", alignItems: "center" }}>
                  <img
                    src={comment.user?.profile_pic || "/default-profile.png"}
                    alt={comment.user?.name || "User"}
                    style={{
                      width: "35px",
                      height: "35px",
                      borderRadius: "50%",
                      marginRight: "0.5rem",
                      objectFit: "cover",
                      cursor: "pointer",
                    }}
                    onClick={() =>
                      comment.user &&
                      handleUserClick(comment.user.id)
                    }
                  />
                  <div>
                    <strong
                      style={{ cursor: "pointer" }}
                      onClick={() =>
                        comment.user &&
                        handleUserClick(comment.user.id)
                      }
                    >
                      {comment.user?.name}
                    </strong>
                    <p
                      style={{
                        margin: 0,
                        color: "#666",
                        fontSize: "0.85rem",
                      }}
                    >
                      {new Date(comment.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>
                <p style={{ margin: "0.5rem 0 0 0" }}>
                  {comment.text}
                </p>
                {/* Replies */}
                {comment.replies && comment.replies.length > 0 && (
                  <div
                    style={{
                      marginTop: "0.5rem",
                      paddingLeft: "2rem",
                    }}
                  >
                    {comment.replies.map((reply) => (
                      <div
                        key={reply.id}
                        style={{
                          marginBottom: "0.5rem",
                          padding: "0.5rem",
                          borderLeft: "2px solid #ddd",
                        }}
                      >
                        <div
                          style={{ display: "flex", alignItems: "center" }}
                        >
                          <img
                            src={
                              reply.user?.profile_pic ||
                              "/default-profile.png"
                            }
                            alt={reply.user?.name || "User"}
                            style={{
                              width: "28px",
                              height: "28px",
                              borderRadius: "50%",
                              marginRight: "0.5rem",
                              objectFit: "cover",
                              cursor: "pointer",
                            }}
                            onClick={() =>
                              reply.user &&
                              handleUserClick(reply.user.id)
                            }
                          />
                          <div>
                            <strong
                              style={{
                                cursor: "pointer",
                                fontSize: "0.9rem",
                              }}
                              onClick={() =>
                                reply.user &&
                                handleUserClick(reply.user.id)
                              }
                            >
                              {reply.user?.name}
                            </strong>
                            <p
                              style={{
                                margin: 0,
                                color: "#666",
                                fontSize: "0.75rem",
                              }}
                            >
                              {new Date(reply.created_at).toLocaleString()}
                            </p>
                          </div>
                        </div>
                        <p
                          style={{
                            margin: "0.25rem 0 0 0",
                            fontSize: "0.9rem",
                          }}
                        >
                          {reply.text}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default BlogDetailPage;