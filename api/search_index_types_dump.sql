-- MySQL dump 10.13  Distrib 8.0.41, for Linux (x86_64)
--
-- Host: mysql-kdk-knowledge-dev-eastus-001.mysql.database.azure.com    Database: kdk_chatbot
-- ------------------------------------------------------
-- Server version	8.0.40-azure

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `search_index_types`
--

DROP TABLE IF EXISTS `search_index_types`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `search_index_types` (
  `id` varchar(36) NOT NULL,
  `folder_name` varchar(255) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `folder_name` (`folder_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `search_index_types`
--

LOCK TABLES `search_index_types` WRITE;
/*!40000 ALTER TABLE `search_index_types` DISABLE KEYS */;
INSERT INTO `search_index_types` VALUES ('9e56b6c1-33b5-4f65-a95d-f852630b9931','02_手引書・手順書(特定工事)','2025-03-09 22:50:48'),('b2c1dfb5-b8e0-47b9-857a-fa00ebaa4a88','03_社会インフラ統轄本部現場管理指針','2025-03-09 22:50:28'),('b3deec79-fdf2-4132-b918-60fb1f632fdb','04_事故防止カード','2025-03-09 22:50:27'),('e982c376-792c-4013-a788-bb049e34e9ad','01_手引書・手順書(工事全般)','2025-03-09 22:50:25');
/*!40000 ALTER TABLE `search_index_types` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-03-10 22:57:04
