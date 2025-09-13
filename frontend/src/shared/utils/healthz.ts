export async function waitForBackendReady(options?: { baseUrl?: string; timeoutMs?: number; maxAttempts?: number; initialDelayMs?: number; }) {
    const baseUrl = options?.baseUrl || '';
    const timeoutMs = options?.timeoutMs ?? 60000; // extend to 60s
    const maxAttempts = options?.maxAttempts ?? 8; // allow a few more attempts
    const initialDelayMs = options?.initialDelayMs ?? 300; // start small

    const deadline = Date.now() + timeoutMs;
    let delay = initialDelayMs;

    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        try {
            const ctrl = new AbortController();
            const t = setTimeout(() => ctrl.abort(), Math.min(1500, delay));
            // Use vite proxy to reach backend inside docker network
            const res = await fetch(`${baseUrl}/api/healthz`, { signal: ctrl.signal });
            clearTimeout(t);
            if (res.ok) return true;
        } catch (_) {
            // ignore and backoff
        }
        if (Date.now() + delay > deadline) break;
        await new Promise((r) => setTimeout(r, delay));
        delay = Math.min(delay * 2, 2000);
    }
    return false;
}

export async function fetchAfterReady(input: RequestInfo | URL, init?: RequestInit) {
    await waitForBackendReady({});
    return fetch(input, init);
}
