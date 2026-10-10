-- Database Schema for Mr. Beast AI Multilingual Voice Robot
-- MySQL Database Initialization & Migration Script

CREATE DATABASE IF NOT EXISTS mr_beast_db;
USE mr_beast_db;

-- 1. Table: user_info
-- Stores user personal information, consent, and behavioral metrics
CREATE TABLE IF NOT EXISTS user_info (
    id INT AUTO_INCREMENT PRIMARY KEY,
    uuid VARCHAR(64) UNIQUE DEFAULT NULL,
    name VARCHAR(200) NOT NULL,
    age_range VARCHAR(32),
    gender VARCHAR(16),
    college_or_job VARCHAR(255),
    address VARCHAR(255) DEFAULT NULL,
    email VARCHAR(255) DEFAULT NULL,
    phone VARCHAR(32) DEFAULT NULL,
    preferred_language VARCHAR(16) DEFAULT 'en',
    photo_path VARCHAR(500) DEFAULT NULL,
    consent ENUM('Yes', 'No') DEFAULT 'No',
    sync_status ENUM('synced', 'pending') DEFAULT 'synced',
    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    conversation_count INT DEFAULT 0,
    avg_conversation_length FLOAT DEFAULT 0.0,
    engagement_score FLOAT DEFAULT 0.0,
    cluster_id INT DEFAULT NULL,
    INDEX idx_name (name),
    INDEX idx_last_seen (last_seen),
    INDEX idx_uuid (uuid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Table: user_images
-- Stores face images and embeddings for recognition
CREATE TABLE IF NOT EXISTS user_images (
    image_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    file_path VARCHAR(500),
    embedding TEXT,  -- JSON string of face embedding vector
    captured_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_primary BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES user_info(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Table: conversation_log
-- Stores conversations for multi-turn understanding
CREATE TABLE IF NOT EXISTS conversation_log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    speaker ENUM('User', 'Robot') NOT NULL,
    message TEXT NOT NULL,
    language VARCHAR(16) DEFAULT 'en',
    intent VARCHAR(100),
    confidence FLOAT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_info(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Table: user_behavior
-- Stores behavioral patterns for clustering
CREATE TABLE IF NOT EXISTS user_behavior (
    behavior_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    session_date DATE,
    conversation_length INT DEFAULT 0,
    time_spent_seconds INT DEFAULT 0,
    speaking_speed FLOAT DEFAULT 0.0,
    confirmation_count INT DEFAULT 0,
    emotion_happy_count INT DEFAULT 0,
    emotion_neutral_count INT DEFAULT 0,
    emotion_sad_count INT DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES user_info(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_session_date (session_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Table: registration_sessions
-- Tracks multi-turn conversational registration state
CREATE TABLE IF NOT EXISTS registration_sessions (
    session_id VARCHAR(64) PRIMARY KEY,
    user_id INT DEFAULT NULL,
    language VARCHAR(16) DEFAULT 'en',
    current_state VARCHAR(32) NOT NULL,
    collected_data TEXT,  -- JSON serialized state data
    is_confirmed BOOLEAN DEFAULT FALSE,
    status ENUM('in_progress', 'completed', 'cancelled', 'error') DEFAULT 'in_progress',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_info(id) ON DELETE SET NULL,
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. Table: sync_queue
-- Durable queue for offline persistence and synchronization
CREATE TABLE IF NOT EXISTS sync_queue (
    sync_id INT AUTO_INCREMENT PRIMARY KEY,
    uuid VARCHAR(64) NOT NULL UNIQUE,
    entity_type VARCHAR(32) NOT NULL,
    action VARCHAR(16) NOT NULL,
    payload TEXT NOT NULL,
    status ENUM('pending', 'synced', 'failed') DEFAULT 'pending',
    retry_count INT DEFAULT 0,
    last_error TEXT DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    synced_at DATETIME DEFAULT NULL,
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Insert default robot user for system identification
INSERT INTO user_info (name, age_range, gender, college_or_job, consent) 
VALUES ('Mr. Beast', 'AI', 'Robot', 'Voice Assistant', 'Yes')
ON DUPLICATE KEY UPDATE name=name;
