import React from 'react';
import { Blog } from './blogTypes';
import './BlogListPage.css';

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
  // Calculate actual comment count (excluding temporary IDs)
  const actualCommentCount = blog.footer.comments.filter(id => !id.startsWith('temp-')).length;

  return (
    <li 
      key={blog.id} 
      className="blog-card"
      onClick={() => onBlogClick(blog.id)}
    >
      {/* Header */}
      <div className="blog-card-header">
        <img
          src={blog.header.user.profile_pic || '/default-profile.png'}
          alt={blog.header.user.name}
          className="blog-card-user-image"
          onClick={(e) => onUserClick(blog.header.user.id, e)}
        />
        <div className="blog-card-user-info">
          <h3 
            className="blog-card-user-name user-clickable"
            onClick={(e) => onUserClick(blog.header.user.id, e)}
          >
            {blog.header.user.name}
          </h3>
          <p className="blog-card-user-relation">{blog.header.user.relation}</p>
          <p className="blog-card-meta">
            {new Date(blog.header.created_at).toLocaleString()} • {blog.header.type}
          </p>
          {blog.header.narrative && (
            <p className="blog-card-narrative">
              {blog.header.narrative}
            </p>
          )}
        </div>
      </div>

      {/* Body */}
      <div className="blog-card-body">
        {/* Target user */}
        {blog.body.body_type_fields.target_user && (
          <div 
            className="blog-card-target-user user-clickable"
            onClick={(e) => {
              e.stopPropagation();
              onUserClick(blog.body.body_type_fields.target_user!.id, e);
            }}
          >
            <img
              src={blog.body.body_type_fields.target_user.profile_pic || '/default-profile.png'}
              alt={blog.body.body_type_fields.target_user.name}
              className="blog-card-target-user-image"
            />
            <div className="blog-card-target-user-info">
              <span className="blog-card-target-user-name">{blog.body.body_type_fields.target_user.name}</span>
              <span className="blog-card-target-user-relation">
                ({blog.body.body_type_fields.target_user.relation})
              </span>
            </div>
          </div>
        )}

        {/* Milestone */}
        {blog.body.body_type_fields.milestone && (
          <div className="blog-card-milestone">
            <div className="blog-card-milestone-content">
              <h4 className="blog-card-milestone-title">
                {blog.body.body_type_fields.milestone.title}
              </h4>
              {blog.body.body_type_fields.milestone.text && (
                <p className="blog-card-milestone-text">
                  {blog.body.body_type_fields.milestone.text}
                </p>
              )}
            </div>
            {blog.body.body_type_fields.milestone.photo_id && blog.body.body_type_fields.milestone.type && (
                <div className="BlogDetailPage-milestone-image-container">
                  <img
                    src={`http://pfs-ui-f7bnfbg9agb4cwcu.canadacentral-01.azurewebsites.net/${blog.body.body_type_fields.milestone.type}/${blog.body.body_type_fields.milestone.photo_id}.jpg`}
                    alt={blog.body.body_type_fields.milestone.title}
                    className="BlogDetailPage-milestone-image"
                    onError={(e) => {
                      const target = e.target as HTMLImageElement;
                      // target.src = "http://localhost:3000/initiation/1.jpg";
                      target.src = "https://pfs-ui-f7bnfbg9agb4cwcu.canadacentral-01.azurewebsites.net/initiation/1.jpg";
                    }}
                  />
                </div>
              )}
          </div>
        )}

        {/* Report insight details */}
        {blog.header.type === 'report_insight' && blog.body.body_type_fields.report_kind && (
          <div
            className="blog-card-report report-insight-nav"
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
            <h4 className="blog-card-report-title">
              {formatReportTitle(
                blog.body.body_type_fields.report_kind,
                blog.body.body_type_fields.time_type || ''
              )}
            </h4>
            {blog.body.body_type_fields.date && (
              <p className="blog-card-report-date">
                {blog.body.body_type_fields.date}
              </p>
            )}
            {blog.body.body_type_fields.location && (
              <p className="blog-card-report-location">
                <strong>📍</strong> {blog.body.body_type_fields.location}
              </p>
            )}
            {blog.body.body_type_fields.new_users !== undefined && (
              <p className="blog-card-report-users">
                <strong>New Users:</strong> {blog.body.body_type_fields.new_users}
              </p>
            )}
          </div>
        )}

        {/* Other type-specific fields */}
        {blog.header.type === 'report_insight' && !blog.body.body_type_fields.report_kind && (
          <>
            {blog.body.body_type_fields.report_type && (
              <p className="blog-card-report-type">
                <strong>Report Type:</strong> {blog.body.body_type_fields.report_type}
              </p>
            )}
            {blog.body.body_type_fields.report_id && (
              <p className="blog-card-report-id">
                <strong>Report ID:</strong> {blog.body.body_type_fields.report_id}
              </p>
            )}
          </>
        )}
        {blog.header.type === 'consumption' && (
          <>
            {blog.body.body_type_fields.title && (
              <p className="blog-card-consumption-title">
                <strong>Title:</strong> {blog.body.body_type_fields.title}
              </p>
            )}
            {blog.body.body_type_fields.url && (
              <p className="blog-card-consumption-url">
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
          <p className="blog-card-question">
            {blog.body.body_type_fields.question?.text}
          </p>
        )}
        {blog.header.type === 'failed_initiation' && (
          <>
            {blog.body.body_type_fields.location && (
              <p className="blog-card-failed-location">
                <strong>📍</strong> {blog.body.body_type_fields.location}
              </p>
            )}
            {blog.body.body_type_fields.target_details && (
              <p className="blog-card-target-details">
                <strong>Other Details:</strong> {blog.body.body_type_fields.target_details}
              </p>
            )}
            {blog.body.body_type_fields.failure_reason && (
              <p className="blog-card-failure-reason">
                <strong>Failure Reason:</strong> {blog.body.body_type_fields.failure_reason}
              </p>
            )}
          </>
        )}

        {/* Body text */}
        <div className="blog-card-body-text">
          <p>{blog.body.body_text ?? 'No content available'}</p>
        </div>
      </div>

      {/* Footer with reaction buttons */}
      <div 
        className="blog-card-footer"
        onClick={(e) => e.stopPropagation()}
      >
        <button 
          className={`reaction-btn btn-like ${blog.footer.has_liked ? 'active' : ''}`}
          onClick={(e) => onLikeClick(blog.id, e)}
        >
          <i className="far fa-heart"></i> Like ({blog.footer.likes.length})
        </button>
        
        <button 
          className={`reaction-btn btn-share ${blog.footer.has_shared ? 'active' : ''}`}
          onClick={(e) => onShareClick(blog.id, e)}
        >
          <i className="far fa-share-square"></i> {blog.footer.has_shared ? 'Unshare' : 'Share'} ({blog.footer.shares.length})
        </button>
        
        <span 
          className="reaction-btn blog-card-comment-btn"
          onClick={(e) => onCommentClick(blog.id, e)}
        >
          <i className="far fa-comment"></i> Comments ({actualCommentCount})
        </span>
      </div>
    </li>
  );
};

export default BlogCard;