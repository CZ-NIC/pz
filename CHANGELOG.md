# CHANGELOG

## 1.1.0 (unreleased)
- CHANGED: tuple output delimited by a tab instead of ', '

## 1.0.0 (2021-03-19)
- CHANGED: `--end` clause renamed from `--finally`
- auto-importing works in the `--setup` clause
- will not internally change commands starting with a reserved keyword (ex: `if s ==` will not be changed to `s = if s ===`)
- generator
- skip processing if not needed to speed up
- command chaining tuned up
- `--format`, `--stderr`, `--overflow-safe` flags
- `counter` variable
- raw bytes support

## 0.9 (2020-12-02)
- other modules added for auto-import
- global instances of collections
- regular matches output
- regular flags
- `--finally` flag in opposition to `--setup`
- allowing callables to be output
- raw output
- `--lines` flag, variables `lines` and `numbers`
- added Python3.6 support


## 0.8 (2020-11-25)
- fully working
