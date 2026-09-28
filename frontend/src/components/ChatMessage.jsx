import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { User, Bot, ChevronDown, ChevronUp, Activity, Cpu, ShieldAlert } from 'lucide-react';

function FormattedText({ text }) {
  if (!text) return null;

  // Clean technical brackets e.g. "[Product Name]" if any slip through
  let cleanedText = text.replace(/\[([^\]]+)\]/g, '$1:');
  cleanedText = cleanedText.replace(/•\s*/g, '* ');
  cleanedText = cleanedText.replace(/([^\n])\n(\*|-|\d+\.)\s+/g, '$1\n\n$2 ');

  return (
    <div className="formatted-text">
      <ReactMarkdown 
        remarkPlugins={[remarkGfm]}
        components={{
          h3: ({ node, ...props }) => <h4 className="formatted-heading" {...props} />,
          h4: ({ node, ...props }) => <h4 className="formatted-heading" {...props} />,
          p: ({ node, ...props }) => <p className="formatted-paragraph" {...props} />,
          ul: ({ node, ...props }) => <ul className="formatted-list" {...props} />,
          ol: ({ node, ...props }) => <ol className="formatted-ordered-list" {...props} />,
          li: ({ node, ...props }) => <li className="formatted-list-item" {...props} />,
          strong: ({ node, ...props }) => <strong className="clinical-strong" {...props} />
        }}
      >
        {cleanedText}
      </ReactMarkdown>
    </div>
  );
}

export default function ChatMessage({ message }) {
  const isUser = message.sender === 'user';
  const [showInsights, setShowInsights] = useState(false);

  const triageData = message.triage_output || {};
  const executionSteps = message.execution_steps || [];
  const riskLevel = triageData.risk_level || 'LOW';
  const extractionSource = triageData.extraction_source || 'llm';

  const riskClass = 
    riskLevel === 'HIGH' ? 'badge-risk-high' :
    riskLevel === 'MEDIUM' ? 'badge-risk-medium' : 'badge-risk-low';

  return (
    <div className="message-row">
      <div className={`avatar ${isUser ? 'user-avatar' : 'ai-avatar'}`}>
        {isUser ? <User size={18} /> : <Bot size={20} />}
      </div>

      <div className="message-content">
        <div className="message-header">
          <span>{isUser ? 'You' : 'EviBite AI'}</span>
          <span className="message-time">
            {new Date(message.timestamp || Date.now()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>

        <div className={`message-bubble ${isUser ? 'user-bubble' : ''}`}>
          {isUser ? message.text : <FormattedText text={message.text} />}
        </div>

        {/* Collapsible Agent Reasoning / Trace Drawer for AI Responses */}
        {!isUser && triageData && (
          <div className="agent-insights-pill">
            <div className="insights-header" onClick={() => setShowInsights(!showInsights)}>
              <div className="insights-title">
                <Activity size={14} color="#10b981" />
                <span>Agent Orchestration Details</span>
              </div>
              
              <div className="meta-badges">
                <span className="badge badge-source">
                  <Cpu size={10} style={{ marginRight: 4, display: 'inline' }} />
                  {extractionSource}
                </span>
                <span className={`badge ${riskClass}`}>
                  Risk: {riskLevel}
                </span>
                {showInsights ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              </div>
            </div>

            {showInsights && (
              <div className="insights-body">
                <div>
                  <strong>Primary Intent:</strong> {triageData.primary_intent || 'unknown'}
                </div>
                {triageData.products && triageData.products.length > 0 && (
                  <div>
                    <strong>Extracted Product:</strong> {triageData.products.map(p => p.name || p.barcode).join(', ')}
                  </div>
                )}
                {triageData.allergens && triageData.allergens.length > 0 && (
                  <div style={{ color: '#f43f5e' }}>
                    <ShieldAlert size={12} style={{ display: 'inline', marginRight: 4 }} />
                    <strong>Detected Allergens:</strong> {triageData.allergens.join(', ')}
                  </div>
                )}
                
                <div style={{ marginTop: 4 }}>
                  <strong>Execution Path:</strong>
                  <div className="step-flow" style={{ marginTop: 4 }}>
                    {executionSteps.map((step, idx) => (
                      <React.Fragment key={idx}>
                        <span className="step-chip">
                          {step.agent} ({step.action})
                        </span>
                        {idx < executionSteps.length - 1 && <span style={{ color: '#6b7280' }}>→</span>}
                      </React.Fragment>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
