## 2024-05-24 - Keyboard Navigation in Game Launcher
**Learning:** Pygame's `MOUSEMOTION` event is sensitive and can trigger even without user intent on some systems.
**Action:** When implementing hybrid input (Mouse + Keyboard), decoupling visual selection from input state is crucial. However, treating any `MOUSEMOTION` as an intent to switch to mouse mode is effective but requires ensuring that keyboard navigation aggressively clears mouse selection to avoid conflict. A robust pattern is:
1. `selected_index` tracks keyboard selection (-1 if mouse active).
2. Mouse motion sets `selected_index = -1`.
3. Key press sets `selected_index` (snapping to mouse position if transitioning).
4. Render loop prioritizes `selected_index` if valid, otherwise falls back to mouse collision.
**Visuals:** Always ensure hitboxes (logic) and visuals are distinct if design requires padding/margins. Use `rect.inflate()` for drawing smaller cards inside larger click targets.
