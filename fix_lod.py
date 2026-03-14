import re

file_path = r"c:\Users\diete\Repositories\Games\src\games\Zombie_Survival\src\game.py"
with open(file_path, encoding="utf-8") as f:
    content = f.read()

# Replace common self.player.* accesses
replacements = {
    r"self\.player\.x": r"self.player_x",
    r"self\.player\.y": r"self.player_y",
    r"self\.player\.angle": r"self.player_angle",
    r"self\.player\.health": r"self.player_health",
    r"self\.player\.alive": r"self.player_alive",
    r"self\.player\.is_moving": r"self.player_is_moving",
    r"self\.player\.current_weapon": r"self.player_current_weapon",
    r"self\.player\.stamina": r"self.player_stamina",
    r"self\.player\.bombs": r"self.player_bombs",
    r"self\.combat_manager\.kills": r"self.kills",
    r"self\.combat_manager\.kill_combo_count": r"self.kill_combo_count",
    r"self\.combat_manager\.kill_combo_timer": r"self.kill_combo_timer",
    r"self\.combat_manager\.last_death_pos": r"self.last_death_pos",
}

for old, new in replacements.items():
    content = re.sub(old, new, content)

# We need to inject the properties into the game.py file
properties = """
    # --- Law of Demeter (LOD) Flattened Properties ---
    @property
    def player_x(self) -> float:
        return self.player.x if self.player else 0.0
        
    @property
    def player_y(self) -> float:
        return self.player.y if self.player else 0.0

    @property
    def player_angle(self) -> float:
        return self.player.angle if self.player else 0.0

    @property
    def player_health(self) -> int:
        return self.player.health if self.player else 0
        
    @player_health.setter
    def player_health(self, value: int) -> None:
        if self.player:
            self.player.health = value

    @property
    def player_alive(self) -> bool:
        return self.player.alive if self.player else False

    @property
    def player_is_moving(self) -> bool:
        return self.player.is_moving if self.player else False
        
    @player_is_moving.setter
    def player_is_moving(self, value: bool) -> None:
        if self.player:
            self.player.is_moving = value

    @property
    def player_current_weapon(self) -> str:
        return self.player.current_weapon if self.player else "pistol"
        
    @player_current_weapon.setter
    def player_current_weapon(self, value: str) -> None:
        if self.player:
            self.player.current_weapon = value

    @property
    def player_stamina(self) -> float:
        return self.player.stamina if self.player else 0.0
        
    @player_stamina.setter
    def player_stamina(self, value: float) -> None:
        if self.player:
            self.player.stamina = value
            
    @property
    def player_bombs(self) -> int:
        return self.player.bombs if self.player else 0
        
    @player_bombs.setter
    def player_bombs(self, value: int) -> None:
        if self.player:
            self.player.bombs = value
    # ------------------------------------------------
"""

# Insert properties right before _wire_event_bus
insert_pos = content.find("    def _wire_event_bus(self) -> None:")
if insert_pos != -1:
    content = content[:insert_pos] + properties + "\n" + content[insert_pos:]

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
