-- Database Schema for Mr. Beast Voice Robot
-- MySQL Database Initialization Script

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS mr_beast_db;
USE mr_beast_db;

-- Table: user_info
-- Stores user personal information and consent
CREATE TABLE IF NOT EXISTS user_info (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    age_range VARCHAR(32),
    gender VARCHAR(16),
    college_or_job VARCHAR(255),
    consent ENUM('Yes', 'No') DEFAULT 'No',
    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    conversation_count INT DEFAULT 0,
    avg_conversation_length FLOAT DEFAULT 0.0,
    engagement_score FLOAT DEFAULT 0.0,
    cluster_id INT DEFAULT NULL,
    INDEX idx_name (name),
    INDEX idx_last_seen (last_seen)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Table: user_images
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

-- Table: conversation_log
-- Stores all conversations for analysis
CREATE TABLE IF NOT EXISTS conversation_log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    speaker ENUM('User', 'Robot') NOT NULL,
    message TEXT NOT NULL,
    intent VARCHAR(100),
    confidence FLOAT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_info(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Table: user_behavior
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

-- Insert default robot user for system messages
INSERT INTO user_info (name, age_range, gender, college_or_job, consent) 
VALUES ('Mr. Beast', 'AI', 'Robot', 'Voice Assistant', 'Yes')
ON DUPLICATE KEY UPDATE name=name;
