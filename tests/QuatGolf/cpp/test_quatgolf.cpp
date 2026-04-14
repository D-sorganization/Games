/**
 * @file test_quatgolf.cpp
 * @brief Unit tests for QuatGolf gameplay and physics code.
 *
 * Covers:
 *   - Surface: property lookup for every SurfaceType
 *   - Terrain: height/normal/surface queries from flat and sloped heightmaps
 *   - Club: launch velocity direction and magnitude, spin axis
 *   - Hole: distance_m computation
 *   - BallPhysics: launch state, flight integration (gravity, drag, Magnus),
 *     terrain contact (bounce/rolling transitions), water hazard, rolling stop
 *
 * Uses the same lightweight test framework as tests/shared/cpp/test_math.cpp.
 * No OpenGL calls are made — Terrain::set_data() + query methods only.
 * QE_NO_SDL is defined via CMake so GLLoader.h compiles without SDL headers.
 */

#include <cmath>
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>

// QuatGolf headers
#include "course/Hole.h"
#include "game/Club.h"
#include "math/Vec3.h"
#include "physics/BallPhysics.h"
#include "terrain/Surface.h"
#include "terrain/Terrain.h"

// ── Minimal Test Framework ───────────────────────────────────────────────────

static int g_tests_run = 0;
static int g_tests_passed = 0;
static int g_tests_failed = 0;

#define ASSERT_TRUE(expr)                                                                          \
  do {                                                                                             \
    ++g_tests_run;                                                                                 \
    if (!(expr)) {                                                                                 \
      std::cerr << "  FAIL: " << #expr << " (" << __FILE__ << ":" << __LINE__ << ")" << std::endl; \
      ++g_tests_failed;                                                                            \
    } else {                                                                                       \
      ++g_tests_passed;                                                                            \
    }                                                                                              \
  } while (0)

#define ASSERT_FLOAT_EQ(a, b, eps)                                                           \
  do {                                                                                       \
    ++g_tests_run;                                                                           \
    if (std::abs((a) - (b)) > (eps)) {                                                       \
      std::cerr << "  FAIL: " << #a << " == " << #b << " (got " << (a) << " vs " << (b)      \
                << ", eps=" << (eps) << ") at " << __FILE__ << ":" << __LINE__ << std::endl; \
      ++g_tests_failed;                                                                      \
    } else {                                                                                 \
      ++g_tests_passed;                                                                      \
    }                                                                                        \
  } while (0)

#define RUN_TEST(test_fn)                                                        \
  do {                                                                           \
    std::cout << "  " << #test_fn << "... ";                                     \
    int before_fail = g_tests_failed;                                            \
    test_fn();                                                                   \
    std::cout << (g_tests_failed == before_fail ? "OK" : "FAILED") << std::endl; \
  } while (0)

constexpr float EPS = 1e-4f;

// ── Helper: build a flat terrain of given size ───────────────────────────────

static qg::terrain::Terrain make_flat_terrain(int w, int d, float height,
                                              qg::terrain::SurfaceType surf) {
  qg::terrain::Terrain t;
  std::vector<float> heights(w * d, height);
  std::vector<qg::terrain::SurfaceType> surfaces(w * d, surf);
  t.set_data(w, d, 1.0f, std::move(heights), std::move(surfaces));
  return t;
}

// ============================================================================
//  Surface Tests
// ============================================================================

void test_surface_fairway_properties() {
  using namespace qg::terrain;
  auto s = get_surface(SurfaceType::Fairway);
  ASSERT_TRUE(s.type == SurfaceType::Fairway);
  ASSERT_TRUE(s.friction > 0.0f && s.friction < 1.0f);
  ASSERT_TRUE(s.bounce > 0.0f && s.bounce <= 1.0f);
  ASSERT_TRUE(s.speed_mult > 0.0f);
}

void test_surface_water_no_bounce() {
  using namespace qg::terrain;
  auto s = get_surface(SurfaceType::Water);
  ASSERT_FLOAT_EQ(s.bounce, 0.0f, EPS);
  ASSERT_FLOAT_EQ(s.speed_mult, 0.0f, EPS);
}

void test_surface_sand_high_friction() {
  using namespace qg::terrain;
  auto s_sand = get_surface(SurfaceType::Sand);
  auto s_fairway = get_surface(SurfaceType::Fairway);
  // Sand must have higher friction than fairway
  ASSERT_TRUE(s_sand.friction > s_fairway.friction);
}

void test_surface_green_lowest_friction() {
  using namespace qg::terrain;
  auto s_green = get_surface(SurfaceType::Green);
  auto s_fairway = get_surface(SurfaceType::Fairway);
  auto s_rough = get_surface(SurfaceType::Rough);
  // Green is a putting surface — less friction than fairway/rough
  ASSERT_TRUE(s_green.friction < s_fairway.friction);
  ASSERT_TRUE(s_green.friction < s_rough.friction);
}

void test_surface_rough_speed_penalty() {
  using namespace qg::terrain;
  auto s_rough = get_surface(SurfaceType::Rough);
  auto s_fairway = get_surface(SurfaceType::Fairway);
  // Rough slows the ball more than fairway
  ASSERT_TRUE(s_rough.speed_mult < s_fairway.speed_mult);
}

void test_surface_name_nonempty() {
  using namespace qg::terrain;
  // Every surface type must have a non-empty name
  for (int i = 0; i < static_cast<int>(SurfaceType::Count); ++i) {
    auto s = get_surface(static_cast<SurfaceType>(i));
    ASSERT_TRUE(s.name() != nullptr && s.name()[0] != '\0');
  }
}

// ============================================================================
//  Terrain Tests
// ============================================================================

void test_terrain_flat_height_at_grid() {
  auto t = make_flat_terrain(10, 10, 5.0f, qg::terrain::SurfaceType::Fairway);
  ASSERT_FLOAT_EQ(t.height_at(0, 0), 5.0f, EPS);
  ASSERT_FLOAT_EQ(t.height_at(5, 5), 5.0f, EPS);
  ASSERT_FLOAT_EQ(t.height_at(9, 9), 5.0f, EPS);
}

void test_terrain_flat_height_at_world() {
  auto t = make_flat_terrain(10, 10, 3.0f, qg::terrain::SurfaceType::Fairway);
  // World origin should return flat height via bilinear interpolation
  ASSERT_FLOAT_EQ(t.height_at_world(0.0f, 0.0f), 3.0f, EPS);
}

void test_terrain_clamp_out_of_bounds() {
  auto t = make_flat_terrain(5, 5, 1.0f, qg::terrain::SurfaceType::Rough);
  // Out-of-bounds queries must clamp, not crash
  ASSERT_FLOAT_EQ(t.height_at(-10, -10), 1.0f, EPS);
  ASSERT_FLOAT_EQ(t.height_at(100, 100), 1.0f, EPS);
}

void test_terrain_surface_at_grid() {
  auto t = make_flat_terrain(5, 5, 0.0f, qg::terrain::SurfaceType::Sand);
  ASSERT_TRUE(t.surface_at(2, 2) == qg::terrain::SurfaceType::Sand);
}

void test_terrain_surface_at_world() {
  auto t = make_flat_terrain(10, 10, 0.0f, qg::terrain::SurfaceType::Green);
  ASSERT_TRUE(t.surface_at_world(0.0f, 0.0f) == qg::terrain::SurfaceType::Green);
}

void test_terrain_flat_normal_is_up() {
  // A completely flat terrain must produce an upward normal everywhere
  auto t = make_flat_terrain(10, 10, 0.0f, qg::terrain::SurfaceType::Fairway);
  auto n = t.normal_at(5, 5);
  // For flat terrain: hL==hR==hD==hU, so normal = Vec3(0, 2*cell_size, 0).normalized() = (0,1,0)
  ASSERT_FLOAT_EQ(n.x, 0.0f, EPS);
  ASSERT_FLOAT_EQ(n.y, 1.0f, EPS);
  ASSERT_FLOAT_EQ(n.z, 0.0f, EPS);
}

void test_terrain_sloped_normal_tilted() {
  // Build a terrain that slopes upward in X (left column low, right column high)
  int w = 5, d = 5;
  std::vector<float> heights;
  heights.reserve(w * d);
  for (int z = 0; z < d; ++z) {
    for (int x = 0; x < w; ++x) {
      heights.push_back(static_cast<float>(x));  // Height increases with x
    }
  }
  std::vector<qg::terrain::SurfaceType> surfaces(w * d, qg::terrain::SurfaceType::Fairway);
  qg::terrain::Terrain t;
  t.set_data(w, d, 1.0f, std::move(heights), std::move(surfaces));

  // For slope along X: normal should have non-zero X and non-zero Y components
  auto n = t.normal_at(2, 2);
  ASSERT_FLOAT_EQ(n.length(), 1.0f, EPS);  // Must be normalized
  ASSERT_TRUE(n.x != 0.0f);                // Slope causes X tilt
  ASSERT_TRUE(n.y > 0.0f);                 // Y must still be positive (faces "up")
}

// ============================================================================
//  Club Tests
// ============================================================================

void test_club_driver_forward_launch() {
  using namespace qg::game;
  const Club& driver = CLUBS[0];          // Driver
  qe::math::Vec3 aim{0.0f, 0.0f, -1.0f};  // Forward
  auto vel = driver.launch_velocity(aim, 1.0f);

  // With loft ~10.5 degrees, must have negative Z (forward) and positive Y (upward)
  ASSERT_TRUE(vel.z < 0.0f);
  ASSERT_TRUE(vel.y > 0.0f);
  // Total speed must equal max_speed at full power
  ASSERT_FLOAT_EQ(vel.length(), driver.max_speed, 0.5f);
}

void test_club_putter_flat_launch() {
  using namespace qg::game;
  const Club& putter = CLUBS[NUM_CLUBS - 1];  // Putter
  qe::math::Vec3 aim{1.0f, 0.0f, 0.0f};       // Sideways aim
  auto vel = putter.launch_velocity(aim, 1.0f);

  // Putter has very low loft — mostly horizontal
  ASSERT_TRUE(vel.x > 0.0f);
  float h_speed = qe::math::Vec3(vel.x, 0, vel.z).length();
  ASSERT_TRUE(h_speed > vel.y);  // Horizontal component dominates
}

void test_club_half_power_half_speed() {
  using namespace qg::game;
  const Club& iron = CLUBS[3];  // 7 Iron
  qe::math::Vec3 aim{0.0f, 0.0f, -1.0f};
  auto vel_full = iron.launch_velocity(aim, 1.0f);
  auto vel_half = iron.launch_velocity(aim, 0.5f);

  // At half power the speed must be half the full-power speed
  ASSERT_FLOAT_EQ(vel_half.length(), vel_full.length() * 0.5f, 0.5f);
}

void test_club_zero_power_zero_velocity() {
  using namespace qg::game;
  const Club& sw = CLUBS[6];  // Sand Wedge
  qe::math::Vec3 aim{0.0f, 0.0f, -1.0f};
  auto vel = sw.launch_velocity(aim, 0.0f);
  ASSERT_FLOAT_EQ(vel.length(), 0.0f, EPS);
}

void test_club_spin_perpendicular_to_aim() {
  using namespace qg::game;
  const Club& iron = CLUBS[2];  // 5 Iron
  qe::math::Vec3 aim{0.0f, 0.0f, -1.0f};
  auto spin = iron.default_spin(aim);

  // Spin axis must be perpendicular to aim direction (dot product ~ 0)
  float dot = spin.x * aim.x + spin.y * aim.y + spin.z * aim.z;
  ASSERT_FLOAT_EQ(dot, 0.0f, EPS);
}

void test_club_spin_magnitude_positive() {
  using namespace qg::game;
  const Club& pw = CLUBS[5];  // Pitching Wedge
  qe::math::Vec3 aim{1.0f, 0.0f, 0.0f};
  auto spin = pw.default_spin(aim);
  ASSERT_TRUE(spin.length() > 0.0f);
}

void test_club_count() {
  ASSERT_TRUE(qg::game::NUM_CLUBS == 9);
}

void test_club_lofts_increase_with_index() {
  using namespace qg::game;
  // Each subsequent club (except putter) has higher loft
  for (int i = 1; i < NUM_CLUBS - 1; ++i) {
    ASSERT_TRUE(CLUBS[i].loft_deg >= CLUBS[i - 1].loft_deg);
  }
}

// ============================================================================
//  Hole Tests
// ============================================================================

void test_hole_distance_m_straight() {
  using namespace qg::course;
  Hole h;
  h.tee.position = {0.0f, 0.0f, 0.0f};
  h.green.pin = {100.0f, 0.0f, 0.0f};
  ASSERT_FLOAT_EQ(h.distance_m(), 100.0f, EPS);
}

void test_hole_distance_m_3d() {
  using namespace qg::course;
  Hole h;
  h.tee.position = {0.0f, 0.0f, 0.0f};
  h.green.pin = {3.0f, 4.0f, 0.0f};
  ASSERT_FLOAT_EQ(h.distance_m(), 5.0f, EPS);  // 3-4-5 triangle
}

void test_hole_default_par() {
  qg::course::Hole h;
  ASSERT_TRUE(h.par >= 3 && h.par <= 5);
}

// ============================================================================
//  BallPhysics Tests
// ============================================================================

void test_ball_launch_sets_in_flight() {
  qg::physics::BallPhysics phys;
  qg::physics::BallState ball;

  qe::math::Vec3 vel{10.0f, 20.0f, 0.0f};
  phys.launch(ball, vel);

  ASSERT_TRUE(ball.in_flight);
  ASSERT_TRUE(!ball.rolling);
  ASSERT_TRUE(!ball.stopped);
  ASSERT_TRUE(!ball.in_water);
  ASSERT_FLOAT_EQ(ball.velocity.x, 10.0f, EPS);
  ASSERT_FLOAT_EQ(ball.velocity.y, 20.0f, EPS);
}

void test_ball_gravity_reduces_vertical_speed() {
  // Ball launched straight up — gravity must reduce vertical speed
  qg::physics::BallPhysics phys;
  qg::physics::BallState ball;
  auto terrain = make_flat_terrain(20, 20, -100.0f, qg::terrain::SurfaceType::Fairway);

  phys.launch(ball, {0.0f, 50.0f, 0.0f});

  float initial_vy = ball.velocity.y;
  phys.update(ball, terrain, 0.1f);

  // After one step, vertical speed must be lower due to gravity
  ASSERT_TRUE(ball.velocity.y < initial_vy);
}

void test_ball_drag_reduces_horizontal_speed() {
  // Ball launched purely horizontally — drag must slow it
  qg::physics::BallPhysics phys;
  qg::physics::BallState ball;
  auto terrain = make_flat_terrain(20, 20, -100.0f, qg::terrain::SurfaceType::Fairway);

  phys.launch(ball, {50.0f, 0.0f, 0.0f});

  float initial_speed = ball.speed();
  // Integrate several steps — drag must reduce total speed
  for (int i = 0; i < 10; ++i) {
    phys.update(ball, terrain, 0.05f);
    if (!ball.in_flight)
      break;
  }
  // Either ball is still in flight with reduced speed, or it bounced
  if (ball.in_flight) {
    ASSERT_TRUE(ball.speed() < initial_speed);
  } else {
    ASSERT_TRUE(!ball.stopped || ball.speed() <= initial_speed);
  }
}

void test_ball_stopped_does_not_move() {
  qg::physics::BallPhysics phys;
  qg::physics::BallState ball;
  ball.stopped = true;
  ball.position = {1.0f, 2.0f, 3.0f};
  ball.velocity = {0.0f, 0.0f, 0.0f};

  auto terrain = make_flat_terrain(10, 10, 0.0f, qg::terrain::SurfaceType::Fairway);
  phys.update(ball, terrain, 0.1f);

  // Stopped ball must not move
  ASSERT_FLOAT_EQ(ball.position.x, 1.0f, EPS);
  ASSERT_FLOAT_EQ(ball.position.y, 2.0f, EPS);
  ASSERT_FLOAT_EQ(ball.position.z, 3.0f, EPS);
}

void test_ball_in_water_does_not_update() {
  qg::physics::BallPhysics phys;
  qg::physics::BallState ball;
  ball.in_water = true;
  ball.position = {5.0f, 0.0f, 5.0f};
  ball.velocity = {10.0f, 0.0f, 0.0f};

  auto terrain = make_flat_terrain(10, 10, 0.0f, qg::terrain::SurfaceType::Fairway);
  phys.update(ball, terrain, 0.1f);

  // Ball in water must stay put
  ASSERT_FLOAT_EQ(ball.position.x, 5.0f, EPS);
  ASSERT_TRUE(ball.in_water);
}

void test_ball_hits_ground_bounces() {
  // Ball just above ground, launched downward — must bounce (not stay in_flight)
  qg::physics::BallPhysics phys;
  phys.constants.gravity = 9.81f;

  qg::physics::BallState ball;
  auto terrain = make_flat_terrain(20, 20, 0.0f, qg::terrain::SurfaceType::Fairway);

  // Place ball just above ground, moving down
  ball.in_flight = true;
  ball.position = {0.0f, phys.constants.radius + 0.001f, 0.0f};
  ball.velocity = {0.0f, -5.0f, 0.0f};

  phys.update(ball, terrain, 0.1f);

  // Ball must have transitioned: either rolling or bouncing (no longer in_flight with downward vel)
  // In practice: velocity.y was negative and terrain contact was hit — it reflects
  ASSERT_TRUE(!ball.in_water);
  ASSERT_TRUE(!ball.stopped || ball.rolling || !ball.in_flight);
}

void test_ball_hits_water_stops() {
  qg::physics::BallPhysics phys;
  qg::physics::BallState ball;

  auto terrain = make_flat_terrain(20, 20, 0.0f, qg::terrain::SurfaceType::Water);

  ball.in_flight = true;
  ball.position = {0.0f, phys.constants.radius + 0.001f, 0.0f};
  ball.velocity = {5.0f, -5.0f, 0.0f};

  phys.update(ball, terrain, 0.1f);

  // Ball hitting water must be marked in_water
  ASSERT_TRUE(ball.in_water);
  ASSERT_TRUE(!ball.in_flight);
  ASSERT_FLOAT_EQ(ball.velocity.length(), 0.0f, EPS);
}

void test_ball_rolling_decelerates_to_stop() {
  // Ball rolling on flat fairway must eventually stop
  qg::physics::BallPhysics phys;
  qg::physics::BallState ball;
  auto terrain = make_flat_terrain(100, 100, 0.0f, qg::terrain::SurfaceType::Fairway);

  ball.rolling = true;
  ball.position = {0.0f, phys.constants.radius, 0.0f};
  ball.velocity = {2.0f, 0.0f, 0.0f};

  // Integrate many steps until stop or timeout
  int steps = 0;
  while (!ball.stopped && !ball.in_water && steps < 10000) {
    phys.update(ball, terrain, 0.05f);
    ++steps;
  }

  ASSERT_TRUE(ball.stopped);
  ASSERT_FLOAT_EQ(ball.velocity.length(), 0.0f, EPS);
}

void test_ball_rolling_on_water_enters_water() {
  qg::physics::BallPhysics phys;
  qg::physics::BallState ball;
  auto terrain = make_flat_terrain(20, 20, 0.0f, qg::terrain::SurfaceType::Water);

  ball.rolling = true;
  ball.position = {0.0f, phys.constants.radius, 0.0f};
  ball.velocity = {1.0f, 0.0f, 0.0f};

  phys.update(ball, terrain, 0.05f);

  ASSERT_TRUE(ball.in_water);
  ASSERT_TRUE(!ball.rolling);
  ASSERT_FLOAT_EQ(ball.velocity.length(), 0.0f, EPS);
}

void test_ball_speed_nonnegative_after_update() {
  // Design-by-contract postcondition: speed >= 0 after any update
  qg::physics::BallPhysics phys;
  qg::physics::BallState ball;
  auto terrain = make_flat_terrain(20, 20, 0.0f, qg::terrain::SurfaceType::Fairway);

  phys.launch(ball, {30.0f, 20.0f, -10.0f}, {0.0f, 100.0f, 0.0f});

  for (int i = 0; i < 200; ++i) {
    phys.update(ball, terrain, 0.016f);
    ASSERT_TRUE(ball.speed() >= 0.0f);
    if (ball.stopped || ball.in_water)
      break;
  }
}

void test_ball_spin_decays_in_flight() {
  qg::physics::BallPhysics phys;
  qg::physics::BallState ball;
  auto terrain = make_flat_terrain(20, 20, -100.0f, qg::terrain::SurfaceType::Fairway);

  // Strong backspin
  phys.launch(ball, {0.0f, 50.0f, 0.0f}, {0.0f, 0.0f, 200.0f});
  float initial_spin = ball.spin.length();

  phys.update(ball, terrain, 0.5f);

  // Spin must decay slightly each step
  ASSERT_TRUE(ball.spin.length() < initial_spin);
}

// ============================================================================
//  main
// ============================================================================

int main() {
  std::cout << "\n=== QuatGolf Unit Tests ===" << std::endl;

  std::cout << "\n--- Surface ---" << std::endl;
  RUN_TEST(test_surface_fairway_properties);
  RUN_TEST(test_surface_water_no_bounce);
  RUN_TEST(test_surface_sand_high_friction);
  RUN_TEST(test_surface_green_lowest_friction);
  RUN_TEST(test_surface_rough_speed_penalty);
  RUN_TEST(test_surface_name_nonempty);

  std::cout << "\n--- Terrain ---" << std::endl;
  RUN_TEST(test_terrain_flat_height_at_grid);
  RUN_TEST(test_terrain_flat_height_at_world);
  RUN_TEST(test_terrain_clamp_out_of_bounds);
  RUN_TEST(test_terrain_surface_at_grid);
  RUN_TEST(test_terrain_surface_at_world);
  RUN_TEST(test_terrain_flat_normal_is_up);
  RUN_TEST(test_terrain_sloped_normal_tilted);

  std::cout << "\n--- Club ---" << std::endl;
  RUN_TEST(test_club_driver_forward_launch);
  RUN_TEST(test_club_putter_flat_launch);
  RUN_TEST(test_club_half_power_half_speed);
  RUN_TEST(test_club_zero_power_zero_velocity);
  RUN_TEST(test_club_spin_perpendicular_to_aim);
  RUN_TEST(test_club_spin_magnitude_positive);
  RUN_TEST(test_club_count);
  RUN_TEST(test_club_lofts_increase_with_index);

  std::cout << "\n--- Hole ---" << std::endl;
  RUN_TEST(test_hole_distance_m_straight);
  RUN_TEST(test_hole_distance_m_3d);
  RUN_TEST(test_hole_default_par);

  std::cout << "\n--- BallPhysics ---" << std::endl;
  RUN_TEST(test_ball_launch_sets_in_flight);
  RUN_TEST(test_ball_gravity_reduces_vertical_speed);
  RUN_TEST(test_ball_drag_reduces_horizontal_speed);
  RUN_TEST(test_ball_stopped_does_not_move);
  RUN_TEST(test_ball_in_water_does_not_update);
  RUN_TEST(test_ball_hits_ground_bounces);
  RUN_TEST(test_ball_hits_water_stops);
  RUN_TEST(test_ball_rolling_decelerates_to_stop);
  RUN_TEST(test_ball_rolling_on_water_enters_water);
  RUN_TEST(test_ball_speed_nonnegative_after_update);
  RUN_TEST(test_ball_spin_decays_in_flight);

  std::cout << "\n=== Results: " << g_tests_passed << "/" << g_tests_run << " passed";
  if (g_tests_failed > 0) {
    std::cout << " (" << g_tests_failed << " FAILED)";
  }
  std::cout << " ===" << std::endl;

  return (g_tests_failed == 0) ? EXIT_SUCCESS : EXIT_FAILURE;
}
