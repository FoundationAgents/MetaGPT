const DEFAULT_BAREWIRE_PROXY_URL = process.env.BAREWIRE_PROXY_URL || 'https://barewire.example.com/proxy';

let originalFetch: typeof fetch | null = null;
let currentBarewireProxyUrl: string = DEFAULT_BAREWIRE_PROXY_URL;
let isInterceptorActive = false;

/**
 * Validates if a string is a well-formed URL.
 * @param url The string to validate.
 * @returns True if the string is a valid URL, false otherwise.
 */
function isValidUrl(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

/**
 * Normalizes a URL string by removing a trailing slash if present.
 * @param url The URL string to normalize.
 * @returns The normalized URL string without a trailing slash.
 */
function normalizeUrl(url: string): string {
  return url.endsWith('/') ? url.slice(0, -1) : url;
}

/**
 * Initializes and activates the Barewire fetch interceptor.
 * This function will replace the global `fetch` with a wrapped version
 * that proxies requests through the Barewire edge proxy.
 *
 * The Barewire proxy is expected to receive the original target URL
 * as a query parameter named 'targetUrl'.
 * Example: `https://barewire.example.com/proxy?targetUrl=https%3A%2F%2Fapi.example.com%2Fdata`
 *
 * @param options Configuration options for the interceptor.
 * @param options.proxyUrl The URL of the Barewire edge proxy. If not provided,
 *                         it will default to `process.env.BAREWIRE_PROXY_URL`
 *                         or a default placeholder. This URL will be normalized
 *                         (trailing slash removed if present).
 * @throws Error if the provided `proxyUrl` is invalid.
 */
export function activateBarewireInterceptor(options?: { proxyUrl?: string }): void {
  if (isInterceptorActive) {
    console.warn('Barewire fetch interceptor is already active. Deactivate it first to reconfigure.');
    return;
  }

  const { proxyUrl = DEFAULT_BAREWIRE_PROXY_URL } = options || {};

  if (!isValidUrl(proxyUrl)) {
    throw new Error(`Invalid Barewire proxy URL provided: ${proxyUrl}`);
  }

  currentBarewireProxyUrl = normalizeUrl(proxyUrl);
  originalFetch = window.fetch; // Store the original fetch function

  const barewireFetchInterceptor: typeof fetch = async (input, init) => {
    // If for some reason the interceptor is deactivated internally or proxy URL is missing,
    // fall back to the original fetch. This provides a safety net.
    if (!isInterceptorActive || !currentBarewireProxyUrl) {
      return originalFetch!(input, init);
    }

    let targetUrl: URL;
    let requestInit: RequestInit | undefined = init;
    let originalRequest: Request | undefined;

    // Determine the target URL from the fetch input
    if (input instanceof Request) {
      originalRequest = input;
      targetUrl = new URL(originalRequest.url);
      // Merge init options, allowing them to override properties from the Request object.
      requestInit = { ...originalRequest, ...init };
    } else if (typeof input === 'string') {
      // Resolve relative URLs against the current window location
      targetUrl = new URL(input, window.location.href);
    } else if (input instanceof URL) {
      targetUrl = input;
    } else {
      // For any other unexpected input type, just pass it to the original fetch
      console.warn('Barewire interceptor encountered unknown fetch input type, passing through:', input);
      return originalFetch!(input, init);
    }

    // Construct the proxied URL with the target URL as a query parameter
    const proxiedUrl = new URL(currentBarewireProxyUrl);
    proxiedUrl.searchParams.set('targetUrl', targetUrl.toString());

    let finalInput: RequestInfo;
    if (originalRequest) {
      // If the original input was a Request object, we must create a new Request object
      // with the proxied URL. We clone relevant properties from the original request
      // and merge with any provided `init` options.
      finalInput = new Request(proxiedUrl.toString(), {
        method: originalRequest.method,
        headers: new Headers(originalRequest.headers), // Clone headers to prevent mutation
        // Handle body carefully: prefer `init.body`, otherwise use `originalRequest.body`.
        // Note: ReadableStream bodies can only be consumed once.
        // If originalRequest.body was already consumed, it will be null.
        // If it's a stream and not yet consumed, it will be passed through correctly.
        body: requestInit?.body !== undefined ? requestInit.body : originalRequest.body,
        mode: originalRequest.mode,
        credentials: originalRequest.credentials,
        cache: originalRequest.cache,
        redirect: originalRequest.redirect,
        referrer: originalRequest.referrer,
        referrerPolicy: originalRequest.referrerPolicy,
        integrity: originalRequest.integrity,
        keepalive: originalRequest.keepalive,
        signal: originalRequest.signal,
        // Ensure that any other properties from requestInit also get applied,
        // overriding originalRequest properties if they conflict.
        ...requestInit,
        // The `body` property is explicitly handled above to prevent accidental double-consumption
        // or incorrect merging when `requestInit.body` is absent.
      });
    } else {
      // If the original input was a string or URL, the final input is the proxied URL string.
      finalInput = proxiedUrl.toString();
      // requestInit (which merges `init`) will be used directly by the original fetch.
    }

    // Call the original fetch with the modified URL and potentially modified init
    return originalFetch!(finalInput, requestInit);
  };

  window.fetch = barewireFetchInterceptor;
  isInterceptorActive = true;
  console.info(`Barewire fetch interceptor activated. Proxying requests through: ${currentBarewireProxyUrl}`);
}

/**
 * Deactivates the Barewire fetch interceptor and restores the original `fetch` function.
 */
export function deactivateBarewireInterceptor(): void {
  if (isInterceptorActive && originalFetch) {
    window.fetch = originalFetch;
    originalFetch = null;
    isInterceptorActive = false;
    console.info('Barewire fetch interceptor deactivated. Original fetch restored.');
  } else {
    console.warn('Barewire fetch interceptor is not active or has already been deactivated.');
  }
}

/**
 * Returns the current status of the Barewire interceptor.
 * @returns An object indicating whether the interceptor is active and the proxy URL being used.
 */
export function getBarewireInterceptorStatus(): { isActive: boolean; proxyUrl: string | null } {
  return {
    isActive: isInterceptorActive,
    proxyUrl: isInterceptorActive ? currentBarewireProxyUrl : null,
  };
}