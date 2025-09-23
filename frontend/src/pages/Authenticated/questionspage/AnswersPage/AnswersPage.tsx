import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import type { AppDispatch, RootState } from "../../../../store";
import { fetchQuestionAnswers } from './answersSlice';
import BlogCard from '../../blogrelated/blogpage/BlogCard';
import './AnswersPage.css';

interface Answer {
  id: string;
}

interface AnswersState {
  question: {
    id: number;
    text: string;
    rank: number;
  } | null;
  answers: Answer[];
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
}

const AnswersPage: React.FC = () => {
  const { questionId } = useParams<{ questionId: string }>();
  const navigate = useNavigate();
  const dispatch = useDispatch<AppDispatch>();
  const { question, answers, status, error } = useSelector((state: RootState) => state.answers);
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    if (questionId) {
      dispatch(fetchQuestionAnswers(questionId));
    }
  }, [dispatch, questionId]);

  const handleBlogClick = (blogId: string) => {};
  const handleUserClick = (userId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    navigate(`/profile/${userId}`);
  };
  const handleLikeClick = (blogId: string, e: React.MouseEvent) => {
    e.stopPropagation();
  };
  const handleShareClick = (blogId: string, e: React.MouseEvent) => {
    e.stopPropagation();
  };
  const handleCommentClick = (blogId: string, e: React.MouseEvent) => {
    e.stopPropagation();
  };
  const handleReportClick = (report_kind?: string, time_type?: string, id?: string, level?: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
  };
  const formatReportTitle = (report_kind: string, time_type: string) => {
    return `${report_kind} ${time_type} Report`;
  };

  if (status === 'loading') {
    return (
      <div className="answers-page">
        <div className="answers-loading">
          <div className="answers-spinner"></div>
          <p>Loading answers...</p>
        </div>
      </div>
    );
  }

  if (status === 'failed') {
    return (
      <div className="answers-page">
        <div className="answers-error">
          <p>Error: {error}</p>
          <button onClick={() => navigate(-1)}>Go Back</button>
        </div>
      </div>
    );
  }

  return (
    <div className="answers-page">
      <div className="answers-container">
        <div className="answers-header">
          <button className="answers-back-btn" onClick={() => navigate(-1)}>
            &larr; Back
          </button>
          <h1 className="answers-title">Answers to Question</h1>
          {question && (
            <div className="question-card">
              <div className="question-rank">#{question.rank}</div>
              <p className="question-text">{question.text}</p>
            </div>
          )}
        </div>

        <div className="answers-list">
          {answers.length === 0 ? (
            <div className="no-answers">
              <p>No answers yet. Be the first to answer this question!</p>
              <button 
                className="write-answer-btn"
                onClick={() => navigate('/blog-creator', { 
                  state: { 
                    question_id: question?.id,
                    question_text: question?.text,
                    question_rank: question?.rank,
                    question_kind: "question"
                  }
                })}
              >
                Write Your Answer
              </button>
            </div>
          ) : (
            answers.map((blog) => (
              <BlogCard
                key={blog.id}
                blog={{
                  ...blog,
                  comments: (blog.comments ?? []).map((comment: any) => ({
                    ...comment,
                    user: {
                      ...comment.user,
                      relation: comment.user?.relation ?? ""
                    }
                  }))
                }}
                onBlogClick={handleBlogClick}
                onUserClick={handleUserClick}
                onLikeClick={handleLikeClick}
                onShareClick={handleShareClick}
                onCommentClick={handleCommentClick}
                onReportClick={handleReportClick}
                formatReportTitle={formatReportTitle}
              />
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default AnswersPage;
