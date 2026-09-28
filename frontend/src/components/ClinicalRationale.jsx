import React, { useState, useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { 
  Sparkles, 
  Check, 
  Copy, 
  Activity, 
  ShieldCheck, 
  ShoppingBag, 
  Lightbulb, 
  HeartPulse, 
  Info,
  Scale,
  Globe
} from 'lucide-react';

/**
 * Normalizes raw Gemini output into well-structured GitHub-flavored Markdown.
 * Fixes run-together headers like "1. The Physiological Rationale Your target...",
 * unformatted bullets, and awkward horizontal rules.
 */
function normalizeClinicalMarkdown(rawText) {
  if (!rawText) return '';
  let res = rawText;

  // Convert bullet character • to markdown *
  res = res.replace(/•\s*/g, '* ');

  // Standardize dividers
  res = res.replace(/(\n|^)---\s*(\n|$)/g, '\n\n---\n\n');

  // Clinical section title keywords that Gemini commonly outputs
  const sectionKeywords = [
    'The Physiological Rationale',
    'Physiological Rationale',
    'Supermarket Selection Strategy',
    'Supermarket Selection',
    'Supermarket Strategy',
    'Product Selection Strategy',
    'Allergen Safety',
    'Health Precautions',
    'Allergies & Health Conditions',
    'Clinical Precautions',
    'Practical Tips',
    'Actionable Tips',
    'Meal Prep & Shopping Tips',
    'Meal Prep Tips',
    'Shopping Tips',
    'Nutrition Strategy',
    'Macronutrient Distribution',
    'Dietary Strategy'
  ];

  // Fix explicit known clinical section titles with or without leading number
  sectionKeywords.forEach(kw => {
    const escaped = kw.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const reg = new RegExp(`(?:^|\\n)(?:(?:###|##|#)\\s+)?(?:(\\d+)\\.\\s+)?(${escaped})(?:[:\\-\\s]+)?(?:\\n|\\s+(?=[A-Z]))(.*)`, 'gi');
    res = res.replace(reg, (m, num, title, rest) => {
      const prefix = num ? `${num}. ` : '';
      return `\n\n### ${prefix}${title.trim()}\n\n${(rest || '').trim()}`;
    });
  });

  // Fix generic "N. Title" where title is followed by capital letter sentences
  res = res.replace(/(?:^|\n)(?!###)(\d+)\.\s+([A-Z][A-Za-z0-9\s&,/-]{3,40}?)(?::|\s+(?=(?:Your|Since|We|The|To|Our|Based|Because|Maintaining|As|In|For|By|With)\b|\n))(.*)/g, (m, num, title, rest) => {
    // Avoid action steps like "Wash vegetables"
    if (/^(Wash|Chop|Store|Cook|Drink|Eat|Buy|Preheat|Add|Mix)\b/i.test(title)) {
      return m;
    }
    return '\n\n### ' + num + '. ' + title.trim() + '\n\n' + rest.trim();
  });

  // Ensure bullet items have line breaks before them so react-markdown parses list properly
  res = res.replace(/([^\n])\n(\*|-)\s+/g, '$1\n\n$2 ');

  // Collapse excessive 3+ newlines to clean 2
  res = res.replace(/\n{3,}/g, '\n\n');

  return res.trim();
}

/**
 * Returns a contextual icon for headings based on their text content
 */
function getHeadingIcon(text) {
  const lower = (text || '').toLowerCase();
  if (lower.includes('physiological') || lower.includes('rationale') || lower.includes('energy') || lower.includes('calor')) {
    return <Activity size={18} className="text-emerald" />;
  }
  if (lower.includes('supermarket') || lower.includes('selection') || lower.includes('product') || lower.includes('grocery')) {
    return <ShoppingBag size={18} className="text-emerald" />;
  }
  if (lower.includes('allergen') || lower.includes('safety') || lower.includes('precaution') || lower.includes('health condition')) {
    return <ShieldCheck size={18} className="text-emerald" />;
  }
  if (lower.includes('tip') || lower.includes('prep') || lower.includes('shopping') || lower.includes('practical')) {
    return <Lightbulb size={18} className="text-emerald" />;
  }
  return <HeartPulse size={18} className="text-emerald" />;
}

export default function ClinicalRationale({ explanation, targets, profile }) {
  const [copied, setCopied] = useState(false);

  const cleanMarkdown = useMemo(() => {
    return normalizeClinicalMarkdown(explanation);
  }, [explanation]);

  const handleCopy = () => {
    if (!explanation) return;
    navigator.clipboard.writeText(explanation);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="explanation-card clinical-rationale-container">
      {/* Header Bar */}
      <div className="explanation-header">
        <div className="explanation-title-wrap">
          <div className="clinical-icon-badge">
            <Sparkles size={20} className="text-emerald" />
          </div>
          <div>
            <h2 className="clinical-title">AI Dietitian Clinical Strategy & Rationale</h2>
            <p className="clinical-subtitle">Personalized physiological analysis, product rationale & health precautions</p>
          </div>
        </div>

        <div className="clinical-header-actions">
          <button 
            type="button" 
            className="clinical-copy-btn" 
            onClick={handleCopy}
            title="Copy Strategy to Clipboard"
          >
            {copied ? (
              <>
                <Check size={14} className="text-emerald" />
                <span>Copied</span>
              </>
            ) : (
              <>
                <Copy size={14} />
                <span>Copy</span>
              </>
            )}
          </button>
          <span className="llm-model-badge">Gemini Flash Intelligence</span>
        </div>
      </div>

      {/* Target Pill Ribbon (Quick glance of key biometrics) */}
      {targets && (
        <div className="clinical-pill-ribbon">
          <div className="clinical-pill">
            <Scale size={13} className="text-emerald" />
            <span>Target: <strong>{targets.daily_calories} kcal</strong></span>
          </div>
          <div className="clinical-pill">
            <Activity size={13} className="text-emerald" />
            <span>Protein: <strong>{targets.protein_target}g</strong></span>
          </div>
          <div className="clinical-pill">
            <span>Carbs: <strong>{targets.carbs_target}g</strong></span>
          </div>
          <div className="clinical-pill">
            <span>Fats: <strong>{targets.fat_target}g</strong></span>
          </div>
          {profile?.country && (
            <div className="clinical-pill">
              <Globe size={13} className="text-emerald" />
              <span>Market: <strong>{profile.country}</strong></span>
            </div>
          )}
          {profile?.allergies && profile.allergies.length > 0 && (
            <div className="clinical-pill clinical-pill-allergen">
              <ShieldCheck size={13} />
              <span>Allergen Shield: <strong>{profile.allergies.join(', ')} Free</strong></span>
            </div>
          )}
        </div>
      )}

      {/* Rich Markdown Body */}
      <div className="clinical-body-rich">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            h1: ({ node, children, ...props }) => (
              <h2 className="clinical-section-heading" {...props}>
                <span className="heading-icon-wrap">{getHeadingIcon(String(children))}</span>
                <span>{children}</span>
              </h2>
            ),
            h2: ({ node, children, ...props }) => (
              <h2 className="clinical-section-heading" {...props}>
                <span className="heading-icon-wrap">{getHeadingIcon(String(children))}</span>
                <span>{children}</span>
              </h2>
            ),
            h3: ({ node, children, ...props }) => (
              <h3 className="clinical-section-heading" {...props}>
                <span className="heading-icon-wrap">{getHeadingIcon(String(children))}</span>
                <span>{children}</span>
              </h3>
            ),
            p: ({ node, children, ...props }) => (
              <p className="clinical-paragraph" {...props}>{children}</p>
            ),
            ul: ({ node, children, ...props }) => (
              <ul className="clinical-list" {...props}>{children}</ul>
            ),
            ol: ({ node, children, ...props }) => (
              <ol className="clinical-ordered-list" {...props}>{children}</ol>
            ),
            li: ({ node, children, ...props }) => (
              <li className="clinical-list-item" {...props}>
                <span className="list-dot" />
                <span className="list-text">{children}</span>
              </li>
            ),
            strong: ({ node, children, ...props }) => (
              <strong className="clinical-strong" {...props}>{children}</strong>
            ),
            hr: () => <hr className="clinical-divider" />,
            blockquote: ({ node, children, ...props }) => (
              <div className="clinical-callout">
                <Info size={16} className="callout-icon" />
                <div className="callout-content">{children}</div>
              </div>
            )
          }}
        >
          {cleanMarkdown}
        </ReactMarkdown>
      </div>
    </div>
  );
}
