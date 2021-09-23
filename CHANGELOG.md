# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [3.0.0] - TDB

### Added

-   Added visualisation of the network using the `Network.display` method
-   Added the ability to retrieve portions of the network through the 
    `__getitem__` method of the `Network` class.
-   Added export of portions of the network to graphviz dot format.
-   Added methods to return metrics for entire major systems (e.g. the devices)
    or for subsystems of the major systems (such as for station keeping).
-   Added ability to apply k_factors to components with given markers.

### Changed

-   Refactored entire module to improve readability.
-   Changed API to use `SubNetwork` and `Network` classes to collect data and 
    control execution.
-   Ideal components (with type "ideal") are not treated correctly (i.e. zero
    failure rate and infinite MTTF).
-   Components with type "n/a" are now removed from the network.

### Removed

-   Removed pandas dependency.

### Fixed

-   Fixed calculation of "star" network topologies (i.e. when multiple sub-hubs
    connect the devices).
-   Fixed bug when only moorings data was provided (i.e. substations are
    present. See https://github.com/DTOcean/dtocean/issues/36

## [2.0.0] - 2019-03-08

### Changed

-   Stopped production of RAM_outputs.txt file.
-   mttfreq (to test if the calculated mttf is less than the value given) is now
    an optional input to the Variables class.
-   The Syshier.binomial method was moved to an independent function in the core
    module.
-   The Syshier.subsysmttf method was moved to an independent function in the 
    core module.

### Fixed

-   Fixed bug where foundations that were "not required" would break the
    assessment.
-   Fixed logical level for setting dummy userhierdict when the user networks 
    are not supplied.
-   Fixed issue with electrical or moorings networks being supplied
    independently.
-   Fixed bug where direct-embedment anchors were not given a failure rate.
-   Fixed issue where inputs could be modified outside of the scope of the
    module.
-   Fixed bug when checking for subhubs in networks.
-   Fixed bug with float being passed to numpy.linspace for number of samples.

## [1.0.0] - 2017-01-05

### Added

-   Initial import of dtocean-economics from SETIS.
