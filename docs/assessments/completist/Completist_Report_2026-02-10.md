# Completist Report: 2026-02-10

## Executive Summary
- **Critical Gaps**: 1
- **Feature Gaps (TODO)**: 16
- **Technical Debt**: 1
- **Documentation Gaps**: 0

## Visualization
### Status Overview
```mermaid
pie title Completion Status
    "Impl Gaps (Critical)" : 1
    "Feature Requests (TO" + "DO)" : 16
    "Technical Debt (FIX" + "ME)" : 1
    "Doc Gaps" : 0
```

### Top Impacted Modules
```mermaid
pie title Issues by Module
    "src" : 15
    "scripts" : 3
```

## Critical Incomplete (Top 50)
| File | Line | Type | Impact | Coverage | Complexity |
|---|---|---|---|---|---|
| `./scripts/shared/quality_checks_common.py` | 13 | NotImplementedError | 1 | 2 | 4 |

## Feature Gap Matrix
| Module | Feature Gap | Type |
|---|---|---|
| `./scripts/shared/quality_checks_common.py` | (re.compile(r"\bTODO\b"), "TODO placeholder found"), | TODO |
| `./src/games/vendor/three/three.module.js` | // TODO lengthSquared? | TODO |
| `./src/games/vendor/three/three.module.js` | //TODO: make this more efficient | TODO |
| `./src/games/vendor/three/three.module.js` | // TODO: Copied from Object3D.toJSON | TODO |
| `./src/games/vendor/three/three.module.js` | // TODO (abelnation): RectAreaLight BRDF data needs to be moved from example to main src | TODO |
| `./src/games/vendor/three/three.module.js` | // TODO Attribute may not be available on context restore | TODO |
| `./src/games/vendor/three/three.module.js` | // TODO Send this event to Three.js DevTools | TODO |
| `./src/games/vendor/three/three.module.js` | // TODO (abelnation): set RectAreaLight shadow uniforms | TODO |
| `./src/games/vendor/three/three.module.js` | // TODO : do it if required only | TODO |
| `./src/games/vendor/three/three.module.js` | // TODO: Uniformly handle mipmap definitions | TODO |
| `./src/games/vendor/three/three.module.js` | newRenderTarget.isXRRenderTarget = true; // TODO Remove this when possible, see #23278 | TODO |
| `./src/games/vendor/three/three.module.js` | // TODO: Better way to apply this offset? | TODO |
| `./src/games/vendor/three/three.module.js` | // TODO (abelnation): add area lights shadow info to uniforms | TODO |
| `./src/games/vendor/three/three.module.js` | this.currentPoint.set( x, y ); // TODO consider referencing vectors instead of copying? | TODO |
| `./src/games/vendor/three/three.module.js` | this.intensity = json.intensity; // TODO: Move this bit to Light.fromJSON(); | TODO |
| `./src/games/vendor/three/three.module.js` | // TODO: delete this comment? | TODO |

## Technical Debt Register
| File | Line | Issue | Type |
|---|---|---|---|
| `./scripts/shared/quality_checks_common.py` | 11 | (re.compile(r"\bFIXME\b"), "FIXME placeholder found"), | FIXME |

## Recommended Implementation Order
Prioritized by Impact (High) and Complexity (Low).
| Priority | File | Issue | Metrics (I/C/C) |
|---|---|---|---|
| 1 | `./scripts/shared/quality_checks_common.py` | (re.compile(r"\bTODO\b"), "TODO placeholder found"), | 1/2/3 |
| 2 | `./src/games/vendor/three/three.module.js` | // TODO lengthSquared? | 1/2/3 |
| 3 | `./src/games/vendor/three/three.module.js` | //TODO: make this more efficient | 1/2/3 |
| 4 | `./src/games/vendor/three/three.module.js` | // TODO: Copied from Object3D.toJSON | 1/2/3 |
| 5 | `./src/games/vendor/three/three.module.js` | // TODO (abelnation): RectAreaLight BRDF data needs to be moved from example to  | 1/2/3 |
| 6 | `./src/games/vendor/three/three.module.js` | // TODO Attribute may not be available on context restore | 1/2/3 |
| 7 | `./src/games/vendor/three/three.module.js` | // TODO Send this event to Three.js DevTools | 1/2/3 |
| 8 | `./src/games/vendor/three/three.module.js` | // TODO (abelnation): set RectAreaLight shadow uniforms | 1/2/3 |
| 9 | `./src/games/vendor/three/three.module.js` | // TODO : do it if required only | 1/2/3 |
| 10 | `./src/games/vendor/three/three.module.js` | // TODO: Uniformly handle mipmap definitions | 1/2/3 |
| 11 | `./src/games/vendor/three/three.module.js` | newRenderTarget.isXRRenderTarget = true; // TODO Remove this when possible, see  | 1/2/3 |
| 12 | `./src/games/vendor/three/three.module.js` | // TODO: Better way to apply this offset? | 1/2/3 |
| 13 | `./src/games/vendor/three/three.module.js` | // TODO (abelnation): add area lights shadow info to uniforms | 1/2/3 |
| 14 | `./src/games/vendor/three/three.module.js` | this.currentPoint.set( x, y ); // TODO consider referencing vectors instead of c | 1/2/3 |
| 15 | `./src/games/vendor/three/three.module.js` | this.intensity = json.intensity; // TODO: Move this bit to Light.fromJSON(); | 1/2/3 |
| 16 | `./src/games/vendor/three/three.module.js` | // TODO: delete this comment? | 1/2/3 |
| 17 | `./scripts/shared/quality_checks_common.py` | (re.compile(r"NotImplementedError"), "NotImplementedError placeholder"), | 1/2/4 |

## Issues Created