/**
 * @file test_core_game_ai.cpp
 * @brief Tests for core (Entity, AABB, Transform, Projectile), game (Combat),
 *        and ai (NavigationSystem) modules.
 *
 * CPU-only tests — no GL context required.
 *
 * Compile:
 *   g++ -std=c++17 -DNDEBUG -I.. tests/test_core_game_ai.cpp -o
 * tests/test_core_game_ai
 */

#include <cmath>
#include <cstdlib>
#include <iostream>
#include <vector>

// ── Headers under test ──────────────────────────────────────────────────────
#include "../core/AABB.h"
#include "../core/Entity.h"
#include "../core/Projectile.h"
#include "../core/Transform.h"

#include "../game/Combat.h"

#include "../ai/NavigationSystem.h"

// ── Simple Test Framework (same as test_loaders.cpp) ────────────────────────

static int g_passed = 0;
static int g_failed = 0;
static int g_total = 0;

#define CHECK(cond)                                                            \
  do {                                                                         \
    g_total++;                                                                 \
    if (!(cond)) {                                                             \
      std::cerr << "  FAIL: " << #cond << "  [" << __FILE__ << ":" << __LINE__ \
                << "]" << std::endl;                                           \
      g_failed++;                                                              \
    } else {                                                                   \
      g_passed++;                                                              \
    }                                                                          \
  } while (0)

#define CHECK_APPROX(a, b, eps)                                                \
  do {                                                                         \
    g_total++;                                                                 \
    if (std::abs((a) - (b)) > (eps)) {                                         \
      std::cerr << "  FAIL: " << #a << " ~ " << #b << "  (got " << (a)         \
                << " vs " << (b) << ", eps=" << (eps) << ")  [" << __FILE__    \
                << ":" << __LINE__ << "]" << std::endl;                        \
      g_failed++;                                                              \
    } else {                                                                   \
      g_passed++;                                                              \
    }                                                                          \
  } while (0)

#define SECTION(name) std::cout << "  [" << name << "]" << std::endl

// ═══════════════════════════════════════════════════════════════════════════
// AABB Tests
// ═══════════════════════════════════════════════════════════════════════════

void test_aabb() {
  std::cout << "[Test] AABB\n";
  using qe::core::AABB;
  using qe::math::Vec3;

  SECTION("from_center uniform");
  {
    AABB box = AABB::from_center(Vec3(0, 0, 0), 1.0f);
    CHECK_APPROX(box.min.x, -1.0f, 1e-6f);
    CHECK_APPROX(box.max.x, 1.0f, 1e-6f);
    CHECK_APPROX(box.min.y, -1.0f, 1e-6f);
    CHECK_APPROX(box.max.y, 1.0f, 1e-6f);
  }

  SECTION("from_center with half-extents");
  {
    AABB box = AABB::from_center(Vec3(5, 5, 5), Vec3(1, 2, 3));
    CHECK_APPROX(box.min.x, 4.0f, 1e-6f);
    CHECK_APPROX(box.max.z, 8.0f, 1e-6f);
  }

  SECTION("center and size");
  {
    AABB box(Vec3(2, 4, 6), Vec3(8, 10, 12));
    Vec3 c = box.center();
    CHECK_APPROX(c.x, 5.0f, 1e-6f);
    CHECK_APPROX(c.y, 7.0f, 1e-6f);
    Vec3 s = box.size();
    CHECK_APPROX(s.x, 6.0f, 1e-6f);
    CHECK_APPROX(s.z, 6.0f, 1e-6f);
  }

  SECTION("contains point inside");
  {
    AABB box = AABB::from_center(Vec3(0, 0, 0), 2.0f);
    CHECK(box.contains(Vec3(0, 0, 0)));
    CHECK(box.contains(Vec3(1.5f, 1.5f, 1.5f)));
  }

  SECTION("contains point outside");
  {
    AABB box = AABB::from_center(Vec3(0, 0, 0), 1.0f);
    CHECK(!box.contains(Vec3(2, 0, 0)));
    CHECK(!box.contains(Vec3(0, -2, 0)));
  }

  SECTION("intersects overlapping");
  {
    AABB a = AABB::from_center(Vec3(0, 0, 0), 1.0f);
    AABB b = AABB::from_center(Vec3(1, 0, 0), 1.0f);
    CHECK(a.intersects(b));
    CHECK(b.intersects(a));
  }

  SECTION("intersects non-overlapping");
  {
    AABB a = AABB::from_center(Vec3(0, 0, 0), 1.0f);
    AABB b = AABB::from_center(Vec3(5, 0, 0), 1.0f);
    CHECK(!a.intersects(b));
  }

  SECTION("ray_intersect hit");
  {
    AABB box = AABB::from_center(Vec3(5, 0, 0), 1.0f);
    float t = 0;
    bool hit = box.ray_intersect(Vec3(0, 0, 0), Vec3(1, 0, 0).normalized(), t);
    CHECK(hit);
    CHECK_APPROX(t, 4.0f, 1e-4f); // Hit near face of box at x=4
  }

  SECTION("ray_intersect miss");
  {
    AABB box = AABB::from_center(Vec3(5, 0, 0), 1.0f);
    float t = 0;
    bool hit = box.ray_intersect(Vec3(0, 0, 0), Vec3(0, 1, 0).normalized(), t);
    CHECK(!hit);
  }

  SECTION("ray_intersect behind origin");
  {
    AABB box = AABB::from_center(Vec3(-5, 0, 0), 1.0f);
    float t = 0;
    bool hit = box.ray_intersect(Vec3(0, 0, 0), Vec3(1, 0, 0).normalized(), t);
    CHECK(!hit); // Box is behind ray
  }

  SECTION("transformed with scale");
  {
    AABB box = AABB::from_center(Vec3(0, 0, 0), 1.0f);
    AABB scaled = box.transformed(Vec3(10, 0, 0), Vec3(2, 2, 2));
    CHECK_APPROX(scaled.center().x, 10.0f, 1e-5f);
    CHECK_APPROX(scaled.size().x, 4.0f, 1e-5f);
  }

  SECTION("transformed with negative scale");
  {
    AABB box(Vec3(1, 1, 1), Vec3(3, 3, 3));
    AABB flipped = box.transformed(Vec3(0, 0, 0), Vec3(-1, 1, 1));
    CHECK(flipped.min.x <= flipped.max.x); // min < max ensured
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Entity Tests
// ═══════════════════════════════════════════════════════════════════════════

void test_entity() {
  std::cout << "[Test] Entity\n";
  using qe::core::Entity;
  using qe::math::Vec3;

  SECTION("default construction");
  {
    Entity e;
    CHECK(e.alive);
    CHECK_APPROX(e.health, 100.0f, 1e-6f);
    CHECK_APPROX(e.max_health, 100.0f, 1e-6f);
    CHECK(e.destructible);
  }

  SECTION("take_damage reduces health");
  {
    Entity e;
    bool killed = e.take_damage(30.0f);
    CHECK(!killed);
    CHECK_APPROX(e.health, 70.0f, 1e-6f);
    CHECK(e.alive);
    CHECK(e.hit_flash > 0.0f);
  }

  SECTION("take_damage kills at zero");
  {
    Entity e;
    bool killed = e.take_damage(100.0f);
    CHECK(killed);
    CHECK_APPROX(e.health, 0.0f, 1e-6f);
    CHECK(!e.alive);
  }

  SECTION("take_damage overkill clamps");
  {
    Entity e;
    e.take_damage(200.0f);
    CHECK_APPROX(e.health, 0.0f, 1e-6f);
  }

  SECTION("dead entity ignores damage");
  {
    Entity e;
    e.take_damage(100.0f);
    bool result = e.take_damage(50.0f);
    CHECK(!result);
    CHECK_APPROX(e.health, 0.0f, 1e-6f);
  }

  SECTION("indestructible ignores damage");
  {
    Entity e;
    e.destructible = false;
    bool result = e.take_damage(50.0f);
    CHECK(!result);
    CHECK_APPROX(e.health, 100.0f, 1e-6f);
  }

  SECTION("hit_flash decays with update");
  {
    Entity e;
    e.take_damage(10.0f);
    CHECK(e.hit_flash > 0.0f);
    e.update(0.5f); // 0.5 seconds > 0.3 flash duration
    CHECK_APPROX(e.hit_flash, 0.0f, 1e-6f);
  }

  SECTION("respawn restores health and position");
  {
    Entity e;
    e.spawn_position = Vec3(5, 0, 5);
    e.position = Vec3(10, 0, 10);
    e.take_damage(100.0f);
    e.respawn();
    CHECK(e.alive);
    CHECK_APPROX(e.health, 100.0f, 1e-6f);
    CHECK_APPROX(e.position.x, 5.0f, 1e-6f);
    CHECK_APPROX(e.position.z, 5.0f, 1e-6f);
  }

  SECTION("health_fraction");
  {
    Entity e;
    e.take_damage(25.0f);
    CHECK_APPROX(e.health_fraction(), 0.75f, 1e-6f);
  }

  SECTION("update triggers respawn after delay");
  {
    Entity e;
    e.respawn_delay = 1.0f;
    e.take_damage(100.0f);
    CHECK(!e.alive);
    e.update(0.5f);
    CHECK(!e.alive); // Not enough time
    e.update(0.6f);  // Total 1.1s > 1.0s delay
    CHECK(e.alive);  // Respawned
  }

  SECTION("world_bounds applies position and scale");
  {
    Entity e;
    e.position = Vec3(10, 0, 0);
    e.scale = Vec3(2, 2, 2);
    auto wb = e.world_bounds();
    CHECK_APPROX(wb.center().x, 10.0f, 1e-4f);
    CHECK(wb.size().x > 1.0f); // Scaled up
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Transform Tests
// ═══════════════════════════════════════════════════════════════════════════

void test_transform() {
  std::cout << "[Test] Transform\n";
  using qe::core::Transform;
  using qe::math::Quaternion;
  using qe::math::Vec3;

  constexpr float EPS = 1e-4f;

  SECTION("default is identity");
  {
    Transform t;
    CHECK_APPROX(t.position().x, 0.0f, EPS);
    CHECK_APPROX(t.position().y, 0.0f, EPS);
    CHECK_APPROX(t.position().z, 0.0f, EPS);
    CHECK_APPROX(t.scale().x, 1.0f, EPS);
    CHECK_APPROX(t.scale().y, 1.0f, EPS);
    CHECK_APPROX(t.scale().z, 1.0f, EPS);
  }

  SECTION("translate moves position");
  {
    Transform t;
    t.translate(Vec3(3, 4, 5));
    CHECK_APPROX(t.position().x, 3.0f, EPS);
    CHECK_APPROX(t.position().y, 4.0f, EPS);
    CHECK_APPROX(t.position().z, 5.0f, EPS);
  }

  SECTION("translate_local respects rotation");
  {
    Transform t;
    // Rotate 90 degrees around Y axis
    t.rotate_axis(Vec3::up(), 3.14159265f / 2.0f);
    t.translate_local(
        Vec3(0, 0, -1)); // Forward in local = should move in rotated direction
    // After 90 Y rotation, local -Z maps to world -X (approximately)
    CHECK(std::abs(t.position().x) > 0.5f || std::abs(t.position().z) > 0.5f);
  }

  SECTION("rotate_axis changes orientation");
  {
    Transform t;
    t.rotate_axis(Vec3::up(), 3.14159265f / 2.0f);
    Vec3 fwd = t.forward();
    // After 90 Y rotation, forward (-Z) should become approximately -X
    CHECK(std::abs(fwd.x) > 0.5f);
  }

  SECTION("forward, right, up orthogonal");
  {
    Transform t;
    t.rotate_axis(Vec3::up(), 0.5f);
    Vec3 f = t.forward();
    Vec3 r = t.right();
    Vec3 u = t.up();
    float dot_fr = f.dot(r);
    float dot_fu = f.dot(u);
    CHECK_APPROX(dot_fr, 0.0f, 0.01f);
    CHECK_APPROX(dot_fu, 0.0f, 0.01f);
  }

  SECTION("look_at faces target");
  {
    Transform t;
    t.set_position(Vec3(0, 0, 0));
    t.look_at(Vec3(0, 0, -10));
    Vec3 fwd = t.forward();
    // Should point in -Z direction
    CHECK(fwd.z < -0.9f);
  }

  SECTION("interpolate midpoint");
  {
    Transform a;
    a.set_position(Vec3(0, 0, 0));
    Transform b;
    b.set_position(Vec3(10, 0, 0));
    Transform mid = Transform::interpolate(a, b, 0.5f);
    CHECK_APPROX(mid.position().x, 5.0f, EPS);
  }

  SECTION("to_matrix produces valid TRS");
  {
    Transform t;
    t.set_position(Vec3(1, 2, 3));
    auto m = t.to_matrix();
    // Column-major: translation in m[3][0], m[3][1], m[3][2]
    CHECK_APPROX(m.m[3][0], 1.0f, EPS);
    CHECK_APPROX(m.m[3][1], 2.0f, EPS);
    CHECK_APPROX(m.m[3][2], 3.0f, EPS);
  }

  SECTION("to_matrix caches (dirty flag)");
  {
    Transform t;
    auto m1 = t.to_matrix();
    auto m2 = t.to_matrix(); // Should use cache
    CHECK_APPROX(m1.m[0][0], m2.m[0][0], EPS);
    CHECK_APPROX(m1.m[3][0], m2.m[3][0], EPS);
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Projectile Tests
// ═══════════════════════════════════════════════════════════════════════════

void test_projectile() {
  std::cout << "[Test] Projectile\n";
  using qe::core::Projectile;
  using qe::math::Vec3;

  constexpr float EPS = 1e-4f;

  SECTION("initial state");
  {
    Projectile p;
    CHECK(p.active);
    CHECK_APPROX(p.age, 0.0f, EPS);
    CHECK(p.is_alive());
  }

  SECTION("update moves position");
  {
    Projectile p;
    p.velocity = Vec3(10, 0, 0);
    p.update(0.1f);
    CHECK_APPROX(p.position.x, 1.0f, EPS);
  }

  SECTION("update ages correctly");
  {
    Projectile p;
    p.update(0.5f);
    CHECK_APPROX(p.age, 0.5f, EPS);
  }

  SECTION("lifetime expiry deactivates");
  {
    Projectile p;
    p.lifetime = 1.0f;
    p.update(1.1f);
    CHECK(!p.active);
    CHECK(!p.is_alive());
  }

  SECTION("below ground deactivates");
  {
    Projectile p;
    p.position = Vec3(0, 0, 0);
    p.velocity = Vec3(0, -20, 0);
    p.update(1.0f); // y = -20, below -1
    CHECK(!p.active);
  }

  SECTION("brightness decays with age");
  {
    Projectile p;
    p.lifetime = 2.0f;
    float initial = p.brightness;
    p.update(1.0f);
    CHECK(p.brightness < initial);
  }

  SECTION("bounds returns AABB at position");
  {
    Projectile p;
    p.position = Vec3(5, 0, 0);
    p.radius = 0.5f;
    auto b = p.bounds();
    CHECK(b.contains(Vec3(5, 0, 0)));
    CHECK(!b.contains(Vec3(10, 0, 0)));
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// CombatStats Tests
// ═══════════════════════════════════════════════════════════════════════════

void test_combat_stats() {
  std::cout << "[Test] CombatStats\n";
  using qe::game::CombatStats;

  SECTION("accuracy zero when no shots");
  {
    CombatStats s;
    CHECK_APPROX(s.accuracy(), 0.0f, 1e-6f);
  }

  SECTION("accuracy correct ratio");
  {
    CombatStats s;
    s.total_shots = 10;
    s.total_hits = 7;
    CHECK_APPROX(s.accuracy(), 70.0f, 1e-4f);
  }

  SECTION("reset zeroes all");
  {
    CombatStats s;
    s.score = 500;
    s.total_shots = 20;
    s.total_hits = 15;
    s.reset();
    CHECK(s.score == 0);
    CHECK(s.total_shots == 0);
    CHECK(s.total_hits == 0);
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Combat Function Tests
// ═══════════════════════════════════════════════════════════════════════════

void test_combat() {
  std::cout << "[Test] Combat\n";
  using qe::core::Entity;
  using qe::core::Projectile;
  using qe::game::CombatConfig;
  using qe::game::CombatStats;
  using qe::math::Vec3;

  SECTION("shoot spawns projectile and increments shots");
  {
    CombatConfig cfg;
    CombatStats stats;
    std::vector<Projectile> projectiles;
    std::vector<Entity> entities;

    qe::game::shoot(Vec3(0, 0, 0), Vec3(1, 0, 0), cfg, projectiles, entities,
                    stats);
    CHECK(projectiles.size() == 1);
    CHECK(stats.total_shots == 1);
  }

  SECTION("shoot hitscan hit increments hits");
  {
    CombatConfig cfg;
    CombatStats stats;
    std::vector<Projectile> projectiles;
    std::vector<Entity> entities;

    Entity target;
    target.position = Vec3(5, 0, 0);
    target.local_bounds = qe::core::AABB::from_center(Vec3::zero(), 1.0f);
    entities.push_back(target);

    qe::game::shoot(Vec3(0, 0, 0), Vec3(1, 0, 0), cfg, projectiles, entities,
                    stats);
    CHECK(stats.total_hits == 1);
    CHECK(entities[0].health < 100.0f);
  }

  SECTION("shoot kill adds score");
  {
    CombatConfig cfg;
    cfg.projectile_damage = 200.0f; // One-shot kill
    CombatStats stats;
    std::vector<Projectile> projectiles;
    std::vector<Entity> entities;

    Entity target;
    target.position = Vec3(5, 0, 0);
    target.local_bounds = qe::core::AABB::from_center(Vec3::zero(), 1.0f);
    entities.push_back(target);

    qe::game::shoot(Vec3(0, 0, 0), Vec3(1, 0, 0), cfg, projectiles, entities,
                    stats);
    CHECK(stats.score == cfg.kill_score);
    CHECK(!entities[0].alive);
  }

  SECTION("update_projectiles removes dead");
  {
    std::vector<Projectile> projectiles;
    Projectile p;
    p.lifetime = 0.1f;
    projectiles.push_back(p);

    qe::game::update_projectiles(projectiles, 0.2f);
    CHECK(projectiles.empty());
  }

  SECTION("check_projectile_collisions damages and deactivates");
  {
    CombatStats stats;
    std::vector<Projectile> projectiles;
    std::vector<Entity> entities;

    Projectile p;
    p.position = Vec3(5, 0, 0);
    p.radius = 1.0f;
    p.damage = 20.0f;
    projectiles.push_back(p);

    Entity target;
    target.position = Vec3(5, 0, 0);
    target.local_bounds = qe::core::AABB::from_center(Vec3::zero(), 1.0f);
    entities.push_back(target);

    qe::game::check_projectile_collisions(projectiles, entities, stats);
    CHECK(!projectiles[0].active);
    CHECK(entities[0].health < 100.0f);
    CHECK(stats.total_hits == 1);
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// NavigationSystem Tests
// ═══════════════════════════════════════════════════════════════════════════

void test_navigation() {
  std::cout << "[Test] NavigationSystem\n";
  using qe::ai::NavigationSystem;
  using qe::math::Vec3;

  SECTION("init creates correct grid");
  {
    NavigationSystem nav;
    nav.init(10, 10, 1.0f);
    CHECK(nav.width == 10);
    CHECK(nav.depth == 10);
    CHECK(static_cast<int>(nav.nodes.size()) == 100);
  }

  SECTION("get_node valid coordinates");
  {
    NavigationSystem nav;
    nav.init(10, 10, 1.0f);
    // Center of grid should be accessible
    auto *node = nav.get_node(0, 0);
    CHECK(node != nullptr);
  }

  SECTION("get_node out of bounds");
  {
    NavigationSystem nav;
    nav.init(10, 10, 1.0f);
    auto *node = nav.get_node(100, 100);
    CHECK(node == nullptr);
  }

  SECTION("mark_obstacle makes nodes unwalkable");
  {
    NavigationSystem nav;
    nav.init(10, 10, 1.0f);
    nav.mark_obstacle(0, 0, 0.5f);
    auto *node = nav.get_node(0, 0);
    CHECK(node != nullptr);
    CHECK(!node->walkable);
  }

  SECTION("find_path direct path");
  {
    NavigationSystem nav;
    nav.init(20, 20, 1.0f);
    auto path = nav.find_path(Vec3(-5, 0, 0), Vec3(5, 0, 0));
    CHECK(!path.empty());
    CHECK(path.size() >= 2);
  }

  SECTION("find_path around obstacle");
  {
    NavigationSystem nav;
    nav.init(20, 20, 1.0f);

    // Create a wall across the middle (but leave gaps at edges)
    for (int x = -3; x <= 3; ++x) {
      nav.mark_obstacle(static_cast<float>(x), 0, 0.3f);
    }

    auto path = nav.find_path(Vec3(0, 0, -3), Vec3(0, 0, 3));
    CHECK(!path.empty());
    // Path should be longer than direct distance since it goes around
    CHECK(path.size() > 6);
  }

  SECTION("find_path no path when fully blocked");
  {
    NavigationSystem nav;
    nav.init(10, 10, 1.0f);

    // Block a ring around the start node's neighborhood
    auto *start = nav.get_node(0, 0);
    if (start) {
      for (auto *neighbor : start->neighbors) {
        neighbor->walkable = false;
      }
    }

    auto path = nav.find_path(Vec3(0, 0, 0), Vec3(3, 0, 3));
    CHECK(path.empty());
  }

  SECTION("find_path start equals end");
  {
    NavigationSystem nav;
    nav.init(10, 10, 1.0f);
    auto path = nav.find_path(Vec3(0, 0, 0), Vec3(0, 0, 0));
    // Should return single-element path
    CHECK(path.size() == 1);
  }

  SECTION("find_path unwalkable start returns empty");
  {
    NavigationSystem nav;
    nav.init(10, 10, 1.0f);
    auto *start = nav.get_node(0, 0);
    if (start)
      start->walkable = false;
    auto path = nav.find_path(Vec3(0, 0, 0), Vec3(3, 0, 0));
    CHECK(path.empty());
  }

  SECTION("multiple searches use fresh data");
  {
    NavigationSystem nav;
    nav.init(20, 20, 1.0f);

    auto path1 = nav.find_path(Vec3(-5, 0, 0), Vec3(5, 0, 0));
    CHECK(!path1.empty());

    auto path2 = nav.find_path(Vec3(-3, 0, -3), Vec3(3, 0, 3));
    CHECK(!path2.empty());

    // Both should succeed independently
    CHECK(nav.current_search_id >= 2);
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Main
// ═══════════════════════════════════════════════════════════════════════════

int main() {
  std::cout << "=== QuatEngine Core/Game/AI Tests ===\n\n";

  test_aabb();
  test_entity();
  test_transform();
  test_projectile();
  test_combat_stats();
  test_combat();
  test_navigation();

  std::cout << "\n=== Results: " << g_passed << " passed, " << g_failed
            << " failed, " << g_total << " total ===\n";

  return g_failed > 0 ? 1 : 0;
}
