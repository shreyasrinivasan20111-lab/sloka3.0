/**
 * Enhanced authentication handler for serverless environment
 * Handles session expiration and provides better user experience
 */

class AuthHandler {
    constructor() {
        this.checkInterval = null;
        this.lastAuthCheck = 0;
        this.authCheckDelay = 30000; // Check every 30 seconds
    }

    /**
     * Initialize authentication monitoring
     */
    init() {
        this.startPeriodicCheck();
        this.setupRequestInterceptor();
    }

    /**
     * Start periodic authentication checks
     */
    startPeriodicCheck() {
        if (this.checkInterval) {
            clearInterval(this.checkInterval);
        }

        this.checkInterval = setInterval(() => {
            this.checkAuthStatus();
        }, this.authCheckDelay);
    }

    /**
     * Check current authentication status
     */
    async checkAuthStatus() {
        try {
            const now = Date.now();
            if (now - this.lastAuthCheck < 10000) {
                return; // Don't check too frequently
            }
            this.lastAuthCheck = now;

            const response = await fetch('/api/check-auth', {
                method: 'GET',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();

            if (!result.authenticated) {
                this.handleSessionExpired(result);
            } else {
                // Update UI with current user info if needed
                if (window.updateUserDisplay) {
                    window.updateUserDisplay(result.user);
                }
            }
        } catch (error) {
            console.warn('Auth check failed:', error);
        }
    }

    /**
     * Handle session expiration
     */
    handleSessionExpired(result) {
        // Clear any local user state
        if (window.clearUserState) {
            window.clearUserState();
        }

        // Show appropriate message
        let message = 'Your session has expired. Please login again.';
        if (result.error === 'session_invalid' && result.message) {
            message = result.message;
        }

        // Show user-friendly notification
        this.showSessionExpiredNotification(message);

        // Redirect to login page after a short delay
        setTimeout(() => {
            if (window.location.pathname !== '/frontend/index.html' && 
                window.location.pathname !== '/') {
                window.location.href = '/frontend/index.html';
            }
        }, 3000);
    }

    /**
     * Show session expired notification
     */
    showSessionExpiredNotification(message) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = 'session-expired-notification';
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-exclamation-circle"></i>
                <span>${message}</span>
                <button onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;

        // Add styles
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
            border-radius: 5px;
            padding: 15px;
            max-width: 400px;
            z-index: 10000;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            animation: slideInRight 0.3s ease-out;
        `;

        // Add to page
        document.body.appendChild(notification);

        // Auto-remove after 8 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 8000);
    }

    /**
     * Setup request interceptor to handle auth errors
     */
    setupRequestInterceptor() {
        // Override fetch to handle auth errors globally
        const originalFetch = window.fetch;
        window.fetch = async (...args) => {
            try {
                const response = await originalFetch(...args);
                
                if (response.status === 401) {
                    const result = await response.json().catch(() => ({}));
                    this.handleSessionExpired(result);
                }
                
                return response;
            } catch (error) {
                throw error;
            }
        };
    }

    /**
     * Enhanced login function with better error handling
     */
    async login(email, password) {
        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify({ email, password })
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || `Login failed with status ${response.status}`);
            }

            // Start monitoring after successful login
            this.startPeriodicCheck();
            
            return result;
        } catch (error) {
            console.error('Login error:', error);
            throw error;
        }
    }

    /**
     * Enhanced signup function
     */
    async signup(email, password) {
        try {
            const response = await fetch('/api/signup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify({ email, password })
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || `Signup failed with status ${response.status}`);
            }

            // Start monitoring after successful signup
            this.startPeriodicCheck();
            
            return result;
        } catch (error) {
            console.error('Signup error:', error);
            throw error;
        }
    }

    /**
     * Logout function
     */
    async logout() {
        try {
            if (this.checkInterval) {
                clearInterval(this.checkInterval);
                this.checkInterval = null;
            }

            const response = await fetch('/api/logout', {
                method: 'POST',
                credentials: 'include'
            });

            // Clear local state regardless of response
            if (window.clearUserState) {
                window.clearUserState();
            }

            // Redirect to login page
            window.location.href = '/frontend/index.html';
        } catch (error) {
            console.error('Logout error:', error);
            // Still redirect even if logout request fails
            window.location.href = '/frontend/index.html';
        }
    }

    /**
     * Destroy the auth handler
     */
    destroy() {
        if (this.checkInterval) {
            clearInterval(this.checkInterval);
            this.checkInterval = null;
        }
    }
}

// Add CSS for notifications
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    .session-expired-notification .notification-content {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .session-expired-notification button {
        background: none;
        border: none;
        font-size: 18px;
        cursor: pointer;
        color: inherit;
        margin-left: auto;
    }
`;
document.head.appendChild(style);

// Create global instance
window.authHandler = new AuthHandler();

// Auto-initialize when page loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.authHandler.init();
    });
} else {
    window.authHandler.init();
}
