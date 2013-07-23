use map;
ALTER TABLE  `campus_mapobj` ADD  `modified` DATETIME NOT NULL
UPDATE `campus_mapobj` SET `modified` = now();