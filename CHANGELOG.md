# Changelog – Tomiras Beszel API

## 0.4.1 – 2025-02-XX
### Added
- Full Intel GPU monitoring:
  - Usage
  - Tile power
  - Package power
  - Memory stats
  - Temperature
- GPU engine utilization for:
  - Render/3D
  - Blitter
  - Video
  - VideoEnhance
- Battery sensor support
- Human-readable uptime formatting
- Updated manifest with proper `config_flow` and upstream compatibility

### Changed
- Integration domain reverted to `beszel_api` for compatibility with branding
- Code refactoring for stable Home Assistant loading

### Notes
- This version is based on upstream `beszel-ha` but contains extensive enhancements.
