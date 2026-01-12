## 2025-02-14 - Game Launcher Keyboard Navigation
**Learning:** In Pygame, coupling hover states strictly to `collidepoint(mouse_pos)` makes keyboard navigation impossible. Decoupling selection state into a `selected_index` variable (defaulting to -1 for mouse mode) allows seamless hybrid input.
**Action:** When implementing menus in Pygame, always use a `selected_index` state variable and update it via both mouse motion (to -1 or new index) and keyboard events, rather than relying solely on frame-by-frame mouse polling.
