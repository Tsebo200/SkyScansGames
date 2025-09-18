import React, { useState, useCallback, useMemo } from 'react';

const ScoreDashboard = React.memo(({ scores, game }) => {
  const [selectedMetric, setSelectedMetric] = useState(null);
  const [showModal, setShowModal] = useState(false);

  if (!scores) return null;

  const scoreItems = useMemo(() => [
    {
      label: 'Reviews Score',
      value: scores.reviews_score,
      color: '#ff6b6b',
      key: 'reviews_score'
    },
    {
      label: 'Graphic Quality Score',
      value: scores.graphic_score,
      color: '#4ecdc4',
      key: 'graphic_score'
    },
    {
      label: 'Microtransactions Score',
      value: scores.microtransactions_score,
      color: '#45b7d1',
      key: 'microtransactions_score'
    },
    {
      label: 'Game Mechanics Score',
      value: scores.game_mechanics_score,
      color: '#f9ca24',
      key: 'game_mechanics_score'
    },
    {
      label: 'Completeness Score',
      value: scores.completeness_score,
      color: '#f0932b',
      key: 'completeness_score'
    },
    {
      label: 'Story Quality Score',
      value: scores.story_quality_score,
      color: '#eb4d4b',
      key: 'story_quality_score'
    },
    {
      label: 'Accessibility Score',
      value: scores.accessibility_score,
      color: '#6c5ce7',
      key: 'accessibility_score'
    },
  ], [scores]);

  const handleMetricClick = useCallback((metricKey) => {
    setSelectedMetric(metricKey);
    setShowModal(true);
  }, []);

  const closeModal = useCallback(() => {
    setShowModal(false);
    setSelectedMetric(null);
  }, []);

  const getReasoning = useCallback((metricKey) => {
    return scores.reasoning?.[metricKey] || { short: 'No reasoning available', detailed: 'No detailed reasoning available' };
  }, [scores.reasoning]);

  const selectedReasoning = useMemo(() => {
    if (!selectedMetric) return null;
    return getReasoning(selectedMetric);
  }, [selectedMetric, getReasoning]);

  const overallScoreColor = useMemo(() => {
    const score = scores.overall_score;
    return score >= 90 ? '#4ecdc4' : score >= 70 ? '#f9ca24' : '#ff6b6b';
  }, [scores.overall_score]);

  return (
    <div style={{ padding: '20px' }}>
      <h2 style={{
        color: '#fff',
        textAlign: 'center',
        marginBottom: '30px',
        background: 'rgba(255, 255, 255, 0.1)',
        padding: '15px 30px',
        borderRadius: '25px',
        border: '1px solid rgba(255, 255, 255, 0.2)',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',
        fontSize: '2rem',
        fontWeight: '300'
      }}>
        {game.title} - Quality Analysis
      </h2>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
        gap: '25px',
        marginBottom: '30px'
      }}>
        {scoreItems.map((item, index) => (
          <div key={index}
            style={{
              background: 'rgba(255, 255, 255, 0.1)',
              borderRadius: '20px',
              padding: '25px',
              textAlign: 'center',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',
              transition: 'transform 0.2s ease, box-shadow 0.2s ease',
              cursor: 'pointer'
            }}
            onClick={() => handleMetricClick(item.key)}
            title={getReasoning(item.key).short}
            onMouseEnter={(e) => {
              e.target.style.transform = 'translateY(-2px)';
              e.target.style.boxShadow = '0 8px 25px rgba(0, 0, 0, 0.15)';
            }}
            onMouseLeave={(e) => {
              e.target.style.transform = 'translateY(0)';
              e.target.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.1)';
            }}
          >
            <h3 style={{
              margin: '0 0 15px 0',
              color: '#fff',
              fontSize: '1.2rem',
              fontWeight: '400'
            }}>
              {item.label}
            </h3>
            <div style={{
              fontSize: '3rem',
              fontWeight: 'bold',
              color: item.color,
              textShadow: '0 0 5px rgba(255, 255, 255, 0.2)',
              marginBottom: '10px'
            }}>
              {item.value}%
            </div>
            <div style={{
              width: '100%',
              height: '8px',
              background: 'rgba(255, 255, 255, 0.2)',
              borderRadius: '4px',
              overflow: 'hidden'
            }}>
              <div style={{
                width: `${item.value}%`,
                height: '100%',
                background: `linear-gradient(90deg, ${item.color}, ${item.color}aa)`,
                borderRadius: '4px',
                transition: 'width 0.8s ease'
              }}></div>
            </div>
          </div>
        ))}
      </div>
      <div style={{
        background: 'rgba(255, 255, 255, 0.15)',
        borderRadius: '25px',
        padding: '30px',
        textAlign: 'center',
        border: '1px solid rgba(255, 255, 255, 0.3)',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',
        position: 'relative',
        overflow: 'hidden',
        cursor: 'pointer'
      }}
      onClick={() => handleMetricClick('overall_score')}
      title={getReasoning('overall_score').short}
      >
        <h3 style={{
          margin: '0 0 20px 0',
          color: '#fff',
          fontSize: '2rem',
          fontWeight: '300',
          position: 'relative',
          zIndex: 1
        }}>
          Overall Quality Score
        </h3>
        <div style={{
          fontSize: '5rem',
          fontWeight: 'bold',
          color: '#fff',
          textShadow: '0 0 10px rgba(255, 255, 255, 0.3)',
          position: 'relative',
          zIndex: 1
        }}>
          {scores.overall_score}%
        </div>
        <div style={{
          width: '200px',
          height: '200px',
          margin: '20px auto 0',
          borderRadius: '50%',
          background: `conic-gradient(${overallScoreColor} ${scores.overall_score}%, rgba(255, 255, 255, 0.1) ${scores.overall_score}%)`,
          position: 'relative',
          zIndex: 1,
          boxShadow: '0 0 15px rgba(255, 255, 255, 0.1)'
        }}>
          <div style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            width: '160px',
            height: '160px',
            borderRadius: '50%',
            background: 'rgba(255, 255, 255, 0.1)'
          }}></div>
        </div>
      </div>

      {/* Data Source Disclaimer */}
      <div style={{
        marginTop: '30px',
        background: 'rgba(255, 255, 255, 0.08)',
        borderRadius: '15px',
        padding: '20px',
        border: '1px solid rgba(255, 255, 255, 0.15)',
        boxShadow: '0 2px 15px rgba(0, 0, 0, 0.05)'
      }}>
        <h4 style={{
          margin: '0 0 10px 0',
          color: '#fff',
          fontSize: '1rem',
          fontWeight: '500',
          textAlign: 'center'
        }}>
          📊 Data Source Information
        </h4>
        <p style={{
          margin: 0,
          color: 'rgba(255, 255, 255, 0.8)',
          fontSize: '0.9rem',
          lineHeight: '1.4',
          textAlign: 'center'
        }}>
          Scores are generated using data from <strong>RAWG.io</strong>, which aggregates information from various sources.
          Metacritic scores may vary slightly from official values due to timing and source differences.
          For official critic scores, please check <strong>Metacritic.com</strong> directly.
        </p>
      </div>

      {showModal && selectedMetric && selectedReasoning && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0, 0, 0, 0.8)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}
        onClick={closeModal}
        >
          <div style={{
            background: 'rgba(255, 255, 255, 0.95)',
            borderRadius: '20px',
            padding: '30px',
            maxWidth: '500px',
            maxHeight: '70vh',
            overflowY: 'auto',
            border: '1px solid rgba(255, 255, 255, 0.3)',
            boxShadow: '0 10px 40px rgba(0, 0, 0, 0.2)'
          }}
          onClick={(e) => e.stopPropagation()}
          >
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '20px'
            }}>
              <h3 style={{
                margin: 0,
                color: '#333',
                fontSize: '1.5rem',
                fontWeight: '600'
              }}>
                {selectedMetric === 'overall_score' ? 'Overall Quality Score' :
                 scoreItems.find(item => item.key === selectedMetric)?.label || 'Score Details'}
              </h3>
              <button
                onClick={closeModal}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: '1.5rem',
                  cursor: 'pointer',
                  color: '#666',
                  padding: '5px'
                }}
              >
                ×
              </button>
            </div>
            <div style={{
              color: '#555',
              lineHeight: '1.6',
              fontSize: '1rem'
            }}>
              <p style={{
                fontWeight: '500',
                color: '#333',
                marginBottom: '15px',
                fontSize: '1.1rem'
              }}>
                {selectedReasoning.short}
              </p>
              <p style={{
                margin: 0,
                textAlign: 'justify'
              }}>
                {selectedReasoning.detailed}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
});

export default ScoreDashboard;