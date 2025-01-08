-- Repositories table
CREATE TABLE IF NOT EXISTS repositories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    last_synced TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(url)
);

-- Messages table with repository reference and enhanced fields
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repository_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    author TEXT,
    url TEXT,
    message_type TEXT,
    parent_title TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (repository_id) REFERENCES repositories(id)
);

-- Index for faster timestamp-based queries
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);

-- Index for repository lookups
CREATE INDEX IF NOT EXISTS idx_messages_repository ON messages(repository_id);

-- Index for repository URL lookups
CREATE INDEX IF NOT EXISTS idx_repositories_url ON repositories(url);

-- Index for message type lookups
CREATE INDEX IF NOT EXISTS idx_messages_type ON messages(message_type);
