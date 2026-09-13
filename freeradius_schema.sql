-- ==================================================================
-- FreeRADIUS MySQL Schema for زنار (Zinar) RADIUS Management System
-- This schema should be imported into the 'radius' database
-- ==================================================================

CREATE DATABASE IF NOT EXISTS radius CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE radius;

-- جدول radcheck: سمات المصادقة
CREATE TABLE IF NOT EXISTS radcheck (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(64) NOT NULL DEFAULT '',
    attribute VARCHAR(64) NOT NULL DEFAULT '',
    op VARCHAR(2) NOT NULL DEFAULT '==',
    value VARCHAR(253) NOT NULL DEFAULT '',
    INDEX username_idx (username(32))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- جدول radreply: سمات الرد
CREATE TABLE IF NOT EXISTS radreply (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(64) NOT NULL DEFAULT '',
    attribute VARCHAR(64) NOT NULL DEFAULT '',
    op VARCHAR(2) NOT NULL DEFAULT '=',
    value VARCHAR(253) NOT NULL DEFAULT '',
    INDEX username_idx (username(32))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- جدول userinfo: معلومات المستخدم الإضافية
CREATE TABLE IF NOT EXISTS userinfo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(64) NOT NULL DEFAULT '',
    firstname VARCHAR(64) DEFAULT '',
    lastname VARCHAR(64) DEFAULT '',
    email VARCHAR(128) DEFAULT '',
    phone VARCHAR(32) DEFAULT '',
    UNIQUE KEY username_idx (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- جدول radusergroup: مجموعة المستخدم
CREATE TABLE IF NOT EXISTS radusergroup (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(64) NOT NULL DEFAULT '',
    groupname VARCHAR(64) NOT NULL DEFAULT '',
    priority INT NOT NULL DEFAULT 0,
    INDEX username_idx (username(32))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- جدول radgroupcheck: سمات مجموعة المصادقة
CREATE TABLE IF NOT EXISTS radgroupcheck (
    id INT AUTO_INCREMENT PRIMARY KEY,
    groupname VARCHAR(64) NOT NULL DEFAULT '',
    attribute VARCHAR(64) NOT NULL DEFAULT '',
    op VARCHAR(2) NOT NULL DEFAULT '==',
    value VARCHAR(253) NOT NULL DEFAULT '',
    INDEX groupname_idx (groupname(32))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- جدول radgroupreply: سمات مجموعة الرد
CREATE TABLE IF NOT EXISTS radgroupreply (
    id INT AUTO_INCREMENT PRIMARY KEY,
    groupname VARCHAR(64) NOT NULL DEFAULT '',
    attribute VARCHAR(64) NOT NULL DEFAULT '',
    op VARCHAR(2) NOT NULL DEFAULT '=',
    value VARCHAR(253) NOT NULL DEFAULT '',
    INDEX groupname_idx (groupname(32))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- جدول radpostauth: سجل المصادقة
CREATE TABLE IF NOT EXISTS radpostauth (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(64) NOT NULL DEFAULT '',
    pass VARCHAR(64) NOT NULL DEFAULT '',
    reply VARCHAR(32) NOT NULL DEFAULT '',
    authdate TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX username_idx (username(32))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- جدول radacct: سجل المحاسبة (مهم جداً)
CREATE TABLE IF NOT EXISTS radacct (
    radacctid BIGINT AUTO_INCREMENT PRIMARY KEY,
    acctsessionid VARCHAR(64) NOT NULL DEFAULT '',
    acctuniqueid VARCHAR(32) NOT NULL DEFAULT '',
    username VARCHAR(64) NOT NULL DEFAULT '',
    realm VARCHAR(64) DEFAULT '',
    nasipaddress VARCHAR(15) NOT NULL DEFAULT '',
    nasportid VARCHAR(32) DEFAULT '',
    nasporttype VARCHAR(32) DEFAULT '',
    acctstarttime DATETIME NULL,
    acctupdatetime DATETIME NULL,
    acctstoptime DATETIME NULL,
    acctinterval INT(12) DEFAULT NULL,
    acctsessiontime INT(12) DEFAULT NULL,
    acctauthentic VARCHAR(32) DEFAULT '',
    connectinfo_start VARCHAR(128) DEFAULT '',
    connectinfo_stop VARCHAR(128) DEFAULT '',
    acctinputoctets BIGINT(12) DEFAULT NULL,
    acctoutputoctets BIGINT(12) DEFAULT NULL,
    calledstationid VARCHAR(50) DEFAULT '',
    callingstationid VARCHAR(50) DEFAULT '',
    acctterminatecause VARCHAR(32) DEFAULT '',
    servicetype VARCHAR(32) DEFAULT '',
    framedprotocol VARCHAR(32) DEFAULT '',
    framedipaddress VARCHAR(15) NOT NULL DEFAULT '',
    acctstartdelay INT(12) DEFAULT NULL,
    acctstopdelay INT(12) DEFAULT NULL,
    xascendsessionsvrkey VARCHAR(32) DEFAULT '',
    INDEX username_idx (username(32)),
    INDEX acctsessionid_idx (acctsessionid(8)),
    INDEX acctuniqueid_idx (acctuniqueid),
    INDEX nasipaddress_idx (nasipaddress),
    INDEX acctstarttime_idx (acctstarttime),
    INDEX acctstoptime_idx (acctstoptime),
    INDEX acctupdatetime_idx (acctupdatetime)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- جدول nas: أجهزة NAS
CREATE TABLE IF NOT EXISTS nas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nasname VARCHAR(128) NOT NULL DEFAULT '',
    shortname VARCHAR(32) DEFAULT '',
    type VARCHAR(32) DEFAULT 'other',
    ports INT(5) DEFAULT NULL,
    secret VARCHAR(128) NOT NULL DEFAULT '',
    server VARCHAR(64) DEFAULT '',
    community VARCHAR(128) DEFAULT '',
    description VARCHAR(200) DEFAULT '',
    UNIQUE KEY nasname_idx (nasname(128))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;