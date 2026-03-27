// Push Notification Logic

const PushManager = {
    vapidPublicKey: '{{ config["VAPID_PUBLIC_KEY"] }}', // Will be injected via template or global var

    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/-/g, '+')
            .replace(/_/g, '/');

        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);

        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    },

    async register() {
        if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
            console.warn('Push messaging is not supported');
            return;
        }

        try {
            const registration = await navigator.serviceWorker.register('/static/sw.js');
            console.log('Service Worker registered');
            return registration;
        } catch (error) {
            console.error('Service Worker Error', error);
        }
    },

    async subscribe() {
        const registration = await navigator.serviceWorker.ready;

        try {
            const subscription = await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: this.urlBase64ToUint8Array(this.vapidPublicKey)
            });

            // Send subscription to backend
            await fetch('/notifications/subscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('input[name="csrf_token"]')?.value || ''
                    // Note: If not in a form, might need to get token from meta tag
                },
                body: JSON.stringify(subscription)
            });

            console.log('User is subscribed.');
            return true;
        } catch (err) {
            console.error('Failed to subscribe the user: ', err);
            return false;
        }
    }
};
