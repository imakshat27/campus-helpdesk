import { afterEach, describe, expect, it, vi } from 'vitest';
import { api } from './api';

afterEach(() => { vi.unstubAllEnvs(); vi.unstubAllGlobals(); });

describe('deployed API connection', () => {
  it('uses the configured Render URL and forwards staff authentication', async () => {
    vi.stubEnv('VITE_API_BASE_URL', 'https://helpdesk.example.onrender.com/api/');
    const request = vi.fn().mockResolvedValue({ ok: true, json: async () => [] });
    vi.stubGlobal('fetch', request);
    await api('/staff/tickets', { headers: { Authorization: 'Basic test-credential' } });
    expect(request).toHaveBeenCalledWith('https://helpdesk.example.onrender.com/api/staff/tickets', expect.objectContaining({ headers: { 'Content-Type': 'application/json', Authorization: 'Basic test-credential' } }));
  });

  it('keeps the local proxy when no public API URL is configured', async () => {
    vi.stubEnv('VITE_API_BASE_URL', '');
    const request = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ database: 'connected' }) });
    vi.stubGlobal('fetch', request);
    await api('/health');
    expect(request).toHaveBeenCalledWith('/api/health', expect.anything());
  });

  it('reports an unavailable backend without a simulated successful response', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('network unavailable')));
    await expect(api('/chat', { method: 'POST' })).rejects.toThrow('Could not reach the helpdesk');
  });
});
