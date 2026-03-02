// src/utils/sanitize.js
// Shared HTML sanitizer using DOMPurify — prevents XSS from AI-generated content

import DOMPurify from 'dompurify';

// Allow only safe HTML tags and attributes for formatted AI responses
const PURIFY_CONFIG = {
    ALLOWED_TAGS: [
        'strong', 'b', 'em', 'i', 'br', 'span', 'p', 'div',
        'ul', 'ol', 'li', 'table', 'thead', 'tbody', 'tr', 'th', 'td',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'pre', 'code',
        'a', 'img', 'audio', 'source'
    ],
    ALLOWED_ATTR: [
        'class', 'id', 'href', 'target', 'rel', 'src', 'alt',
        'controls', 'preload', 'type', 'style'
    ],
    ALLOW_DATA_ATTR: false,
    // Force all links to open in new tab safely
    ADD_ATTR: ['target'],
};

/**
 * Sanitize HTML string to prevent XSS.
 * Use this before passing to dangerouslySetInnerHTML.
 */
export function sanitizeHtml(dirty) {
    if (!dirty) return '';
    const clean = DOMPurify.sanitize(dirty, PURIFY_CONFIG);
    // Ensure external links have rel="noopener noreferrer"
    return clean.replace(/<a\s/g, '<a rel="noopener noreferrer" target="_blank" ');
}

/**
 * Format markdown-like text to HTML and sanitize.
 * Shared formatter for all feature pages.
 */
export function formatAndSanitize(text) {
    if (!text) return '';
    const html = text
        // Bold
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        // Italic
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        // Numbered list items
        .replace(/^(\d+)\.\s/gm, '<span class="list-num">$1.</span> ')
        // Bullet list items with dash
        .replace(/^-\s(.+)/gm, '<span class="list-bullet">•</span> $1')
        // Line breaks
        .replace(/\n/g, '<br/>');
    return sanitizeHtml(html);
}
