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
VALUES (1, 'Default Repository', 'local');

-- Messages table schema
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repository_id INTEGER DEFAULT 1,
    content TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    author TEXT,
    git_commit_hash TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (repository_id) REFERENCES repositories(id)
);

-- Create indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(created_at);
CREATE INDEX IF NOT EXISTS idx_messages_git_hash ON messages(git_commit_hash);
