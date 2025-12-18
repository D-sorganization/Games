# Zombie Hallway Fix Packages

This directory packages three playable hallway builds side-by-side so you can pick the variant that runs best in your environment without juggling multiple pull requests.

## Contents
- **Fix 1**: Based on `zombie-hallway-v1` with local Three.js modules, simple ammo + boss HUD.
- **Fix 2**: Based on `zombie-hallway-v2` with tighter combat pacing, kill counter, and the same local module dependencies.
- **Fix 3**: Based on the weapon-switching variant (pistol + rifle) with a jump-scare death screen and local module dependencies.

Each package is self-contained except for the shared Three.js assets under `../vendor/three`.

## How to run
1. Open the desired `Fix */index.html` file in a browser.
2. Click **Enter Hallway** to lock the pointer and start.
3. If the page is opened from the filesystem, allow pointer lock when prompted.

All builds import Three.js and PointerLockControls from `../vendor/three` so they work offline and avoid CDN black screens.
