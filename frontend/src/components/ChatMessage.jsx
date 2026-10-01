import React, { useState } from 'react';
import { User, Bot, ChevronDown, ChevronUp, Activity, Cpu, ShieldAlert } from 'lucide-react';

function parseInlineMarkdown(text) {
  if (!text) return text;
  const parts = [];
  let lastIndex = 0;
  const regex = /(\*\*.*?\*\*|\*.*?\*|`.*?`)/g;
  let match;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.substring(lastIndex, match.index));
    }
    const val = match[0];
    if (val.startsWith('**') && val.endsWith('**')) {
      parts.push(<strong key={match.index}>{val.slice(2, -2)}</strong>);
    } else if (val.startsWith('*') && val.endsWith('*')) {
      parts.push(<em key={match.index}>{val.slice(1, -1)}</em>);
    } else if (val.startsWith('`') && val.endsWith('`')) {
      parts.push(<code key={match.index} style={{ background: '#f1f5f9', padding: '1px 5px', borderRadius: '3px', fontSize: '0.9em' }}>{val.slice(1, -1)}</code>);
    } else {
      parts.push(val);
    }
    lastIndex = regex.lastIndex;
  }

  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex));
  }

  return parts.length > 0 ? parts : text;
}

function FormattedText({ text }) {
  if (!text) return null;

  // Clean technical brackets e.g. "[Product Name]" if any slip through
  const cleanedText = text.replace(/\[([^\]]+)\]/g, '$1:');
  const lines = cleanedText.split('\n');

  return (
    <div className="formatted-text">
      {lines.map((line, idx) => {
        const trimmed = line.trim();
        if (!trimmed) return <div key={idx} className="line-spacer" style={{ height: '6px' }} />;

        // Headers ### or ## or #
        if (trimmed.startsWith('### ') || trimmed.startsWith('## ') || trimmed.startsWith('# ')) {
          const headerText = trimmed.replace(/^#+\s*/, '');
          return (
            <h4 key={idx} className="formatted-heading">
              {parseInlineMarkdown(headerText)}
            </h4>
          );
        }

        // Bullet points: -, *, •, or numbered lists e.g. 1.
        if (trimmed.startsWith('- ') || trimmed.startsWith('* ') || trimmed.startsWith('• ') || /^\d+\.\s+/.test(trimmed)) {
          const isNumbered = /^\d+\.\s+/.test(trimmed);
          const numMatch = trimmed.match(/^(\d+\.)\s+/);
          const dot = isNumbered && numMatch ? numMatch[1] : '•';
          const itemText = isNumbered ? trimmed.replace(/^\d+\.\s+/, '') : trimmed.replace(/^[-*•]\s*/, '');
          return (
            <div key={idx} className="formatted-bullet">
              <span className="bullet-dot">{dot}</span>
              <span className="bullet-content">{parseInlineMarkdown(itemText)}</span>
            </div>
          );
        }

        return (
          <p key={idx} className="formatted-paragraph">
            {parseInlineMarkdown(trimmed)}
          </p>
        );
      })}
    </div>
  );
}

export default function ChatMessage({ message }) {
  const isUser = message.sender === 'user';
  const [showInsights, setShowInsights] = useState(false);

  const triageData = message.triage_output || {};
  const executionSteps = message.execution_steps || [];
  const extractionSource = triageData.extraction_source || 'llm';

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
