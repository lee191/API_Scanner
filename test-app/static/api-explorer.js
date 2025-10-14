// API explorer
const APIExplorer = { discover: () => fetch('/api/internal/discover'), endpoints: () => fetch('/api/internal/endpoints'), test: (endpoint) => fetch(endpoint) };
