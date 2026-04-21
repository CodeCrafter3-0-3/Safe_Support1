import { BackgroundSyncPlugin } from 'workbox-background-sync';
import { registerRoute } from 'workbox-routing';
import { NetworkOnly } from 'workbox-strategies';

self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

// Define the Background Sync plugin
const bgSyncPlugin = new BackgroundSyncPlugin('haven-offline-reports', {
  maxRetentionTime: 24 * 60, // Retry for up to 24 hours (specified in minutes)
});

// Intercept POST requests to the backend (e.g., saving reports, generating text)
registerRoute(
  ({ request, url }) => request.method === 'POST' && (url.pathname.includes('/api/save') || url.pathname.includes('/api/generate-text')),
  new NetworkOnly({
    plugins: [bgSyncPlugin],
  }),
  'POST'
);