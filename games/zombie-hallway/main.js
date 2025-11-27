import * as THREE from 'https://unpkg.com/three@0.160.0/build/three.module.js';
import { PointerLockControls } from 'https://unpkg.com/three@0.160.0/examples/jsm/controls/PointerLockControls.js';

const PLAYER_RADIUS = 1;
const PLAYER_BASE_SPEED = 10;
const PLAYER_SPRINT_MULTIPLIER = 1.35;
const PLAYER_HEALTH_MAX = 100;
const ZOMBIE_DAMAGE = 10;
const ZOMBIE_HEALTH = 80;
const ZOMBIE_SPEED = 3.2;
const ZOMBIE_ATTACK_RANGE = 2.4;
const ZOMBIE_ATTACK_COOLDOWN = 1.1;
const PISTOL_DAMAGE = 10;
const HALLWAY_LENGTH = 220;
const HALLWAY_WIDTH = 24;
const HALLWAY_HEIGHT = 14;
const BOSS_HEALTH = ZOMBIE_HEALTH * 2;
const BOSS_FIREBALL_INTERVAL = 3.5;
const FIREBALL_DAMAGE = 15;
const FIREBALL_SPEED = 7;

const canvasRenderer = new THREE.WebGLRenderer({ antialias: true });
canvasRenderer.setPixelRatio(window.devicePixelRatio);
canvasRenderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(canvasRenderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x111115);

const camera = new THREE.PerspectiveCamera(
  75,
  window.innerWidth / window.innerHeight,
  0.1,
  500
);
const controls = new PointerLockControls(camera, document.body);
controls.getObject().position.set(0, 2, HALLWAY_LENGTH * 0.45);
scene.add(controls.getObject());

const hemiLight = new THREE.HemisphereLight(0xa0a0ff, 0x404025, 0.8);
scene.add(hemiLight);
const dirLight = new THREE.DirectionalLight(0xffffff, 0.65);
dirLight.position.set(12, 18, 10);
scene.add(dirLight);

const obstacles = [];
const enemies = [];
const fireballs = [];

const uiHealth = document.getElementById('health');
const uiBossHealth = document.getElementById('boss-health');
const crosshair = document.getElementById('crosshair');
const startOverlay = document.getElementById('start-overlay');
const startButton = document.getElementById('start');

let playerHealth = PLAYER_HEALTH_MAX;
let isAiming = false;
let moveForward = false;
let moveBackward = false;
let moveLeft = false;
let moveRight = false;
let isJumping = false;
let velocityY = 0;
let bossEnemy = null;

const tmpBox = new THREE.Box3();
const tmpVec = new THREE.Vector3();
const clock = new THREE.Clock();

function addObstacle(mesh) {
  mesh.updateMatrixWorld(true);
  const box = new THREE.Box3().setFromObject(mesh);
  obstacles.push(box);
}

function buildHallway() {
  const floorGeom = new THREE.BoxGeometry(HALLWAY_WIDTH, 1, HALLWAY_LENGTH);
  const wallGeom = new THREE.BoxGeometry(1, HALLWAY_HEIGHT, HALLWAY_LENGTH);
  const ceilingGeom = new THREE.BoxGeometry(HALLWAY_WIDTH, 1, HALLWAY_LENGTH);
  const floorMat = new THREE.MeshStandardMaterial({ color: 0x2c2c30 });
  const wallMat = new THREE.MeshStandardMaterial({ color: 0x1b1b1f, roughness: 0.4 });
  const ceilingMat = new THREE.MeshStandardMaterial({ color: 0x15151b });

  const floor = new THREE.Mesh(floorGeom, floorMat);
  floor.position.set(0, -0.5, 0);
  floor.receiveShadow = true;
  scene.add(floor);
  addObstacle(floor);

  const ceiling = new THREE.Mesh(ceilingGeom, ceilingMat);
  ceiling.position.set(0, HALLWAY_HEIGHT, 0);
  scene.add(ceiling);
  addObstacle(ceiling);

  const wallLeft = new THREE.Mesh(wallGeom, wallMat);
  wallLeft.position.set(-HALLWAY_WIDTH * 0.5, HALLWAY_HEIGHT * 0.5 - 0.5, 0);
  scene.add(wallLeft);
  addObstacle(wallLeft);

  const wallRight = new THREE.Mesh(wallGeom, wallMat);
  wallRight.position.set(HALLWAY_WIDTH * 0.5, HALLWAY_HEIGHT * 0.5 - 0.5, 0);
  scene.add(wallRight);
  addObstacle(wallRight);

  const buildingMat = new THREE.MeshStandardMaterial({ color: 0x3b3b45, roughness: 0.6 });
  const buildingPositions = [-60, -110, -150];
  buildingPositions.forEach((zPos, index) => {
    const width = 6 + index * 2;
    const depth = 8;
    const height = 6 + index;
    const geom = new THREE.BoxGeometry(width, height, depth);
    const mesh = new THREE.Mesh(geom, buildingMat);
    mesh.position.set(index % 2 === 0 ? -6 : 6, height / 2 - 0.5, zPos);
    scene.add(mesh);
    addObstacle(mesh);
  });
}

function createZombieMesh(isBoss = false) {
  const group = new THREE.Group();
  const bodyHeight = isBoss ? 6 : 3;
  const bodyRadius = isBoss ? 1.4 : 0.9;

  const skinTone = isBoss ? 0x6d3f2e : 0x6c5b4c;
  const clothes = isBoss ? 0x9a0000 : 0x2e7d32;

  const body = new THREE.Mesh(
    new THREE.CapsuleGeometry(bodyRadius, bodyHeight - 1.2, 6, 8),
    new THREE.MeshStandardMaterial({ color: clothes, roughness: 0.8 })
  );
  body.position.y = bodyHeight * 0.5;
  group.add(body);

  const head = new THREE.Mesh(
    new THREE.SphereGeometry(bodyRadius * 0.75, 16, 14),
    new THREE.MeshStandardMaterial({ color: skinTone, roughness: 0.6 })
  );
  head.position.set(0, body.position.y + bodyHeight * 0.45, 0);
  group.add(head);

  const legGeom = new THREE.BoxGeometry(bodyRadius * 0.7, bodyHeight * 0.7, bodyRadius * 0.7);
  const legMat = new THREE.MeshStandardMaterial({ color: clothes, roughness: 0.9 });
  const leftLeg = new THREE.Mesh(legGeom, legMat);
  const rightLeg = new THREE.Mesh(legGeom, legMat);
  leftLeg.position.set(-bodyRadius * 0.5, bodyHeight * 0.15, 0);
  rightLeg.position.set(bodyRadius * 0.5, bodyHeight * 0.15, 0);
  group.add(leftLeg);
  group.add(rightLeg);

  const healthBar = buildHealthBar(isBoss);
  healthBar.position.set(0, head.position.y + (isBoss ? 2 : 1.2), 0);
  group.add(healthBar);

  return { group, body, head, leftLeg, rightLeg, healthBar };
}

function buildHealthBar(isBoss = false) {
  const barGroup = new THREE.Group();
  const width = isBoss ? 4 : 2;
  const height = 0.2;
  const background = new THREE.Mesh(
    new THREE.PlaneGeometry(width, height),
    new THREE.MeshBasicMaterial({ color: 0x303030 })
  );
  const foreground = new THREE.Mesh(
    new THREE.PlaneGeometry(width, height),
    new THREE.MeshBasicMaterial({ color: isBoss ? 0xff4d4d : 0x4caf50 })
  );
  foreground.position.z = 0.01;
  foreground.scale.x = 1;
  barGroup.add(background);
  barGroup.add(foreground);
  barGroup.foreground = foreground;
  return barGroup;
}

class Enemy {
  constructor(position, isBoss = false) {
    this.isBoss = isBoss;
    this.maxHealth = isBoss ? BOSS_HEALTH : ZOMBIE_HEALTH;
    this.health = this.maxHealth;
    this.speed = isBoss ? ZOMBIE_SPEED * 0.7 : ZOMBIE_SPEED;
    this.attackDamage = isBoss ? ZOMBIE_DAMAGE * 1.5 : ZOMBIE_DAMAGE;
    this.attackCooldown = isBoss ? ZOMBIE_ATTACK_COOLDOWN * 0.8 : ZOMBIE_ATTACK_COOLDOWN;
    this.lastAttack = 0;
    this.fireCooldown = 0;
    this.attackRange = ZOMBIE_ATTACK_RANGE + (isBoss ? 0.6 : 0);
    const meshParts = createZombieMesh(isBoss);
    this.group = meshParts.group;
    this.body = meshParts.body;
    this.head = meshParts.head;
    this.leftLeg = meshParts.leftLeg;
    this.rightLeg = meshParts.rightLeg;
    this.healthBar = meshParts.healthBar;
    this.hitMesh = meshParts.body;
    this.group.position.copy(position);
  }

  update(delta, time, targetPosition) {
    const direction = tmpVec.copy(targetPosition).sub(this.group.position);
    const distance = direction.length();
    if (distance > 0.1) {
      direction.normalize();
      const speedMultiplier = Math.min(1.2, distance / 12);
      const moveDistance = this.speed * speedMultiplier * delta;
      direction.multiplyScalar(moveDistance);
      const nextPos = tmpVec.copy(this.group.position).add(direction);
      if (!willCollide(nextPos)) {
        this.group.position.copy(nextPos);
      }
      this.animateLegs(time, moveDistance * 8);
      this.group.lookAt(targetPosition.x, this.group.position.y, targetPosition.z);
    }

    this.healthBar.lookAt(camera.position);

    if (distance < this.attackRange && time - this.lastAttack > this.attackCooldown) {
      this.lastAttack = time;
      applyDamageToPlayer(this.attackDamage);
    }

    if (this.isBoss) {
      this.fireCooldown -= delta;
      if (this.fireCooldown <= 0 && distance < 80) {
        this.fireCooldown = BOSS_FIREBALL_INTERVAL;
        launchFireball(this.group.position, targetPosition);
      }
    }
  }

  animateLegs(time, strideSpeed) {
    const swing = Math.sin(time * strideSpeed) * 0.6;
    this.leftLeg.rotation.x = swing;
    this.rightLeg.rotation.x = -swing;
  }

  applyDamage(amount) {
    this.health = Math.max(0, this.health - amount);
    const ratio = this.health / this.maxHealth;
    this.healthBar.foreground.scale.x = Math.max(0.001, ratio);
    this.healthBar.foreground.position.x = -(1 - ratio) * (this.healthBar.foreground.geometry.parameters.width / 2);
  }
}

function willCollide(position) {
  for (const box of obstacles) {
    const closestX = Math.max(box.min.x, Math.min(position.x, box.max.x));
    const closestY = Math.max(box.min.y, Math.min(position.y, box.max.y));
    const closestZ = Math.max(box.min.z, Math.min(position.z, box.max.z));
    const dx = position.x - closestX;
    const dy = position.y - closestY;
    const dz = position.z - closestZ;
    if (dx * dx + dy * dy + dz * dz < PLAYER_RADIUS * PLAYER_RADIUS) {
      return true;
    }
  }
  return false;
}

function addZombies() {
  const positions = [
    new THREE.Vector3(0, 0, 30),
    new THREE.Vector3(-5, 0, -20),
    new THREE.Vector3(6, 0, -70),
    new THREE.Vector3(-4, 0, -120),
  ];
  positions.forEach((pos) => {
    const enemy = new Enemy(pos, false);
    enemies.push(enemy);
    scene.add(enemy.group);
  });

  bossEnemy = new Enemy(new THREE.Vector3(0, 0, -HALLWAY_LENGTH * 0.45), true);
  enemies.push(bossEnemy);
  scene.add(bossEnemy.group);
}

function applyDamageToPlayer(amount) {
  playerHealth = Math.max(0, playerHealth - amount);
  uiHealth.textContent = `${playerHealth}`;
  if (playerHealth <= 0) {
    endGame('You were overrun! Refresh to try again.');
  }
}

function endGame(message) {
  alert(message);
  startOverlay.classList.remove('hidden');
  controls.unlock();
  isAiming = false;
  crosshair.classList.remove('aiming');
}

function launchFireball(origin, target) {
  const direction = new THREE.Vector3().subVectors(target, origin).normalize();
  const sphere = new THREE.Mesh(
    new THREE.SphereGeometry(0.6, 12, 10),
    new THREE.MeshStandardMaterial({ color: 0xff6d00, emissive: 0xff3d00 })
  );
  const spawn = origin.clone();
  spawn.y += 2;
  sphere.position.copy(spawn);
  scene.add(sphere);
  fireballs.push({ mesh: sphere, velocity: direction.multiplyScalar(FIREBALL_SPEED), born: clock.getElapsedTime() });
}

function updateFireballs(delta) {
  const playerPos = controls.getObject().position;
  for (let i = fireballs.length - 1; i >= 0; i -= 1) {
    const fireball = fireballs[i];
    fireball.mesh.position.addScaledVector(fireball.velocity, delta);
    if (fireball.mesh.position.distanceTo(playerPos) < 2) {
      applyDamageToPlayer(FIREBALL_DAMAGE);
      scene.remove(fireball.mesh);
      fireballs.splice(i, 1);
      continue;
    }
    if (clock.getElapsedTime() - fireball.born > 8) {
      scene.remove(fireball.mesh);
      fireballs.splice(i, 1);
    }
  }
}

function updateEnemies(delta, elapsedTime) {
  const playerPos = controls.getObject().position;
  enemies.forEach((enemy) => enemy.update(delta, elapsedTime, playerPos));
  if (bossEnemy) {
    uiBossHealth.textContent = bossEnemy.health > 0 ? `${bossEnemy.health}` : 'Defeated';
  }
}

function handleShooting() {
  const raycaster = new THREE.Raycaster();
  const origin = new THREE.Vector3();
  origin.copy(camera.position);
  raycaster.set(origin, camera.getWorldDirection(new THREE.Vector3()));

  const hitTargets = [];
  enemies.forEach((enemy) => {
    if (enemy.health <= 0) return;
    tmpBox.setFromObject(enemy.hitMesh);
    const intersection = raycaster.ray.intersectBox(tmpBox, new THREE.Vector3());
    if (intersection) {
      hitTargets.push({ enemy, point: intersection });
    }
  });

  if (hitTargets.length === 0) return;
  hitTargets.sort((a, b) =>
    camera.position.distanceTo(a.point) - camera.position.distanceTo(b.point)
  );
  const target = hitTargets[0].enemy;
  target.applyDamage(PISTOL_DAMAGE);
  if (target.health <= 0) {
    scene.remove(target.group);
  }
}

function onMouseDown(event) {
  if (event.button === 0) {
    controls.lock();
  }
  if (event.button === 2) {
    event.preventDefault();
    handleShooting();
  }
}

function setupInput() {
  const onKeyDown = (event) => {
    switch (event.code) {
      case 'ArrowUp':
      case 'KeyW':
        moveForward = true;
        break;
      case 'ArrowLeft':
      case 'KeyA':
        moveLeft = true;
        break;
      case 'ArrowDown':
      case 'KeyS':
        moveBackward = true;
        break;
      case 'ArrowRight':
      case 'KeyD':
        moveRight = true;
        break;
      case 'Space':
        if (!isJumping) {
          isJumping = true;
          velocityY = 8;
        }
        break;
    }
  };

  const onKeyUp = (event) => {
    switch (event.code) {
      case 'ArrowUp':
      case 'KeyW':
        moveForward = false;
        break;
      case 'ArrowLeft':
      case 'KeyA':
        moveLeft = false;
        break;
      case 'ArrowDown':
      case 'KeyS':
        moveBackward = false;
        break;
      case 'ArrowRight':
      case 'KeyD':
        moveRight = false;
        break;
    }
  };

  document.addEventListener('keydown', onKeyDown);
  document.addEventListener('keyup', onKeyUp);
  document.addEventListener('mousedown', onMouseDown);
  document.addEventListener('contextmenu', (e) => e.preventDefault());
  controls.addEventListener('lock', () => {
    isAiming = true;
    crosshair.classList.add('aiming');
    startOverlay.classList.add('hidden');
  });
  controls.addEventListener('unlock', () => {
    isAiming = false;
    crosshair.classList.remove('aiming');
  });
}

function updatePlayer(delta) {
  if (!isAiming) return;
  const direction = new THREE.Vector3();
  direction.z = Number(moveForward) - Number(moveBackward);
  direction.x = Number(moveRight) - Number(moveLeft);
  direction.normalize();

  const speed = PLAYER_BASE_SPEED * (moveForward && moveRight ? 0.9 : 1);
  const sprint = moveForward && moveLeft ? PLAYER_SPRINT_MULTIPLIER : 1;
  const moveDistance = speed * sprint * delta;

  if (direction.lengthSq() > 0) {
    const move = direction.applyQuaternion(camera.quaternion);
    move.y = 0;
    move.normalize().multiplyScalar(moveDistance);
    const nextPos = tmpVec.copy(controls.getObject().position).add(move);
    if (!willCollide(nextPos)) {
      controls.getObject().position.copy(nextPos);
    }
  }

  velocityY -= 20 * delta;
  const nextY = controls.getObject().position.y + velocityY * delta;
  if (nextY <= 2) {
    velocityY = 0;
    isJumping = false;
    controls.getObject().position.y = 2;
  } else {
    controls.getObject().position.y = nextY;
  }
}

function resizeRenderer() {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  canvasRenderer.setSize(window.innerWidth, window.innerHeight);
}

function animate() {
  requestAnimationFrame(animate);
  const delta = clock.getDelta();
  const elapsed = clock.getElapsedTime();
  updatePlayer(delta);
  updateEnemies(delta, elapsed);
  updateFireballs(delta);
  canvasRenderer.render(scene, camera);
}

function init() {
  buildHallway();
  addZombies();
  setupInput();
  resizeRenderer();
  window.addEventListener('resize', resizeRenderer);
  uiHealth.textContent = `${playerHealth}`;
  animate();
}

startButton.addEventListener('click', () => {
  startOverlay.classList.add('hidden');
  controls.lock();
});

init();
