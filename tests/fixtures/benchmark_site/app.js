// Benchmark fixture for route_api_discovery detection coverage.
// Each block intentionally contains a known pattern. Tests assert that
// the discovery tool finds every path/api/secret listed below.
// DO NOT prettify or modify spacing without updating tests.

// === fetch / axios (already supported baseline) ===
fetch('/api/users');
fetch(`/api/users/${id}`);
axios.get('/api/orders');
axios.post('/api/cart', body);
axios({ method: 'POST', url: '/api/checkout', baseURL: 'https://bench.local' });

// === Modern fetch wrappers ===
ky.get('/api/profile');
ky.post('/api/profile', { json: payload });
got('https://bench.local/v1/items');
superagent.get('/api/health').end(cb);

// === Vue / Nuxt ===
$fetch('/api/nuxt/posts');
useFetch('/api/nuxt/items');

// === React Router / Vue Router / Svelte navigation ===
router.push('/dashboard');
useNavigate()('/profile');
goto('/svelte/route');
navigate('/orders/list');

// === Angular HttpClient ===
this.http.get('/api/angular/users');
this.http.post('/api/angular/login', creds);
this.http.put('/api/angular/profile', data);
this.http.delete('/api/angular/sessions/42');

// === jQuery legacy ===
$.ajax({ url: '/api/jquery/list', method: 'GET' });
$.get('/api/jquery/get-only');
$.post('/api/jquery/post-only', body);

// === Custom client / chainable ===
apiClient.get('/api/custom/me');
api.users.list('/api/custom/users');

// === GraphQL ===
const QUERY = gql`query GetUsers { users { id name } }`;
const MUTATION = gql`mutation CreateUser($input: UserInput!) { createUser(input: $input) { id } }`;
fetch('/graphql', { method: 'POST', body: JSON.stringify({ query: '{ orders { id } }' }) });

// === Realtime ===
const ws = new WebSocket('wss://bench.local/ws/notifications');
const sock = io('https://bench.local/realtime/chat');
const stream = new EventSource('/api/sse/events');

// === HTML resource hints (kept here as a string for the JS scope; HTML doc has them too) ===
// see index.html for <link rel="preload" href="/api/init"> etc.

// === Route templates ===
const routes = [
  { path: '/users/:id', component: User },
  { path: '/admin/{orgId}/dashboard', component: Admin },
];

// === Hash / query-only ===
location.href = '#/login';
location.search = '?action=signup';

// === Database connection strings (secret) ===
const DB_PG  = "postgres://app:s3cret-pw@db.internal:5432/app_db";
const DB_MY  = "mysql://root:r00tpass@10.0.0.5/payments";
const DB_MGO = "mongodb://writer:writepass@mongo:27017/orders";
const DB_RD  = "redis://:r3dispass@cache.internal:6379/0";

// === Webhook URLs (secret) ===
const SLACK_HOOK   = "https://hooks[.]slack[.]com/services/T01ABCDEF/B02ZZZZZZ/abcdefghijklmnopqrstuvwx";
const DISCORD_HOOK = "https://discord.com/api/webhooks/123456789012345678/abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ012345_abcd";

// === Twilio / SendGrid (secret) ===
const TWILIO_SID = "ACabcdefabcdefabcdefabcdefabcdef12";
const SG_API_KEY = "SG.abcdefghijklmnopqrstuv.abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMN";

// === Data attributes leak (in HTML, but client may construct same) ===
document.body.dataset.api = '/api/data-attr/config';

// === Template literal with interpolation (after normalization should keep path) ===
fetch(`/api/users/${userId}/profile`);
fetch(`/api/${tenant}/billing`);

// === Hash route ===
location.href = '#/account/settings';

// === XHR open() ===
xhr.open('GET', '/api/xhr/legacy');

// === Custom http client variants ===
http.put('/api/custom-http/put-only');
http.delete('/api/custom-http/del-only');

// === Angular Resource ===
$resource('/api/resource/items/:id');

// === RxJS / WebClient ajax ===
ajax.getJSON('/api/rxjs/users');

// === Hardcoded GraphQL queries via fetch with /graphql endpoint already covered above ===
// === Webpack public path leak (often reveals deep API) ===
__webpack_public_path__ = '/static/dist/';
window.__APP_CONFIG__ = { apiBase: '/api/v2', wsBase: 'wss://bench.local/v2/ws' };

// === Connection-string-like in HTTP URL credentials (must NOT be flagged as DB) ===
const safeHttp = "https://user:pass@bench.local/api/with-creds";

// === False-positive guard: example/dummy strings should not be detected as APIs ===
const help = "See documentation at /api/docs for usage";
const example = "// example: /api/example-only";

// === Method chaining custom client ===
request.url('/api/chain/start').method('POST').send();
