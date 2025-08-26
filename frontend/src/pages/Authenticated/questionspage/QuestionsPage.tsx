import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import type { AppDispatch, RootState } from "../../../store";
import { fetchQuestions } from './questionsSlice';
import { useNavigate } from 'react-router-dom';
import './QuestionsPage.css';

const QuestionsPage: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const navigate = useNavigate();
  const { questions, status, error, pagination } = useSelector((state: RootState) => state.questions);
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    dispatch(fetchQuestions({ page: currentPage }));
  }, [dispatch, currentPage]);

  const handleNextPage = () => {
    if (pagination.hasNext) {
      setCurrentPage(currentPage + 1);
    }
  };

  const handlePrevPage = () => {
    if (pagination.hasPrevious) {
      setCurrentPage(currentPage - 1);
    }
  };

  const handleWriteAnswerClick = (question: any) => {
    // Navigate to BlogCreator with question data
    navigate('/blog-creator', { 
      state: { 
        question_id: question.id,
        question_text: question.text,
        question_rank: question.rank,
        question_kind: "question" // to identify in BlogCreator
      }
    });
  };

  const handleShowAnswersClick = (questionId: string) => {
    navigate(`/answers/${questionId}`);
  };

  return (
    <div className="qpage">
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
                <div key={question.id} className="qpage-card">
                  <div className="qpage-content">
                    <div className="qpage-card-header">
                      <div className="qpage-rank">#{question.rank}</div>
                      <p className="qpage-text">{question.text}</p>
                    </div>
                    <div className="qpage-actions">
                      <button 
                        className="qpage-answer-btn"
                        onClick={() => handleWriteAnswerClick(question)}
                      >
                        Write Your Answer
                      </button>
                      <button 
                        className="qpage-show-answers-btn"
                        onClick={() => handleShowAnswersClick(String(question.id))}
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