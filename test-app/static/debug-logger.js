// Debug logger
const Logger = { log: (msg) => fetch('/api/internal/debug/log', { method: 'POST', body: JSON.stringify({msg}) }) };
