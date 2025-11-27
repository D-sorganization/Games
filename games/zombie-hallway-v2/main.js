const PLAYER_SPEED = 12;
const PLAYER_SPRINT = 18;
const PLAYER_HEIGHT = 1.8;
const JUMP_VELOCITY = 10;
const GRAVITY = 30;
const PISTOL_DAMAGE = 10;
const ZOMBIE_HEALTH = 80;
const BOSS_HEALTH = 200;
const ZOMBIE_DAMAGE = 10;
const BOSS_DAMAGE = 15;
const ATTACK_RANGE = 1.6;
const FIREBALL_DAMAGE = 15;
const FIREBALL_SPEED = 12;
const FIREBALL_COOLDOWN = 2.3;
const SHOOT_COOLDOWN = 0.35;
const BASE_FOV = 65;
const AIM_FOV = 45;

let scene, camera, renderer, controls;
let moveForward = false, moveBackward = false, moveLeft = false, moveRight = false, canJump = false, isSprinting = false;
let velocityY = 0;
let clock = new THREE.Clock();
let enemies = [];
let projectiles = [];
let ammo = 120;
let lastShot = 0;
let playerHealth = 100;
let kills = 0;
let bossRef = null;
let gameOver = false;
const colliders = [];

const startOverlay = document.getElementById('start');
const startButton = document.getElementById('play');
const uiHp = document.getElementById('hp');
const uiBoss = document.getElementById('boss');
const uiAmmo = document.getElementById('ammo');
const uiKills = document.getElementById('kills');
const crosshair = document.getElementById('crosshair');
const damageFlash = document.getElementById('damageFlash');

startButton.addEventListener('click', () => {
  startOverlay.style.display = 'none';
  init();
  animate();
});

document.addEventListener('contextmenu', (e) => e.preventDefault());

document.addEventListener('mousedown', (e) => {
  if (!controls || !controls.isLocked) return;
  if (e.button === 0) {
    // aim
    camera.fov = AIM_FOV;
    camera.updateProjectionMatrix();
    crosshair.style.transform = 'translate(-50%, -50%) scale(0.75)';
  } else if (e.button === 2) {
    shoot();
  }
});

document.addEventListener('mouseup', (e) => {
  if (e.button === 0) {
    camera.fov = BASE_FOV;
    camera.updateProjectionMatrix();
    crosshair.style.transform = 'translate(-50%, -50%) scale(1)';
  }
});

function init() {
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x0c0c0c);

  camera = new THREE.PerspectiveCamera(BASE_FOV, window.innerWidth / window.innerHeight, 0.1, 500);
  camera.position.set(0, PLAYER_HEIGHT, 0);

  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(window.innerWidth, window.innerHeight);
  document.body.appendChild(renderer.domElement);

  controls = new THREE.PointerLockControls(camera, renderer.domElement);
  renderer.domElement.addEventListener('click', () => controls.lock());

  scene.add(new THREE.HemisphereLight(0xffffff, 0x555555, 1.1));
  const dirLight = new THREE.DirectionalLight(0xffffff, 0.6);
  dirLight.position.set(5, 10, 2);
  scene.add(dirLight);

  buildLevel();
  spawnEnemyWave();

  window.addEventListener('resize', onResize);
}

function buildLevel() {
  const floorGeom = new THREE.BoxGeometry(8, 0.5, 240);
  const floor = new THREE.Mesh(floorGeom, new THREE.MeshStandardMaterial({ color: 0x202020 }));
  floor.position.set(0, -0.25, 0);
  scene.add(floor);
  colliders.push(new THREE.Box3().setFromObject(floor));

  const wallMat = new THREE.MeshStandardMaterial({ color: 0x2f2f2f });
  const wallGeom = new THREE.BoxGeometry(0.5, 6, 240);
  const leftWall = new THREE.Mesh(wallGeom, wallMat);
  leftWall.position.set(-4.25, 2.5, 0);
  const rightWall = leftWall.clone();
  rightWall.position.x = 4.25;
  scene.add(leftWall, rightWall);
  [leftWall, rightWall].forEach(w => colliders.push(new THREE.Box3().setFromObject(w)));

  const ceiling = new THREE.Mesh(new THREE.BoxGeometry(8, 0.5, 240), new THREE.MeshStandardMaterial({ color: 0x151515 }));
  ceiling.position.set(0, 5.75, 0);
  scene.add(ceiling);
  colliders.push(new THREE.Box3().setFromObject(ceiling));

  const coverMat = new THREE.MeshStandardMaterial({ color: 0x505050 });
  for (let i = 0; i < 7; i++) {
    const cover = new THREE.Mesh(new THREE.BoxGeometry(2, 3.2, 4), coverMat);
    cover.position.set(i % 2 === 0 ? -1.5 : 1.5, 1.6, 20 + i * 30);
    scene.add(cover);
    colliders.push(new THREE.Box3().setFromObject(cover));
  }
}

function spawnEnemyWave() {
  const positions = [15, 40, 70, 110, 140, 180, 215];
  positions.forEach((z, idx) => {
    const isBoss = idx === positions.length - 1;
    const enemy = buildEnemy(isBoss);
    enemy.group.position.set(isBoss ? 0 : (idx % 2 === 0 ? -2 : 2), 0, z);
    enemies.push(enemy);
    scene.add(enemy.group);
    if (isBoss) bossRef = enemy;
  });
  uiBoss.textContent = bossRef ? `Boss: ${bossRef.health}` : 'Boss: --';
}

function buildEnemy(isBoss) {
  const torso = new THREE.Mesh(new THREE.CapsuleGeometry(isBoss ? 0.7 : 0.5, isBoss ? 1.8 : 1.2, 6, 12), new THREE.MeshStandardMaterial({ color: isBoss ? 0x8c3f3f : 0x6b8a6f }));
  const group = new THREE.Group();
  group.add(torso);

  const barBg = new THREE.Mesh(new THREE.PlaneGeometry(1.4, 0.1), new THREE.MeshBasicMaterial({ color: 0x111111 }));
  const bar = new THREE.Mesh(new THREE.PlaneGeometry(1.4, 0.1), new THREE.MeshBasicMaterial({ color: 0x4caf50 }));
  bar.position.z = 0.01;
  const barWrap = new THREE.Group();
  barWrap.add(barBg, bar);
  barWrap.position.set(0, isBoss ? 2.1 : 1.6, 0);
  group.add(barWrap);

  return {
    isBoss,
    group,
    bar,
    health: isBoss ? BOSS_HEALTH : ZOMBIE_HEALTH,
    maxHealth: isBoss ? BOSS_HEALTH : ZOMBIE_HEALTH,
    lastAttack: 0,
    lastFire: 0,
    alive: true
  };
}

function shoot() {
  const now = clock.getElapsedTime();
  if (now - lastShot < SHOOT_COOLDOWN || ammo <= 0 || gameOver) return;
  lastShot = now;
  ammo -= 1;
  uiAmmo.textContent = `Ammo: ${ammo}`;

  const ray = new THREE.Raycaster();
  ray.setFromCamera(new THREE.Vector2(), camera);
  const hits = ray.intersectObjects(enemies.filter(e => e.alive).map(e => e.group), true);
  if (hits.length === 0) return;
  const enemy = enemies.find(e => e.group === hits[0].object.parent || e.group.children.includes(hits[0].object));
  if (!enemy || !enemy.alive) return;
  enemy.health -= PISTOL_DAMAGE;
  enemy.bar.scale.x = Math.max(enemy.health, 0) / enemy.maxHealth;
  enemy.bar.position.x = (Math.max(enemy.health, 0) / enemy.maxHealth - 1) * 0.7;
  if (enemy.health <= 0) {
    enemy.alive = false;
    enemy.group.visible = false;
    kills += 1;
    uiKills.textContent = `Kills: ${kills}`;
  }
  if (enemy.isBoss) {
    uiBoss.textContent = `Boss: ${Math.max(enemy.health, 0)}`;
  }
}

function updateEnemies(delta) {
  const playerPos = controls.getObject().position.clone();
  enemies.forEach(enemy => {
    if (!enemy.alive) return;
    const dir = new THREE.Vector3().subVectors(playerPos, enemy.group.position);
    dir.y = 0;
    const distance = dir.length();
    if (distance > 0) dir.normalize();
    const moveSpeed = enemy.isBoss ? 4 : 5.2;
    enemy.group.position.addScaledVector(dir, moveSpeed * delta);

    if (distance < ATTACK_RANGE) {
      const now = clock.getElapsedTime();
      if (now - enemy.lastAttack > 1) {
        applyDamage(enemy.isBoss ? BOSS_DAMAGE : ZOMBIE_DAMAGE);
        enemy.lastAttack = now;
      }
    }

    if (enemy.isBoss) {
      const now = clock.getElapsedTime();
      if (now - enemy.lastFire > FIREBALL_COOLDOWN) {
        launchFireball(enemy, playerPos);
        enemy.lastFire = now;
      }
    }
  });
}

function launchFireball(enemy, targetPos) {
  const geometry = new THREE.SphereGeometry(0.16, 10, 10);
  const material = new THREE.MeshBasicMaterial({ color: 0xff6633 });
  const mesh = new THREE.Mesh(geometry, material);
  mesh.position.copy(enemy.group.position).add(new THREE.Vector3(0, 1.4, 0));
  const dir = new THREE.Vector3().subVectors(targetPos, mesh.position).setY(0).normalize();
  projectiles.push({ mesh, dir, alive: true });
  scene.add(mesh);
}

function updateProjectiles(delta) {
  projectiles = projectiles.filter(p => p.alive);
  projectiles.forEach(p => {
    p.mesh.position.addScaledVector(p.dir, FIREBALL_SPEED * delta);
    if (p.mesh.position.distanceTo(controls.getObject().position) < 1) {
      applyDamage(FIREBALL_DAMAGE);
      p.alive = false;
      scene.remove(p.mesh);
    }
    if (Math.abs(p.mesh.position.z) > 260) {
      p.alive = false;
      scene.remove(p.mesh);
    }
  });
}

function applyDamage(amount) {
  if (gameOver) return;
  playerHealth = Math.max(0, playerHealth - amount);
  uiHp.textContent = `HP: ${playerHealth}`;
  damageFlash.classList.add('active');
  setTimeout(() => damageFlash.classList.remove('active'), 150);
  if (playerHealth <= 0) {
    endGame('You were overrun. Refresh to retry.');
  }
}

function endGame(message) {
  if (gameOver) return;
  gameOver = true;
  alert(message);
}

function willCollide(nextPos) {
  const box = new THREE.Box3().setFromCenterAndSize(nextPos.clone().setY(1), new THREE.Vector3(0.6, 2, 0.6));
  return colliders.some(c => c.intersectsBox(box));
}

function movePlayer(delta) {
  const forward = new THREE.Vector3();
  controls.getDirection(forward);
  forward.y = 0; forward.normalize();
  const right = new THREE.Vector3().crossVectors(forward, new THREE.Vector3(0, 1, 0)).normalize();

  const moveDir = new THREE.Vector3();
  if (moveForward) moveDir.add(forward);
  if (moveBackward) moveDir.sub(forward);
  if (moveLeft) moveDir.sub(right);
  if (moveRight) moveDir.add(right);
  if (moveDir.lengthSq() > 0) moveDir.normalize();

  const speed = isSprinting ? PLAYER_SPRINT : PLAYER_SPEED;
  const displacement = moveDir.clone().multiplyScalar(speed * delta);
  const nextPos = controls.getObject().position.clone().add(displacement);
  if (!willCollide(nextPos)) controls.getObject().position.copy(nextPos);

  velocityY -= GRAVITY * delta;
  controls.getObject().position.y += velocityY * delta;
  if (controls.getObject().position.y < PLAYER_HEIGHT) {
    velocityY = 0;
    controls.getObject().position.y = PLAYER_HEIGHT;
    canJump = true;
  }
}

document.addEventListener('keydown', (event) => {
  switch (event.code) {
    case 'ArrowUp':
    case 'KeyW': moveForward = true; break;
    case 'ArrowLeft':
    case 'KeyA': moveLeft = true; break;
    case 'ArrowDown':
    case 'KeyS': moveBackward = true; break;
    case 'ArrowRight':
    case 'KeyD': moveRight = true; break;
    case 'Space': if (canJump) { velocityY = JUMP_VELOCITY; canJump = false; } break;
    case 'ShiftLeft': isSprinting = true; break;
  }
});

document.addEventListener('keyup', (event) => {
  switch (event.code) {
    case 'ArrowUp':
    case 'KeyW': moveForward = false; break;
    case 'ArrowLeft':
    case 'KeyA': moveLeft = false; break;
    case 'ArrowDown':
    case 'KeyS': moveBackward = false; break;
    case 'ArrowRight':
    case 'KeyD': moveRight = false; break;
    case 'ShiftLeft': isSprinting = false; break;
  }
});

function onResize() {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
}

function animate() {
  if (gameOver) return;
  requestAnimationFrame(animate);
  const delta = clock.getDelta();
  movePlayer(delta);
  updateEnemies(delta);
  updateProjectiles(delta);
  renderer.render(scene, camera);
}
