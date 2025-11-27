import * as THREE from "https://cdn.jsdelivr.net/npm/three@0.161.0/build/three.module.js";
import { PointerLockControls } from "https://cdn.jsdelivr.net/npm/three@0.161.0/examples/jsm/controls/PointerLockControls.js";

const HALL_LENGTH = 120;
const HALL_WIDTH = 22;
const PLAYER_HEIGHT = 1.8;
const PLAYER_SPEED = 9;
const PLAYER_JUMP_VELOCITY = 8;
const GRAVITY = 25;
const ZOMBIE_HEALTH = 80;
const ZOMBIE_DAMAGE = 10;
const ZOMBIE_MELEE_RANGE = 1.6;
const ZOMBIE_SPEED = 2;
const ZOMBIE_COUNT = 6;
const BOSS_HEALTH = 160;
const BOSS_DAMAGE = 15;
const BOSS_FIREBALL_INTERVAL = 3.2;
const BOSS_FIREBALL_SPEED = 6;
const PISTOL_DAMAGE = 10;
const SHOT_RANGE = 60;
const BUILDING_SPACING = 30;
const BUILDING_DEPTH = 8;
const BUILDING_WIDTH = 6;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0b0d10);

const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 300);
camera.position.set(0, PLAYER_HEIGHT, 6);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

const controls = new PointerLockControls(camera, renderer.domElement);

const clock = new THREE.Clock();
const keyState = {};
const colliders = [];
const zombies = [];
const fireballs = [];
let boss = null;

const healthText = document.getElementById("health-value");
const instructions = document.getElementById("instructions");
const startButton = document.getElementById("start");
const reticle = document.querySelector("#reticle span");
const damageOverlay = document.getElementById("damage-overlay");
const hud = document.getElementById("hud");

let playerHealth = 100;
let canShoot = true;
let aiming = false;
let onGround = false;
const playerVelocity = new THREE.Vector3();

function setupLights() {
  const ambient = new THREE.AmbientLight(0x6f7a8a, 0.6);
  scene.add(ambient);

  const directional = new THREE.DirectionalLight(0xe8f0ff, 0.9);
  directional.position.set(-5, 12, 8);
  scene.add(directional);

  const fill = new THREE.PointLight(0x8ec5ff, 0.3, 40);
  fill.position.set(0, 4, -HALL_LENGTH / 2);
  scene.add(fill);
}

function createHallway() {
  const floorGeometry = new THREE.PlaneGeometry(HALL_WIDTH, HALL_LENGTH);
  const floorMaterial = new THREE.MeshStandardMaterial({ color: 0x1f2227, roughness: 0.8, metalness: 0.05 });
  const floor = new THREE.Mesh(floorGeometry, floorMaterial);
  floor.rotation.x = -Math.PI / 2;
  floor.position.z = -HALL_LENGTH / 2;
  floor.receiveShadow = true;
  scene.add(floor);

  const wallMaterial = new THREE.MeshStandardMaterial({ color: 0x292e35, roughness: 0.5 });
  const wallHeight = 6;
  const wallThickness = 0.5;
  const wallGeometry = new THREE.BoxGeometry(wallThickness, wallHeight, HALL_LENGTH);

  const leftWall = new THREE.Mesh(wallGeometry, wallMaterial);
  leftWall.position.set(-HALL_WIDTH / 2, wallHeight / 2, -HALL_LENGTH / 2);
  scene.add(leftWall);
  colliders.push(new THREE.Box3().setFromObject(leftWall));

  const rightWall = new THREE.Mesh(wallGeometry, wallMaterial);
  rightWall.position.set(HALL_WIDTH / 2, wallHeight / 2, -HALL_LENGTH / 2);
  scene.add(rightWall);
  colliders.push(new THREE.Box3().setFromObject(rightWall));

  const backWallGeometry = new THREE.BoxGeometry(HALL_WIDTH, wallHeight, wallThickness);
  const backWall = new THREE.Mesh(backWallGeometry, wallMaterial);
  backWall.position.set(0, wallHeight / 2, 0.5);
  scene.add(backWall);
  colliders.push(new THREE.Box3().setFromObject(backWall));

  const endWall = new THREE.Mesh(backWallGeometry, wallMaterial);
  endWall.position.set(0, wallHeight / 2, -HALL_LENGTH - 0.5);
  scene.add(endWall);
  colliders.push(new THREE.Box3().setFromObject(endWall));

  const ceilingGeometry = new THREE.PlaneGeometry(HALL_WIDTH, HALL_LENGTH);
  const ceilingMaterial = new THREE.MeshStandardMaterial({ color: 0x0f1114, roughness: 0.9 });
  const ceiling = new THREE.Mesh(ceilingGeometry, ceilingMaterial);
  ceiling.position.set(0, wallHeight, -HALL_LENGTH / 2);
  ceiling.rotation.x = Math.PI / 2;
  scene.add(ceiling);
}

function createBuildings() {
  const buildingMaterial = new THREE.MeshStandardMaterial({ color: 0x2f3c4f, roughness: 0.6, metalness: 0.05 });
  const buildingHeight = 4;
  const buildingGeometry = new THREE.BoxGeometry(BUILDING_WIDTH, buildingHeight, BUILDING_DEPTH);

  for (let z = -BUILDING_SPACING; z > -HALL_LENGTH; z -= BUILDING_SPACING) {
    const offset = (HALL_WIDTH / 2 - BUILDING_WIDTH / 2 - 1.5);
    const buildingLeft = new THREE.Mesh(buildingGeometry, buildingMaterial);
    buildingLeft.position.set(-offset, buildingHeight / 2, z);
    scene.add(buildingLeft);
    colliders.push(new THREE.Box3().setFromObject(buildingLeft));

    const buildingRight = new THREE.Mesh(buildingGeometry, buildingMaterial);
    buildingRight.position.set(offset, buildingHeight / 2, z - BUILDING_DEPTH);
    scene.add(buildingRight);
    colliders.push(new THREE.Box3().setFromObject(buildingRight));
  }
}

function createHealthBar(maxHealth) {
  const group = new THREE.Group();

  const backgroundGeom = new THREE.PlaneGeometry(1.6, 0.15);
  const backgroundMat = new THREE.MeshBasicMaterial({ color: 0x330000, side: THREE.DoubleSide });
  const background = new THREE.Mesh(backgroundGeom, backgroundMat);
  group.add(background);

  const barGeom = new THREE.PlaneGeometry(1.5, 0.1);
  const barMat = new THREE.MeshBasicMaterial({ color: 0x6df76d, side: THREE.DoubleSide });
  const bar = new THREE.Mesh(barGeom, barMat);
  bar.position.z = 0.01;
  bar.position.x = -0.05;
  bar.scale.x = 1;
  group.add(bar);

  return { group, bar, maxHealth };
}

function createZombie(isBoss = false, positionZ = -20) {
  const zombieGroup = new THREE.Group();
  const bodyHeight = isBoss ? 2.6 : 1.6;
  const legHeight = isBoss ? 1.4 : 0.9;
  const bodyWidth = isBoss ? 1.1 : 0.7;

  const bodyGeom = new THREE.BoxGeometry(bodyWidth, bodyHeight, bodyWidth);
  const bodyMat = new THREE.MeshStandardMaterial({ color: isBoss ? 0x5c352d : 0x3d5c2c, roughness: 0.6 });
  const body = new THREE.Mesh(bodyGeom, bodyMat);
  body.position.y = legHeight + bodyHeight / 2;
  zombieGroup.add(body);

  const headGeom = new THREE.SphereGeometry(isBoss ? 0.55 : 0.35, 18, 18);
  const headMat = new THREE.MeshStandardMaterial({ color: 0x6a8c5a, roughness: 0.4 });
  const head = new THREE.Mesh(headGeom, headMat);
  head.position.y = legHeight + bodyHeight + (isBoss ? 0.55 : 0.4);
  zombieGroup.add(head);

  const legGeom = new THREE.BoxGeometry(bodyWidth / 2, legHeight, bodyWidth / 1.6);
  const legMat = new THREE.MeshStandardMaterial({ color: 0x2f4026, roughness: 0.7 });
  const leftLeg = new THREE.Mesh(legGeom, legMat);
  const rightLeg = new THREE.Mesh(legGeom, legMat);
  leftLeg.position.set(-bodyWidth / 4, legHeight / 2, 0);
  rightLeg.position.set(bodyWidth / 4, legHeight / 2, 0);
  zombieGroup.add(leftLeg);
  zombieGroup.add(rightLeg);

  const healthBar = createHealthBar(isBoss ? BOSS_HEALTH : ZOMBIE_HEALTH);
  healthBar.group.position.set(0, legHeight + bodyHeight + 0.9, 0);
  zombieGroup.add(healthBar.group);

  zombieGroup.position.set(0, 0, positionZ);
  scene.add(zombieGroup);

  return {
    group: zombieGroup,
    body,
    leftLeg,
    rightLeg,
    healthBar,
    health: isBoss ? BOSS_HEALTH : ZOMBIE_HEALTH,
    lastAttack: 0,
    isBoss,
  };
}

function spawnZombies() {
  for (let i = 0; i < ZOMBIE_COUNT; i += 1) {
    const laneOffset = i % 2 === 0 ? -4 : 4;
    const zPos = -15 - i * 12;
    const zombie = createZombie(false, zPos);
    zombie.group.position.x = laneOffset;
    zombies.push(zombie);
  }

  boss = createZombie(true, -HALL_LENGTH + 12);
  boss.group.scale.setScalar(1.3);
  boss.healthBar.group.position.y += 0.4;
}

function updateHealthBar(zombie) {
  const ratio = Math.max(zombie.health, 0) / zombie.healthBar.maxHealth;
  zombie.healthBar.bar.scale.x = ratio;
  zombie.healthBar.bar.position.x = -0.75 + ratio * 0.75;
  zombie.healthBar.group.lookAt(camera.position);
}

function applyDamage(target, amount) {
  target.health -= amount;
  updateHealthBar(target);
  if (target.health <= 0) {
    target.group.visible = false;
    target.isDefeated = true;
  }
}

function handleShot() {
  if (!controls.isLocked || !canShoot) return;

  const raycaster = new THREE.Raycaster();
  const direction = new THREE.Vector3();
  camera.getWorldDirection(direction);
  raycaster.set(camera.position, direction);

  const candidates = zombies
    .filter((z) => !z.isDefeated)
    .map((z) => z.body);
  if (boss && !boss.isDefeated) {
    candidates.push(boss.body);
  }

  const intersects = raycaster.intersectObjects(candidates, true);
  if (intersects.length > 0 && intersects[0].distance <= SHOT_RANGE) {
    const meshHit = intersects[0].object;
    const zombie = zombies.find((z) => z.body === meshHit) || (boss && boss.body === meshHit ? boss : null);
    if (zombie) {
      applyDamage(zombie, PISTOL_DAMAGE);
    }
  }

  canShoot = false;
  setTimeout(() => {
    canShoot = true;
  }, 300);
}

function showDamageOverlay() {
  damageOverlay.classList.add("active");
  setTimeout(() => damageOverlay.classList.remove("active"), 200);
}

function applyPlayerDamage(amount) {
  playerHealth = Math.max(playerHealth - amount, 0);
  healthText.textContent = playerHealth.toString();
  showDamageOverlay();
}

function updateZombieMovement(delta) {
  const playerPosition = controls.getObject().position.clone();
  const actors = [...zombies];
  if (boss) {
    actors.push(boss);
  }

  actors.forEach((zombie) => {
    if (zombie.isDefeated) return;
    const direction = playerPosition.clone().sub(zombie.group.position);
    const distance = direction.length();
    direction.normalize();

    const walkSpeed = zombie.isBoss ? ZOMBIE_SPEED * 0.8 : ZOMBIE_SPEED;
    const moveStep = walkSpeed * delta;
    zombie.group.position.addScaledVector(direction, moveStep);

    const stepCycle = (performance.now() / 1000) * walkSpeed * 3;
    zombie.leftLeg.rotation.x = Math.sin(stepCycle) * 0.8;
    zombie.rightLeg.rotation.x = Math.cos(stepCycle) * 0.8;

    updateHealthBar(zombie);

    const now = performance.now() / 1000;
    if (distance < (zombie.isBoss ? ZOMBIE_MELEE_RANGE + 0.4 : ZOMBIE_MELEE_RANGE) && now - zombie.lastAttack > 1) {
      applyPlayerDamage(zombie.isBoss ? BOSS_DAMAGE : ZOMBIE_DAMAGE);
      zombie.lastAttack = now;
    }
  });
}

function updateFireballs(delta) {
  if (boss && !boss.isDefeated) {
    boss.fireTimer = (boss.fireTimer || 0) + delta;
    const playerPos = controls.getObject().position.clone();
    if (boss.fireTimer >= BOSS_FIREBALL_INTERVAL) {
      const origin = boss.group.position.clone();
      origin.y += 1.6;
      const direction = playerPos.sub(origin).normalize();
      const geometry = new THREE.SphereGeometry(0.35, 12, 12);
      const material = new THREE.MeshBasicMaterial({ color: 0xff5722 });
      const fireball = new THREE.Mesh(geometry, material);
      fireball.position.copy(origin);
      scene.add(fireball);
      fireballs.push({ mesh: fireball, velocity: direction.multiplyScalar(BOSS_FIREBALL_SPEED), age: 0 });
      boss.fireTimer = 0;
    }
  }

  const playerPos = controls.getObject().position;
  for (let i = fireballs.length - 1; i >= 0; i -= 1) {
    const projectile = fireballs[i];
    projectile.mesh.position.addScaledVector(projectile.velocity, delta);
    projectile.age += delta;

    if (projectile.mesh.position.distanceTo(playerPos) < 1.1) {
      applyPlayerDamage(12);
      scene.remove(projectile.mesh);
      fireballs.splice(i, 1);
      continue;
    }

    const bounds = new THREE.Box3().setFromObject(projectile.mesh);
    const hitWall = colliders.some((box) => box.intersectsBox(bounds));
    if (projectile.age > 8 || hitWall) {
      scene.remove(projectile.mesh);
      fireballs.splice(i, 1);
    }
  }
}

function movePlayer(delta) {
  const damping = Math.exp(-4 * delta);
  playerVelocity.x *= damping;
  playerVelocity.z *= damping;

  if (keyState["KeyW"]) playerVelocity.z -= PLAYER_SPEED * delta;
  if (keyState["KeyS"]) playerVelocity.z += PLAYER_SPEED * delta;
  if (keyState["KeyA"]) playerVelocity.x -= PLAYER_SPEED * delta;
  if (keyState["KeyD"]) playerVelocity.x += PLAYER_SPEED * delta;

  if (onGround && keyState["Space"]) {
    playerVelocity.y = PLAYER_JUMP_VELOCITY;
    onGround = false;
  }

  playerVelocity.y -= GRAVITY * delta;

  const controlObject = controls.getObject();
  const oldPosition = controlObject.position.clone();
  controlObject.translateX(playerVelocity.x * delta);
  controlObject.translateY(playerVelocity.y * delta);
  controlObject.translateZ(playerVelocity.z * delta);

  if (controlObject.position.y < PLAYER_HEIGHT) {
    playerVelocity.y = 0;
    controlObject.position.y = PLAYER_HEIGHT;
    onGround = true;
  }

  const playerBox = new THREE.Box3().setFromCenterAndSize(controlObject.position.clone(), new THREE.Vector3(1.2, 2, 1.2));
  const collision = colliders.some((box) => box.intersectsBox(playerBox));
  if (collision) {
    controlObject.position.copy(oldPosition);
    playerVelocity.x = 0;
    playerVelocity.z = 0;
  }
}

function handleResize() {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
}

function animate() {
  requestAnimationFrame(animate);
  const delta = clock.getDelta();

  if (controls.isLocked) {
    movePlayer(delta);
    updateZombieMovement(delta);
    updateFireballs(delta);
  }

  camera.fov = aiming ? 60 : 75;
  camera.updateProjectionMatrix();

  renderer.render(scene, camera);
}

function setupEvents() {
  window.addEventListener("resize", handleResize);

  document.addEventListener("keydown", (event) => {
    keyState[event.code] = true;
  });

  document.addEventListener("keyup", (event) => {
    keyState[event.code] = false;
  });

  document.addEventListener("mousedown", (event) => {
    if (event.button === 0) {
      aiming = true;
      reticle.classList.add("aiming");
      if (!controls.isLocked) controls.lock();
    }
    if (event.button === 2) {
      handleShot();
    }
  });

  document.addEventListener("mouseup", (event) => {
    if (event.button === 0) {
      aiming = false;
      reticle.classList.remove("aiming");
    }
  });

  document.addEventListener("contextmenu", (event) => {
    event.preventDefault();
  });

  controls.addEventListener("lock", () => {
    instructions.classList.add("hidden");
    hud.classList.remove("hidden");
    document.getElementById("reticle").classList.remove("hidden");
  });

  controls.addEventListener("unlock", () => {
    instructions.classList.remove("hidden");
    hud.classList.add("hidden");
  });

  startButton.addEventListener("click", () => {
    controls.lock();
  });
}

function init() {
  setupLights();
  createHallway();
  createBuildings();
  spawnZombies();
  scene.add(controls.getObject());
  controls.getObject().position.set(0, PLAYER_HEIGHT, 4);
  setupEvents();
  animate();
}

init();
