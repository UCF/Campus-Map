use map;
ALTER TABLE  `campus_mapobj` ADD  `blah` DATETIME NOT NULL
UPDATE `campus_mapobj` SET `modified` = now();