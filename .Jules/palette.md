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

## 2024-05-24 - Keyboard Navigation in Game Launcher
**Learning:** Pygame's `MOUSEMOTION` event is sensitive and can trigger even without user intent on some systems.
**Action:** When implementing hybrid input (Mouse + Keyboard), decoupling visual selection from input state is crucial. However, treating any `MOUSEMOTION` as an intent to switch to mouse mode is effective but requires ensuring that keyboard navigation aggressively clears mouse selection to avoid conflict. A robust pattern is:
1. `selected_index` tracks keyboard selection (-1 if mouse active).
2. Mouse motion sets `selected_index = -1`.
3. Key press sets `selected_index` (snapping to mouse position if transitioning).
4. Render loop prioritizes `selected_index` if valid, otherwise falls back to mouse collision.
**Visuals:** Always ensure hitboxes (logic) and visuals are distinct if design requires padding/margins. Use `rect.inflate()` for drawing smaller cards inside larger click targets.

## 2025-02-14 - Game Launcher Keyboard Navigation
**Learning:** In Pygame, coupling hover states strictly to `collidepoint(mouse_pos)` makes keyboard navigation impossible. Decoupling selection state into a `selected_index` variable (defaulting to -1 for mouse mode) allows seamless hybrid input.
**Action:** When implementing menus in Pygame, always use a `selected_index` state variable and update it via both mouse motion (to -1 or new index) and keyboard events, rather than relying solely on frame-by-frame mouse polling.

## 2025-05-20 - [Duplicate Text Rendering]
**Learning:** Drawing text twice at the same position with different fonts (or even same fonts) creates a blurry, unreadable artifact that impacts accessibility, often resulting from copy-paste errors.
**Action:** Always audit rendering loops for duplicate draw calls, especially for static UI elements.
