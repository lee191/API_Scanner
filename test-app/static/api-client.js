// API client
const APIClient = { get: (path) => fetch('/api/internal' + path), post: (path, data) => fetch('/api/internal' + path, {method:'POST', body: JSON.stringify(data)}) };
