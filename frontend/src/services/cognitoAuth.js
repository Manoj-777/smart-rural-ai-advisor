// src/services/cognitoAuth.js
// Cognito authentication — sign-up with phone+PIN, sign-in, token management

import {
    CognitoUserPool,
    CognitoUser,
    AuthenticationDetails,
    CognitoUserAttribute,
} from 'amazon-cognito-identity-js';

const POOL_DATA = {
    UserPoolId: 'ap-south-1_X58lNMEcn',
    ClientId: '4c3c6he88im15hmv5rdkv3m6h0',
};

const userPool = new CognitoUserPool(POOL_DATA);

/**
 * Format phone to Cognito format: +91XXXXXXXXXX
 */
function formatPhone(phone) {
    const digits = phone.replace(/\D/g, '').slice(-10);
    return `+91${digits}`;
}

/**
 * Sign up a new user with phone number and PIN.
 * Cognito sends an SMS verification code automatically.
 * @param {string} phone - 10-digit phone
 * @param {string} pin   - 6+ char PIN/password
 * @param {string} name  - Farmer name
 * @returns {Promise<{ userSub: string, codeDeliveryDetails: object }>}
 */
export function signUp(phone, pin, name) {
    return new Promise((resolve, reject) => {
        const cognitoPhone = formatPhone(phone);
        const attributes = [
            new CognitoUserAttribute({ Name: 'phone_number', Value: cognitoPhone }),
            new CognitoUserAttribute({ Name: 'name', Value: name }),
        ];

        userPool.signUp(cognitoPhone, pin, attributes, null, (err, result) => {
            if (err) return reject(err);
            resolve({
                userSub: result.userSub,
                codeDeliveryDetails: result.codeDeliveryDetails,
            });
        });
    });
}

/**
 * Confirm sign-up with the OTP code sent via SMS.
 * @param {string} phone - 10-digit phone
 * @param {string} code  - 6-digit OTP
 * @returns {Promise<string>} 'SUCCESS'
 */
export function confirmSignUp(phone, code) {
    return new Promise((resolve, reject) => {
        const cognitoPhone = formatPhone(phone);
        const cognitoUser = new CognitoUser({
            Username: cognitoPhone,
            Pool: userPool,
        });

        cognitoUser.confirmRegistration(code, true, (err, result) => {
            if (err) return reject(err);
            resolve(result); // 'SUCCESS'
        });
    });
}

/**
 * Resend the sign-up confirmation code.
 * @param {string} phone - 10-digit phone
 * @returns {Promise<object>} code delivery details
 */
export function resendConfirmationCode(phone) {
    return new Promise((resolve, reject) => {
        const cognitoPhone = formatPhone(phone);
        const cognitoUser = new CognitoUser({
            Username: cognitoPhone,
            Pool: userPool,
        });

        cognitoUser.resendConfirmationCode((err, result) => {
            if (err) return reject(err);
            resolve(result);
        });
    });
}

/**
 * Sign in with phone + PIN. Returns a session with JWT tokens.
 * @param {string} phone - 10-digit phone
 * @param {string} pin   - PIN/password
 * @returns {Promise<{ idToken: string, accessToken: string, refreshToken: string }>}
 */
export function signIn(phone, pin) {
    return new Promise((resolve, reject) => {
        const cognitoPhone = formatPhone(phone);
        const cognitoUser = new CognitoUser({
            Username: cognitoPhone,
            Pool: userPool,
        });

        const authDetails = new AuthenticationDetails({
            Username: cognitoPhone,
            Password: pin,
        });

        cognitoUser.authenticateUser(authDetails, {
            onSuccess: (session) => {
                resolve({
                    idToken: session.getIdToken().getJwtToken(),
                    accessToken: session.getAccessToken().getJwtToken(),
                    refreshToken: session.getRefreshToken().getToken(),
                });
            },
            onFailure: (err) => reject(err),
        });
    });
}

/**
 * Get the current authenticated user's session (auto-refreshes if needed).
 * Returns null if no user is signed in.
 * @returns {Promise<{ idToken: string, accessToken: string, phone: string, name: string } | null>}
 */
export function getSession() {
    return new Promise((resolve) => {
        const user = userPool.getCurrentUser();
        if (!user) return resolve(null);

        user.getSession((err, session) => {
            if (err || !session || !session.isValid()) return resolve(null);

            // Try to get user attributes but don't let it block
            // (getUserAttributes makes a network call that can hang)
            const fallbackTimer = setTimeout(() => {
                resolve({
                    idToken: session.getIdToken().getJwtToken(),
                    accessToken: session.getAccessToken().getJwtToken(),
                    phone: '',
                    name: '',
                });
            }, 2000);

            user.getUserAttributes((attrErr, attrs) => {
                clearTimeout(fallbackTimer);
                let phone = '';
                let name = '';
                if (!attrErr && attrs) {
                    for (const a of attrs) {
                        if (a.Name === 'phone_number') phone = a.Value;
                        if (a.Name === 'name') name = a.Value;
                    }
                }
                resolve({
                    idToken: session.getIdToken().getJwtToken(),
                    accessToken: session.getAccessToken().getJwtToken(),
                    phone,
                    name,
                });
            });
        });
    });
}

/**
 * Get only the current ID token (for API calls).
 * Returns null if not authenticated.
 * @returns {Promise<string | null>}
 */
export function getIdToken() {
    return new Promise((resolve) => {
        const user = userPool.getCurrentUser();
        if (!user) return resolve(null);

        user.getSession((err, session) => {
            if (err || !session || !session.isValid()) return resolve(null);
            resolve(session.getIdToken().getJwtToken());
        });
    });
}

/**
 * Sign out the current user (clears local session).
 */
export function signOut() {
    const user = userPool.getCurrentUser();
    if (user) user.signOut();
}

/**
 * Check if a user exists in the pool by attempting a forgotten password flow.
 * (Lightweight existence check without credentials.)
 * @param {string} phone - 10-digit phone
 * @returns {Promise<boolean>}
 */
export function userExists(phone) {
    return new Promise((resolve) => {
        const cognitoPhone = formatPhone(phone);
        const cognitoUser = new CognitoUser({
            Username: cognitoPhone,
            Pool: userPool,
        });

        // forgotPassword will fail with UserNotFoundException if user doesn't exist
        cognitoUser.forgotPassword({
            onSuccess: () => resolve(true),
            onFailure: (err) => {
                if (err.code === 'UserNotFoundException') return resolve(false);
                // CodeDeliveryDetails means user exists (code was sent)
                // Any other error — assume user exists to be safe
                resolve(true);
            },
            inputVerificationCode: () => {
                // User exists and code was sent — abort the flow
                resolve(true);
            },
        });
    });
}
