## 2024-05-22 - [Keyboard Navigation in Pygame]
**Learning:** Pygame's event loop makes hybrid input (Mouse + Keyboard) state management tricky; unified `selected_index` updated by both `MOUSEMOTION` and `KEYDOWN` provides the smoothest experience without fighting.
**Action:** Always unify selection state rather than maintaining separate "hover" and "focus" states for grid menus.
