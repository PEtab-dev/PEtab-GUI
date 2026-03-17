Changelog
=========

0.3.0 (2026-03-17)
------------------

Optimization
............
- Introduced cache for dataframes, reducing proxy calls by up to 66% (#224)

Bugfixes
........
- Fixed simulation support despite missing nominal value by pulling from SBML (#238)
- Fixed error checking for empty condition table (#237)
- Fixed error in condition file when there is only one column (#236)
- Fixed issue with assigning np.nan values to all columns in a new row (#233)
- Fixed issue where second or third observables could not be highlighted in the same plot (#232)
- Fixed issue where minimization made data tables vanish (#228)

Documentation
.............
- Added YouTube video and mentioned examples (#227)

Installation / Packaging
.........................
- Limited pandas version to before 3.0.0 (#236) (Temporary)

0.2.0 (2026-01-26)
------------------

General
.......
- Added Tool Menu for Check PEtab and Simulate actions (#222)
- Added SBML export functionality (#220)
- Added delete from header feature for table models (#216)
- Added option to hide SBML view for sole Antimony view (#210)
- Added offboarding information window after saving model (#209)
- Fixed multi-file upload to support multiple measurement and other files (#207)

Documentation
.............
- Added next steps guide with code examples (#219)
- Added Boehm example and simple conversion example (#218)
- Added tutorial walkthrough with pictures and extended feature documentation (#217)

0.1.5 (2025-11-25)
------------------

Initial release with core PEtab GUI functionality.
