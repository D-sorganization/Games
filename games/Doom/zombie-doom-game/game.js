// Game constants
const SCREEN_WIDTH = 1024;
const SCREEN_HEIGHT = 768;
const TILE_SIZE = 64;
const FOV = Math.PI / 3; // 60 degrees
const MAX_DEPTH = 40;
const NUM_RAYS = SCREEN_WIDTH / 2;

const PLAYER_PISTOL_DAMAGE = 10;
const PLAYER_RIFLE_DAMAGE = 18;
const RIFLE_COOLDOWN = 180;
const ZOMBIE_DAMAGE = 10;
const ZOMBIE_HEALTH = 80;
const ATTACK_RANGE = 70;
const FIREBALL_DAMAGE = 15;
const FIREBALL_SPEED = 2.4;
const FIREBALL_COOLDOWN = 2200;

// Game map (1 = wall, 0 = empty, 2 = door, 3 = exit)
const mapLayout = [
    '111111111111111111111111111111111111111111111111',
    '100000000000000000000000000000000000000000000001',
    '100000001111100000000000000111111000000000000001',
    '100000001111100000000100000111111000000000000001',
    '100000001111100000011100000111111000000000000001',
    '100000000000000111000000000000000000011110000001',
    '100000000000000000000000000000000000000000000001',
    '100000000001111000000000000000000001111000000001',
    '100011100000000000000111100000000000000001111001',
    '100000000000000000000000000000000000000000000001',
    '100000000000000000000001111000000000000000000031',
    '111111111111111111111111111111111111111111111111'
];

const map = mapLayout.map(row => row.split('').map(Number));
const MAP_HEIGHT = map.length;
const MAP_WIDTH = map[0].length;

// Game state
let gameState = {
    running: false,
    won: false,
    gameOver: false
};

// Player
const player = {
    x: 2 * TILE_SIZE,
    y: 2 * TILE_SIZE,
    angle: 0,
    speed: 0,
    strafeSpeed: 0,
    rotationSpeed: 0,
    health: 100,
    maxHealth: 100,
    pistolAmmo: 120,
    rifleAmmo: 90,
    kills: 0
};

// Enemies
const enemyTypes = {
    zombie: {
        color: '#6b8a6f',
        speed: 1.4,
        damage: ZOMBIE_DAMAGE,
        attackCooldown: 900,
        sprite: 'Zombie',
        scale: 1,
        fireball: null
    },
    boss: {
        color: '#8c3f3f',
        speed: 1.1,
        damage: 15,
        attackCooldown: 800,
        sprite: 'Boss',
        scale: 2,
        fireball: { damage: FIREBALL_DAMAGE, speed: FIREBALL_SPEED, cooldown: FIREBALL_COOLDOWN }
    }
};

const enemies = [
    { x: 6 * TILE_SIZE, y: 6 * TILE_SIZE, type: 'zombie' },
    { x: 12 * TILE_SIZE, y: 5 * TILE_SIZE, type: 'zombie' },
    { x: 18 * TILE_SIZE, y: 8 * TILE_SIZE, type: 'zombie' },
    { x: 26 * TILE_SIZE, y: 5 * TILE_SIZE, type: 'zombie' },
    { x: 32 * TILE_SIZE, y: 7 * TILE_SIZE, type: 'zombie' },
    { x: 38 * TILE_SIZE, y: 4 * TILE_SIZE, type: 'zombie' },
    { x: 44 * TILE_SIZE, y: 6 * TILE_SIZE, type: 'boss' }
].map(enemy => ({
    ...enemy,
    health: enemy.type === 'boss' ? ZOMBIE_HEALTH * 2 : ZOMBIE_HEALTH,
    maxHealth: enemy.type === 'boss' ? ZOMBIE_HEALTH * 2 : ZOMBIE_HEALTH,
    angle: 0,
    lastAttack: 0,
    lastFireball: 0,
    mouthOpen: false,
    mouthTimer: 0,
    eyeRotation: 0,
    droolOffset: 0,
    legPhase: 0
}));

const projectiles = [];

// Input handling
const keys = {};

// Weapon state
const weapon = {
    bobOffset: 0,
    shootAnimOffset: 0,
    isShooting: false,
    lastShot: { pistol: 0, rifle: 0 },
    cooldown: { pistol: 300, rifle: RIFLE_COOLDOWN },
    damage: { pistol: PLAYER_PISTOL_DAMAGE, rifle: PLAYER_RIFLE_DAMAGE },
    current: 'pistol',
    isHolstered: false,
    aiming: false
};

let minimapVisible = true;
let currentFov = FOV;

// Canvas setup
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
canvas.width = SCREEN_WIDTH;
canvas.height = SCREEN_HEIGHT;

// Start screen
const startScreen = document.getElementById('startScreen');
const startButton = document.getElementById('startButton');
const jumpScare = document.getElementById('jumpscare');
let jumpScareShown = false;

startButton.addEventListener('click', () => {
    startScreen.style.display = 'none';
    gameState.running = true;
    canvas.requestPointerLock();
    gameLoop();
});

// Event listeners
document.addEventListener('keydown', (e) => {
    const key = e.key.toLowerCase();
    keys[key] = true;

    if (key === 'e') {
        openDoor();
    }

    if (key === 'h') {
        weapon.isHolstered = !weapon.isHolstered;
    }

    if (key === 'm') {
        minimapVisible = !minimapVisible;
    }

    if (key === '1') {
        weapon.current = 'pistol';
    }

    if (key === '2') {
        weapon.current = 'rifle';
    }
});

document.addEventListener('keyup', (e) => {
    keys[e.key.toLowerCase()] = false;
});

document.addEventListener('mousemove', (e) => {
    if (document.pointerLockElement === canvas) {
        player.angle += e.movementX * 0.002;
    }
});

canvas.addEventListener('contextmenu', (e) => {
    e.preventDefault();
});

canvas.addEventListener('mousedown', (e) => {
    if (gameState.running && !gameState.gameOver && !gameState.won) {
        canvas.requestPointerLock();

        if (e.button === 0) {
            weapon.aiming = true;
            currentFov = FOV * 0.85;
        }

        if (e.button === 2) {
            shoot();
        }
    }
});

document.addEventListener('mouseup', (e) => {
    if (e.button === 0) {
        weapon.aiming = false;
        currentFov = FOV;
    }
});

function triggerJumpScare() {
    if (jumpScareShown) return;
    jumpScareShown = true;
    jumpScare.style.display = 'flex';
    try {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.frequency.value = 160;
        gain.gain.value = 0.25;
        osc.connect(gain).connect(audioCtx.destination);
        osc.start();
        gain.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + 0.6);
        osc.stop(audioCtx.currentTime + 0.65);
    } catch (err) {
        console.warn('Audio unavailable for jumpscare', err);
    }
}

function handlePlayerDeath() {
    if (gameState.gameOver) return;
    gameState.gameOver = true;
    triggerJumpScare();
}

// Helper functions
function castRay(rayAngle, originX = player.x, originY = player.y) {
    const rayX = Math.cos(rayAngle);
    const rayY = Math.sin(rayAngle);

    let distanceToWall = 0;
    let hitWall = false;
    let wallType = 0;
    let side = 0; // 0 = vertical, 1 = horizontal

    while (!hitWall && distanceToWall < MAX_DEPTH) {
        distanceToWall += 0.1;

        const testX = originX + rayX * distanceToWall * TILE_SIZE;
        const testY = originY + rayY * distanceToWall * TILE_SIZE;

        const mapX = Math.floor(testX / TILE_SIZE);
        const mapY = Math.floor(testY / TILE_SIZE);

        if (mapX < 0 || mapX >= MAP_WIDTH || mapY < 0 || mapY >= MAP_HEIGHT) {
            hitWall = true;
            distanceToWall = MAX_DEPTH;
        } else if (map[mapY][mapX] > 0) {
            hitWall = true;
            wallType = map[mapY][mapX];

            // Determine which side was hit
            const blockMidX = mapX * TILE_SIZE + TILE_SIZE / 2;
            const blockMidY = mapY * TILE_SIZE + TILE_SIZE / 2;

            const dx = testX - blockMidX;
            const dy = testY - blockMidY;

            side = Math.abs(dx) > Math.abs(dy) ? 0 : 1;
        }
    }

    return { distance: distanceToWall, wallType, side };
}

function hasLineOfSight(originX, originY, targetX, targetY) {
    const angle = Math.atan2(targetY - originY, targetX - originX);
    const ray = castRay(angle, originX, originY);
    const distanceToTarget = Math.hypot(targetX - originX, targetY - originY) / TILE_SIZE;
    return ray.distance >= distanceToTarget - 0.1;
}

function drawWalls() {
    // Sky
    ctx.fillStyle = '#2a2a3e';
    ctx.fillRect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT / 2);

    // Floor
    ctx.fillStyle = '#3d3d3d';
    ctx.fillRect(0, SCREEN_HEIGHT / 2, SCREEN_WIDTH, SCREEN_HEIGHT / 2);

    // Cast rays
    for (let x = 0; x < NUM_RAYS; x++) {
        const rayAngle = (player.angle - currentFov / 2) + (x / NUM_RAYS) * currentFov;
        const ray = castRay(rayAngle);

        const distance = ray.distance * Math.cos(rayAngle - player.angle); // Corrects fisheye distortion
        const wallHeight = (TILE_SIZE / distance) * 277;

        // Wall color based on type and side
        let color;
        if (ray.wallType === 1) {
            color = ray.side === 0 ? '#8B4513' : '#654321';
        } else if (ray.wallType === 2) {
            color = ray.side === 0 ? '#4a4a4a' : '#333333'; // Door
        } else if (ray.wallType === 3) {
            color = ray.side === 0 ? '#00ff00' : '#00cc00'; // Exit
        }

        // Draw wall slice
        const drawX = x * (SCREEN_WIDTH / NUM_RAYS);
        const drawY = (SCREEN_HEIGHT - wallHeight) / 2;

        ctx.fillStyle = color;
        ctx.fillRect(drawX, drawY, SCREEN_WIDTH / NUM_RAYS + 1, wallHeight);

        // Add darkness based on distance
        const darkness = Math.min(distance / MAX_DEPTH, 0.7);
        ctx.fillStyle = `rgba(0, 0, 0, ${darkness})`;
        ctx.fillRect(drawX, drawY, SCREEN_WIDTH / NUM_RAYS + 1, wallHeight);
    }
}

function drawEnemySprite(spriteX, spriteY, spriteSize, enemy) {
    const type = enemyTypes[enemy.type];
    const bodyWidth = spriteSize * 0.6;
    const bodyHeight = spriteSize;
    const headSize = spriteSize * 0.4;
    const centerX = spriteX + spriteSize / 2;
    const bodyX = centerX - bodyWidth / 2;
    const bodyY = spriteY + spriteSize * 0.05;

    // Legs with speed-synced stride
    const legStride = Math.sin(enemy.legPhase) * spriteSize * 0.08;
    const legWidth = spriteSize * 0.18;
    const legHeight = spriteSize * 0.45;
    const legY = bodyY + bodyHeight * 0.55;

    ctx.fillStyle = '#2a2a2a';
    ctx.fillRect(centerX - bodyWidth * 0.45 + legStride, legY, legWidth, legHeight);
    ctx.fillRect(centerX + bodyWidth * 0.25 - legStride, legY, legWidth, legHeight);

    ctx.fillStyle = type.color;
    ctx.fillRect(bodyX, bodyY + headSize * 0.8, bodyWidth, bodyHeight * 0.6);

    ctx.fillStyle = '#2a1c1c';
    ctx.fillRect(bodyX, bodyY + bodyHeight * 0.65, bodyWidth, bodyHeight * 0.1);

    ctx.fillStyle = '#d9d9d9';
    ctx.fillRect(centerX - headSize / 2, bodyY, headSize, headSize);

    // Eyes with spinning pupils
    const eyeRadius = headSize * 0.12;
    const pupilRadius = eyeRadius * 0.6;
    const eyeYOffset = headSize * 0.25;
    const eyeSpacing = headSize * 0.18;

    ctx.fillStyle = '#ffffff';
    ctx.beginPath();
    ctx.arc(centerX - eyeSpacing, bodyY + eyeYOffset, eyeRadius, 0, Math.PI * 2);
    ctx.arc(centerX + eyeSpacing, bodyY + eyeYOffset, eyeRadius, 0, Math.PI * 2);
    ctx.fill();

    const pupilAngle = enemy.eyeRotation;
    const pupilOffset = eyeRadius * 0.4;
    const pupilXOffset = Math.cos(pupilAngle) * pupilOffset;
    const pupilYOffset = Math.sin(pupilAngle) * pupilOffset;

    ctx.fillStyle = '#222222';
    ctx.beginPath();
    ctx.arc(centerX - eyeSpacing + pupilXOffset, bodyY + eyeYOffset + pupilYOffset, pupilRadius, 0, Math.PI * 2);
    ctx.arc(centerX + eyeSpacing + pupilXOffset, bodyY + eyeYOffset + pupilYOffset, pupilRadius, 0, Math.PI * 2);
    ctx.fill();

    // Mouth animation
    const mouthWidth = headSize * 0.7;
    const mouthHeight = enemy.mouthOpen ? headSize * 0.3 : headSize * 0.12;
    const mouthX = centerX - mouthWidth / 2;
    const mouthY = bodyY + headSize * 0.65;

    ctx.fillStyle = '#b42a2a';
    ctx.fillRect(mouthX, mouthY, mouthWidth, mouthHeight);

    ctx.fillStyle = '#eeeeee';
    const toothWidth = mouthWidth / 6;
    const toothHeight = mouthHeight * 0.6;
    for (let i = 0; i < 6; i++) {
        ctx.fillRect(mouthX + i * toothWidth, mouthY, toothWidth * 0.6, toothHeight);
    }

    // Drool
    ctx.strokeStyle = '#7ed6ff';
    ctx.lineWidth = Math.max(2, spriteSize * 0.01);
    const droolLength = mouthHeight * 1.2 + (enemy.droolOffset % 10);
    ctx.beginPath();
    ctx.moveTo(mouthX + mouthWidth * 0.1, mouthY + mouthHeight);
    ctx.lineTo(mouthX + mouthWidth * 0.1, mouthY + mouthHeight + droolLength);
    ctx.moveTo(mouthX + mouthWidth * 0.9, mouthY + mouthHeight);
    ctx.lineTo(mouthX + mouthWidth * 0.9, mouthY + mouthHeight + droolLength * 0.8);
    ctx.stroke();

    // Claws or weapons indicator
    ctx.fillStyle = '#f4f4f4';
    ctx.fillRect(centerX - bodyWidth * 0.45, bodyY + bodyHeight * 0.6, bodyWidth * 0.15, bodyHeight * 0.2);
    ctx.fillRect(centerX + bodyWidth * 0.3, bodyY + bodyHeight * 0.6, bodyWidth * 0.15, bodyHeight * 0.2);
}

function drawEnemies() {
    // Sort enemies by distance (far to near)
    const sortedEnemies = enemies
        .filter(enemy => enemy.health > 0)
        .map(enemy => {
            const dx = enemy.x - player.x;
            const dy = enemy.y - player.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            const angle = Math.atan2(dy, dx) - player.angle;
            return { enemy, distance, angle };
        })
        .sort((a, b) => b.distance - a.distance);

    sortedEnemies.forEach(({ enemy, distance, angle }) => {
        // Normalize angle to -PI to PI
        let normalizedAngle = angle;
        while (normalizedAngle > Math.PI) normalizedAngle -= 2 * Math.PI;
        while (normalizedAngle < -Math.PI) normalizedAngle += 2 * Math.PI;

        // Check if enemy is in FOV
        if (Math.abs(normalizedAngle) < currentFov / 2 + 0.5) {
            if (!hasLineOfSight(player.x, player.y, enemy.x, enemy.y)) {
                return;
            }

            const type = enemyTypes[enemy.type];
            const spriteSize = (TILE_SIZE / distance) * 277 * type.scale;
            const spriteX = SCREEN_WIDTH / 2 + (normalizedAngle / currentFov) * SCREEN_WIDTH - spriteSize / 2;
            const spriteY = SCREEN_HEIGHT / 2 - spriteSize / 2;

            drawEnemySprite(spriteX, spriteY, spriteSize, enemy);

            // Draw health bar
            const healthBarWidth = spriteSize;
            const healthBarHeight = 5;
            const healthPercent = enemy.health / enemy.maxHealth;

            ctx.fillStyle = '#ff0000';
            ctx.fillRect(spriteX, spriteY - 10, healthBarWidth, healthBarHeight);
            ctx.fillStyle = '#00ff00';
            ctx.fillRect(spriteX, spriteY - 10, healthBarWidth * healthPercent, healthBarHeight);
        }
    });
}

function drawProjectiles() {
    const sortedProjectiles = projectiles
        .map(projectile => {
            const dx = projectile.x - player.x;
            const dy = projectile.y - player.y;
            const distance = Math.max(0.1, Math.sqrt(dx * dx + dy * dy));
            const angle = Math.atan2(dy, dx) - player.angle;
            return { projectile, distance, angle };
        })
        .sort((a, b) => b.distance - a.distance);

    sortedProjectiles.forEach(({ projectile, distance, angle }) => {
        let normalizedAngle = angle;
        while (normalizedAngle > Math.PI) normalizedAngle -= 2 * Math.PI;
        while (normalizedAngle < -Math.PI) normalizedAngle += 2 * Math.PI;

        if (
            Math.abs(normalizedAngle) < currentFov / 2 + 0.5 &&
            hasLineOfSight(player.x, player.y, projectile.x, projectile.y)
        ) {
            const spriteSize = (TILE_SIZE / distance) * 90;
            const spriteX =
                SCREEN_WIDTH / 2 + (normalizedAngle / currentFov) * SCREEN_WIDTH - spriteSize / 2;
            const spriteY = SCREEN_HEIGHT / 2 - spriteSize / 2;

            const gradient = ctx.createRadialGradient(
                spriteX + spriteSize / 2,
                spriteY + spriteSize / 2,
                spriteSize * 0.1,
                spriteX + spriteSize / 2,
                spriteY + spriteSize / 2,
                spriteSize * 0.6
            );

            gradient.addColorStop(0, '#ffcc66');
            gradient.addColorStop(0.5, '#ff6600');
            gradient.addColorStop(1, 'rgba(0,0,0,0)');

            ctx.fillStyle = gradient;
            ctx.beginPath();
            ctx.arc(spriteX + spriteSize / 2, spriteY + spriteSize / 2, spriteSize / 2, 0, Math.PI * 2);
            ctx.fill();
        }
    });
}

function drawWeapon() {
    if (weapon.isHolstered) {
        return;
    }

    const aimLift = weapon.aiming ? 25 : 0;
    const weaponY =
        SCREEN_HEIGHT - 200 + Math.sin(weapon.bobOffset) * 10 + weapon.shootAnimOffset - aimLift;
    const weaponX = SCREEN_WIDTH / 2 - 50 + (weapon.aiming ? 8 : 0);

    // Draw simple gun
    ctx.fillStyle = '#444';
    ctx.fillRect(weaponX, weaponY, 100, 200);

    ctx.fillStyle = '#666';
    ctx.fillRect(weaponX + 20, weaponY, 60, 150);

    ctx.fillStyle = '#222';
    ctx.fillRect(weaponX + 35, weaponY, 30, 80);

    // Muzzle flash
    if (weapon.shootAnimOffset < 0) {
        ctx.fillStyle = '#ffff00';
        ctx.fillRect(weaponX + 25, weaponY - 20, 50, 20);
    }
}

function drawHUD() {
    // Health
    ctx.fillStyle = '#ff0000';
    ctx.font = '24px Courier New';
    ctx.fillText(`HEALTH: ${Math.max(0, player.health)}`, 20, 30);

    // Ammo
    ctx.fillStyle = '#ffff00';
    ctx.fillText(`Pistol: ${player.pistolAmmo} | Rifle: ${player.rifleAmmo}`, 20, 60);

    // Kills
    ctx.fillStyle = '#00ff00';
    ctx.fillText(`KILLS: ${player.kills}/${enemies.length}`, 20, 90);

    // Weapon state
    ctx.fillStyle = weapon.isHolstered ? '#ffaa00' : '#00ff00';
    const holsterText = weapon.isHolstered ? 'HOLSTERED' : 'READY';
    ctx.fillText(`GUN: ${holsterText} | ${weapon.current.toUpperCase()}`, 20, 120);

    // Crosshair
    ctx.strokeStyle = '#00ff00';
    ctx.lineWidth = 2;
    const crosshairSize = weapon.aiming ? 6 : 10;
    ctx.beginPath();
    ctx.moveTo(SCREEN_WIDTH / 2 - crosshairSize, SCREEN_HEIGHT / 2);
    ctx.lineTo(SCREEN_WIDTH / 2 + crosshairSize, SCREEN_HEIGHT / 2);
    ctx.moveTo(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - crosshairSize);
    ctx.lineTo(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + crosshairSize);
    ctx.stroke();
}

function updatePlayer(deltaTime) {
    // Movement
    player.speed = 0;
    player.strafeSpeed = 0;

    const sprinting = keys['shift'];
    const moveAmount = sprinting ? 4.5 : 3;
    if (keys['w']) player.speed = moveAmount;
    if (keys['s']) player.speed = -moveAmount;
    if (keys['a']) player.strafeSpeed = -moveAmount;
    if (keys['d']) player.strafeSpeed = moveAmount;

    // Calculate new position
    const newX = player.x + Math.cos(player.angle) * player.speed + Math.cos(player.angle + Math.PI / 2) * player.strafeSpeed;
    const newY = player.y + Math.sin(player.angle) * player.speed + Math.sin(player.angle + Math.PI / 2) * player.strafeSpeed;

    // Collision detection
    const mapX = Math.floor(newX / TILE_SIZE);
    const mapY = Math.floor(newY / TILE_SIZE);

    if (map[mapY] && map[mapY][mapX] === 0) {
        player.x = newX;
        player.y = newY;
    }

    // Check for exit
    if (map[mapY] && map[mapY][mapX] === 3 && player.kills === enemies.length) {
        gameState.won = true;
    }

    // Weapon bobbing
    if (player.speed !== 0 || player.strafeSpeed !== 0) {
        weapon.bobOffset += weapon.aiming ? 0.08 : 0.15;
    }

    // Weapon shoot animation
    if (weapon.shootAnimOffset < 0) {
        weapon.shootAnimOffset += 5;
    }
}

function updateEnemies(deltaTime) {
    const currentTime = Date.now();

    enemies.forEach(enemy => {
        if (enemy.health <= 0) return;

        const type = enemyTypes[enemy.type];
        const dx = player.x - enemy.x;
        const dy = player.y - enemy.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        const angleToPlayer = Math.atan2(dy, dx);

        enemy.eyeRotation += deltaTime * 10;
        enemy.droolOffset = (enemy.droolOffset + deltaTime * 40) % 20;

        const seesPlayer =
            distance < 900 && hasLineOfSight(enemy.x, enemy.y, player.x, player.y);
        let movement = 0;

        if (seesPlayer) {
            enemy.mouthTimer += deltaTime;
            if (enemy.mouthTimer > 0.25) {
                enemy.mouthOpen = !enemy.mouthOpen;
                enemy.mouthTimer = 0;
            }

            const newX = enemy.x + Math.cos(angleToPlayer) * type.speed;
            const newY = enemy.y + Math.sin(angleToPlayer) * type.speed;

            const mapX = Math.floor(newX / TILE_SIZE);
            const mapY = Math.floor(newY / TILE_SIZE);

            if (map[mapY] && map[mapY][mapX] === 0) {
                movement = Math.sqrt((newX - enemy.x) ** 2 + (newY - enemy.y) ** 2);
                enemy.x = newX;
                enemy.y = newY;
            }

            const attackReach = ATTACK_RANGE + (enemy.type === 'boss' ? 10 : 0);
            if (distance < attackReach && currentTime - enemy.lastAttack > type.attackCooldown) {
                player.health -= type.damage;
                enemy.lastAttack = currentTime;

                if (player.health <= 0) {
                    handlePlayerDeath();
                }
            }

            if (type.fireball && currentTime - enemy.lastFireball > type.fireball.cooldown) {
                projectiles.push({
                    x: enemy.x,
                    y: enemy.y,
                    angle: angleToPlayer,
                    speed: type.fireball.speed,
                    damage: type.fireball.damage
                });
                enemy.lastFireball = currentTime;
            }
        } else if (currentTime % 1500 < 40) {
            const wanderAngle = (enemy.x + enemy.y + currentTime * 0.0005) % (Math.PI * 2);
            const newX = enemy.x + Math.cos(wanderAngle) * type.speed * 0.4;
            const newY = enemy.y + Math.sin(wanderAngle) * type.speed * 0.4;

            const mapX = Math.floor(newX / TILE_SIZE);
            const mapY = Math.floor(newY / TILE_SIZE);

            if (map[mapY] && map[mapY][mapX] === 0) {
                movement = Math.sqrt((newX - enemy.x) ** 2 + (newY - enemy.y) ** 2);
                enemy.x = newX;
                enemy.y = newY;
            }
        }

        enemy.legPhase += movement * 0.2;
    });
}

function updateProjectiles(deltaTime) {
    for (let i = projectiles.length - 1; i >= 0; i--) {
        const projectile = projectiles[i];
        projectile.x += Math.cos(projectile.angle) * projectile.speed * TILE_SIZE * deltaTime;
        projectile.y += Math.sin(projectile.angle) * projectile.speed * TILE_SIZE * deltaTime;

        const mapX = Math.floor(projectile.x / TILE_SIZE);
        const mapY = Math.floor(projectile.y / TILE_SIZE);

        if (
            mapX < 0 ||
            mapX >= MAP_WIDTH ||
            mapY < 0 ||
            mapY >= MAP_HEIGHT ||
            (map[mapY] && map[mapY][mapX] > 0)
        ) {
            projectiles.splice(i, 1);
            continue;
        }

        const distanceToPlayer = Math.hypot(projectile.x - player.x, projectile.y - player.y);
        if (distanceToPlayer < 24) {
            player.health -= projectile.damage;
            projectiles.splice(i, 1);

            if (player.health <= 0) {
                handlePlayerDeath();
            }
        }
    }
}

function shoot() {
    const currentTime = Date.now();

    if (weapon.isHolstered) return;
    const weaponId = weapon.current;
    const ammoKey = weaponId === 'rifle' ? 'rifleAmmo' : 'pistolAmmo';
    const cooldown = weapon.cooldown[weaponId];

    if (currentTime - weapon.lastShot[weaponId] < cooldown) return;
    if (player[ammoKey] <= 0) return;

    player[ammoKey]--;
    weapon.lastShot[weaponId] = currentTime;
    weapon.shootAnimOffset = -30;

    // Check if we hit an enemy
    const centerRay = castRay(player.angle);

    enemies.forEach(enemy => {
        if (enemy.health <= 0) return;

        const dx = enemy.x - player.x;
        const dy = enemy.y - player.y;
        const distance = Math.sqrt(dx * dx + dy * dy) / TILE_SIZE;
        const angle = Math.atan2(dy, dx);

        let angleDiff = angle - player.angle;
        while (angleDiff > Math.PI) angleDiff -= 2 * Math.PI;
        while (angleDiff < -Math.PI) angleDiff += 2 * Math.PI;

        const baseAim = weaponId === 'rifle' ? 0.08 : 0.1;
        const aimAllowance =
            (weapon.aiming ? baseAim : baseAim + 0.1) + Math.max(0, 0.05 - distance * 0.002);

        // Check if enemy is in crosshair and visible
        if (
            Math.abs(angleDiff) < aimAllowance &&
            distance < centerRay.distance &&
            hasLineOfSight(player.x, player.y, enemy.x, enemy.y)
        ) {
            enemy.health -= weapon.damage[weaponId];

            if (enemy.health <= 0) {
                player.kills++;
            }
        }
    });
}

function openDoor() {
    const doorCheckDist = 1.5;
    const checkX = player.x + Math.cos(player.angle) * TILE_SIZE * doorCheckDist;
    const checkY = player.y + Math.sin(player.angle) * TILE_SIZE * doorCheckDist;

    const mapX = Math.floor(checkX / TILE_SIZE);
    const mapY = Math.floor(checkY / TILE_SIZE);

    if (map[mapY] && map[mapY][mapX] === 2) {
        map[mapY][mapX] = 0; // Open door
    }
}

function drawGameOver() {
    ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
    ctx.fillRect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT);

    ctx.fillStyle = '#ff0000';
    ctx.font = '64px Courier New';
    ctx.textAlign = 'center';
    ctx.fillText('GAME OVER', SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2);

    ctx.fillStyle = '#ffffff';
    ctx.font = '24px Courier New';
    ctx.fillText('Refresh to try again', SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 50);
    ctx.textAlign = 'left';
}

function drawMinimap() {
    if (!minimapVisible) return;

    const mapScale = 4;
    const minimapWidth = MAP_WIDTH * mapScale;
    const minimapHeight = MAP_HEIGHT * mapScale;
    const offset = 20;

    ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
    ctx.fillRect(
        SCREEN_WIDTH - minimapWidth - offset - 10,
        offset - 10,
        minimapWidth + 20,
        minimapHeight + 20
    );

    for (let y = 0; y < MAP_HEIGHT; y++) {
        for (let x = 0; x < MAP_WIDTH; x++) {
            const tile = map[y][x];
            if (tile === 1) {
                ctx.fillStyle = '#6b4b3e';
            } else if (tile === 2) {
                ctx.fillStyle = '#9d9d9d';
            } else if (tile === 3) {
                ctx.fillStyle = '#00cc44';
            } else {
                ctx.fillStyle = '#1b1b1b';
            }

            ctx.fillRect(
                SCREEN_WIDTH - minimapWidth - offset + x * mapScale,
                offset + y * mapScale,
                mapScale,
                mapScale
            );
        }
    }

    // Player
    ctx.fillStyle = '#ffff00';
    ctx.fillRect(
        SCREEN_WIDTH - minimapWidth - offset + (player.x / TILE_SIZE) * mapScale - 2,
        offset + (player.y / TILE_SIZE) * mapScale - 2,
        4,
        4
    );

    // Player direction
    ctx.strokeStyle = '#ffff00';
    ctx.beginPath();
    ctx.moveTo(
        SCREEN_WIDTH - minimapWidth - offset + (player.x / TILE_SIZE) * mapScale,
        offset + (player.y / TILE_SIZE) * mapScale
    );
    ctx.lineTo(
        SCREEN_WIDTH - minimapWidth - offset + ((player.x / TILE_SIZE) + Math.cos(player.angle)) * mapScale,
        offset + ((player.y / TILE_SIZE) + Math.sin(player.angle)) * mapScale
    );
    ctx.stroke();

    // Enemies
    enemies.forEach(enemy => {
        if (enemy.health <= 0) return;
        ctx.fillStyle = enemyTypes[enemy.type].color;
        ctx.fillRect(
            SCREEN_WIDTH - minimapWidth - offset + (enemy.x / TILE_SIZE) * mapScale - 2,
            offset + (enemy.y / TILE_SIZE) * mapScale - 2,
            4,
            4
        );
    });
}

function drawWin() {
    ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
    ctx.fillRect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT);

    ctx.fillStyle = '#00ff00';
    ctx.font = '64px Courier New';
    ctx.textAlign = 'center';
    ctx.fillText('YOU WIN!', SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2);

    ctx.fillStyle = '#ffffff';
    ctx.font = '24px Courier New';
    ctx.fillText('All enemies eliminated!', SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 50);
    ctx.textAlign = 'left';
}

// Main game loop
let lastTime = Date.now();

function gameLoop() {
    if (!gameState.running) return;

    const currentTime = Date.now();
    const deltaTime = (currentTime - lastTime) / 1000;
    lastTime = currentTime;

    // Clear canvas
    ctx.clearRect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT);

    if (!gameState.gameOver && !gameState.won) {
        // Update
        updatePlayer(deltaTime);
        updateEnemies(deltaTime);
        updateProjectiles(deltaTime);

        // Draw
        drawWalls();
        drawEnemies();
        drawProjectiles();
        drawWeapon();
        drawHUD();
        drawMinimap();
    } else if (gameState.gameOver) {
        drawGameOver();
    } else if (gameState.won) {
        drawWin();
    }

    requestAnimationFrame(gameLoop);
}
