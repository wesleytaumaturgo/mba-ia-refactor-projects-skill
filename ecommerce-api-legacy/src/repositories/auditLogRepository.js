'use strict';

const makeAuditLogRepository = (db) => ({
    insert: (action) =>
        db.run("INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))", [action]),
});

module.exports = { makeAuditLogRepository };
