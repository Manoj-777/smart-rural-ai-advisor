// src/utils/locationUtils.js
// Shared location utilities — Nominatim place name cleaning

/**
 * Clean location names from Nominatim that OpenWeatherMap doesn't understand.
 * Strips administrative suffixes like "Tahsil", "Block", "Mandal", "Taluk", etc.
 */
export function cleanLocationName(name) {
    if (!name) return name;
    return name
        .replace(/\b(Tahsil|Tehsil|Block|Mandal|Taluk[ua]?|Sub-?district|District|Division|Sub-?Division|Municipality|Corporation|Cantonment|Nagar Panchayat|Town|Circle|Range|Panchayat|Samiti|Gram|Assembly|Constituency|Revenue|Hobli|Firka|Community Development)\b/gi, '')
        .replace(/\s{2,}/g, ' ')
        .trim();
}
