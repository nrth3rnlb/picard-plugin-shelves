# CHANGELOG

<!-- version list -->

## v2.0.0 (2026-05-02)

### BREAKING CHANGE

- `get_processors_singleton` has been deprecated; use `processors.instance` for singleton access.
- `ConfigKey.ALBUM_SHELF` has been deprecated, and processors now use a singleton pattern for initialization.
- `constants` is no longer used for configuration and tagging; migrated to `ConfigKey` and `TagKey`.
- The labeling of the manual setting of a shelf name is stored in a separate tag. Existing tags are taken into account and automatically corrected until further notice.
- Configuration updates require manual adjustments. Reconfiguration of workflows and shelves is needed.
- The configuration has been changed, and the plugin must be reconfigured. An automatic migration is not provided, so manual configuration adjustments are necessary.

### Feat

- **workflow**: add transition strategy for empty shelf names in workflow
- **typings**: add typings for Shelves plugin including processing and transition types
- **tagger**: Separation of shelf names and labeling as 'manual'.
- **processors**: implement strategy pattern for shelf name processing
- **options, ui**: refactor shelf and workflow management for clarity and usability
- **tests**: expand test coverage for shelves and workflows
- Configuration adjustments required
- **shelves**: enhance shelf and workflow management
- **shelves**: enhance shelf management and add functionality

### Fix

- **processors**: skip path check for shelves in stage 1 workflow configuration
- **transitions**: correct return value in `apply_transition` method for StrategyEmptyNameToStage2
- **shelves**: correct the version number
- **workflow**: adjust shelf transition logic and enhance test cases
- **workflow**: correct shelf transition logic and enhance test coverage
- **manager**: ShelfNotFoundException import
- **constants**: rename the tag name from `shelf_name` to `shelf`
- **options**: remove unused dependencies and update shelf logic
- **options**: refactor shelf management logic and improve UI bindings
- **options**: improve shelf management logic and update dependencies
- **options**: change shelf scanning logic
- **options**: update shelf scanning
- **manager**: improve log message formatting for uncertain shelf determination
fix(tests): update shelf parameter name in mock assertion for clarity
- **script_functions**: Sicher stellen, dass immer ein String zurück gegeben wird, wenn "musicbrainz_albumid" gesetzt ist.
- **script_functions**: Ensure that a string is always returned if "musicbrainz_albumid" is set.

### Refactor

- **shelves**: remove unused `ShelfActionDetermine` logic
- **shelves**: add `shelf_locked` parameter to voting methods and streamline lock/unlock logic
- **shelves**: improve debug logging in `transitions.py` to include context information
- **processors**: simplify lock state handling and add toggle lock strategy
- **typings**: add `LOCK` and `UNLOCK` to `Direction` enum
- **contexts**: add `TOGGLE_LOCK` to `ProcessingType` enum
- **shelves**: streamline `ShelfActionToggleLock` logic and update album metadata handling
- **shelves**: standardize `manager` import and update `NAME` attribute in `actions.py`
- **shelves**: enable `ShelfActionToggleLock` and register it in album actions
- **shelves**: update `NAME` attribute to clarify purpose in `actions.py`
- **processors**: remove deprecated `build_processing_context_by_file_and_track` method
- **shelves**: remove `exceptions` module and delete unused custom exception classes
- **shelves**: move `ShelfNotDeterminableException` to `utils` and enhance its implementation
- **shelves**: relocate `ShelfNotFoundException` to `manager.py` from `exceptions`
- **processors**: remove unused `decide_voting` method from shelf processors
- **processors**: remove `strategy` attribute and streamline method calls for shelf processing
- **shelves**: standardize `manager` imports as `manager_module` across all modules
- **shelves**: replace direct `ShelfManager` usage with singleton instance method
- **shelves**: remove singleton pattern and redundant initialization checks in `ShelfManager`
- **processors**: streamline `is_applicable` checks and improve early return logic
- simplify shelf processing and remove redundant checks
- **ui**: remove redundant sort calls in shelf management sections
- **ui**: improve tooltips for clarity and enable sorting for shelf lists
- remove unused `log` import and cleanup commented code in `shelves/__init__.py`
- adjust stage shelf capacity checks and fix exception import in tests
- **tests**: enhance unit tests for processor strategies and shelf actions
- **tests**: add mocks for Album, Track, and File in callback test
- **tests**: rename variables and refactor tests with strategy and manager updates
- Refactor the shelf processing strategy and voting system
- Optimize and simplify
- **tests**: streamline transition tests
- **tests**: streamline transition tests and enhance strategy applicability checks
- **processors**: rename classes and update context handling for shelf processing strategies
- **tests**: remove redundant workflow transition tests from processors workflow
- **workflow**: implement workflow transition strategies
- **readme**: update shelf management features and improve documentation clarity
- **processors**: update should_lock method in StrategyKnownNameFromPathDiffersFromTag
- **options, tests**: consolidate widget updates and improve shelf handling logic
- **manager, options, processors, tests**: simplify method docstrings, rename strategy class, and clean up test cases
- **manager, tests**: reorganize imports, simplify method signatures, and clean up test cases
- **script_functions, tests**: simplify shelf function return logic and clean up test cases
- **processors, init**: replace singleton getter with `instance` method and update related wrappers
- **script_functions**: streamline shelf function and remove logging
- **options, dependencies, processors, tests**: remove unused config setting, update dependencies, and refactor processors
- **options, actions, tests**: replace constants usage with ConfigKey and TagKey, streamline imports
- **constants, actions, manager, processors**: streamline shelf-related constants and improve method signatures
- **manager, actions, processors**: rename shelf-related methods and enhance shelf handling logic
- **processors**: enhance shelf name check in voting logic
- **processors, docs**: improve voting logic comments and add documentation files
- **manager, processors, utils**: streamline shelf voting logic and enhance debug functionality
- **actions, processors**: rename unlock and lock actions to toggle lock and streamline logic
- **actions, manager, processors**: rename shelf action classes and improve locking logic
- **manager, exceptions, processors**: simplify shelf handling and improve exception clarity
- **manager**: streamline shelf assignment logic and update source handling
- **actions**: rename shelf action classes for consistency and clarity
- **manager**: enhance documentation and support dependency injection in ShelfManager
- **tests**: enhance `shelf` function tests for clarity and coverage
- **manager**: replace classmethod delegation with instance methods
- **manager**: restructure ShelfManager into modular components
- **script_functions**: rename func_shelf to shelf for clarity
- **tests**: unify constants import across test modules
- **constants**: unify constants import across modules
- **actions, dialogs**: improve shelf name handling and UI interactions
- **actions, dialogs**: improve shelf name handling and UI interactions
- **tests**: update imports to reflect `shelves.options` namespace change
- **script_functions**: rename `$shelf_name()` to `$shelf()` in docstring
- **options**: enhance shelf management and streamline UI workflows
- **options**: enhance shelf management and improve workflow logic
- **options**: streamline workflow widget logic and remove redundant methods
- **shelf, processors, actions, options, utils, tests**: update shelf name extraction and handling to use Path objects and improve strategy logic
- **init, options, widgets, actions.ui, pyproject**: improve code style, fix argument naming, and remove flake8 config
- **options, processors, utils, tests**: update shelf config key usage and improve shelf management logic
- **manager, processors, actions, tests**: implement ShelfManager singleton pattern and update state handling
- **shelves**: remove _ShelfManager singleton, use ShelfManager class directly and update references
- **shelves**: update imports for relative paths and centralize processor usage
- **shelves**: centralize shelf manager usage and update processors integration
- **shelves**: move shelf state logic to manager and update processors integration
- **options, actions, utils**: move shelf config logic to utils and update options page integration
- **options, test**: migrate config.setting to config.settings and update usage
- **options**: remove unused imports and update shelves title string
- **options, ui**: standardize method and button naming for workflow stages
- **options, ui**: enhance workflow management with new widget
- **options**: add buttons for workflow stage transitions
- **options**: add standard icons for workflow stage buttons
- **tests,-ui**: streamline shelves management and update workflows
- **utils**: remove unused method get_shelf_name_from_tag
- **manager**: remove wildcard imports and streamline dependencies
- **constants**: introduce shelf source constants for clarity
- **processors**: improve type hints and simplify file processing logic
- **ui**: update widget names and improve layout in shelves.ui

## v1.7.0 (2025-11-28)

### Chores

- **gitignore**: Ignore tmp.* directories and files
  ([`39fcd0a`](https://github.com/nrth3rnlb/picard-plugin-shelves/commit/39fcd0a588625d95f0dbd1d328fab3ad4845f523))

### Features

- **processors**: Add workflow transition logic
  ([`b5df392`](https://github.com/nrth3rnlb/picard-plugin-shelves/commit/b5df39200e4a289c6f2740598f3d398b6ea9eed4))

- **workflow**: Add a wildcard-option for workflow stage 1 transition
  ([`bf0d09a`](https://github.com/nrth3rnlb/picard-plugin-shelves/commit/bf0d09ae4f15867a7018fc80c4cf335a61b89bca))

### Refactoring

- **init**: Remove unused PLUGIN_USER_GUIDE_URL constant
  ([`c6b646a`](https://github.com/nrth3rnlb/picard-plugin-shelves/commit/c6b646a588c6f6499a2bf19063f52c5516df17b5))

## v1.6.1 (2025-11-21)

### Refactor

- **ui**: redesign shelves config page with tabbed interface
- **ui**: set shelf name dialog

## v1.6.0 (2025-11-19)

### Feat

- **options**: Option to remove shelves that no longer exist from the list

### Refactor

- **options**: update UI file reference and rename "shelves_config.ui" to "shelves.ui"

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

- Update README to include a link to MusicBrainz Picard and improve clarity
  ([`b0489a7`](https://github.com/nrth3rnlb/picard-plugin-shelves/commit/b0489a7561a02f0e129c4ba392621376c3d0d83c))

### Features

- Add ShelfActionDetermine to determine shelf from storage location
  ([`2e14dd5`](https://github.com/nrth3rnlb/picard-plugin-shelves/commit/2e14dd56a5a9cc6af42ccc0af6ef136da10b6a9e))

## v1.2.2 (2025-10-31)

### Bug Fixes

- No shelf if "musicbrainz_albumid" is not set
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
