[![appveyor](https://ci.appveyor.com/api/projects/status/github/DTOcean/dtocean-reliability?branch=master&svg=true)](https://ci.appveyor.com/project/DTOcean/dtocean-reliability)
[![codecov](https://codecov.io/gh/DTOcean/dtocean-reliability/branch/master/graph/badge.svg)](https://codecov.io/gh/DTOcean/dtocean-reliability)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/3bc087b5705e45d1b17e86668f1a67ff)](https://www.codacy.com/project/H0R5E/dtocean-reliability/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=DTOcean/dtocean-reliability&amp;utm_campaign=Badge_Grade_Dashboard&amp;branchId=11738730)
[![release](https://img.shields.io/github/release/DTOcean/dtocean-reliability.svg)](https://github.com/DTOcean/dtocean-reliability/releases/latest)

# DTOcean Reliability Module

The DTOcean Reliability Module provides functions to assess and compare the 
reliability of arrays designed by DTOcean. It also acts as a support 
library for the [dtocean-maintenance]( 
https://github.com/DTOcean/dtocean-maintenance) module. It aggregates the
component "networks" produced by the [dtocean-electrical]( 
https://github.com/DTOcean/dtocean-electrical) and [dtocean-reliability]( 
https://github.com/DTOcean/dtocean-reliability) modules and generates reliability
metrics at sub-system level. When combined with the device sub-system 
reliability values, it can also generate reliability metrics for the array as a 
whole.

See [dtocean-app](https://github.com/DTOcean/dtocean-app) or [dtocean-core](
https://github.com/DTOcean/dtocean-app) to use this package within the DTOcean
ecosystem.

* For python 2.7 only.

## Installation

Installation and development of dtocean-reliability uses the [Anaconda 
Distribution](https://www.anaconda.com/distribution/) (Python 2.7)

### Conda Package

To install:

```
$ conda install -c dataonlygreater dtocean-reliability
```

### Source Code

Conda can be used to install dependencies into a dedicated environment from
the source code root directory:

```
$ conda create -n _dtocean_rely python=2.7 pip
```

Activate the environment, then copy the `.condrc` file to store installation  
channels:

```
$ conda activate _dtocean_rely
$ copy .condarc %CONDA_PREFIX%
```

Install [polite](https://github.com/DTOcean/polite) into the environment. For 
example, if installing it from source:

```
$ cd \\path\\to\\polite
$ conda install --file requirements-conda-dev.txt
$ pip install -e .
```

Finally, install dtocean-reliability and its dependencies using conda and pip:

```
$ cd \\path\\to\\dtocean-reliability
$ conda install --file requirements-conda-dev.txt
$ pip install -e .
```

To deactivate the conda environment:

```
$ conda deactivate
```

### Tests

A test suite is provided with the source code that uses [pytest](
https://docs.pytest.org).

If not already active, activate the conda environment set up in the [Source 
Code](#source-code) section:

```
$ conda activate _dtocean_rely
```

Install packages required for testing to the environment (one time only):

```
$ conda install -y pytest
```

Run the tests:

``` 
$ py.test tests
```

### Uninstall

To uninstall the conda package:

```
$ conda remove dtocean-reliability
```

To uninstall the source code and its conda environment:

```
$ conda remove --name _dtocean_rely --all
```

## Usage

Example scripts are available in the "examples" folder of the source code.

```
$ cd examples
$ python example.py
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first to
discuss what you would like to change.

See [this blog post](
https://www.dataonlygreater.com/latest/professional/2017/03/09/dtocean-development-change-management/)
for information regarding development of the DTOcean ecosystem.

Please make sure to update tests as appropriate.

## Credits

This package was initially created as part of the [EU DTOcean project](
https://www.dtoceanplus.eu/About-DTOceanPlus/History) by:

 * Sam Weller at [the University of Exeter](https://www.exeter.ac.uk/)
 * Jon Hardwick at [the University of Exeter](https://www.exeter.ac.uk/)
 * Mathew Topper at [TECNALIA](https://www.tecnalia.com)

It is now maintained by Mathew Topper at [Data Only Greater](
https://www.dataonlygreater.com/).

## License

[GPL-3.0](https://choosealicense.com/licenses/gpl-3.0/)
