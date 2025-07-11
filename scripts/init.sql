-- Yuyama データベース初期化スクリプト
-- ローカル開発環境用のダミーデータ

-- 文字エンコーディングを明示的に設定
SET NAMES utf8mb4;
SET CHARACTER_SET_CLIENT = utf8mb4;
SET CHARACTER_SET_RESULTS = utf8mb4;
SET CHARACTER_SET_CONNECTION = utf8mb4;

USE yuyama;

-- テーブルが存在しない場合の作成（SQLAlchemyが実行される前に備えて）
CREATE TABLE IF NOT EXISTS `users` (
  `email` varchar(255) NOT NULL,
  `azure_id` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `role` varchar(50) NOT NULL,
  `is_archive` tinyint(1) NOT NULL,
  `id` varchar(26) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`),
  UNIQUE KEY `azure_id` (`azure_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `chat_rooms` (
  `user_id` varchar(26) NOT NULL,
  `name` varchar(255) NOT NULL,
  `custom_prompt` text,
  `is_active_custom_prompt` tinyint(1) DEFAULT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `id` varchar(26) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `chat_rooms_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `chat_messages` (
  `chat_room_id` varchar(26) NOT NULL,
  `role` enum('user','assistant') NOT NULL,
  `message` text NOT NULL,
  `references` json NOT NULL,
  `evaluation` enum('none','good','bad') NOT NULL,
  `assistant_prompt` text,
  `model` varchar(50) NOT NULL,
  `token_usage` int DEFAULT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `index_types` json DEFAULT NULL,
  `id` varchar(26) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `chat_room_id` (`chat_room_id`),
  CONSTRAINT `chat_messages_ibfk_1` FOREIGN KEY (`chat_room_id`) REFERENCES `chat_rooms` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `files` (
  `blob_name` varchar(255) NOT NULL,
  `id` varchar(26) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `indexed_files` (
  `id` int NOT NULL AUTO_INCREMENT,
  `original_blob_name` varchar(512) NOT NULL,
  `indexed_blob_name` varchar(255) NOT NULL,
  `file_type` varchar(50) NOT NULL,
  `index_type` varchar(36) NOT NULL,
  `indexed_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_indexed_files_original_blob_name` (`original_blob_name`),
  KEY `ix_indexed_files_id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `search_index_types` (
  `id` varchar(36) NOT NULL,
  `folder_name` varchar(255) NOT NULL,
  `display_order` int NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `folder_name` (`folder_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ユーザーテーブルの初期データ
INSERT IGNORE INTO users (id, email, azure_id, name, role, is_archive, created_at, updated_at) VALUES
('01MOCK01USER001001001001', 'test.user@example.com', 'azure-mock-user-001', 'Test User', 'user', 0, NOW(), NOW()),
('01MOCK01ADMIN01001001001', 'admin@example.com', 'azure-mock-admin-001', 'Admin User', 'admin', 0, NOW(), NOW()),
('01MOCK01DEMO001001001001', 'demo@kandenko.co.jp', 'azure-demo-user-001', 'Demo User', 'user', 0, NOW(), NOW());

-- チャットルームの初期データ
INSERT IGNORE INTO chat_rooms (id, user_id, name, custom_prompt, is_active_custom_prompt, deleted_at, created_at, updated_at) VALUES
('01ROOM01TEST001001001001', '01MOCK01USER001001001001', 'ローカル開発環境テスト', NULL, NULL, NULL, NOW(), NOW()),
('01ROOM01DEMO001001001001', '01MOCK01DEMO001001001001', 'デモ用チャットルーム', NULL, NULL, NULL, NOW(), NOW()),
('01ROOM01ADMIN1001001001', '01MOCK01ADMIN01001001001', '管理者テストルーム', 'あなたは管理者向けアシスタントです。', 1, NULL, NOW(), NOW());

-- メッセージの初期データ
INSERT IGNORE INTO chat_messages (id, chat_room_id, role, message, `references`, evaluation, assistant_prompt, model, token_usage, deleted_at, index_types, created_at, updated_at) VALUES
('01MSG001USER001001001001', '01ROOM01TEST001001001001', 'user', 'こんにちは！ローカル開発環境のテストです。', '[]', 'none', NULL, 'gpt-4', NULL, NULL, NULL, NOW(), NOW()),
('01MSG001ASST001001001001', '01ROOM01TEST001001001001', 'assistant', 'こんにちは！モック環境での応答です。どのようなお手伝いができますか？', '[]', 'none', 'あなたは親切なアシスタントです。', 'gpt-4', 50, NULL, NULL, NOW(), NOW()),
('01MSG002USER001001001001', '01ROOM01DEMO001001001001', 'user', 'RAGシステムの動作確認をしたいです。', '[]', 'none', NULL, 'gpt-4', NULL, NULL, NULL, NOW(), NOW()),
('01MSG002ASST001001001001', '01ROOM01DEMO001001001001', 'assistant', 'RAGシステムのテストへようこそ！現在はローカルモックモードで動作しています。', '[]', 'none', 'あなたはRAGシステムのアシスタントです。', 'gpt-4', 75, NULL, NULL, NOW(), NOW()),
('01MSG003USER001001001001', '01ROOM01ADMIN1001001001', 'user', '管理機能のテストです。', '[]', 'none', NULL, 'gpt-4', NULL, NULL, NULL, NOW(), NOW()),
('01MSG003ASST001001001001', '01ROOM01ADMIN1001001001', 'assistant', '管理者としてログインされています。システムの状態は正常です。', '[]', 'none', 'あなたは管理者向けアシスタントです。', 'gpt-4', 60, NULL, NULL, NOW(), NOW());

-- ファイル情報の初期データ（サンプル文書）
INSERT IGNORE INTO files (id, blob_name, created_at, updated_at) VALUES
('01FILE01SAMPLE1001001001', 'mock/sample_document.pdf', NOW(), NOW()),
('01FILE01MANUAL1001001001', 'mock/test_manual.docx', NOW(), NOW()),
('01FILE01README001001001', 'mock/readme.txt', NOW(), NOW());

-- インデックスファイル情報の初期データ
INSERT IGNORE INTO indexed_files (original_blob_name, indexed_blob_name, file_type, index_type, indexed_at) VALUES
('mock/sample_document.pdf', 'indexed/sample_document_chunks.json', 'pdf', '01INDEX01TYPE001001001001', NOW()),
('mock/test_manual.docx', 'indexed/test_manual_chunks.json', 'docx', '01INDEX01TYPE001001001001', NOW()),
('mock/readme.txt', 'indexed/readme_chunks.json', 'txt', '01INDEX01TYPE001001001001', NOW());

-- 検索インデックスタイプの初期データ
INSERT IGNORE INTO search_index_types (id, folder_name, display_order, created_at) VALUES
('01INDEX01TYPE001001001001', 'general_documents', 1, NOW()),
('01INDEX02TYPE001001001001', 'technical_manuals', 2, NOW()),
('01INDEX03TYPE001001001001', 'administrative_docs', 3, NOW());

-- 初期データ挿入完了メッセージ
SELECT '✅ ローカル開発環境用の初期データが正常に挿入されました！' AS message;

-- データベースの状態確認
SELECT
    'users' AS table_name,
    COUNT(*) AS record_count
FROM users
UNION ALL
SELECT
    'chat_rooms' AS table_name,
    COUNT(*) AS record_count
FROM chat_rooms
UNION ALL
SELECT
    'chat_messages' AS table_name,
    COUNT(*) AS record_count
FROM chat_messages
UNION ALL
SELECT
    'files' AS table_name,
    COUNT(*) AS record_count
FROM files
UNION ALL
SELECT
    'indexed_files' AS table_name,
    COUNT(*) AS record_count
FROM indexed_files
UNION ALL
SELECT
    'search_index_types' AS table_name,
    COUNT(*) AS record_count
FROM search_index_types;
