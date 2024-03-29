# Development notes

## Initialise dev

- Clone repo
- Run `source ./config/dev-init.sh` from within the root repo directory. This updates pip, installs all required packages (including those required for dev), and installs pre-commit.
  - Note: Some pre-commit hooks are shell scripts, so use linux when developing this package.

## TODO

### Write unit tests for every method and property, including for the indexers and accessors

- [x] `_is_col_test`
- [x] `_decide_if_call`
- [x] `Col.__getitem__` should act like standard df indexer
- [x] `BaseCol._is_col` should should be True
- [x] `Col.__call__`
- [x] `CallCol.__call__`
- [ ] Dunder properties
- [ ] Accessor attrs
  - [ ] `cat`
  - [ ] `dt`
  - [ ] `str`
  - [ ] `sparse`
  - [ ] `plot`
- [ ] Regular properties
- [ ] Indexer properties
- [ ] Dunder methods
- [ ] Regular methods

### Packaging

- [ ] Organise package contents
  - [ ] Add some examples from the analysis folder to the README
- [ ] Reintroduce and pass pre-commit checks
- [ ] Use PipTools (since this is a library) (UNSURE)
- [ ] Add changelog
- [ ] Publish to PyPi

### Future work

- See whether the tests can be run on many versions of pandas
- Since one could feasibly use `col(["a", "b"])` (which could return a data frame), it may be appropriate to include the properties and methods of dataframes in some future release
