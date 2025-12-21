--vault timestamp, salt
CREATE TABLE IF NOT EXISTS vault_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

--user preferences
CREATE TABLE IF NOT EXISTS preferences (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
