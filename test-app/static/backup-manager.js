// Backup manager
const BackupManager = { list: () => fetch('/api/internal/backup/list'), create: () => fetch('/api/internal/backup/create', {method:'POST'}), restore: (id) => fetch('/api/internal/backup/restore/' + id, {method:'POST'}) };
