import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import type { AppDispatch, RootState } from "../../../store";
import { fetchQuestions } from './questionsSlice';
import { useNavigate } from 'react-router-dom';
import './QuestionsPage.css';

const QuestionsPage: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const navigate = useNavigate();
  const { questions, status, error, pagination } = useSelector(
    (state: RootState) => state.questions
  );
  const [currentPage, setCurrentPage] = useState(1);

  // Fetch questions when page changes
  useEffect(() => {
    dispatch(fetchQuestions({ page: currentPage }));
  }, [dispatch, currentPage]);

  // Pagination handlers with better event handling
  const handleNextPage = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (pagination.hasNext) {
      setCurrentPage(prev => prev + 1);
    }
  };

  const handlePrevPage = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (pagination.hasPrevious) {
      setCurrentPage(prev => prev - 1);
    }
  };

  // Navigate to blog creator with question details for answer writing
  const handleWriteAnswerClick = (
    e: React.MouseEvent,
    question: { id: number; text: string; rank: number }
  ) => {
    e.preventDefault();
    e.stopPropagation();
    navigate('/blog-creator', {
      state: {
        question_id: question.id,
        question_text: question.text,
        question_rank: question.rank,
        question_kind: "question",
      },
    });
  };

  // Navigate to answers page for a specific question
 const handleShowAnswersClick = (e: React.MouseEvent, questionId: string) => {
  console.log('Show Answers clicked for:', questionId);
  e.preventDefault();
  e.stopPropagation();
  console.log('Event propagation stopped');
  navigate(`/answers/${questionId}`);
};

  // Add a wrapper handler to prevent any unwanted propagation
  const handleCardClick = (e: React.MouseEvent) => {
    e.stopPropagation();
  };

  return (
    <div className="qpage" onClick={() => {}}> {/* Add empty handler to contain events */}
      <div className="qpage-container">
        <div className="qpage-header">
          <h1 className="qpage-title">Answer These Questions</h1>
          <p className="qpage-subtitle">Deepen your understanding</p>
        </div>

        {status === 'loading' && (
          <div className="qpage-loading">
            <div className="qpage-spinner"></div>
            <p>Loading questions...</p>
          </div>
        )}

        {status === 'failed' && (
          <div className="qpage-error">
            <p>{error}</p>
          </div>
        )}

        {status === 'succeeded' && (
          <>
            <div className="qpage-list">
              {questions.map((question) => (
                <div key={question.id} className="qpage-card" onClick={handleCardClick}>
                  <div className="qpage-content">
                    <div className="qpage-card-header">
                      <div className="qpage-rank">#{question.rank}</div>
                      <p className="qpage-text">{question.text}</p>
                    </div>
                    <div className="qpage-actions">
                      <button
                        className="qpage-answer-btn"
                        onClick={(e) => handleWriteAnswerClick(e, question)}
                      >
                        Write Your Answer
                      </button>
                      <button
                        className="qpage-show-answers-btn"
                        onClick={(e) => handleShowAnswersClick(e, String(question.id))}
                      >
                        Show Answers
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="qpage-pagination">
              <button
                onClick={handlePrevPage}
                disabled={!pagination.hasPrevious}
                className="qpage-pagination-btn"
              >
                Previous
              </button>

              <span className="qpage-pagination-info">
                Page {currentPage} of {pagination.totalPages}
              </span>

              <button
                onClick={handleNextPage}
                disabled={!pagination.hasNext}
                className="qpage-pagination-btn"
              >
                Next
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default QuestionsPage;