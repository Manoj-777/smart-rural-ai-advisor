// src/utils/apiFetch.js
// Authenticated fetch wrapper — attaches Cognito JWT to every API call
// Falls back to unauthenticated fetch if no token available

import { getIdToken } from '../services/cognitoAuth';
import config from '../config';

/**
 * Fetch wrapper that automatically attaches Cognito JWT Authorization header.
 * Usage:  apiFetch('/chat', { method: 'POST', body: JSON.stringify(payload) })
 *
 * @param {string} path     - API path (e.g. '/chat', '/profile/ph_1234567890')
 * @param {RequestInit} opts - Standard fetch options (method, headers, body, etc.)
 * @returns {Promise<Response>}
 */
export async function apiFetch(path, opts = {}) {
    const url = `${config.API_URL}${path}`;
    const token = await getIdToken();

    const headers = {
        ...opts.headers,
    };

    if (token) {
        headers['Authorization'] = token;
    }

    // Ensure Content-Type for JSON bodies if not already set
    if (opts.body && typeof opts.body === 'string' && !headers['Content-Type']) {
        headers['Content-Type'] = 'application/json';
    }

    return fetch(url, { ...opts, headers });
}

/**
 * Shorthand GET with auth
 */
export async function apiGet(path) {
    return apiFetch(path);
}

/**
 * Shorthand POST with auth + JSON body
 */
export async function apiPost(path, body) {
    return apiFetch(path, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
}

/**
 * Shorthand PUT with auth + JSON body
 */
export async function apiPut(path, body) {
    return apiFetch(path, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
}
