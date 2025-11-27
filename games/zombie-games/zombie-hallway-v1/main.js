const PLAYER_SPEED = 12;
const PLAYER_SPRINT = 18;
const PLAYER_HEIGHT = 1.8;
const GRAVITY = 30;
const JUMP_VELOCITY = 10;
const PISTOL_DAMAGE = 10;
const RIFLE_DAMAGE = 18;
const RIFLE_COOLDOWN = 0.22;
const ZOMBIE_HEALTH = 80;
const BOSS_HEALTH = 160;
const ZOMBIE_DAMAGE = 10;
const BOSS_DAMAGE = 15;
const FIREBALL_DAMAGE = 15;
const FIREBALL_SPEED = 14;
const FIREBALL_COOLDOWN = 2.5;
const SHOOT_COOLDOWN = 0.35;
const weaponStats = {
  pistol: { damage: PISTOL_DAMAGE, cooldown: SHOOT_COOLDOWN },
  rifle: { damage: RIFLE_DAMAGE, cooldown: RIFLE_COOLDOWN },
};
const AIM_FOV = 45 * (Math.PI / 180);
const BASE_FOV = 70 * (Math.PI / 180);

let scene, camera, renderer, controls;
let worldBoxes = [];
let playerVelocityY = 0;
let lastShot = { pistol: 0, rifle: 0 };
let ammo = { pistol: 60, rifle: 90 };
let currentWeapon = 'pistol';
let playerHealth = 100;
let gameEnded = false;
let clock = new THREE.Clock();
let enemies = [];
let projectiles = [];
let bossEnemy = null;

const overlay = document.getElementById('overlay');
const startButton = document.getElementById('startButton');
const uiHealth = document.getElementById('health');
const uiBossHealth = document.getElementById('bossHealth');
const uiAmmo = document.getElementById('ammo');
const crosshair = document.getElementById('crosshair');
const damageFlash = document.getElementById('damageFlash');
const jumpscare = document.getElementById('jumpscare');
let jumpScareShown = false;

function updateAmmoUI() {
  uiAmmo.textContent = `Weapon: ${currentWeapon.toUpperCase()} | Pistol: ${ammo.pistol} | Rifle: ${ammo.rifle}`;
}

startButton.addEventListener('click', () => {
  overlay.style.display = 'none';
  updateAmmoUI();
  init();
  animate();
});

document.addEventListener('contextmenu', e => e.preventDefault());

document.addEventListener('mousedown', (e) => {
  if (!controls || !controls.isLocked) return;
  if (e.button === 0) {
    handleShoot();
  } else if (e.button === 2) {
    camera.fov = THREE.MathUtils.lerp(camera.fov, AIM_FOV, 0.8);
    camera.updateProjectionMatrix();
    crosshair.style.transform = 'translate(-50%, -50%) scale(0.7)';
  }
});

document.addEventListener('mouseup', (e) => {
  if (e.button === 2) {
    camera.fov = BASE_FOV;
    camera.updateProjectionMatrix();
    crosshair.style.transform = 'translate(-50%, -50%) scale(1)';
  }
});

function init() {
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x111111);

  camera = new THREE.PerspectiveCamera(BASE_FOV, window.innerWidth / window.innerHeight, 0.1, 1000);
  camera.position.set(0, PLAYER_HEIGHT, 0);

  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(window.innerWidth, window.innerHeight);
  document.body.appendChild(renderer.domElement);

  controls = new THREE.PointerLockControls(camera, renderer.domElement);
  renderer.domElement.addEventListener('click', () => controls.lock());

  const light = new THREE.HemisphereLight(0xffffff, 0x444444, 1.1);
  scene.add(light);

  buildCorridor();
  spawnEnemies();

  window.addEventListener('resize', onWindowResize);
}

function buildCorridor() {
  const floorGeom = new THREE.BoxGeometry(6, 0.5, 200);
  const floor = new THREE.Mesh(floorGeom, new THREE.MeshStandardMaterial({ color: 0x202020 }));
  floor.position.set(0, -0.25, 0);
  floor.receiveShadow = true;
  scene.add(floor);
  worldBoxes.push(floorGeom.boundingBox || new THREE.Box3().setFromObject(floor));

  const wallMat = new THREE.MeshStandardMaterial({ color: 0x303030 });
  const leftWall = new THREE.Mesh(new THREE.BoxGeometry(0.5, 6, 200), wallMat);
  leftWall.position.set(-3.25, 2.5, 0);
  const rightWall = leftWall.clone();
  rightWall.position.x = 3.25;
  const ceiling = new THREE.Mesh(new THREE.BoxGeometry(6, 0.5, 200), new THREE.MeshStandardMaterial({ color: 0x222222 }));
  ceiling.position.set(0, 5.75, 0);
  scene.add(leftWall, rightWall, ceiling);
  [leftWall, rightWall, ceiling].forEach(mesh => worldBoxes.push(new THREE.Box3().setFromObject(mesh)));

  // Add cover buildings along the corridor
  const coverMat = new THREE.MeshStandardMaterial({ color: 0x555555 });
  for (let i = 0; i < 6; i++) {
    const cover = new THREE.Mesh(new THREE.BoxGeometry(2, 3, 4), coverMat);
    cover.position.set((i % 2 === 0 ? -1.5 : 1.5), 1.5, 25 + i * 25);
    scene.add(cover);
    worldBoxes.push(new THREE.Box3().setFromObject(cover));
  }
}

function spawnEnemies() {
  const zombiePositions = [10, 30, 60, 90, 120, 150];
  zombiePositions.forEach((zPos, idx) => {
    const isBoss = idx === zombiePositions.length - 1;
    const enemy = createEnemy(isBoss);
    enemy.group.position.set(isBoss ? 0 : (idx % 2 === 0 ? -1 : 1), 0, zPos);
    enemies.push(enemy);
    scene.add(enemy.group);
    if (isBoss) bossEnemy = enemy;
  });
}

function createEnemy(isBoss) {
  const bodyGeom = new THREE.CapsuleGeometry(isBoss ? 0.6 : 0.45, isBoss ? 1.6 : 1.2, 6, 12);
  const body = new THREE.Mesh(bodyGeom, new THREE.MeshStandardMaterial({ color: isBoss ? 0x8c3f3f : 0x6b8a6f }));
  const health = isBoss ? BOSS_HEALTH : ZOMBIE_HEALTH;
  const group = new THREE.Group();
  group.add(body);

  const healthBarBg = new THREE.Mesh(new THREE.PlaneGeometry(1.2, 0.08), new THREE.MeshBasicMaterial({ color: 0x111111 }));
  const healthBar = new THREE.Mesh(new THREE.PlaneGeometry(1.2, 0.08), new THREE.MeshBasicMaterial({ color: 0x4caf50 }));
  healthBar.position.z = 0.02;
  const barGroup = new THREE.Group();
  barGroup.add(healthBarBg, healthBar);
  barGroup.position.set(0, isBoss ? 1.8 : 1.4, 0);
  group.add(barGroup);

  return {
    isBoss,
    group,
    health,
    maxHealth: health,
    lastAttack: 0,
    lastFire: 0,
    alive: true,
    bar: healthBar
  };
}

function updateHealthBars() {
  enemies.forEach(enemy => {
    const ratio = Math.max(enemy.health, 0) / enemy.maxHealth;
    enemy.bar.scale.x = ratio;
    enemy.bar.position.x = (ratio - 1) * 0.6;
  });
}

function handleShoot() {
  const now = clock.getElapsedTime();
  const stats = weaponStats[currentWeapon];
  if (!stats || now - lastShot[currentWeapon] < stats.cooldown || ammo[currentWeapon] <= 0 || gameEnded) return;
  lastShot[currentWeapon] = now;
  ammo[currentWeapon] -= 1;
  updateAmmoUI();

  const raycaster = new THREE.Raycaster();
  raycaster.setFromCamera(new THREE.Vector2(), camera);
  const intersects = raycaster.intersectObjects(enemies.filter(e => e.alive).map(e => e.group), true);
  if (intersects.length > 0) {
    const target = enemies.find(e => e.group === intersects[0].object.parent || e.group.children.includes(intersects[0].object));
    if (target && target.alive) {
      target.health -= stats.damage;
      if (target.health <= 0) {
        target.alive = false;
        target.group.visible = false;
      }
      uiBossHealth.textContent = bossEnemy ? `Boss: ${Math.max(bossEnemy.health, 0)}` : 'Boss: -';
    }
  }
}

function updateEnemies(delta) {
  const playerPos = controls.getObject().position;
  enemies.forEach(enemy => {
    if (!enemy.alive) return;
    const direction = new THREE.Vector3().subVectors(playerPos, enemy.group.position);
    direction.y = 0; // prevent upward drift
    if (direction.lengthSq() < 0.0001) return;
    direction.normalize();
    const moveSpeed = enemy.isBoss ? 4 : 5;
    enemy.group.position.addScaledVector(direction, moveSpeed * delta);

    // Melee damage
    if (direction.length() < 1.5) {
      const now = clock.getElapsedTime();
      if (now - enemy.lastAttack > 1) {
        applyDamage(enemy.isBoss ? BOSS_DAMAGE : ZOMBIE_DAMAGE);
        enemy.lastAttack = now;
      }
    }

    // Boss fireballs
    if (enemy.isBoss) {
      const now = clock.getElapsedTime();
      if (now - enemy.lastFire > FIREBALL_COOLDOWN) {
        spawnFireball(enemy);
        enemy.lastFire = now;
      }
    }
  });
}

function spawnFireball(enemy) {
  const geometry = new THREE.SphereGeometry(0.15, 8, 8);
  const material = new THREE.MeshBasicMaterial({ color: 0xff5522 });
  const mesh = new THREE.Mesh(geometry, material);
  mesh.position.copy(enemy.group.position).add(new THREE.Vector3(0, 1, 0));
  const dir = new THREE.Vector3().subVectors(controls.getObject().position, mesh.position).normalize();
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
    if (Math.abs(p.mesh.position.z) > 220) {
      p.alive = false;
      scene.remove(p.mesh);
    }
  });
}

function applyDamage(amount) {
  if (gameEnded) return;
  playerHealth = Math.max(0, playerHealth - amount);
  uiHealth.textContent = `Health: ${playerHealth}`;
  damageFlash.classList.add('active');
  setTimeout(() => damageFlash.classList.remove('active'), 180);
  if (playerHealth <= 0) {
    endGame('You were overrun!');
  }
}

function endGame(message) {
  if (gameEnded) return;
  gameEnded = true;
  showJumpScare(message);
}

function showJumpScare(message = 'BRAAAINS!') {
  if (jumpScareShown) return;
  jumpScareShown = true;
  jumpscare.textContent = message;
  jumpscare.classList.add('active');
  try {
    const audio = new (window.AudioContext || window.webkitAudioContext)();
    const osc = audio.createOscillator();
    const gain = audio.createGain();
    osc.frequency.value = 170;
    gain.gain.value = 0.22;
    osc.connect(gain).connect(audio.destination);
    osc.start();
    gain.gain.exponentialRampToValueAtTime(0.0001, audio.currentTime + 0.5);
    osc.stop(audio.currentTime + 0.55);
  } catch (e) {
    console.warn('Unable to play jumpscare audio', e);
  }
}

function onWindowResize() {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
}

function willCollide(pos) {
  const box = new THREE.Box3().setFromCenterAndSize(pos.clone().setY(1), new THREE.Vector3(0.6, 2, 0.6));
  return worldBoxes.some(collider => collider.intersectsBox(box));
}

function movePlayer(delta) {
  const direction = new THREE.Vector3();
  const forward = new THREE.Vector3();
  const right = new THREE.Vector3();
  controls.getDirection(forward);
  forward.y = 0; forward.normalize();
  right.crossVectors(forward, new THREE.Vector3(0, 1, 0)).normalize();

  const speed = isSprinting ? PLAYER_SPRINT : PLAYER_SPEED;
  if (moveForward) direction.add(forward);
  if (moveBackward) direction.sub(forward);
  if (moveLeft) direction.sub(right);
  if (moveRight) direction.add(right);
  if (direction.lengthSq() > 0) direction.normalize();

  const displacement = direction.multiplyScalar(speed * delta);
  const nextPos = controls.getObject().position.clone().add(displacement);
  if (!willCollide(nextPos)) controls.getObject().position.copy(nextPos);

  // gravity
  playerVelocityY -= GRAVITY * delta;
  controls.getObject().position.y += playerVelocityY * delta;
  if (controls.getObject().position.y < PLAYER_HEIGHT) {
    playerVelocityY = 0;
    controls.getObject().position.y = PLAYER_HEIGHT;
    canJump = true;
  }
}

let moveForward = false, moveBackward = false, moveLeft = false, moveRight = false;
let canJump = false;
let isSprinting = false;

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
    case 'Space': if (canJump) { playerVelocityY = JUMP_VELOCITY; canJump = false; } break;
    case 'ShiftLeft': isSprinting = true; break;
    case 'Digit1': currentWeapon = 'pistol'; updateAmmoUI(); break;
    case 'Digit2': currentWeapon = 'rifle'; updateAmmoUI(); break;
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

function animate() {
  if (gameEnded) return;
  requestAnimationFrame(animate);
  const delta = clock.getDelta();
  movePlayer(delta);
  updateEnemies(delta);
  updateProjectiles(delta);
  updateHealthBars();
  renderer.render(scene, camera);
}
