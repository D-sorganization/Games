// Game constants
const SCREEN_WIDTH = 1024;
const SCREEN_HEIGHT = 768;
const HORIZON = SCREEN_HEIGHT * 0.52;
const SKY_DRIFT_SPEED = 0.04;
const AURORA_SCROLL_SPEED = 0.025;
const MAP_SIZE = 16;
const TILE_SIZE = 64;
const FOV = Math.PI / 3; // 60 degrees
const MAX_DEPTH = 20;
const NUM_RAYS = SCREEN_WIDTH / 2;
const LIGHT_DIRECTION = { x: -0.45, y: 0.65 };
const VIGNETTE_STRENGTH = 0.35;
const FLOOR_DETAIL_STEP = 3;

function buildLevel(rows) {
    return rows.map((row) => row.split('').map(Number));
}

// Game maps (1 = wall, 0 = empty, 2 = door, 3 = exit)
const LEVELS = [
    {
        name: 'Gateway Ruins',
        spawn: { x: 2, y: 2, angle: 0 },
        minEnemies: 4,
        maxEnemies: 6,
        layout: buildLevel([
            '1111111111111111',
            '1000000000000001',
            '1000000000000301',
            '1000000000000001',
            '1000110000011001',
            '1000100000001001',
            '1000001111100001',
            '1000001010102001',
            '1000001010100001',
            '1000001111100001',
            '1000000000000001',
            '1000000000000001',
            '1000000000000001',
            '1000000000000001',
            '1000000000000001',
            '1111111111111111'
        ])
    },
    {
        name: 'Crossfire Halls',
        spawn: { x: 2, y: 13, angle: Math.PI / 2 },
        minEnemies: 5,
        maxEnemies: 8,
        layout: buildLevel([
            '1111111111111111',
            '1000000002000001',
            '1011101110111011',
            '1000100010001001',
            '1000103010001001',
            '1011101110111011',
            '1000100000001001',
            '1000111111101001',
            '1000100000101001',
            '1010102220101011',
            '1000100000101001',
            '1000111111101001',
            '1000000000001001',
            '1000000000001001',
            '1000000000000001',
            '1111111111111111'
        ])
    },
    {
        name: 'Spiral Chambers',
        spawn: { x: 2, y: 2, angle: Math.PI / 4 },
        minEnemies: 6,
        maxEnemies: 9,
        layout: buildLevel([
            '1111111111111111',
            '1000000000000001',
            '1011111111111101',
            '1010000000000101',
            '1010111111110101',
            '1010100000010101',
            '1010101111010101',
            '1010101001010101',
            '1010101011010101',
            '1010101000010101',
            '1010111111110101',
            '1010000000030101',
            '1011111111100101',
            '1000000000000101',
            '1222222222200001',
            '1111111111111111'
        ])
    },
    {
        name: 'Vaulted Plaza',
        spawn: { x: 8, y: 8, angle: 0 },
        minEnemies: 7,
        maxEnemies: 10,
        layout: buildLevel([
            '1111111111111111',
            '1000000000000001',
            '1011110111111101',
            '1010000100000101',
            '1010111101110101',
            '1010100001010101',
            '1010102221010101',
            '1000100001010001',
            '1000100001010001',
            '1010102221010101',
            '1010100001010101',
            '1010111101110101',
            '1010000100000101',
            '1011110111111101',
            '1000000030000001',
            '1111111111111111'
        ])
    },
    {
        name: 'Broken Keep',
        spawn: { x: 2, y: 2, angle: Math.PI / 2 },
        minEnemies: 7,
        maxEnemies: 11,
        layout: buildLevel([
            '1111111111111111',
            '1000001110000001',
            '1011101010111101',
            '1010101010100101',
            '1010101010100101',
            '1010101010100101',
            '1010101010100101',
            '1010101010100101',
            '1010101010100101',
            '1010101010100101',
            '1010101010100101',
            '1010101010100101',
            '1010101010100101',
            '1010111010111101',
            '1000000010000301',
            '1111111111111111'
        ])
    },
    {
        name: 'Ashen Courtyard',
        spawn: { x: 8, y: 2, angle: Math.PI },
        minEnemies: 8,
        maxEnemies: 12,
        layout: buildLevel([
            '1111111111111111',
            '1000000000000001',
            '1011111011111101',
            '1010001010000101',
            '1010201010200101',
            '1010001010000101',
            '1011111011111101',
            '1000000000000001',
            '1000111111100001',
            '1010100000101011',
            '1010103330101011',
            '1010100000101011',
            '1000111111100001',
            '1000000000000001',
            '1000000000000001',
            '1111111111111111'
        ])
    },
    {
        name: 'Arc Furnace',
        spawn: { x: 2, y: 8, angle: 0 },
        minEnemies: 9,
        maxEnemies: 12,
        layout: buildLevel([
            '1111111111111111',
            '1000220000000001',
            '1011111111111101',
            '1010000000000101',
            '1010111111100101',
            '1010100000100101',
            '1010103030100101',
            '1010100000100101',
            '1010111111100101',
            '1010000000000101',
            '1011111111111101',
            '1000000000000001',
            '1000000220000001',
            '1011111111111101',
            '1000000000000001',
            '1111111111111111'
        ])
    },
    {
        name: 'Chokepoint Canyons',
        spawn: { x: 2, y: 2, angle: Math.PI / 2 },
        minEnemies: 9,
        maxEnemies: 13,
        layout: buildLevel([
            '1111111111111111',
            '1000000000000001',
            '1011111111111101',
            '1000100000100001',
            '1110101110101111',
            '1000101010101001',
            '1011101010111011',
            '1010001010001011',
            '1010111011101011',
            '1010100030101011',
            '1010101010101011',
            '1010101010101011',
            '1010101010101011',
            '1000000000000001',
            '1000002220000001',
            '1111111111111111'
        ])
    },
    {
        name: 'Citadel Approach',
        spawn: { x: 8, y: 14, angle: -Math.PI / 2 },
        minEnemies: 10,
        maxEnemies: 14,
        layout: buildLevel([
            '1111111111111111',
            '1000000000000001',
            '1011111111111101',
            '1010000000000101',
            '1010111111100101',
            '1010100000100101',
            '1010101110100101',
            '1010101010100101',
            '1010101010100101',
            '1010101110100101',
            '1010100000100101',
            '1010111111100101',
            '1010000000000101',
            '1011111111111101',
            '1000000000030001',
            '1111111111111111'
        ])
    },
    {
        name: 'Hellmouth',
        spawn: { x: 2, y: 2, angle: Math.PI / 4 },
        minEnemies: 11,
        maxEnemies: 15,
        layout: buildLevel([
            '1111111111111111',
            '1000000000000001',
            '1011111111111101',
            '1010000000000101',
            '1010111111100101',
            '1010100000100101',
            '1010103330100101',
            '1010100000100101',
            '1010111111100101',
            '1010000000000101',
            '1011111111111101',
            '1000000000000001',
            '1000222222200001',
            '1011111111111101',
            '1000000000000001',
            '1111111111111111'
        ])
    }
];

let map = LEVELS[0].layout.map((row) => [...row]);
let currentLevelIndex = 0;

// Game state
let gameState = {
    running: false,
    won: false,
    gameOver: false
};

// Player
const player = {
    x: LEVELS[0].spawn.x * TILE_SIZE,
    y: LEVELS[0].spawn.y * TILE_SIZE,
    angle: LEVELS[0].spawn.angle,
    speed: 0,
    strafeSpeed: 0,
    rotationSpeed: 0,
    health: 100,
    maxHealth: 100,
    ammo: 0,
    kills: 0
};

// Enemies
const enemyTypes = {
    demon: {
        color: '#b52b1d',
        speed: 1.6,
        damage: 12,
        shootCooldown: 1800,
        sprite: 'Demon',
        health: 40
    },
    dinosaur: {
        color: '#3fa34d',
        speed: 2.2,
        damage: 14,
        shootCooldown: 1500,
        sprite: 'Dino',
        health: 45
    },
    raider: {
        color: '#7a5cff',
        speed: 1.8,
        damage: 10,
        shootCooldown: 1200,
        sprite: 'Raider',
        health: 35
    }
};

let enemies = [];

// Input handling
const keys = {};
let mouseX = 0;
let mouseLocked = false;

// Weapon state
const weaponLoadout = [
    {
        name: 'Trusty Pistol',
        damage: 20,
        shootCooldown: 280,
        ammo: 90,
        baseColor: '#444',
        midColor: '#666',
        muzzleColor: '#ffea76'
    },
    {
        name: 'Boomstick',
        damage: 35,
        shootCooldown: 520,
        ammo: 65,
        baseColor: '#5c3b2e',
        midColor: '#7a5a3f',
        muzzleColor: '#ffbb55'
    },
    {
        name: 'Plasma Burster',
        damage: 18,
        shootCooldown: 160,
        ammo: 140,
        baseColor: '#133d7a',
        midColor: '#1f63c4',
        muzzleColor: '#66e2ff'
    }
];

const weapon = {
    bobOffset: 0,
    shootAnimOffset: 0,
    isShooting: false,
    lastShot: 0,
    shootCooldown: weaponLoadout[0].shootCooldown,
    isHolstered: false,
    damage: weaponLoadout[0].damage,
    baseColor: weaponLoadout[0].baseColor,
    midColor: weaponLoadout[0].midColor,
    muzzleColor: weaponLoadout[0].muzzleColor,
    name: weaponLoadout[0].name,
    maxAmmo: weaponLoadout[0].ammo
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
    startNewGame();
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

function randomInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

function randomChoice(list) {
    return list[Math.floor(Math.random() * list.length)];
}

function randomizeWeaponLoadout() {
    const selection = randomChoice(weaponLoadout);
    weapon.name = selection.name;
    weapon.damage = selection.damage;
    weapon.shootCooldown = selection.shootCooldown;
    weapon.baseColor = selection.baseColor;
    weapon.midColor = selection.midColor;
    weapon.muzzleColor = selection.muzzleColor;
    weapon.maxAmmo = selection.ammo;
    weapon.bobOffset = 0;
    weapon.shootAnimOffset = 0;
    weapon.isHolstered = false;
    player.ammo = selection.ammo;
}

function spawnEnemiesForLevel(level) {
    enemies = [];

    const openTiles = [];
    for (let y = 1; y < MAP_SIZE - 1; y++) {
        for (let x = 1; x < MAP_SIZE - 1; x++) {
            if (map[y][x] === 0) {
                const spawnDistance = Math.hypot(x - level.spawn.x, y - level.spawn.y);
                if (spawnDistance > 2) {
                    openTiles.push({ x, y });
                }
            }
        }
    }

    const enemyCount = randomInt(level.minEnemies, level.maxEnemies);
    for (let i = 0; i < enemyCount && openTiles.length > 0; i++) {
        const position = openTiles.splice(randomInt(0, openTiles.length - 1), 1)[0];
        const typeKey = randomChoice(Object.keys(enemyTypes));
        const type = enemyTypes[typeKey];
        const healthVariance = 0.9 + Math.random() * 0.25;
        const speedVariance = 0.9 + Math.random() * 0.35;
        const damageVariance = 0.9 + Math.random() * 0.35;

        const enemy = {
            x: position.x * TILE_SIZE + TILE_SIZE / 2,
            y: position.y * TILE_SIZE + TILE_SIZE / 2,
            health: Math.round(type.health * healthVariance),
            maxHealth: Math.round(type.health * healthVariance),
            angle: 0,
            type: typeKey,
            lastShot: 0,
            mouthOpen: false,
            mouthTimer: 0,
            eyeRotation: 0,
            droolOffset: 0,
            speed: type.speed * speedVariance,
            damage: Math.round(type.damage * damageVariance),
            shootCooldown: type.shootCooldown * (0.85 + Math.random() * 0.3),
            behaviorSeed: Math.random() * 1000,
            wanderTimer: 0
        };

        enemies.push(enemy);
    }
}

function loadLevel(levelIndex, isNewRun = false) {
    currentLevelIndex = levelIndex;
    const level = LEVELS[currentLevelIndex];
    map = level.layout.map((row) => [...row]);
    player.x = level.spawn.x * TILE_SIZE;
    player.y = level.spawn.y * TILE_SIZE;
    player.angle = level.spawn.angle;
    player.kills = 0;

    if (isNewRun) {
        player.health = player.maxHealth;
        player.ammo = weapon.maxAmmo;
    } else {
        player.health = Math.min(player.maxHealth, player.health + 25);
        player.ammo = Math.min(weapon.maxAmmo, player.ammo + Math.round(weapon.maxAmmo * 0.25));
    }

    spawnEnemiesForLevel(level);
}

function startNewGame() {
    gameState.running = true;
    gameState.won = false;
    gameState.gameOver = false;
    randomizeWeaponLoadout();
    loadLevel(0, true);
}

const lightMagnitude = Math.hypot(LIGHT_DIRECTION.x, LIGHT_DIRECTION.y) || 1;
const normalizedLight = {
    x: LIGHT_DIRECTION.x / lightMagnitude,
    y: LIGHT_DIRECTION.y / lightMagnitude
};

function hexToRgb(hex) {
    const value = parseInt(hex.replace('#', ''), 16);
    return {
        r: (value >> 16) & 255,
        g: (value >> 8) & 255,
        b: value & 255
    };
}

function shadeColor(hex, factor, alpha = 1) {
    const { r, g, b } = hexToRgb(hex);
    const apply = (channel) => Math.min(255, Math.max(0, Math.round(channel * factor)));
    return `rgba(${apply(r)}, ${apply(g)}, ${apply(b)}, ${alpha})`;
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

function drawSkyAndFloor() {
    const baseSky = ctx.createLinearGradient(0, 0, 0, HORIZON);
    baseSky.addColorStop(0, '#050714');
    baseSky.addColorStop(0.4, '#0f1533');
    baseSky.addColorStop(0.75, '#141937');
    baseSky.addColorStop(1, '#1c1f3d');

    const normalizedAngle = ((player.angle % (Math.PI * 2)) + Math.PI * 2) % (Math.PI * 2);
    const time = Date.now() * 0.001;
    const skyOffset = ((normalizedAngle / (Math.PI * 2)) + time * SKY_DRIFT_SPEED) * SCREEN_WIDTH;

    ctx.save();
    ctx.translate(-skyOffset, 0);
    for (let i = -1; i <= 1; i++) {
        ctx.fillStyle = baseSky;
        ctx.fillRect(i * SCREEN_WIDTH, 0, SCREEN_WIDTH, HORIZON);

        const aurora = ctx.createLinearGradient(
            i * SCREEN_WIDTH,
            HORIZON * 0.25,
            (i + 1) * SCREEN_WIDTH,
            HORIZON * 0.65
        );
        const auroraPulse = 0.08 + Math.sin(time * 0.8) * 0.04;
        const auroraShift = Math.sin(time * AURORA_SCROLL_SPEED * 6) * 0.1 * SCREEN_WIDTH;
        aurora.addColorStop(0, `rgba(124, 150, 255, ${0.12 + auroraPulse})`);
        aurora.addColorStop(0.5, `rgba(255, 255, 255, ${0.07 + auroraPulse * 0.6})`);
        aurora.addColorStop(1, `rgba(124, 150, 255, ${0.12 + auroraPulse})`);

        ctx.fillStyle = aurora;
        ctx.fillRect(i * SCREEN_WIDTH + auroraShift, 0, SCREEN_WIDTH, HORIZON);
    }
    ctx.restore();

    const floorGradient = ctx.createLinearGradient(0, HORIZON, 0, SCREEN_HEIGHT);
    floorGradient.addColorStop(0, '#3a3a44');
    floorGradient.addColorStop(0.4, '#2a2a31');
    floorGradient.addColorStop(1, '#101015');

    ctx.fillStyle = floorGradient;
    ctx.fillRect(0, HORIZON, SCREEN_WIDTH, SCREEN_HEIGHT - HORIZON);

    for (let y = HORIZON; y < SCREEN_HEIGHT; y += FLOOR_DETAIL_STEP) {
        const depthFactor = (y - HORIZON) / (SCREEN_HEIGHT - HORIZON);
        const fog = Math.min(0.7, depthFactor * 0.95);
        const sheen = Math.max(0, 0.16 - depthFactor * 0.16);
        const parallax = Math.pow(1 - depthFactor, 2.4);
        const stripeWidth = 280 * parallax;
        const stripeX = SCREEN_WIDTH / 2 - stripeWidth / 2;

        ctx.fillStyle = `rgba(0, 0, 0, ${fog})`;
        ctx.fillRect(0, y, SCREEN_WIDTH, FLOOR_DETAIL_STEP);

        if (sheen > 0) {
            const sheenAlpha = sheen * parallax;
            ctx.fillStyle = `rgba(160, 160, 180, ${sheenAlpha})`;
            ctx.fillRect(stripeX, y, stripeWidth, 1);
        }
    }

    const groundGlow = ctx.createRadialGradient(
        SCREEN_WIDTH / 2,
        SCREEN_HEIGHT,
        SCREEN_HEIGHT * 0.05,
        SCREEN_WIDTH / 2,
        SCREEN_HEIGHT,
        SCREEN_HEIGHT * 0.55
    );
    groundGlow.addColorStop(0, 'rgba(90, 110, 140, 0.2)');
    groundGlow.addColorStop(1, 'rgba(0, 0, 0, 0)');

    ctx.fillStyle = groundGlow;
    ctx.fillRect(0, HORIZON, SCREEN_WIDTH, SCREEN_HEIGHT - HORIZON);
}

function drawWalls() {
    drawSkyAndFloor();

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
        const drawY = HORIZON - wallHeight / 2;

        const surfaceNormal = ray.side === 0
            ? { x: Math.sign(Math.cos(rayAngle)) || 1, y: 0 }
            : { x: 0, y: Math.sign(Math.sin(rayAngle)) || 1 };

        const lightInfluence = Math.max(
            0,
            surfaceNormal.x * normalizedLight.x + surfaceNormal.y * normalizedLight.y
        );
        const ambient = 0.25;
        const lightFactor = Math.min(1, ambient + lightInfluence * 0.75);

        const gradient = ctx.createLinearGradient(drawX, drawY, drawX, drawY + wallHeight);
        gradient.addColorStop(0, shadeColor(color, lightFactor + 0.1));
        gradient.addColorStop(0.65, shadeColor(color, lightFactor));
        gradient.addColorStop(1, shadeColor(color, Math.max(0.2, lightFactor - 0.12)));

        ctx.fillStyle = gradient;
        ctx.fillRect(drawX, drawY, SCREEN_WIDTH / NUM_RAYS + 1, wallHeight);

        // Add darkness based on distance
        const darkness = Math.min(distance / MAX_DEPTH, 0.75);
        ctx.fillStyle = `rgba(0, 0, 0, ${darkness})`;
        ctx.fillRect(drawX, drawY, SCREEN_WIDTH / NUM_RAYS + 1, wallHeight);

        const contactShadow = Math.min(0.45, darkness + 0.15);
        ctx.fillStyle = `rgba(0, 0, 0, ${contactShadow})`;
        ctx.fillRect(drawX, drawY + wallHeight - 3, SCREEN_WIDTH / NUM_RAYS + 1, 5);

        const rimHighlight = Math.max(0, 0.18 - darkness);
        if (rimHighlight > 0) {
            ctx.fillStyle = `rgba(255, 255, 255, ${rimHighlight * 0.15})`;
            ctx.fillRect(drawX, drawY, 1.5, wallHeight);
        }
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
            const spriteCenterX = spriteX + spriteSize / 2;
            const groundY = HORIZON + (SCREEN_HEIGHT - HORIZON) * 0.15 + Math.min(1, distance / (MAX_DEPTH * TILE_SIZE)) * (SCREEN_HEIGHT - HORIZON) * 0.45;
            const shadowWidth = spriteSize * 0.6;
            const shadowHeight = spriteSize * 0.14;
            const shadowGradient = ctx.createRadialGradient(
                spriteCenterX,
                groundY,
                shadowWidth * 0.1,
                spriteCenterX,
                groundY,
                shadowWidth * 0.6
            );
            shadowGradient.addColorStop(0, 'rgba(0, 0, 0, 0.35)');
            shadowGradient.addColorStop(1, 'rgba(0, 0, 0, 0)');

            ctx.fillStyle = shadowGradient;
            ctx.fillRect(
                spriteCenterX - shadowWidth / 2,
                groundY - shadowHeight / 2,
                shadowWidth,
                shadowHeight
            );

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

function drawVignette() {
    const vignette = ctx.createRadialGradient(
        SCREEN_WIDTH / 2,
        SCREEN_HEIGHT * 0.55,
        Math.min(SCREEN_WIDTH, SCREEN_HEIGHT) * 0.25,
        SCREEN_WIDTH / 2,
        SCREEN_HEIGHT * 0.55,
        Math.max(SCREEN_WIDTH, SCREEN_HEIGHT) * 0.7
    );

    vignette.addColorStop(0, 'rgba(0, 0, 0, 0)');
    vignette.addColorStop(1, `rgba(0, 0, 0, ${VIGNETTE_STRENGTH})`);

    ctx.fillStyle = vignette;
    ctx.fillRect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT);
}

function drawWeapon() {
    if (weapon.isHolstered) {
        return;
    }

    const weaponY = SCREEN_HEIGHT - 200 + Math.sin(weapon.bobOffset) * 10 + weapon.shootAnimOffset;
    const weaponX = SCREEN_WIDTH / 2 - 50;

    // Draw simple gun
    ctx.fillStyle = weapon.baseColor;
    ctx.fillRect(weaponX, weaponY, 100, 200);

    ctx.fillStyle = shadeColor(weapon.midColor, 1.1);
    ctx.fillRect(weaponX + 20, weaponY, 60, 150);

    ctx.fillStyle = shadeColor(weapon.baseColor, 0.6);
    ctx.fillRect(weaponX + 35, weaponY, 30, 80);

    // Muzzle flash
    if (weapon.shootAnimOffset < 0) {
        ctx.fillStyle = weapon.muzzleColor;
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
    ctx.fillText(`AMMO: ${player.ammo}/${weapon.maxAmmo}`, 20, 60);

    // Kills
    ctx.fillStyle = '#00ff00';
    ctx.fillText(`KILLS: ${player.kills}/${enemies.length}`, 20, 90);

    // Weapon state
    ctx.fillStyle = weapon.isHolstered ? '#ffaa00' : '#00ff00';
    const holsterText = weapon.isHolstered ? 'HOLSTERED' : 'READY';
    ctx.fillText(`GUN: ${weapon.name} - ${holsterText}`, 20, 120);

    ctx.fillStyle = '#7cd1ff';
    ctx.fillText(
        `LEVEL: ${currentLevelIndex + 1}/${LEVELS.length} - ${LEVELS[currentLevelIndex].name}`,
        20,
        150
    );

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
        if (currentLevelIndex < LEVELS.length - 1) {
            loadLevel(currentLevelIndex + 1);
        } else {
            gameState.won = true;
        }
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

            const surge = 1 + Math.sin((currentTime + enemy.behaviorSeed) * 0.002) * 0.2;
            const jitter = Math.sin((currentTime + enemy.behaviorSeed) * 0.0035) * 0.35;
            const moveAngle = angleToPlayer + jitter;
            const step = enemy.speed * surge;
            const newX = enemy.x + Math.cos(moveAngle) * step;
            const newY = enemy.y + Math.sin(moveAngle) * step;

            const mapX = Math.floor(newX / TILE_SIZE);
            const mapY = Math.floor(newY / TILE_SIZE);

            if (map[mapY] && map[mapY][mapX] === 0) {
                enemy.x = newX;
                enemy.y = newY;
            }

            if (distance < 220 && currentTime - enemy.lastShot > enemy.shootCooldown) {
                player.health -= enemy.damage;
                enemy.lastShot = currentTime;

                if (player.health <= 0) {
                    gameState.gameOver = true;
                }
            }
        } else if (currentTime - enemy.wanderTimer > 1200 + (enemy.behaviorSeed % 400)) {
            enemy.wanderTimer = currentTime;
            const wanderAngle = Math.random() * Math.PI * 2;
            const newX = enemy.x + Math.cos(wanderAngle) * enemy.speed * 0.6;
            const newY = enemy.y + Math.sin(wanderAngle) * enemy.speed * 0.6;

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
            enemy.health -= weapon.damage;

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
    ctx.fillText('All levels cleared!', SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 50);
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
        drawVignette();
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
