"""
adobe_sign_oauth_local.py
--------------------------
Runs the full Adobe Sign OAuth2 Authorization Code flow locally on macOS.
After authorization, makes a GET /agreements API call and prints the results.

HOW IT WORKS:
  1. Opens your browser to Adobe Sign's login page
  2. You log in and click "Allow Access"
  3. Adobe Sign redirects to http://localhost:8080/callback
  4. This script's temporary server catches that redirect
  5. Extracts the authorization code from the URL
  6. Exchanges it for an access token
  7. Makes the API call you want
  8. Saves tokens to a local file so you don't re-authorize every time

REQUIREMENTS:
  pip install requests

SETUP:
  1. In Adobe Sign admin console, add this Redirect URI to your app:
       http://localhost:8080/callback
  2. Fill in your CLIENT_ID and CLIENT_SECRET below
  3. Run:  python3 adobe_sign_oauth_local.py
"""

import json
import os
import sys
import time
import webbrowser
import threading
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

import requests


# ── Configuration ─────────────────────────────────────────────────────────────
# ✏️  Fill these in before running

CLIENT_ID     = 'YOUR_CLIENT_ID_HERE'
CLIENT_SECRET = 'YOUR_CLIENT_SECRET_HERE'
SHARD         = 'na2'   # your account shard: na1, na2, eu1, jp1, etc.

# Local server settings — these must match what you registered in Adobe Sign
REDIRECT_HOST = 'localhost'
REDIRECT_PORT = 8080
REDIRECT_URI  = f'http://{REDIRECT_HOST}:{REDIRECT_PORT}/callback'

# Scopes to request
SCOPES = 'agreement_read:account user_login:self user_read:self'

# Where to save tokens between runs (keeps you from re-authorizing every time)
TOKEN_FILE = Path.home() / '.adobe_sign_tokens.json'

# ── OAuth2 Endpoints (derived from shard) ─────────────────────────────────────
AUTH_URL    = f'https://secure.{SHARD}.adobesign.com/public/oauth/v2'
TOKEN_URL   = f'https://api.{SHARD}.adobesign.com/oauth/v2/token'
REFRESH_URL = f'https://api.{SHARD}.adobesign.com/oauth/v2/refresh'
BASE_URI_URL= f'https://api.{SHARD}.adobesign.com/api/rest/v6/baseUris'


# ── Step 1 — Token Storage ────────────────────────────────────────────────────

def save_tokens(tokens: dict):
    """Save tokens to a local JSON file so you don't re-authorize every run."""
    with open(TOKEN_FILE, 'w') as f:
        json.dump(tokens, f, indent=2)
    # Restrict file permissions — tokens are sensitive
    os.chmod(TOKEN_FILE, 0o600)
    print(f'  Tokens saved to {TOKEN_FILE}')


def load_tokens() -> dict | None:
    """Load previously saved tokens from disk. Returns None if none exist."""
    if not TOKEN_FILE.exists():
        return None
    try:
        with open(TOKEN_FILE) as f:
            return json.load(f)
    except Exception:
        return None


def tokens_are_expired(tokens: dict) -> bool:
    """Check if the access token has expired based on saved expiry time."""
    expires_at = tokens.get('expires_at', 0)
    # Add a 60-second buffer so we refresh slightly before true expiry
    return time.time() > (expires_at - 60)


# ── Step 2 — Authorization Code Flow ─────────────────────────────────────────

# This variable is shared between the HTTP server thread and the main thread
_auth_code = None
_auth_error = None


class CallbackHandler(BaseHTTPRequestHandler):
    """
    Tiny HTTP server that listens for ONE request — the OAuth2 redirect
    from Adobe Sign after the user logs in and approves access.
    """

    def do_GET(self):
        """Called automatically when Adobe Sign redirects the browser here."""
        global _auth_code, _auth_error

        # Parse the URL query parameters
        # URL looks like: http://localhost:8080/callback?code=XXXX&state=YYYY
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if 'code' in params:
            _auth_code = params['code'][0]
            # Send a success page back to the browser
            self._respond(200,
                '<h2 style="font-family:Arial;color:#1a73e8">'
                '&#10003; Authorization successful!</h2>'
                '<p style="font-family:Arial">You can close this tab and '
                'return to your terminal.</p>'
            )
        elif 'error' in params:
            _auth_error = params.get('error_description', ['Unknown error'])[0]
            self._respond(400,
                f'<h2 style="font-family:Arial;color:#d93025">'
                f'&#10007; Authorization failed</h2>'
                f'<p style="font-family:Arial">{_auth_error}</p>'
            )
        else:
            self._respond(400, '<p>Unexpected callback — no code or error.</p>')

    def _respond(self, status: int, html: str):
        """Send an HTML response back to the browser."""
        body = html.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        """Suppress the default server request logging to keep output clean."""
        pass


def run_authorization_flow() -> dict:
    """
    Opens the browser to Adobe Sign's login page, waits for the redirect,
    and exchanges the authorization code for tokens.
    Returns the token dict.
    """
    global _auth_code, _auth_error
    _auth_code = None
    _auth_error = None

    # Build the authorization URL with all required parameters
    auth_params = {
        'response_type': 'code',
        'client_id':     CLIENT_ID,
        'redirect_uri':  REDIRECT_URI,
        'scope':         SCOPES,
        'state':         'local_python_client',  # CSRF protection — any string works
    }
    full_auth_url = AUTH_URL + '?' + urllib.parse.urlencode(auth_params)

    # Start the local callback server in a background thread
    # It will handle exactly one request then become idle
    server = HTTPServer((REDIRECT_HOST, REDIRECT_PORT), CallbackHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True  # thread dies when main program exits
    server_thread.start()

    print(f'\n Opening Adobe Sign login in your browser...')
    print(f' If the browser does not open, paste this URL manually:\n')
    print(f'  {full_auth_url}\n')

    # Open the browser automatically on macOS
    webbrowser.open(full_auth_url)

    # Wait for the callback (poll every 0.5 seconds, timeout after 120 seconds)
    print(' Waiting for you to authorize in the browser...')
    timeout = 120
    elapsed = 0
    while _auth_code is None and _auth_error is None and elapsed < timeout:
        time.sleep(0.5)
        elapsed += 0.5

    # Shut down the temporary server
    server.shutdown()

    if _auth_error:
        raise RuntimeError(f'Adobe Sign authorization denied: {_auth_error}')
    if _auth_code is None:
        raise RuntimeError('Authorization timed out after 120 seconds. Try again.')

    print(f' Authorization code received. Exchanging for tokens...')

    # Exchange the authorization code for access + refresh tokens
    token_response = requests.post(TOKEN_URL, data={
        'grant_type':   'authorization_code',
        'code':         _auth_code,
        'redirect_uri': REDIRECT_URI,
        'client_id':    CLIENT_ID,
        'client_secret':CLIENT_SECRET,
    })

    if token_response.status_code != 200:
        raise RuntimeError(
            f'Token exchange failed: HTTP {token_response.status_code}\n'
            f'{token_response.text}'
        )

    tokens = token_response.json()

    # Calculate and store the expiry time (access token lasts 1 hour = 3600 seconds)
    tokens['expires_at'] = time.time() + tokens.get('expires_in', 3600)

    return tokens


# ── Step 3 — Token Refresh ────────────────────────────────────────────────────

def refresh_access_token(tokens: dict) -> dict:
    """
    Uses the stored refresh token to get a new access token.
    Called automatically when the access token has expired.
    The refresh token is valid for 60 days from last use.
    """
    print('  Access token expired — refreshing...')

    response = requests.post(REFRESH_URL, data={
        'grant_type':    'refresh_token',
        'refresh_token': tokens['refresh_token'],
        'client_id':     CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    })

    if response.status_code != 200:
        raise RuntimeError(
            f'Token refresh failed: HTTP {response.status_code}\n'
            f'{response.text}\n'
            f'You may need to re-authorize. Delete {TOKEN_FILE} and run again.'
        )

    new_tokens = response.json()
    # Preserve the refresh token if the response does not include a new one
    if 'refresh_token' not in new_tokens:
        new_tokens['refresh_token'] = tokens['refresh_token']
    new_tokens['expires_at'] = time.time() + new_tokens.get('expires_in', 3600)

    return new_tokens


# ── Step 4 — Get a Valid Token ────────────────────────────────────────────────

def get_valid_tokens() -> dict:
    """
    Main token management function. Tries to use saved tokens, refreshes
    if expired, or runs the full authorization flow if none exist.
    This is the only function you need to call to get a working access token.
    """
    tokens = load_tokens()

    if tokens is None:
        print('No saved tokens found — starting authorization flow.')
        tokens = run_authorization_flow()
        save_tokens(tokens)
        print('  Authorization complete.\n')

    elif tokens_are_expired(tokens):
        print('Saved tokens found but access token is expired.')
        try:
            tokens = refresh_access_token(tokens)
            save_tokens(tokens)
            print('  Token refreshed successfully.\n')
        except RuntimeError as e:
            # Refresh token may also be expired (after 60 days of no use)
            print(f'  Refresh failed: {e}')
            print('  Starting fresh authorization flow...')
            TOKEN_FILE.unlink(missing_ok=True)
            tokens = run_authorization_flow()
            save_tokens(tokens)

    else:
        print('Using saved tokens (still valid).\n')

    return tokens


# ── Step 5 — API Helper ───────────────────────────────────────────────────────

def adobe_sign_get(url: str, access_token: str, stream: bool = False):
    """
    Makes an authenticated GET request to the Adobe Sign API.
    Raises an exception on non-2xx responses.

    stream=True is used for binary downloads (PDF files) so the
    response is not loaded entirely into memory at once.
    """
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
    }
    response = requests.get(url, headers=headers, stream=stream)

    if response.status_code == 401:
        raise RuntimeError(
            'API returned 401 Unauthorized. '
            'Delete the token file and re-authorize:\n'
            f'  rm {TOKEN_FILE}'
        )
    if response.status_code >= 400:
        raise RuntimeError(
            f'API error {response.status_code}: {response.text[:300]}'
        )

    return response


# ── Step 6 — Adobe Sign API Calls ─────────────────────────────────────────────

def get_base_uri(access_token: str) -> str:
    """
    Fetches and returns the correct API base URI for your account shard.
    Always call this first — your account may be on a different server
    than the default shard URL.
    """
    response = adobe_sign_get(BASE_URI_URL, access_token)
    data = response.json()
    return data['apiAccessPoint'].rstrip('/')


def get_agreements(base_uri: str, access_token: str,
                   status: str = 'SIGNED',
                   page_size: int = 20) -> list:
    """
    Returns a list of agreements filtered by status.
    Paginates automatically to collect all results.

    Parameters:
        base_uri:   From get_base_uri()
        access_token: Current access token
        status:     Filter — 'SIGNED', 'OUT_FOR_SIGNATURE', 'CANCELLED', etc.
        page_size:  How many per page (max 100)
    """
    agreements = []
    next_cursor = None

    print(f'  Fetching {status} agreements...')

    while True:
        url = (f'{base_uri}/api/rest/v6/agreements'
               f'?query={status}&pageSize={page_size}')

        if next_cursor:
            url += f'&cursor={urllib.parse.quote(next_cursor)}'

        response = adobe_sign_get(url, access_token)
        data = response.json()

        page = data.get('userAgreementList', [])
        agreements.extend(page)

        print(f'    Fetched {len(page)} agreements '
              f'(total so far: {len(agreements)})')

        # Check if there is a next page
        next_cursor = data.get('page', {}).get('nextCursor')
        if not next_cursor:
            break

        # Rate limit: Adobe Sign allows 5 requests/second
        time.sleep(0.25)

    return agreements


def download_agreement_pdf(base_uri: str, agreement_id: str,
                            access_token: str,
                            output_dir: str = '.') -> str:
    """
    Downloads the combined signed PDF (with audit trail) for one agreement.
    Saves it to output_dir and returns the local file path.
    """
    url = (f'{base_uri}/api/rest/v6/agreements/{agreement_id}'
           f'/combinedDocument'
           f'?attachAuditReport=true&attachSupportingDocuments=true')

    # Update Accept header for PDF download
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/pdf',
    }
    response = requests.get(url, headers=headers, stream=True)

    if response.status_code != 200:
        raise RuntimeError(
            f'PDF download failed: HTTP {response.status_code}'
        )

    file_path = os.path.join(output_dir, f'{agreement_id}.pdf')
    with open(file_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    return file_path


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print('=' * 60)
    print('Adobe Sign API — Local Python Client')
    print('=' * 60)

    # 1. Get a valid access token (authorize, refresh, or use cached)
    tokens = get_valid_tokens()
    access_token = tokens['access_token']

    # 2. Get the correct base URI for this account
    print('Fetching base URI...')
    base_uri = get_base_uri(access_token)
    print(f'  Base URI: {base_uri}\n')

    # 3. Get signed agreements
    agreements = get_agreements(base_uri, access_token, status='SIGNED')

    print(f'\nFound {len(agreements)} SIGNED agreement(s).\n')

    if not agreements:
        print('No signed agreements found. Done.')
        return

    # 4. Print a summary table
    print(f'{"#":<4} {"Agreement Name":<45} {"Date":<25} {"ID":<15}')
    print('-' * 95)
    for i, ag in enumerate(agreements, 1):
        name = ag.get('name', 'Unnamed')[:44]
        date = ag.get('displayDate', '')[:24]
        ag_id = ag.get('id', '')[-12:]  # show last 12 chars of ID
        print(f'{i:<4} {name:<45} {date:<25} ...{ag_id}')

    # 5. Optionally download the first PDF for testing
    print()
    answer = input('Download the first agreement PDF? (y/n): ').strip().lower()
    if answer == 'y':
        first = agreements[0]
        print(f'\nDownloading: {first["name"]}')
        output_dir = os.path.expanduser('~/Downloads')
        file_path = download_agreement_pdf(
            base_uri, first['id'], access_token, output_dir
        )
        print(f'  Saved to: {file_path}')
        print(f'  Open it to verify the audit trail is appended.')

    print('\nDone.')


if __name__ == '__main__':
    # Validate credentials are set before doing anything
    if CLIENT_ID == 'YOUR_CLIENT_ID_HERE':
        print('ERROR: Please set CLIENT_ID and CLIENT_SECRET in the script.')
        sys.exit(1)
    main()
