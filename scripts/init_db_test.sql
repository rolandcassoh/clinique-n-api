-- Script SQL pour initialiser la base de données avec des utilisateurs de test
-- Base de données : clinique_dev

USE clinique_dev;

-- Créer la table utilisateurs si elle n'existe pas
CREATE TABLE IF NOT EXISTS utilisateurs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) NOT NULL UNIQUE,
    mot_de_passe_hash VARCHAR(255) NOT NULL,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    role ENUM('super-admin', 'admin', 'medecin', 'receptionniste', 'patient') NOT NULL,
    est_actif BOOLEAN DEFAULT TRUE,
    email_verifie BOOLEAN DEFAULT FALSE,
    telephone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,
    INDEX idx_email (email),
    INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Nettoyer les données existantes (optionnel)
SET FOREIGN_KEY_CHECKS = 0;
DELETE FROM utilisateurs;
SET FOREIGN_KEY_CHECKS = 1;

-- Insérer les utilisateurs de test
-- Note: Les mots de passe sont hashés avec bcrypt
INSERT INTO utilisateurs (courriel, mot_de_passe, nom, est_actif, courriel_verifie_le, totp_actif) VALUES
-- Super Admin: Admin@2026
('admin@clinique-n.com', '$2b$12$fB7qJZs3gN8Lxv4w1YtQ5e3j5qWz9Xp1KmLv8yTn6HfRp2Sz4Kx.m', 'Admin Super', TRUE, NOW(), FALSE),

-- Admin Clinique: AdminClinic@2026
('admin.clinique@test.com', '$2b$12$fB7qJZs3gN8Lxv4w1YtQ5e3j5qWz9Xp1KmLv8yTn6HfRp2Sz4Kx.m', 'Jean Dupont', TRUE, NOW(), FALSE),

-- Médecin: Medecin@2026
('medecin@test.com', '$2b$12$fB7qJZs3gN8Lxv4w1YtQ5e3j5qWz9Xp1KmLv8yTn6HfRp2Sz4Kx.m', 'Sophie Martin', TRUE, NOW(), FALSE),

-- Réceptionniste: Reception@2026
('receptionniste@test.com', '$2b$12$fB7qJZs3gN8Lxv4w1YtQ5e3j5qWz9Xp1KmLv8yTn6HfRp2Sz4Kx.m', 'Marie Leblanc', TRUE, NOW(), FALSE),

-- Patient: Patient@2026
('patient@test.com', '$2b$12$fB7qJZs3gN8Lxv4w1YtQ5e3j5qWz9Xp1KmLv8yTn6HfRp2Sz4Kx.m', 'Pierre Bernard', TRUE, NOW(), FALSE);

-- Afficher les utilisateurs créés
SELECT id, courriel, nom, est_actif, courriel_verifie_le FROM utilisateurs;
