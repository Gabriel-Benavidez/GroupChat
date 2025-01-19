-- Repositories table first
CREATE TABLE IF NOT EXISTS repositories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    last_synced TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(url)
);

-- Default repository
INSERT OR IGNORE INTO repositories (id, name, url) 
VALUES (1, 'default', 'default');

-- Messages table schema
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repository_id INTEGER DEFAULT 1,
    content TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    author TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (repository_id) REFERENCES repositories(id)
);

-- Add git_commit_hash column if it doesn't exist
ALTER TABLE messages ADD COLUMN git_commit_hash TEXT;

-- Index for faster timestamp-based queries
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(created_at);

-- Index for git commit hash lookups
CREATE INDEX IF NOT EXISTS idx_messages_git_hash ON messages(git_commit_hash);
