# CHANGELOG

<!-- version list -->

## v1.6.1 (2025-11-21)

### Refactor

- **ui**: redesign shelves config page with tabbed interface
- **ui**: set shelf name dialog

## v1.6.0 (2025-11-19)

### Feat

- **options**: Option to remove shelves that no longer exist from the list

### Refactor

- **options**: update UI file reference and rename shelves_config.ui to shelves.ui

## v1.5.0 (2025-11-18)

### Feat

- **options**: Option to remove shelves that no longer exist from the list

### Fix

- **shelves**: Various import errors fixed.
- Correct formatting and improve docstring clarity across multiple files

### Refactor

- **shelves**: Improve thread safety in get_album_shelf and maintainability in vote_for_shelf

## v1.4.1 (2025-11-06)

### Bug Fixes

- Cleaning up the release process
  ([`ffd9369`](https://github.com/nrth3rnlb/picard-plugin-shelves/commit/ffd93695a23d95d04622897ea96d54ff913d9d6d))


## v1.4.0 (2025-11-06)

### Bug Fixes

- Enhance PR creation workflow to handle release events and improve changelog generation
  ([`53b4597`](https://github.com/nrth3rnlb/picard-plugin-shelves/commit/53b4597080a985f85b52f466af446a0a86877e59))

- Improve changelog formatting and update PR creation logic in workflow
  ([`5c1211b`](https://github.com/nrth3rnlb/picard-plugin-shelves/commit/5c1211bf43c1eb7a06807f3e115c58e4f2b1df74))

- Improve error logging in fallback shelf detection and remove unused class
  ([`1acc974`](https://github.com/nrth3rnlb/picard-plugin-shelves/commit/1acc9744ab5b27fa207f945bcf6626256e05221b))

- Remove issuetracker entry from .gitignore and clean up pyproject.toml
  ([`0650ad0`](https://github.com/nrth3rnlb/picard-plugin-shelves/commit/0650ad020d9783c81f2aa2c3e0913aaef182aa80))

- Remove unnecessary gh auth login step in PR creation workflow
  ([`6d2e3e2`](https://github.com/nrth3rnlb/picard-plugin-shelves/commit/6d2e3e2e617268032c38a87cb7fe24ea2da73ca7))

- Update branch naming logic in PR creation workflow to handle release events
  ([`b833d6a`](https://github.com/nrth3rnlb/picard-plugin-shelves/commit/b833d6a14c7f2e7bf75382abef2581d7fd9a1c29))

### Features

- Add file post addition and removal processors for album shelf management
  ([`3eef069`](https://github.com/nrth3rnlb/picard-plugin-shelves/commit/3eef069c5725c9b06da9c85005b4953e867fa646))


## v1.3.1 (2025-11-01)

### Bug Fixes

- Add validation for PICARD_PLUGINS_PAT secret and update repository URL in workflow
  ([`c51a084`](https://github.com/nrth3rnlb/picard-plugin-shelves/commit/c51a08403ba23dd161f0e77e9070af537719fb23))

- Enhance workflow inputs for PR creation with release tag and notes
  ([`c7aebb1`](https://github.com/nrth3rnlb/picard-plugin-shelves/commit/c7aebb1c6ed29c2ac30456f134cad8b64342befd))

- Improve echo command and update git push command in workflow
  ([`7ee162e`](https://github.com/nrth3rnlb/picard-plugin-shelves/commit/7ee162e177509c6f586ce036f71d0dac34748e34))

- Update Git configuration and improve push command in workflow
  ([`cdec944`](https://github.com/nrth3rnlb/picard-plugin-shelves/commit/cdec944051b5c023f36af4c73ca37ffd03cc9f14))

- Update Git configuration to use global settings in workflow
  ([`e669b0d`](https://github.com/nrth3rnlb/picard-plugin-shelves/commit/e669b0d1ee8aa37cfc63801294d3ba10e495b67f))

- Update GitHub Actions workflow to improve repository synchronization and PR creation
  ([`af2a4cb`](https://github.com/nrth3rnlb/picard-plugin-shelves/commit/af2a4cbbb110f69205ff93e171f182b93a366771))

- Update PR creation workflow to use GH_TOKEN directly and improve README synchronization details
  ([`ce08aa3`](https://github.com/nrth3rnlb/picard-plugin-shelves/commit/ce08aa37159f7788efe79b12b38b4323be05c7a0))

- Update repository URL and echo command for PR creation in workflow
  ([`1b8bbc9`](https://github.com/nrth3rnlb/picard-plugin-shelves/commit/1b8bbc90a9de232d7cd9b2b009ff2e9eb60012b9))


## v1.3.0 (2025-11-01)

### Documentation

- Update README to include link to MusicBrainz Picard and improve clarity
  ([`b0489a7`](https://github.com/nrth3rnlb/picard-plugin-shelves/commit/b0489a7561a02f0e129c4ba392621376c3d0d83c))

### Features

- Add DetermineShelfAction to determine shelf from storage location
  ([`2e14dd5`](https://github.com/nrth3rnlb/picard-plugin-shelves/commit/2e14dd56a5a9cc6af42ccc0af6ef136da10b6a9e))

  
## v1.2.2 (2025-10-31)

### Bug Fixes

- No shelf if musicbrainz_albumid is not set
  ([`f6d6193`](https://github.com/nrth3rnlb/picard-plugin-shelves/commit/f6d619379acafa52e0f5928d7ab6201209ef5251))

### Documentation

- Enhance plugin description and add license file
  ([`9211574`](https://github.com/nrth3rnlb/picard-plugin-shelves/commit/9211574b5bff2a745605eff7f48201ba3525cb79))


## v1.2.1 (2025-10-30)

### Bug Fixes

- __version__ again
  ([`296a08e`](https://github.com/nrth3rnlb/picard-plugin-shelves/commit/296a08e227af5d03d755e8db3e439992aa3b8f5a))


## v1.2.0 (2025-10-30)


## v1.1.1 (2025-10-30)


## v1.0.0 (2025-10-30)

- Initial Release
