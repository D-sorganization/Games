# Changelog

All notable changes to the Games repository will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Comprehensive assessment framework (A-O) with 15 quality categories

### Fixed

- Missing 'dy' parameter in ParticleSystem.add_plasma_particle
- Removed ruff output debris files from root

### Changed

- Cleaned root directory structure

## [1.0.0] - 2025-12-01

### Games Included

#### Force Field

- Space shooter with physics-based gameplay
- Particle system with plasma effects
- Score tracking and difficulty progression

#### Duum

- Doom-style raycasting engine
- Vectorized DDA algorithm using NumPy
- Textured walls and sprite rendering

#### Zombie Games

- Top-down zombie survival
- Wave-based gameplay mechanics

#### Classic Games

- Snake with modern graphics
- Tetris implementation
- Pong with AI opponent

### Infrastructure

- Unified Pygame architecture
- Shared renderer components
- Type-safe codebase (mypy strict)
