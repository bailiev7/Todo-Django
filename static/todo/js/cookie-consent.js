document.addEventListener('DOMContentLoaded', function() {
    const consentBanner = document.getElementById('cookie-consent-banner');
    const acceptBtn = document.getElementById('cookie-consent-accept');
    const declineBtn = document.getElementById('cookie-consent-decline');

    const CONSENT_KEY = 'cookie-consent-accepted';
    const CONSENT_EXPIRY = 365 * 24 * 60 * 60 * 1000;

    function hasConsent() {
        const consent = localStorage.getItem(CONSENT_KEY);
        if (!consent) return null;

        const { timestamp, accepted } = JSON.parse(consent);
        const now = Date.now();

        if (now - timestamp > CONSENT_EXPIRY) {
            localStorage.removeItem(CONSENT_KEY);
            return null;
        }

        return accepted;
    }

    function setConsent(accepted) {
        const consent = {
            timestamp: Date.now(),
            accepted: accepted
        };
        localStorage.setItem(CONSENT_KEY, JSON.stringify(consent));
        hideBanner();
    }

    function hideBanner() {
        if (consentBanner) {
            consentBanner.classList.add('hidden');
        }
    }

    const hasUserConsent = hasConsent();

    if (hasUserConsent === null) {
        if (consentBanner) {
            consentBanner.classList.remove('hidden');
        }
    } else {
        hideBanner();
    }

    if (acceptBtn) {
        acceptBtn.addEventListener('click', function() {
            setConsent(true);
        });
    }

    if (declineBtn) {
        declineBtn.addEventListener('click', function() {
            setConsent(false);
        });
    }
});
