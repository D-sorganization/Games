// Game constants
const SCREEN_WIDTH = 1024;
const SCREEN_HEIGHT = 768;
const MAP_SIZE = 16;
const TILE_SIZE = 64;
const FOV = Math.PI / 3; // 60 degrees
const MAX_DEPTH = 20;
const NUM_RAYS = SCREEN_WIDTH / 2;

// Game map (1 = wall, 0 = empty, 2 = door, 3 = exit)
const map = [
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,1,1,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,1,1,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,3,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
];

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
    ammo: 50,
    kills: 0
};

// Enemies
const enemyTypes = {
    demon: { color: '#b52b1d', speed: 1.6, damage: 12, shootCooldown: 1800, sprite: 'Demon' },
    dinosaur: { color: '#3fa34d', speed: 2.2, damage: 14, shootCooldown: 1500, sprite: 'Dino' },
    raider: { color: '#7a5cff', speed: 1.8, damage: 10, shootCooldown: 1200, sprite: 'Raider' }
};

const enemies = [
    {
        x: 6 * TILE_SIZE,
        y: 6 * TILE_SIZE,
        health: 40,
        maxHealth: 40,
        angle: 0,
        type: 'dinosaur',
        lastShot: 0,
        mouthOpen: false,
        mouthTimer: 0,
        eyeRotation: 0,
        droolOffset: 0
    },
    {
        x: 10 * TILE_SIZE,
        y: 5 * TILE_SIZE,
        health: 35,
        maxHealth: 35,
        angle: 0,
        type: 'demon',
        lastShot: 0,
        mouthOpen: false,
        mouthTimer: 0,
        eyeRotation: 0,
        droolOffset: 0
    },
    {
        x: 4 * TILE_SIZE,
        y: 11 * TILE_SIZE,
        health: 30,
        maxHealth: 30,
        angle: 0,
        type: 'raider',
        lastShot: 0,
        mouthOpen: false,
        mouthTimer: 0,
        eyeRotation: 0,
        droolOffset: 0
    },
    {
        x: 11 * TILE_SIZE,
        y: 10 * TILE_SIZE,
        health: 40,
        maxHealth: 40,
        angle: 0,
        type: 'demon',
        lastShot: 0,
        mouthOpen: false,
        mouthTimer: 0,
        eyeRotation: 0,
        droolOffset: 0
    }
];

// Input handling
const keys = {};
let mouseX = 0;
let mouseLocked = false;

// Weapon state
const weapon = {
    bobOffset: 0,
    shootAnimOffset: 0,
    isShooting: false,
    lastShot: 0,
    shootCooldown: 300,
    isHolstered: false
};

let minimapVisible = true;

// Canvas setup
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
canvas.width = SCREEN_WIDTH;
canvas.height = SCREEN_HEIGHT;

// Start screen
const startScreen = document.getElementById('startScreen');
const startButton = document.getElementById('startButton');

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
});

document.addEventListener('keyup', (e) => {
    keys[e.key.toLowerCase()] = false;
});

document.addEventListener('mousemove', (e) => {
    if (document.pointerLockElement === canvas) {
        mouseLocked = true;
        player.angle += e.movementX * 0.002;
    }
});

canvas.addEventListener('click', () => {
    if (gameState.running && !gameState.gameOver && !gameState.won) {
        canvas.requestPointerLock();
        shoot();
    }
});

document.addEventListener('pointerlockchange', () => {
    mouseLocked = document.pointerLockElement === canvas;
});

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

        if (mapX < 0 || mapX >= MAP_SIZE || mapY < 0 || mapY >= MAP_SIZE) {
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
        const rayAngle = (player.angle - FOV / 2) + (x / NUM_RAYS) * FOV;
        const ray = castRay(rayAngle);

        const distance = ray.distance * Math.cos(rayAngle - player.angle); // Fix fisheye
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
        if (Math.abs(normalizedAngle) < FOV / 2 + 0.5) {
            if (!hasLineOfSight(player.x, player.y, enemy.x, enemy.y)) {
                return;
            }

            const spriteSize = (TILE_SIZE / distance) * 277;
            const spriteX = SCREEN_WIDTH / 2 + (normalizedAngle / FOV) * SCREEN_WIDTH - spriteSize / 2;
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

function drawWeapon() {
    if (weapon.isHolstered) {
        return;
    }

    const weaponY = SCREEN_HEIGHT - 200 + Math.sin(weapon.bobOffset) * 10 + weapon.shootAnimOffset;
    const weaponX = SCREEN_WIDTH / 2 - 50;

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
    ctx.fillText(`AMMO: ${player.ammo}`, 20, 60);

    // Kills
    ctx.fillStyle = '#00ff00';
    ctx.fillText(`KILLS: ${player.kills}/${enemies.length}`, 20, 90);

    // Weapon state
    ctx.fillStyle = weapon.isHolstered ? '#ffaa00' : '#00ff00';
    const holsterText = weapon.isHolstered ? 'HOLSTERED' : 'READY';
    ctx.fillText(`GUN: ${holsterText}`, 20, 120);

    // Crosshair
    ctx.strokeStyle = '#00ff00';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(SCREEN_WIDTH / 2 - 10, SCREEN_HEIGHT / 2);
    ctx.lineTo(SCREEN_WIDTH / 2 + 10, SCREEN_HEIGHT / 2);
    ctx.moveTo(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 10);
    ctx.lineTo(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 10);
    ctx.stroke();
}

function updatePlayer(deltaTime) {
    // Movement
    player.speed = 0;
    player.strafeSpeed = 0;

    if (keys['w']) player.speed = 3;
    if (keys['s']) player.speed = -3;
    if (keys['a']) player.strafeSpeed = -3;
    if (keys['d']) player.strafeSpeed = 3;

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
        weapon.bobOffset += 0.15;
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

        const seesPlayer = distance < 550 && hasLineOfSight(enemy.x, enemy.y, player.x, player.y);

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
                enemy.x = newX;
                enemy.y = newY;
            }

            if (distance < 220 && currentTime - enemy.lastShot > type.shootCooldown) {
                player.health -= type.damage;
                enemy.lastShot = currentTime;

                if (player.health <= 0) {
                    gameState.gameOver = true;
                }
            }
        } else if (currentTime % 2000 < 50) {
            // small wander to keep them moving
            const wanderAngle = Math.random() * Math.PI * 2;
            const newX = enemy.x + Math.cos(wanderAngle) * type.speed * 0.5;
            const newY = enemy.y + Math.sin(wanderAngle) * type.speed * 0.5;

            const mapX = Math.floor(newX / TILE_SIZE);
            const mapY = Math.floor(newY / TILE_SIZE);

            if (map[mapY] && map[mapY][mapX] === 0) {
                enemy.x = newX;
                enemy.y = newY;
            }
        }
    });
}

function shoot() {
    const currentTime = Date.now();

    if (weapon.isHolstered) return;
    if (currentTime - weapon.lastShot < weapon.shootCooldown) return;
    if (player.ammo <= 0) return;

    player.ammo--;
    weapon.lastShot = currentTime;
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

        const aimAllowance = 0.2 + Math.max(0, 0.05 - distance * 0.002);

        // Check if enemy is in crosshair and visible
        if (Math.abs(angleDiff) < aimAllowance && distance < centerRay.distance && hasLineOfSight(player.x, player.y, enemy.x, enemy.y)) {
            enemy.health -= 20;

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
    const minimapSize = MAP_SIZE * mapScale;
    const offset = 20;

    ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
    ctx.fillRect(SCREEN_WIDTH - minimapSize - offset - 10, offset - 10, minimapSize + 20, minimapSize + 20);

    for (let y = 0; y < MAP_SIZE; y++) {
        for (let x = 0; x < MAP_SIZE; x++) {
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

            ctx.fillRect(SCREEN_WIDTH - minimapSize - offset + x * mapScale, offset + y * mapScale, mapScale, mapScale);
        }
    }

    // Player
    ctx.fillStyle = '#ffff00';
    ctx.fillRect(
        SCREEN_WIDTH - minimapSize - offset + (player.x / TILE_SIZE) * mapScale - 2,
        offset + (player.y / TILE_SIZE) * mapScale - 2,
        4,
        4
    );

    // Player direction
    ctx.strokeStyle = '#ffff00';
    ctx.beginPath();
    ctx.moveTo(
        SCREEN_WIDTH - minimapSize - offset + (player.x / TILE_SIZE) * mapScale,
        offset + (player.y / TILE_SIZE) * mapScale
    );
    ctx.lineTo(
        SCREEN_WIDTH - minimapSize - offset + ((player.x / TILE_SIZE) + Math.cos(player.angle)) * mapScale,
        offset + ((player.y / TILE_SIZE) + Math.sin(player.angle)) * mapScale
    );
    ctx.stroke();

    // Enemies
    enemies.forEach(enemy => {
        if (enemy.health <= 0) return;
        ctx.fillStyle = enemyTypes[enemy.type].color;
        ctx.fillRect(
            SCREEN_WIDTH - minimapSize - offset + (enemy.x / TILE_SIZE) * mapScale - 2,
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

        // Draw
        drawWalls();
        drawEnemies();
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
