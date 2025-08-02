/**
 * Mobile Utilities Module
 * Provides device detection, mobile-specific configurations, and interaction handling
 */

console.log("✅ mobile-utils.js loaded");

// ========================================
// MOBILE DETECTION AND UTILITIES
// ========================================

/**
 * Mobile detection and utility functions
 * Provides device capability detection and mobile-specific configurations
 */
class MobileUtils {
    /**
     * Detect if the current device is mobile based on screen size and touch capability
     * @returns {boolean} True if device is considered mobile
     */
    static isMobile() {
        // Check for touch capability first (most reliable for mobile detection)
        if ('ontouchstart' in window || navigator.maxTouchPoints > 0) {
            return true;
        }

        // Check for mobile screen sizes (including larger phones)
        if (window.innerWidth <= 1024) {
            return true;
        }

        // Check user agent for mobile devices (fallback)
        if (/Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
            return true;
        }

        return false;
    }

    /**
     * Detect if the current device is iOS
     * @returns {boolean} True if device is iOS
     */
    static isIOS() {
        return /iPad|iPhone|iPod/.test(navigator.userAgent);
    }

    /**
     * Detect if the current device is Android
     * @returns {boolean} True if device is Android
     */
    static isAndroid() {
        return /Android/.test(navigator.userAgent);
    }

    /**
     * Check if device supports touch interactions
     * @returns {boolean} True if touch is supported
     */
    static supportsTouch() {
        return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    }

    /**
     * Check if device supports haptic feedback
     * @returns {boolean} True if haptic feedback is available
     */
    static supportsHaptic() {
        return 'vibrate' in navigator || 'hapticFeedback' in navigator;
    }

    /**
     * Get the actual viewport height (accounting for mobile browser UI)
     * @returns {number} Viewport height in pixels
     */
    static getViewportHeight() {
        return window.visualViewport ?
            window.visualViewport.height :
            window.innerHeight;
    }

    /**
     * Get the actual viewport width
     * @returns {number} Viewport width in pixels
     */
    static getViewportWidth() {
        return window.visualViewport ?
            window.visualViewport.width :
            window.innerWidth;
    }

    /**
     * Detect if device is in landscape orientation
     * @returns {boolean} True if in landscape mode
     */
    static isLandscape() {
        return window.innerWidth > window.innerHeight;
    }

    /**
     * Detect if device is in portrait orientation
     * @returns {boolean} True if in portrait mode
     */
    static isPortrait() {
        return window.innerHeight > window.innerWidth;
    }

    /**
     * Get device pixel ratio for high-DPI displays
     * @returns {number} Device pixel ratio
     */
    static getPixelRatio() {
        return window.devicePixelRatio || 1;
    }

    /**
     * Trigger haptic feedback if supported
     * @param {string} type - Type of haptic feedback ('light', 'medium', 'heavy')
     */
    static triggerHaptic(type = 'light') {
        if (this.supportsHaptic()) {
            const patterns = {
                light: 10,
                medium: 20,
                heavy: 50
            };

            if (navigator.vibrate) {
                navigator.vibrate(patterns[type] || patterns.light);
            }
        }
    }

    /**
     * Get safe area insets for devices with notches/home indicators
     * @returns {object} Safe area insets {top, right, bottom, left}
     */
    static getSafeAreaInsets() {
        const style = getComputedStyle(document.documentElement);
        return {
            top: parseInt(style.getPropertyValue('--sat') || '0'),
            right: parseInt(style.getPropertyValue('--sar') || '0'),
            bottom: parseInt(style.getPropertyValue('--sab') || '0'),
            left: parseInt(style.getPropertyValue('--sal') || '0')
        };
    }
}

// ========================================
// MOBILE CONFIGURATION CONSTANTS
// ========================================

/**
 * Mobile-specific configuration constants
 * Based on Apple's Human Interface Guidelines and mobile best practices
 */
const MobileConfig = {
    // Touch interaction settings
    touchTargetSize: 44, // Minimum touch target size in pixels (iOS HIG)
    touchTolerance: 20, // Touch tolerance for precise interactions
    longPressThreshold: 500, // Long press detection time in ms
    doubleTapThreshold: 300, // Double tap time window in ms
    panThreshold: 10, // Minimum distance for pan gesture in pixels

    // Animation timing (following iOS guidelines)
    animations: {
        fast: 200, // Quick feedback animations
        standard: 300, // Standard UI transitions
        slow: 500, // Complex transitions
        spring: { tension: 300, friction: 30 } // Spring animation config
    },

    // Layout breakpoints
    breakpoints: {
        mobileSmall: 375, // iPhone SE and similar
        mobile: 576, // Standard mobile
        mobileLarge: 768, // Large mobile/small tablet
        tablet: 992 // Tablet and above
    },

    // Chart-specific mobile settings
    chart: {
        minHeight: 300, // Minimum chart height on mobile
        maxHeight: '70vh', // Maximum chart height
        portraitHeight: '50vh', // Portrait mode height
        landscapeHeight: '70vh', // Landscape mode height
        settingsHeight: '60vh' // Settings panel height
    },

    // Performance settings
    performance: {
        targetFPS: 60, // Target frame rate
        maxMemoryMB: 50, // Maximum memory usage for chart
        debounceMs: 16 // Debounce time for frequent events (60fps)
    },

    // Haptic feedback settings
    haptic: {
        enabled: true,
        feedbackTypes: {
            selection: 'light',
            success: 'medium',
            error: 'heavy',
            warning: 'medium'
        }
    }
};

// ========================================
// MOBILE INTERACTION STATE MANAGEMENT
// ========================================

/**
 * Mobile interaction state management
 * Tracks touch interactions and gesture states
 */
class MobileInteractionState {
    constructor() {
        this.reset();
    }

    reset() {
        this.touchStartTime = null;
        this.touchStartPosition = { x: 0, y: 0 };
        this.touchCurrentPosition = { x: 0, y: 0 };
        this.isLongPress = false;
        this.gestureType = null; // 'tap', 'pan', 'pinch', 'longpress'
        this.activeTouch = null;
        this.touchCount = 0;
        this.initialDistance = 0; // For pinch gestures
        this.lastTapTime = 0; // For double tap detection
    }

    startTouch(event) {
        const touch = event.touches[0];
        this.touchStartTime = Date.now();
        this.touchStartPosition = { x: touch.clientX, y: touch.clientY };
        this.touchCurrentPosition = { x: touch.clientX, y: touch.clientY };
        this.activeTouch = touch.identifier;
        this.touchCount = event.touches.length;

        if (this.touchCount === 2) {
            // Calculate initial distance for pinch gesture
            const touch2 = event.touches[1];
            this.initialDistance = Math.sqrt(
                Math.pow(touch2.clientX - touch.clientX, 2) +
                Math.pow(touch2.clientY - touch.clientY, 2)
            );
        }
    }

    updateTouch(event) {
        if (this.activeTouch === null) return;

        const touch = Array.from(event.touches).find(t => t.identifier === this.activeTouch);
        if (touch) {
            this.touchCurrentPosition = { x: touch.clientX, y: touch.clientY };
        }
    }

    endTouch() {
        const touchDuration = Date.now() - this.touchStartTime;
        const distance = this.getTouchDistance();

        // Determine gesture type
        if (touchDuration > MobileConfig.longPressThreshold && distance < MobileConfig.panThreshold) {
            this.gestureType = 'longpress';
        } else if (distance > MobileConfig.panThreshold) {
            this.gestureType = 'pan';
        } else if (this.isDoubleTap()) {
            this.gestureType = 'doubletap';
        } else {
            this.gestureType = 'tap';
        }

        this.lastTapTime = Date.now();
    }

    getTouchDistance() {
        return Math.sqrt(
            Math.pow(this.touchCurrentPosition.x - this.touchStartPosition.x, 2) +
            Math.pow(this.touchCurrentPosition.y - this.touchStartPosition.y, 2)
        );
    }

    isDoubleTap() {
        const timeSinceLastTap = Date.now() - this.lastTapTime;
        return timeSinceLastTap < MobileConfig.doubleTapThreshold;
    }

    isPinchGesture() {
        return this.touchCount === 2;
    }
}

// ========================================
// GLOBAL EXPORTS
// ========================================

// Export utilities for global access
window.MobileUtils = MobileUtils;
window.MobileConfig = MobileConfig;
window.MobileInteractionState = MobileInteractionState;

console.log("📱 Mobile utilities initialized and exported globally");