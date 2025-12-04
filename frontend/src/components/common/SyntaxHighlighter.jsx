import React from 'react';

/**
 * Simple Syntax Highlighter Component
 * 
 * Provides basic syntax highlighting for common file types
 * Uses simple regex patterns - reliable and fast
 */
export default function SyntaxHighlighter({ code, language, filename }) {
  // Detect language from filename if not provided
  if (!language && filename) {
    const ext = filename.split('.').pop()?.toLowerCase();
    const langMap = {
      'py': 'python',
      'js': 'javascript',
      'jsx': 'javascript',
      'ts': 'typescript',
      'tsx': 'typescript',
      'json': 'json',
      'xml': 'xml',
      'html': 'html',
      'css': 'css',
      'sql': 'sql',
      'yaml': 'yaml',
      'yml': 'yaml',
      'md': 'markdown',
      'sh': 'bash',
      'bash': 'bash'
    };
    language = langMap[ext] || 'text';
  }

  // Simple syntax highlighting - process in safe order
  const highlightCode = (code, lang) => {
    if (!code) return '';
    
    try {
      // Escape HTML first
      let highlighted = code
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

      if (lang === 'python') {
        // Python syntax highlighting disabled - too complex to get right
        // Just return escaped code without highlighting
      } else if (lang === 'json') {
        // JSON: Process structure carefully
        // 1. Booleans and null first
        highlighted = highlighted.replace(
          /\b(true|false|null)\b/g,
          '<span style="color: #d73a49;">$1</span>'
        );
        
        // 2. JSON keys: "key": pattern
        highlighted = highlighted.replace(
          /"([^"]+)":\s*/g,
          (match, key, offset, string) => {
            // Check if this is a key (followed by value)
            const after = string.substring(offset + match.length).trim();
            if (after.match(/^["{\[\d-]|^(true|false|null)/)) {
              return `<span style="color: #032f62;">"</span><span style="color: #22863a; font-weight: 500;">${key}</span><span style="color: #032f62;">":</span> `;
            }
            return match;
          }
        );
        
        // 3. String values (after colons)
        highlighted = highlighted.replace(
          /:\s*"([^"]*)"/g,
          ': <span style="color: #032f62;">"$1"</span>'
        );
        
        // 4. Numbers (after colons, before commas/braces)
        highlighted = highlighted.replace(
          /:\s*(\d+\.?\d*)(?=\s*[,}\]])/g,
          ': <span style="color: #005cc5;">$1</span>'
        );
      } else {
        // Basic highlighting for other languages
        if (lang === 'javascript' || lang === 'typescript') {
          highlighted = highlighted.replace(
            /(\/\/.*$|\/\*[\s\S]*?\*\/)/gm,
            '<span style="color: #6a737d; font-style: italic;">$1</span>'
          );
        }
        
        // Strings
        highlighted = highlighted.replace(
          /(['"`])((?:\\.|(?!\1)[^\\])*?)\1/g,
          '<span style="color: #032f62;">$1$2$1</span>'
        );
      }

      return highlighted;
    } catch (error) {
      // If highlighting fails, return escaped code
      console.error('Syntax highlighting error:', error);
      return code
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
    }
  };

  const highlightedCode = highlightCode(code, language);

  return (
    <pre style={{
      margin: 0,
      padding: '15px',
      background: '#f6f8fa',
      border: '1px solid #e1e4e8',
      borderRadius: '4px',
      overflow: 'auto',
      fontSize: '13px',
      fontFamily: '"SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace',
      lineHeight: '1.5',
      whiteSpace: 'pre',
      wordWrap: 'normal'
    }}>
      <code dangerouslySetInnerHTML={{ __html: highlightedCode }} />
    </pre>
  );
}
