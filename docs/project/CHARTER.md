# Project Charter

> Drafted 2026-09-25 by the fleet charter sweep (Gemini) from README, git history, and open issues/PRs.
> The project-steward role keeps this current; owners should correct feature statuses.

## End Goal

Games is Jules' unified gaming collection providing complete, playable retro, arcade, puzzle, and 3D games implemented in Python/Pygame and web technologies (Three.js), accessible via a central launcher GUI. Done means all featured titles (Force Field, Duum, Tetris, Wizard of Wor, Peanut Butter Panic, Zombie Survival, and QuatGolf) are fully playable with complete input handling, robust shared rendering engines, comprehensive automated test coverage (>=80%), and strict CI/CD quality gate enforcement on every commit.

## Non-Goals

- General-purpose game engine or framework development (single-purpose gaming platform)
- Commercial game publishing, monetization, or distribution platform features
- Dedicated game asset creation pipeline or standalone art tooling
- Support for complex multiplayer server infrastructure beyond basic survival mechanics

## Features

| ID | Feature | Status | Tracking | Notes |
| --- | --- | --- | --- | --- |
| F1 | Unified Game Launcher | shipped | #851 | Central GUI/CLI launcher orchestrating all games |
| F2 | Force Field 3D FPS | shipped | #821 | Raycasting shooter with modular mixins and bot AI |
| F3 | Duum FPS Reimagining | shipped | #707 | Doom-inspired FPS with procedural levels and weapons |
| F4 | Tetris Enhanced | shipped | - | Classic puzzle game with hold mechanics and combos |
| F5 | Wizard of Wor Remake | shipped | #683 | 2-player arcade shooter with spatial collision grid |
| F6 | Peanut Butter Panic | shipped | #713 | Arcade platformer with collision and enemy mechanics |
| F7 | Zombie Survival Web Game | shipped | #735 | Three.js web-based 3D survival game with Python backend |
| F8 | QuatGolf 3D Mechanics | parked | #770 | Quaternion golf prototype with C++ physics bindings |
| F9 | Shared FPS Architecture | shipped | #736 | Common base class and combat subsystems for FPS titles |
| F10 | C++ Native Bindings | shipped | #682 | ctypes bindings for native physics with C++ CI pipeline |
| F11 | Quality Gate & Test Suite | shipped | #865 | Test suite with >=80% coverage and headless Xvfb |
| F12 | C4 Architecture Verification | shipped | #860 | Architecture map contract enforced by CI script |

## Links

- Status (generated): [`STATUS.md`](STATUS.md)
- Steward playbook: Repository_Management `docs/fleet-project-steward.md`
