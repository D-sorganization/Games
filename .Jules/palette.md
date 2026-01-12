# Palette's Journal

## 2024-05-22 - [Launcher Keyboard Navigation]
**Learning:** Pygame `MOUSEMOTION` events can be "spammy" or trigger without effective movement on some systems/initialization. Checking `event.rel != (0, 0)` is crucial for hybrid input systems (Mouse + Keyboard) to prevent the mouse from instantly overriding keyboard selection just because the cursor exists on screen.
**Action:** When implementing hybrid input in Pygame, always filter `MOUSEMOTION` with `event.rel` or use a "dirty" flag approach to determine active input device.
