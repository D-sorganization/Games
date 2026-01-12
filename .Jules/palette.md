# Palette's Journal

## 2024-05-22 - [Launcher Keyboard Navigation]
**Learning:** Pygame `MOUSEMOTION` events can be "spammy" or trigger without effective movement on some systems/initialization. Checking `event.rel != (0, 0)` is crucial for hybrid input systems (Mouse + Keyboard) to prevent the mouse from instantly overriding keyboard selection just because the cursor exists on screen.
**Action:** When implementing hybrid input in Pygame, always filter `MOUSEMOTION` with `event.rel` or use a "dirty" flag approach to determine active input device.

## 2024-05-22 - [Keyboard Navigation in Pygame]
**Learning:** Pygame's event loop makes hybrid input (Mouse + Keyboard) state management tricky; unified `selected_index` updated by both `MOUSEMOTION` and `KEYDOWN` provides the smoothest experience without fighting.
**Action:** Always unify selection state rather than maintaining separate "hover" and "focus" states for grid menus.

## 2024-05-22 - Keyboard Navigation in Launchers
**Learning:** Purely mouse-based menus in game launchers create a significant accessibility barrier. Adding hybrid keyboard/mouse state (where mouse motion overrides keyboard selection and vice-versa) is a simple pattern that feels intuitive.
**Action:** When designing grid-based menus, always implement arrow key navigation with "wrap-around" or "clamp" logic from the start.
