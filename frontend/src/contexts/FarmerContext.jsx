// src/contexts/FarmerContext.jsx
// Shared farmer identity — single source of truth for farmer_id across all pages
// Phone-number based identity (natural for rural India — no passwords needed)

import { createContext, useContext, useState, useCallback, useEffect } from 'react';
import config from '../config';

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

    // Load profile from DynamoDB when logged in
    useEffect(() => {
        if (!farmerId) return;
        const loadProfile = async () => {
            try {
                const res = await fetch(`${config.API_URL}/profile/${farmerId}`);
                const data = await res.json();
                if (data.data && data.data.name) {
                    setFarmerProfile(data.data);
                    setFarmerNameState(data.data.name);
                    localStorage.setItem(FARMER_NAME_KEY, data.data.name);
                }
            } catch { /* offline — use cached name */ }
        };
        loadProfile();
    }, [farmerId]);

    /**
     * Check if a phone number is already registered (has a profile with a name).
     * Returns the profile data if exists, or null if not registered.
     */
    const checkPhoneExists = useCallback(async (phone) => {
        const cleanPhone = phone.replace(/\D/g, '').slice(-10);
        const id = `ph_${cleanPhone}`;
        try {
            const res = await fetch(`${config.API_URL}/profile/${id}`);
            const data = await res.json();
            if (data.data && data.data.name) {
                return data.data; // registered user
            }
        } catch { /* offline */ }
        return null; // not registered
    }, []);

    /**
     * Login with phone number.
     * Phone number becomes the farmer_id (prefixed with 'ph_' to distinguish from legacy UUIDs).
     * For new users, pass a full profileData object.
     * For returning users, pass no profileData — profile will be loaded from DB.
     * Returns the profile if it exists in DynamoDB (returning user), or the new profile.
     */
    const loginWithPhone = useCallback(async (phone, name = '', profileData = null) => {
        const cleanPhone = phone.replace(/\D/g, '').slice(-10); // last 10 digits
        const id = `ph_${cleanPhone}`;

        localStorage.setItem(FARMER_ID_KEY, id);
        localStorage.setItem(FARMER_PHONE_KEY, cleanPhone);
        setFarmerIdState(id);
        setFarmerPhoneState(cleanPhone);
        setIsLoggedIn(true);

        // Try to load existing profile from DynamoDB
        try {
            const res = await fetch(`${config.API_URL}/profile/${id}`);
            const data = await res.json();
            if (data.data && data.data.name) {
                // Returning user — profile exists
                setFarmerProfile(data.data);
                setFarmerNameState(data.data.name);
                localStorage.setItem(FARMER_NAME_KEY, data.data.name);
                return data.data;
            }
        } catch { /* offline */ }

        // New user — create full profile
        const newProfile = profileData || {
            name, language: 'en-IN', state: '', district: '',
            crops: [], soil_type: '', land_size_acres: 0
        };
        if (newProfile.name || name) {
            if (!newProfile.name) newProfile.name = name;
            try {
                await fetch(`${config.API_URL}/profile/${id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(newProfile)
                });
            } catch { /* will save later */ }
            setFarmerProfile(newProfile);
            setFarmerNameState(newProfile.name);
            localStorage.setItem(FARMER_NAME_KEY, newProfile.name);
        }
        return null;
    }, []);

    const logout = useCallback(() => {
        localStorage.removeItem(FARMER_ID_KEY);
        localStorage.removeItem(FARMER_PHONE_KEY);
        localStorage.removeItem(FARMER_NAME_KEY);
        setFarmerIdState(null);
        setFarmerPhoneState('');
        setFarmerNameState('');
        setFarmerProfile(null);
        setIsLoggedIn(false);
    }, []);

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
            checkPhoneExists,
            loginWithPhone,
            logout,
            updateProfile,
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
