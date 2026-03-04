// src/utils/sanitize.js
// Shared HTML sanitizer using DOMPurify + marked — prevents XSS from AI-generated content

import DOMPurify from 'dompurify';
import { marked } from 'marked';

// Configure marked for chat-friendly output
marked.setOptions({
    gfm: true,          // GitHub-Flavoured Markdown (tables, strikethrough, etc.)
    breaks: true,        // Convert \n → <br> (chat messages aren't wrapped in <p>)
    headerIds: false,    // No auto-generated IDs on headings
    mangle: false,       // Don't mangle email addresses
});

// Custom renderer to add chat-friendly CSS classes
const renderer = new marked.Renderer();

// All headings render as compact h3 inside chat bubbles
renderer.heading = function (text, level) {
    const tag = level <= 3 ? 'h3' : level === 4 ? 'h4' : 'h5';
    return `<${tag} class="chat-heading">${text}</${tag}>`;
};

// Add classes to list items for styling
renderer.listitem = function (text) {
    return `<li class="chat-list-item">${text}</li>\n`;
};

// Tables get a wrapper class
renderer.table = function (header, body) {
    return `<table class="chat-table"><thead>${header}</thead><tbody>${body}</tbody></table>`;
};

// Links open in new tab
renderer.link = function (href, title, text) {
    const titleAttr = title ? ` title="${title}"` : '';
    return `<a href="${href}" target="_blank" rel="noopener noreferrer"${titleAttr}>${text}</a>`;
};

marked.use({ renderer });

// Allow only safe HTML tags and attributes for formatted AI responses
const PURIFY_CONFIG = {
    ALLOWED_TAGS: [
        'strong', 'b', 'em', 'i', 'br', 'span', 'p', 'div',
        'ul', 'ol', 'li', 'table', 'thead', 'tbody', 'tr', 'th', 'td',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'pre', 'code',
        'a', 'audio', 'source', 'blockquote', 'del', 'input', 'img'
    ],
    ALLOWED_ATTR: [
        'class', 'id', 'href', 'target', 'rel', 'src', 'alt',
        'controls', 'preload', 'type'
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
 * Format markdown text to HTML and sanitize.
 * Uses 'marked' for full markdown support — handles headers, bold, italic,
 * lists, tables, code blocks, links, blockquotes, horizontal rules, and more.
 * DOMPurify strips any unsafe HTML the LLM might inject.
 */
export function formatAndSanitize(text) {
    if (!text) return '';
    // marked.parse outputs full HTML from any standard markdown
    const rawHtml = marked.parse(text);
    return sanitizeHtml(rawHtml);
}
