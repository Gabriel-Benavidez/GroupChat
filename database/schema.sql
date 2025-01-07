-- Messages table schema
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    author TEXT,
    git_commit_hash TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Index for faster timestamp-based queries
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);

-- Index for git commit hash lookups
CREATE INDEX IF NOT EXISTS idx_messages_git_hash ON messages(git_commit_hash);
