// src/contexts/FarmerContext.jsx
// Shared farmer identity — Cognito-authenticated, single source of truth
// Phone + PIN auth via AWS Cognito, JWT tokens on every API call

import { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react';
import config from '../config';
import { useGeolocation } from '../hooks/useGeolocation';
import * as cognitoAuth from '../services/cognitoAuth';
import { apiFetch } from '../utils/apiFetch';

const FarmerContext = createContext();

const FARMER_ID_KEY = 'farmer_id';
const FARMER_PHONE_KEY = 'farmer_phone';
const FARMER_NAME_KEY = 'farmer_name';

export function FarmerProvider({ children }) {
    const [farmerId, setFarmerIdState] = useState(() => localStorage.getItem(FARMER_ID_KEY) || null);
    const [farmerPhone, setFarmerPhoneState] = useState(() => localStorage.getItem(FARMER_PHONE_KEY) || '');
    const [farmerName, setFarmerNameState] = useState(() => localStorage.getItem(FARMER_NAME_KEY) || '');
    const [farmerProfile, setFarmerProfile] = useState(null);
    const [isLoggedIn, setIsLoggedIn] = useState(() => !!localStorage.getItem(FARMER_ID_KEY));
    const [authReady, setAuthReady] = useState(false); // true once Cognito session checked

    // GPS geolocation
    const {
        gpsLocation, gpsCoords, gpsStatus, gpsError,
        requestGps, refreshGps, clearGps,
    } = useGeolocation();

    // On mount: restore Cognito session if it exists
    useEffect(() => {
        let didFinish = false;
        const restoreSession = async () => {
            try {
                // Race getSession against a 3-second timeout so the app
                // never gets stuck on a white screen if Cognito SDK hangs
                const session = await Promise.race([
                    cognitoAuth.getSession(),
                    new Promise(resolve => setTimeout(() => resolve(null), 3000)),
                ]);
                if (didFinish) return; // timeout already fired
                if (session && session.idToken) {
                    // Cognito session is valid — restore login state
                    const phone = session.phone?.replace('+91', '') || '';
                    const id = `ph_${phone}`;
                    localStorage.setItem(FARMER_ID_KEY, id);
                    localStorage.setItem(FARMER_PHONE_KEY, phone);
                    setFarmerIdState(id);
                    setFarmerPhoneState(phone);
                    setIsLoggedIn(true);
                    if (session.name) {
                        setFarmerNameState(session.name);
                        localStorage.setItem(FARMER_NAME_KEY, session.name);
                    }
                } else if (localStorage.getItem(FARMER_ID_KEY)) {
                    // No valid Cognito session but local storage has login — clear it
                    localStorage.removeItem(FARMER_ID_KEY);
                    localStorage.removeItem(FARMER_PHONE_KEY);
                    localStorage.removeItem(FARMER_NAME_KEY);
                    setFarmerIdState(null);
                    setFarmerPhoneState('');
                    setFarmerNameState('');
                    setIsLoggedIn(false);
                }
            } catch { /* no session */ }
            didFinish = true;
            setAuthReady(true);
        };
        restoreSession();
    }, []);

    // Load profile from DynamoDB when logged in (uses auth headers)
    useEffect(() => {
        if (!farmerId || !authReady) return;
        const loadProfile = async () => {
            try {
                const res = await apiFetch(`/profile/${farmerId}`);
                const data = await res.json();
                if (data.data && data.data.name) {
                    setFarmerProfile(data.data);
                    setFarmerNameState(data.data.name);
                    localStorage.setItem(FARMER_NAME_KEY, data.data.name);
                }
            } catch { /* offline — use cached name */ }
        };
        loadProfile();
    }, [farmerId, authReady]);

    /**
     * Check if a phone number is already registered (has a profile with a name).
     * Returns the profile data if exists, or null if not registered.
     */
    const checkPhoneExists = useCallback(async (phone) => {
        const cleanPhone = phone.replace(/\D/g, '').slice(-10);
        const id = `ph_${cleanPhone}`;
        try {
            const res = await apiFetch(`/profile/${id}`);
            const data = await res.json();
            if (data.data && data.data.name) {
                return data.data; // registered user
            }
        } catch { /* offline */ }
        return null; // not registered
    }, []);

    /**
     * Sign up a new farmer via Cognito + create DynamoDB profile.
     * @param {string} phone - 10-digit phone
     * @param {string} pin - 6+ char PIN
     * @param {string} name - Farmer name
     * @param {object} profileData - Full profile data
     * @param {string} [email] - Optional email for PIN recovery
     * @returns {Promise<object>} tokens
     */
    const signUpAndLogin = useCallback(async (phone, pin, name, profileData, email) => {
        const cleanPhone = phone.replace(/\D/g, '').slice(-10);
        const id = `ph_${cleanPhone}`;

        // 1. Sign up in Cognito (auto-confirmed via Pre-SignUp trigger)
        await cognitoAuth.signUp(cleanPhone, pin, name, email);

        // 2. Sign in to get JWT tokens
        const tokens = await cognitoAuth.signIn(cleanPhone, pin);

        // 3. Set local state
        localStorage.setItem(FARMER_ID_KEY, id);
        localStorage.setItem(FARMER_PHONE_KEY, cleanPhone);
        localStorage.setItem(FARMER_NAME_KEY, name);
        setFarmerIdState(id);
        setFarmerPhoneState(cleanPhone);
        setFarmerNameState(name);
        setIsLoggedIn(true);

        // 4. Create DynamoDB profile (now with auth token)
        const newProfile = profileData || {
            name, language: 'en-IN', state: '', district: '',
            crops: [], soil_type: '', land_size_acres: 0
        };
        if (!newProfile.name) newProfile.name = name;
        try {
            await apiFetch(`/profile/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newProfile),
            });
        } catch { /* will save later */ }
        setFarmerProfile(newProfile);

        return tokens;
    }, []);

    /**
     * Sign in an existing farmer via Cognito.
     * @param {string} phone - 10-digit phone
     * @param {string} pin - PIN/password
     * @returns {Promise<object>} tokens
     */
    const signInWithPin = useCallback(async (phone, pin) => {
        const cleanPhone = phone.replace(/\D/g, '').slice(-10);
        const id = `ph_${cleanPhone}`;

        // 1. Cognito sign-in
        const tokens = await cognitoAuth.signIn(cleanPhone, pin);

        // 2. Set local state
        localStorage.setItem(FARMER_ID_KEY, id);
        localStorage.setItem(FARMER_PHONE_KEY, cleanPhone);
        setFarmerIdState(id);
        setFarmerPhoneState(cleanPhone);
        setIsLoggedIn(true);

        // 3. Load profile from DynamoDB
        try {
            const res = await apiFetch(`/profile/${id}`);
            const data = await res.json();
            if (data.data && data.data.name) {
                setFarmerProfile(data.data);
                setFarmerNameState(data.data.name);
                localStorage.setItem(FARMER_NAME_KEY, data.data.name);
            }
        } catch { /* offline */ }

        return tokens;
    }, []);

    // Resolved location: GPS (primary) → Profile district/state (secondary)
    const resolvedLocation = gpsLocation
        || farmerProfile?.district
        || farmerProfile?.state
        || null;

    const resolvedCoords = gpsCoords || null;

    // ── Logout ──
    const logout = useCallback(() => {
        cognitoAuth.signOut();
        localStorage.removeItem(FARMER_ID_KEY);
        localStorage.removeItem(FARMER_PHONE_KEY);
        localStorage.removeItem(FARMER_NAME_KEY);
        setFarmerIdState(null);
        setFarmerPhoneState('');
        setFarmerNameState('');
        setFarmerProfile(null);
        setIsLoggedIn(false);
        clearGps();
    }, [clearGps]);

    // Auto-request GPS once logged in (if not already granted/denied)
    useEffect(() => {
        if (isLoggedIn && gpsStatus === 'idle') {
            requestGps();
        }
    }, [isLoggedIn, gpsStatus, requestGps]);

    // ── Session timeout: periodic Cognito token refresh + auto-logout ──
    // Cognito ID/Access tokens expire after 1 hour; the SDK auto-refreshes
    // them using the Refresh Token (valid 30 days). If the refresh token is
    // also expired, getSession() returns null → auto-logout.
    const SESSION_CHECK_MS = 5 * 60 * 1000; // check every 5 minutes
    const sessionCheckRef = useRef(null);

    useEffect(() => {
        if (!isLoggedIn) {
            if (sessionCheckRef.current) clearInterval(sessionCheckRef.current);
            return;
        }

        const checkSession = async () => {
            try {
                const session = await cognitoAuth.getSession();
                if (!session || !session.idToken) {
                    // Refresh token expired — force logout
                    console.warn('[Session] Cognito session expired — logging out');
                    logout();
                }
            } catch {
                // Session invalid
                console.warn('[Session] Cognito session check failed — logging out');
                logout();
            }
        };

        sessionCheckRef.current = setInterval(checkSession, SESSION_CHECK_MS);
        return () => {
            if (sessionCheckRef.current) clearInterval(sessionCheckRef.current);
        };
    }, [isLoggedIn, logout]);

    const updateProfile = useCallback((profile) => {
        setFarmerProfile(profile);
        if (profile?.name) {
            setFarmerNameState(profile.name);
            localStorage.setItem(FARMER_NAME_KEY, profile.name);
        }
    }, []);

    return (
        <FarmerContext.Provider value={{
            farmerId,
            farmerPhone,
            farmerName,
            farmerProfile,
            isLoggedIn,
            authReady,
            checkPhoneExists,
            signUpAndLogin,
            signInWithPin,
            logout,
            updateProfile,
            // GPS location
            gpsLocation,
            gpsCoords,
            gpsStatus,
            gpsError,
            requestGps,
            refreshGps,
            resolvedLocation,
            resolvedCoords,
        }}>
            {children}
        </FarmerContext.Provider>
    );
}

export function useFarmer() {
    const ctx = useContext(FarmerContext);
    if (!ctx) throw new Error('useFarmer must be used within FarmerProvider');
    return ctx;
}
