# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased]

### Changed

- Stopped production of RAM_outputs.txt file.
- mttfreq (to test if the calculated mttf is less than the value given) is now
  an optional input to the Variables class.
- The Syshier.binomial method was moved to an independent function in the core
  module.
- The Syshier.subsysmttf method was moved to an independent function in the core
  module.
  
### Fixed

- Fixed bug where foundations that were "not required" would break the
  assessment.
- Fixed logical level for setting dummy userhierdict when the user networks are
  not supplied.
- Fixed issue with electrical or moorings networks being supplied independently.
- Fixed bug where direct-embedment anchors were not given a failure rate.
- Fixed issue where inputs could be modified outside of the scope of the module.
- Fixed bug when checking for subhubs in networks.

## [1.0.0] - 2017-01-05

### Added

- Initial import of dtocean-economics from SETIS.
