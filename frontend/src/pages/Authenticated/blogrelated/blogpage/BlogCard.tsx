import React from 'react';
import { Blog } from './blogTypes';

interface BlogCardProps {
  blog: Blog;
  onBlogClick: (blogId: string) => void;
  onUserClick: (userId: number, e: React.MouseEvent) => void;
  onLikeClick: (blogId: string, e: React.MouseEvent) => void;
  onShareClick: (blogId: string, e: React.MouseEvent) => void;
  onCommentClick: (blogId: string, e: React.MouseEvent) => void;
  onReportClick: (report_kind?: string, time_type?: string, id?: string, level?: string, e?: React.MouseEvent) => void;
  formatReportTitle: (report_kind: string, time_type: string) => string;
}

const BlogCard: React.FC<BlogCardProps> = ({
  blog,
  onBlogClick,
  onUserClick,
  onLikeClick,
  onShareClick,
  onCommentClick,
  onReportClick,
  formatReportTitle
}) => {
  return (
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
      onClick={() => onBlogClick(blog.id)}
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
          onClick={(e) => onUserClick(blog.header.user.id, e)}
        />
        <div style={{ flex: 1 }}>
          <h3 
            style={{ margin: 0, cursor: 'pointer' }}
            onClick={(e) => onUserClick(blog.header.user.id, e)}
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
              onUserClick(blog.body.body_type_fields.target_user!.id, e);
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
              onReportClick(
                blog.body.body_type_fields.report_kind,
                blog.body.body_type_fields.time_type,
                blog.body.body_type_fields.id,
                blog.body.body_type_fields.level,
                e
              )
            }
            onKeyPress={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                onReportClick(
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
          onClick={(e) => onLikeClick(blog.id, e)}
          style={{
            backgroundColor: 'transparent',
          }}
        >
          <i className="far fa-heart"></i> Like ({blog.footer.likes.length})
        </button>
        
        <button 
          className={`reaction-btn btn-share ${blog.footer.has_shared ? 'active' : ''}`}
          onClick={(e) => onShareClick(blog.id, e)}
          style={{
            backgroundColor: 'transparent',
          }}
        >
          <i className="far fa-share-square"></i> {blog.footer.has_shared ? 'Unshare' : 'Share'} ({blog.footer.shares.length})
        </button>
        
        <span 
          style={{ backgroundColor: 'transparent', color: '#666', cursor: 'pointer' }}
          onClick={(e) => onCommentClick(blog.id, e)}
          className="reaction-btn"
        >
          <i className="far fa-comment"></i> Comments ({blog.footer.comments.length})
        </span>
      </div>
    </li>
  );
};

export default BlogCard;