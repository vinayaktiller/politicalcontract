// BlogListPage.tsx
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../../../api';

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

const BlogListPage: React.FC = () => {
  const [blogs, setBlogs] = useState<Blog[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchBlogs = async () => {
      try {
        const response = await api.get<Blog[]>('/api/blog/circle-blogs/');
        setBlogs(response.data);
        setError(null);
      } catch (err: any) {
        setError(err.message || 'Unknown error');
        setBlogs([]);
      } finally {
        setLoading(false);
      }
    };
    fetchBlogs();
  }, []);

  const handleLike = async (blogId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      const response = await api.post(`/api/blog/blogs/${blogId}/like/`);
      // Assert the type of response.data
      const data = response.data as { action: string };
      // Update the local state with the new like status
      setBlogs(prevBlogs => 
        prevBlogs.map(blog => {
          if (blog.id === blogId) {
            return {
              ...blog,
              footer: {
                ...blog.footer,
                likes: data.action === 'added' 
                  ? [...blog.footer.likes, 0] // Add a placeholder, we'll update count
                  : blog.footer.likes.slice(0, -1), // Remove last like
                has_liked: data.action === 'added'
              }
            };
          }
          return blog;
        })
      );
    } catch (err: any) {
      console.error('Error liking blog:', err);
    }
  };

  const handleShare = async (blogId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      const response = await api.post(`/api/blog/blogs/${blogId}/share/`);
      // Assert the type of response.data
      const data = response.data as { action: string };
      // Update the local state with the new share status
      setBlogs(prevBlogs => 
        prevBlogs.map(blog => {
          if (blog.id === blogId) {
            return {
              ...blog,
              footer: {
                ...blog.footer,
                shares: data.action === 'added' 
                  ? [...blog.footer.shares, 0] // Add a placeholder for share
                  : blog.footer.shares.slice(0, -1), // Remove last share
                has_shared: data.action === 'added'
              }
            };
          }
          return blog;
        })
      );
      
      if (data.action === 'added') {
        alert('Blog shared successfully!');
      } else {
        alert('Blog unshared successfully!');
      }
    } catch (err: any) {
      console.error('Error sharing blog:', err);
      alert('Error sharing blog. Please try again.');
    }
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

  const formatReportTitle = (report_kind: string, time_type: string): string => {
    const kind = report_kind === 'activity_report' ? 'Activity' : 'Initiation';
    const time = time_type.charAt(0).toUpperCase() + time_type.slice(1);
    return `${time} ${kind} Report`;
  };

  const handleReportClick = (report_kind?: string, time_type?: string, id?: string, level?: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    if (!report_kind || !time_type || !id || !level) return;
    if (report_kind === 'activity_report') {
      navigate(`/activity-reports/${time_type}/${id}/${level}`);
    } else {
      navigate(`/reports/${time_type}/${id}/${level}`);
    }
  };

  if (loading) return <div>Loading blogs...</div>;
  if (error) return <div>Error loading blogs: {error}</div>;

  return (
    <div className="blog-list-page" style={{ padding: '2rem', maxWidth: '800px', paddingTop: '50px' }}>
      <style>
        {`
        .report-insight-nav {
          cursor: pointer;
          transition: box-shadow 0.2s, border-color 0.2s;
        }
        .report-insight-nav:hover {
          box-shadow: 0 2px 12px rgba(40,80,120,0.11), 0 2px 4px rgba(40,80,120,0.15);
          border-color: #288fef;
          background: #f2faff;
        }
        .reaction-btn {
          cursor: pointer;
          padding: 0.5rem 1rem;
          border: 1px solid #ddd;
          border-radius: 20px;
          margin-right: 0.5rem;
          background: white;
          transition: all 0.2s ease;
          display: flex;
          align-items: center;
          font-size: 14px;
          color: #555;
        }
        .reaction-btn:hover {
          background: #f8f9fa;
          transform: translateY(-1px);
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .reaction-btn.active {
          background: #e6f7ff;
          border-color: #1890ff;
          color: #1890ff;
        }
        .reaction-btn i {
          margin-right: 5px;
        }
        .btn-like.active {
          color: #1890ff;
          border-color: #1890ff;
          background: #e6f7ff;
        }
        .btn-share.active {
          color: #1890ff;
          border-color: #1890ff;
          background: #e6f7ff;
        }
        .blog-card {
          cursor: pointer;
          transition: all 0.2s ease;
        }
        .blog-card:hover {
          background-color: #f9f9f9;
          transform: translateY(-2px);
          box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .user-clickable {
          cursor: pointer;
        }
        .user-clickable:hover {
          text-decoration: underline;
        }
        `}
      </style>
      <h1>Blogs</h1>
      {blogs.length === 0 && <p>No blogs found.</p>}
      <ul style={{ listStyle: 'none', padding: 0 }}>
        {blogs.slice().reverse().map((blog) => (
          <li 
            key={blog.id} 
            className="blog-card"
            style={{ 
              marginBottom: '2rem', 
              border: '1px solid #eee', 
              borderRadius: '8px',
              padding: '1.5rem',
              transition: 'all 0.2s ease'
            }}
            onClick={() => handleBlogClick(blog.id)}
          >
            {/* Header */}
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '1rem' }}>
              <img
                src={blog.header.user.profile_pic || '/default-profile.png'}
                alt={blog.header.user.name}
                style={{ 
                  width: '50px', 
                  height: '50px', 
                  borderRadius: '50%', 
                  marginRight: '1rem', 
                  objectFit: 'cover',
                  cursor: 'pointer'
                }}
                onClick={(e) => handleUserClick(blog.header.user.id, e)}
              />
              <div style={{ flex: 1 }}>
                <h3 
                  style={{ margin: 0, cursor: 'pointer' }}
                  onClick={(e) => handleUserClick(blog.header.user.id, e)}
                  className="user-clickable"
                >
                  {blog.header.user.name}
                </h3>
                <p style={{ margin: 0, color: '#666' }}>{blog.header.user.relation}</p>
                <p style={{ margin: 0, color: '#666' }}>
                  {new Date(blog.header.created_at).toLocaleString()} • {blog.header.type}
                </p>
                {blog.header.narrative && (
                  <p style={{ margin: '0.5rem 0 0 0', fontStyle: 'italic', color: '#666' }}>
                    {blog.header.narrative}
                  </p>
                )}
              </div>
            </div>

            {/* Body */}
            <div style={{ marginBottom: '1rem' }}>
              {/* Target user */}
              {blog.body.body_type_fields.target_user && (
                <div 
                  style={{ display: 'flex', alignItems: 'center', margin: '0.5rem 0', cursor: 'pointer' }}
                  onClick={(e) => {
                    e.stopPropagation();
                    if (blog.body.body_type_fields.target_user) {
                      handleUserClick(blog.body.body_type_fields.target_user.id, e);
                    }
                  }}
                  className="user-clickable"
                >
                  <img
                    src={blog.body.body_type_fields.target_user.profile_pic || '/default-profile.png'}
                    alt={blog.body.body_type_fields.target_user.name}
                    style={{ width: '30px', height: '30px', borderRadius: '50%', marginRight: '0.5rem', objectFit: 'cover' }}
                  />
                  <div>
                    <span style={{ fontWeight: 'bold' }}>{blog.body.body_type_fields.target_user.name}</span>
                    <span style={{ color: '#666', marginLeft: '0.5rem' }}>
                      ({blog.body.body_type_fields.target_user.relation})
                    </span>
                  </div>
                </div>
              )}

              {/* Milestone */}
              {blog.body.body_type_fields.milestone && (
                <div style={{ margin: '1rem 0', border: '1px solid #e0e0e0', borderRadius: '8px', overflow: 'hidden' }}>
                  <div style={{ padding: '1rem' }}>
                    <h4 style={{ margin: '0 0 0.5rem 0' }}>
                      {blog.body.body_type_fields.milestone.title}
                    </h4>
                    {blog.body.body_type_fields.milestone.text && (
                      <p style={{ margin: '0 0 1rem 0', color: '#666' }}>
                        {blog.body.body_type_fields.milestone.text}
                      </p>
                    )}
                  </div>
                  {blog.body.body_type_fields.milestone.photo_url && (
                    <div style={{ position: 'relative', width: '100%', height: '300px', overflow: 'hidden' }}>
                      <img
                        src={blog.body.body_type_fields.milestone.photo_url}
                        alt={blog.body.body_type_fields.milestone.title}
                        style={{
                          width: '100%',
                          height: '100%',
                          objectFit: 'cover',
                          display: 'block'
                        }}
                        onError={(e) => {
                          const target = e.target as HTMLImageElement;
                          target.src = 'http://localhost:3000/initiation/1.jpg';
                        }}
                      />
                    </div>
                  )}
                </div>
              )}

              {/* Report insight details */}
              {blog.header.type === 'report_insight' && blog.body.body_type_fields.report_kind && (
                <div
                  className="report-insight-nav"
                  style={{ margin: '1rem 0', padding: '1rem', border: '1px solid #e0e0e0', borderRadius: '8px' }}
                  tabIndex={0}
                  role="button"
                  onClick={(e) =>
                    handleReportClick(
                      blog.body.body_type_fields.report_kind,
                      blog.body.body_type_fields.time_type,
                      blog.body.body_type_fields.id,
                      blog.body.body_type_fields.level,
                      e
                    )
                  }
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      handleReportClick(
                        blog.body.body_type_fields.report_kind,
                        blog.body.body_type_fields.time_type,
                        blog.body.body_type_fields.id,
                        blog.body.body_type_fields.level
                      );
                    }
                  }}
                  aria-label="Visit report insight"
                >
                  <h4 style={{ margin: '0 0 0.5rem 0' }}>
                    {formatReportTitle(
                      blog.body.body_type_fields.report_kind,
                      blog.body.body_type_fields.time_type || ''
                    )}
                  </h4>
                  {blog.body.body_type_fields.date && (
                    <p style={{ margin: '0 0 0.5rem 0', color: '#666' }}>
                      {blog.body.body_type_fields.date}
                    </p>
                  )}
                  {blog.body.body_type_fields.location && (
                    <p style={{ margin: '0 0 0.5rem 0', color: '#666' }}>
                      <strong>📍</strong> {blog.body.body_type_fields.location}
                    </p>
                  )}
                  {blog.body.body_type_fields.new_users !== undefined && (
                    <p style={{ margin: '0 0 0.5rem 0', color: '#666' }}>
                      <strong>New Users:</strong> {blog.body.body_type_fields.new_users}
                    </p>
                  )}
                </div>
              )}

              {/* Other type-specific fields */}
              {blog.header.type === 'report_insight' && !blog.body.body_type_fields.report_kind && (
                <>
                  {blog.body.body_type_fields.report_type && (
                    <p>
                      <strong>Report Type:</strong> {blog.body.body_type_fields.report_type}
                    </p>
                  )}
                  {blog.body.body_type_fields.report_id && (
                    <p>
                      <strong>Report ID:</strong> {blog.body.body_type_fields.report_id}
                    </p>
                  )}
                </>
              )}
              {blog.header.type === 'consumption' && (
                <>
                  {blog.body.body_type_fields.title && (
                    <p>
                      <strong>Title:</strong> {blog.body.body_type_fields.title}
                    </p>
                  )}
                  {blog.body.body_type_fields.url && (
                    <p style={{ marginTop: '0.5rem' }}>
                      <strong>URL:</strong>{' '}
                      {blog.body.body_type_fields.url ? (
                        <a 
                          href={blog.body.body_type_fields.url} 
                          target="_blank" 
                          rel="noreferrer"
                          onClick={(e) => e.stopPropagation()}
                        >
                          {blog.body.body_type_fields.url}
                        </a>
                      ) : (
                        '-'
                      )}
                    </p>
                  )}
                </>
              )}
              {blog.header.type === 'answering_question' && blog.body.body_type_fields.question?.text && (
                <p>
                  {blog.body.body_type_fields.question?.text}
                </p>
              )}
              {blog.header.type === 'failed_initiation' && (
                <>
                  {blog.body.body_type_fields.location && (
                    <p style={{ margin: '0 0 0.5rem 0', color: '#666' }}>
                      <strong>📍</strong> {blog.body.body_type_fields.location}
                    </p>
                  )}
                  {blog.body.body_type_fields.target_details && (
                    <p>
                      <strong>Other Details:</strong> {blog.body.body_type_fields.target_details}
                    </p>
                  )}
                  {blog.body.body_type_fields.failure_reason && (
                    <p style={{
                      paddingTop: '1rem',
                      stroke: 'black',
                      borderRadius: '4px'
                    }}>
                      <strong>Failure Reason:</strong> {blog.body.body_type_fields.failure_reason}
                    </p>
                  )}
                </>
              )}

              {/* Body text */}
              <div
                style={{
                  marginTop: '1rem',
                  padding: '1rem',
                  backgroundColor: '#f5f5f5',
                  borderRadius: '4px'
                }}
              >
                <p style={{ margin: 0 }}>{blog.body.body_text ?? 'No content available'}</p>
              </div>
            </div>

            {/* Footer with reaction buttons */}
            <div 
              style={{ display: 'flex',  alignItems: 'center' }}
              onClick={(e) => e.stopPropagation()}
            >
              <button 
                className={`reaction-btn btn-like ${blog.footer.has_liked ? 'active' : ''}`}
                onClick={(e) => handleLike(blog.id, e)}
                style={{
                  backgroundColor: 'transparent',
                }}
              >
                <i className="far fa-heart"></i> Like ({blog.footer.likes.length})
              </button>
              
              <button 
                className={`reaction-btn btn-share ${blog.footer.has_shared ? 'active' : ''}`}
                onClick={(e) => handleShare(blog.id, e)}
                style={{
                  backgroundColor: 'transparent',
                }}
              >
                <i className="far fa-share-square"></i> {blog.footer.has_shared ? 'Unshare' : 'Share'} ({blog.footer.shares.length})
              </button>
              
              <span 
                style={{ backgroundColor: 'transparent', color: '#666', cursor: 'pointer' }}
                onClick={(e) => handleCommentClick(blog.id, e)}
                className="reaction-btn"
              >
                <i className="far fa-comment"></i> Comments ({blog.footer.comments.length})
              </span>
            </div>

          </li>
        ))}
      </ul>
    </div>
  );
};

export default BlogListPage;