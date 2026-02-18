/**
 * @file test_loaders.cpp
 * @brief Comprehensive test suite for the QuatEngine mesh/math/loader modules.
 *
 * Tests are CPU-only (no GL context required). Loader tests use the
 * parse-only APIs that return vertices/indices without GPU upload.
 *
 * Compile:
 *   g++ -std=c++17 -DNDEBUG -I.. tests/test_loaders.cpp -o test_loaders
 *
 * Note: NDEBUG disables QE_REQUIRE asserts and also disables the GL stubs
 *       (since upload/draw are not called in these tests).
 */

#include <cmath>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

// ── Math headers (no GL dependency) ─────────────────────────────────────────
#include "../math/Mat4.h"
#include "../math/Quaternion.h"
#include "../math/Vec3.h"

// ── Loader headers ──────────────────────────────────────────────────────────
// We only use the parse APIs which don't call GL functions.
// STLLoader includes Mesh.h → GLLoader.h which defines GL types,
// but function pointers remain nullptr (fine since parse() never calls them).
#include "../loader/STLLoader.h"
#include "../loader/URDFLoader.h"

// ── Simple Test Framework ───────────────────────────────────────────────────

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

// ═════════════════════════════════════════════════════════════════════════════
// Vec3 Tests
// ═════════════════════════════════════════════════════════════════════════════

void test_vec3() {
  std::cout << "[Test] Vec3\n";
  using qe::math::Vec3;

  SECTION("construction");
  {
    Vec3 v;
    CHECK(v.x == 0.0f && v.y == 0.0f && v.z == 0.0f);
    Vec3 v2(1, 2, 3);
    CHECK(v2.x == 1.0f && v2.y == 2.0f && v2.z == 3.0f);
  }

  SECTION("arithmetic");
  {
    Vec3 a(1, 2, 3), b(4, 5, 6);
    Vec3 sum = a + b;
    CHECK(sum.x == 5.0f && sum.y == 7.0f && sum.z == 9.0f);

    Vec3 diff = b - a;
    CHECK(diff.x == 3.0f && diff.y == 3.0f && diff.z == 3.0f);

    Vec3 scaled = a * 2.0f;
    CHECK(scaled.x == 2.0f && scaled.y == 4.0f && scaled.z == 6.0f);

    Vec3 neg = -a;
    CHECK(neg.x == -1.0f && neg.y == -2.0f && neg.z == -3.0f);
  }

  SECTION("dot product");
  {
    Vec3 a(1, 0, 0), b(0, 1, 0);
    CHECK_APPROX(a.dot(b), 0.0f, 1e-6f);

    Vec3 c(1, 2, 3), d(4, 5, 6);
    CHECK_APPROX(c.dot(d), 32.0f, 1e-6f);
  }

  SECTION("cross product");
  {
    Vec3 x(1, 0, 0), y(0, 1, 0);
    Vec3 z = x.cross(y);
    CHECK_APPROX(z.x, 0.0f, 1e-6f);
    CHECK_APPROX(z.y, 0.0f, 1e-6f);
    CHECK_APPROX(z.z, 1.0f, 1e-6f);

    Vec3 z2 = y.cross(x);
    CHECK_APPROX(z2.z, -1.0f, 1e-6f);
  }

  SECTION("length and normalize");
  {
    Vec3 v(3, 4, 0);
    CHECK_APPROX(v.length(), 5.0f, 1e-6f);
    CHECK_APPROX(v.length_squared(), 25.0f, 1e-6f);

    Vec3 n = v.normalized();
    CHECK_APPROX(n.length(), 1.0f, 1e-6f);
    CHECK_APPROX(n.x, 0.6f, 1e-6f);
    CHECK_APPROX(n.y, 0.8f, 1e-6f);
  }

  SECTION("lerp");
  {
    Vec3 a(0, 0, 0), b(10, 20, 30);
    Vec3 mid = a.lerp(b, 0.5f);
    CHECK_APPROX(mid.x, 5.0f, 1e-6f);
    CHECK_APPROX(mid.y, 10.0f, 1e-6f);
    CHECK_APPROX(mid.z, 15.0f, 1e-6f);

    Vec3 start = a.lerp(b, 0.0f);
    CHECK(start.approx_equal(a));
    Vec3 end = a.lerp(b, 1.0f);
    CHECK(end.approx_equal(b));
  }

  SECTION("approx_equal");
  {
    Vec3 a(1.0f, 2.0f, 3.0f);
    Vec3 b(1.0f + 1e-7f, 2.0f - 1e-7f, 3.0f);
    CHECK(a.approx_equal(b));
    CHECK(!a.approx_equal(Vec3(2.0f, 2.0f, 3.0f)));
  }

  SECTION("static directions");
  {
    CHECK(Vec3::up().y == 1.0f);
    CHECK(Vec3::right().x == 1.0f);
    CHECK(Vec3::forward().z == -1.0f);
    CHECK(Vec3::zero().length_squared() == 0.0f);
  }
}

// ═════════════════════════════════════════════════════════════════════════════
// Quaternion Tests
// ═════════════════════════════════════════════════════════════════════════════

void test_quaternion() {
  std::cout << "[Test] Quaternion\n";
  using qe::math::Quaternion;
  using qe::math::Vec3;

  SECTION("identity");
  {
    auto id = Quaternion::identity();
    CHECK_APPROX(id.w, 1.0f, 1e-6f);
    CHECK_APPROX(id.x, 0.0f, 1e-6f);
    CHECK_APPROX(id.y, 0.0f, 1e-6f);
    CHECK_APPROX(id.z, 0.0f, 1e-6f);
  }

  SECTION("from_axis_angle roundtrip");
  {
    Vec3 axis(0, 1, 0);
    float angle = 1.57f;
    auto q = Quaternion::from_axis_angle(axis, angle);
    auto [recovered_axis, recovered_angle] = q.to_axis_angle();
    CHECK_APPROX(recovered_angle, angle, 1e-4f);
    CHECK_APPROX(std::abs(recovered_axis.dot(axis)), 1.0f, 1e-4f);
  }

  SECTION("identity multiplication");
  {
    auto id = Quaternion::identity();
    auto q = Quaternion::from_axis_angle(Vec3(0, 1, 0), 0.5f);
    auto result = id * q;
    CHECK(result.approx_equal(q));

    auto result2 = q * id;
    CHECK(result2.approx_equal(q));
  }

  SECTION("rotation of point");
  {
    auto q = Quaternion::from_axis_angle(Vec3(0, 1, 0), 3.14159265f / 2.0f);
    Vec3 rotated = q.rotate(Vec3(1, 0, 0));
    CHECK_APPROX(rotated.x, 0.0f, 1e-4f);
    CHECK_APPROX(rotated.y, 0.0f, 1e-4f);
    CHECK_APPROX(rotated.z, -1.0f, 1e-4f);
  }

  SECTION("slerp endpoints");
  {
    auto a = Quaternion::identity();
    auto b = Quaternion::from_axis_angle(Vec3(0, 1, 0), 1.0f);

    auto at_0 = Quaternion::slerp(a, b, 0.0f);
    CHECK(at_0.approx_equal(a, 1e-4f));

    auto at_1 = Quaternion::slerp(a, b, 1.0f);
    CHECK(at_1.approx_equal(b, 1e-4f));
  }

  SECTION("slerp midpoint");
  {
    auto a = Quaternion::identity();
    auto b = Quaternion::from_axis_angle(Vec3(0, 1, 0), 1.0f);
    auto mid = Quaternion::slerp(a, b, 0.5f);
    auto [axis, angle] = mid.to_axis_angle();
    CHECK_APPROX(angle, 0.5f, 0.05f);
  }

  SECTION("conjugate");
  {
    auto q = Quaternion(0.5f, 0.5f, 0.5f, 0.5f);
    auto conj = q.conjugate();
    CHECK_APPROX(conj.w, q.w, 1e-6f);
    CHECK_APPROX(conj.x, -q.x, 1e-6f);
    CHECK_APPROX(conj.y, -q.y, 1e-6f);
    CHECK_APPROX(conj.z, -q.z, 1e-6f);
  }

  SECTION("normalize");
  {
    auto q = Quaternion(1, 2, 3, 4);
    auto n = q.normalized();
    CHECK_APPROX(n.norm(), 1.0f, 1e-6f);
  }
}

// ═════════════════════════════════════════════════════════════════════════════
// Mat4 Tests
// ═════════════════════════════════════════════════════════════════════════════

void test_mat4() {
  std::cout << "[Test] Mat4\n";
  using qe::math::Mat4;
  using qe::math::Quaternion;
  using qe::math::Vec3;

  SECTION("identity * point = point");
  {
    auto id = Mat4::identity();
    Vec3 p(3.14f, 2.71f, 1.41f);
    Vec3 result = id.transform_point(p);
    CHECK(result.approx_equal(p));
  }

  SECTION("translation");
  {
    auto t = Mat4::translation(Vec3(10, 20, 30));
    Vec3 origin(0, 0, 0);
    Vec3 result = t.transform_point(origin);
    CHECK_APPROX(result.x, 10.0f, 1e-6f);
    CHECK_APPROX(result.y, 20.0f, 1e-6f);
    CHECK_APPROX(result.z, 30.0f, 1e-6f);
  }

  SECTION("translate alias");
  {
    auto t1 = Mat4::translation(Vec3(1, 2, 3));
    auto t2 = Mat4::translate(Vec3(1, 2, 3));
    Vec3 p(5, 5, 5);
    CHECK(t1.transform_point(p).approx_equal(t2.transform_point(p)));
  }

  SECTION("scale");
  {
    auto s = Mat4::scale(Vec3(2, 3, 4));
    Vec3 p(1, 1, 1);
    Vec3 result = s.transform_point(p);
    CHECK_APPROX(result.x, 2.0f, 1e-6f);
    CHECK_APPROX(result.y, 3.0f, 1e-6f);
    CHECK_APPROX(result.z, 4.0f, 1e-6f);
  }

  SECTION("uniform scale");
  {
    auto s = Mat4::scale(3.0f);
    Vec3 p(1, 2, 3);
    Vec3 result = s.transform_point(p);
    CHECK_APPROX(result.x, 3.0f, 1e-6f);
    CHECK_APPROX(result.y, 6.0f, 1e-6f);
    CHECK_APPROX(result.z, 9.0f, 1e-6f);
  }

  SECTION("rotation alias");
  {
    auto q = Quaternion::from_axis_angle(Vec3(0, 1, 0), 0.5f);
    auto r1 = Mat4::rotation(q);
    auto r2 = Mat4::rotate(q);
    Vec3 p(1, 0, 0);
    CHECK(r1.transform_point(p).approx_equal(r2.transform_point(p)));
  }

  SECTION("TRS composition");
  {
    Vec3 pos(10, 0, 0);
    auto rot = Quaternion::identity();
    Vec3 scl(2, 2, 2);
    auto trs = Mat4::trs(pos, rot, scl);

    Vec3 p(1, 0, 0);
    Vec3 result = trs.transform_point(p);
    CHECK_APPROX(result.x, 12.0f, 1e-4f);
    CHECK_APPROX(result.y, 0.0f, 1e-4f);
    CHECK_APPROX(result.z, 0.0f, 1e-4f);
  }

  SECTION("perspective sanity");
  {
    float fov = 3.14159265f / 4.0f;
    auto proj = Mat4::perspective(fov, 16.0f / 9.0f, 0.1f, 100.0f);
    CHECK(proj.m[0][0] > 0.0f);
    CHECK(proj.m[1][1] > 0.0f);
    CHECK_APPROX(proj.m[2][3], -1.0f, 1e-6f);
  }

  SECTION("transform_direction ignores translation");
  {
    auto t = Mat4::translation(Vec3(100, 200, 300));
    Vec3 dir(1, 0, 0);
    Vec3 result = t.transform_direction(dir);
    CHECK(result.approx_equal(dir));
  }

  SECTION("multiplication associativity");
  {
    auto a = Mat4::translation(Vec3(1, 0, 0));
    auto b = Mat4::scale(2.0f);
    auto c = Mat4::translation(Vec3(0, 1, 0));
    Vec3 p(1, 1, 1);

    Vec3 r1 = ((a * b) * c).transform_point(p);
    Vec3 r2 = (a * (b * c)).transform_point(p);
    CHECK(r1.approx_equal(r2, 1e-4f));
  }

  SECTION("data() returns column-major pointer");
  {
    auto t = Mat4::translation(Vec3(5, 10, 15));
    const float *d = t.data();
    CHECK_APPROX(d[12], 5.0f, 1e-6f);
    CHECK_APPROX(d[13], 10.0f, 1e-6f);
    CHECK_APPROX(d[14], 15.0f, 1e-6f);
  }
}

// ═════════════════════════════════════════════════════════════════════════════
// URDF Parser Tests
// ═════════════════════════════════════════════════════════════════════════════

void test_urdf_parser() {
  std::cout << "[Test] URDFLoader\n";

  const std::string urdf_path = "test_robot.urdf";
  {
    std::ofstream tmp(urdf_path);
    tmp << R"(
        <robot name="test_bot">
            <link name="base">
                <visual>
                    <geometry><box size="1 1 1"/></geometry>
                    <material name="red"><color rgba="0.8 0.2 0.2 1.0"/></material>
                </visual>
                <inertial><mass value="5.0"/></inertial>
            </link>
            <link name="arm">
                <visual>
                    <geometry><cylinder radius="0.1" length="0.5"/></geometry>
                </visual>
            </link>
            <link name="hand">
                <visual>
                    <geometry><sphere radius="0.05"/></geometry>
                </visual>
            </link>
            <joint name="shoulder" type="revolute">
                <parent link="base"/>
                <child link="arm"/>
                <origin xyz="0 0.5 0" rpy="0 0 1.57"/>
                <axis xyz="0 0 1"/>
            </joint>
            <joint name="wrist" type="fixed">
                <parent link="arm"/>
                <child link="hand"/>
                <origin xyz="0 0.3 0"/>
            </joint>
        </robot>
        )";
  }

  auto result = qe::loader::URDFLoader::load(urdf_path);

  SECTION("basic parse success");
  CHECK(result.success);
  CHECK(result.model.name == "test_bot");

  SECTION("link count");
  CHECK(result.model.links.size() == 3);

  SECTION("joint count");
  CHECK(result.model.joints.size() == 2);

  SECTION("link index map");
  CHECK(result.model.link_index.count("base") == 1);
  CHECK(result.model.link_index.count("arm") == 1);
  CHECK(result.model.link_index.count("hand") == 1);

  SECTION("geometry types");
  {
    int base_idx = result.model.link_index["base"];
    int arm_idx = result.model.link_index["arm"];
    int hand_idx = result.model.link_index["hand"];
    CHECK(result.model.links[base_idx].visual_geom.type ==
          qe::loader::URDFGeomType::Box);
    CHECK(result.model.links[arm_idx].visual_geom.type ==
          qe::loader::URDFGeomType::Cylinder);
    CHECK(result.model.links[hand_idx].visual_geom.type ==
          qe::loader::URDFGeomType::Sphere);
  }

  SECTION("box size");
  {
    int base_idx = result.model.link_index["base"];
    auto &size = result.model.links[base_idx].visual_geom.size;
    CHECK_APPROX(size.x, 1.0f, 1e-6f);
    CHECK_APPROX(size.y, 1.0f, 1e-6f);
    CHECK_APPROX(size.z, 1.0f, 1e-6f);
  }

  SECTION("cylinder radius and length");
  {
    int arm_idx = result.model.link_index["arm"];
    CHECK_APPROX(result.model.links[arm_idx].visual_geom.radius, 0.1f, 1e-6f);
    CHECK_APPROX(result.model.links[arm_idx].visual_geom.length, 0.5f, 1e-6f);
  }

  SECTION("material color");
  {
    int base_idx = result.model.link_index["base"];
    CHECK_APPROX(result.model.links[base_idx].color.r, 0.8f, 1e-6f);
    CHECK_APPROX(result.model.links[base_idx].color.g, 0.2f, 1e-6f);
  }

  SECTION("mass");
  {
    int base_idx = result.model.link_index["base"];
    CHECK_APPROX(result.model.links[base_idx].mass, 5.0f, 1e-6f);
  }

  SECTION("joint parent/child");
  CHECK(result.model.joints[0].parent_link == "base");
  CHECK(result.model.joints[0].child_link == "arm");
  CHECK(result.model.joints[1].parent_link == "arm");
  CHECK(result.model.joints[1].child_link == "hand");

  SECTION("joint type");
  CHECK(result.model.joints[0].type == "revolute");
  CHECK(result.model.joints[1].type == "fixed");

  SECTION("joint origin");
  CHECK_APPROX(result.model.joints[0].origin.xyz.y, 0.5f, 1e-6f);
  CHECK_APPROX(result.model.joints[0].origin.rpy.z, 1.57f, 1e-2f);

  SECTION("joint axis");
  CHECK_APPROX(result.model.joints[0].axis.z, 1.0f, 1e-6f);

  SECTION("root link detection");
  CHECK(result.model.root_link_name() == "base");

  SECTION("children_of");
  {
    auto children = result.model.children_of("base");
    CHECK(children.size() == 1);
    CHECK(children[0]->child_link == "arm");
  }

  SECTION("nonexistent file returns error");
  {
    auto bad = qe::loader::URDFLoader::load("nonexistent.urdf");
    CHECK(!bad.success);
    CHECK(!bad.error.empty());
  }

  std::filesystem::remove(urdf_path);
}

// ═════════════════════════════════════════════════════════════════════════════
// STL Parser Tests (CPU only via parse())
// ═════════════════════════════════════════════════════════════════════════════

void test_stl_ascii_parse() {
  std::cout << "[Test] STLLoader ASCII parse\n";

  const std::string stl_path = "test_ascii.stl";
  {
    std::ofstream f(stl_path);
    f << "solid cube\n"
      << "  facet normal 0 0 -1\n"
      << "    outer loop\n"
      << "      vertex 0 0 0\n"
      << "      vertex 1 0 0\n"
      << "      vertex 1 1 0\n"
      << "    endloop\n"
      << "  endfacet\n"
      << "  facet normal 0 0 -1\n"
      << "    outer loop\n"
      << "      vertex 0 0 0\n"
      << "      vertex 1 1 0\n"
      << "      vertex 0 1 0\n"
      << "    endloop\n"
      << "  endfacet\n"
      << "endsolid cube\n";
  }

  auto result = qe::loader::STLLoader::parse(stl_path);

  SECTION("parse success");
  CHECK(result.success);

  SECTION("triangle count");
  CHECK(result.triangle_count == 2);

  SECTION("index count = 6");
  CHECK(result.indices.size() == 6);

  SECTION("vertex deduplication");
  CHECK(result.vertices.size() == 4);

  SECTION("bounds");
  CHECK_APPROX(result.bounds_min.x, 0.0f, 1e-6f);
  CHECK_APPROX(result.bounds_min.y, 0.0f, 1e-6f);
  CHECK_APPROX(result.bounds_max.x, 1.0f, 1e-6f);
  CHECK_APPROX(result.bounds_max.y, 1.0f, 1e-6f);

  SECTION("normals are set");
  for (const auto &v : result.vertices) {
    CHECK_APPROX(v.normal[2], -1.0f, 1e-6f);
  }

  SECTION("scale factor");
  {
    auto scaled =
        qe::loader::STLLoader::parse(stl_path, 0.6f, 0.6f, 0.6f, 2.0f);
    CHECK(scaled.success);
    CHECK_APPROX(scaled.bounds_max.x, 2.0f, 1e-6f);
    CHECK_APPROX(scaled.bounds_max.y, 2.0f, 1e-6f);
  }

  SECTION("custom color");
  {
    auto colored = qe::loader::STLLoader::parse(stl_path, 1.0f, 0.0f, 0.0f);
    CHECK(colored.success);
    for (const auto &v : colored.vertices) {
      CHECK_APPROX(v.color[0], 1.0f, 1e-6f);
      CHECK_APPROX(v.color[1], 0.0f, 1e-6f);
      CHECK_APPROX(v.color[2], 0.0f, 1e-6f);
    }
  }

  std::filesystem::remove(stl_path);
}

void test_stl_binary_parse() {
  std::cout << "[Test] STLLoader binary parse\n";

  const std::string stl_path = "test_binary.stl";
  {
    std::ofstream f(stl_path, std::ios::binary);

    char header[80] = {};
    std::memcpy(header, "binary stl test", 15);
    f.write(header, 80);

    uint32_t tri_count = 1;
    f.write(reinterpret_cast<char *>(&tri_count), 4);

    float normal[3] = {0.0f, 0.0f, 1.0f};
    f.write(reinterpret_cast<char *>(normal), 12);

    float v0[3] = {0.0f, 0.0f, 0.0f};
    float v1[3] = {1.0f, 0.0f, 0.0f};
    float v2[3] = {0.5f, 1.0f, 0.0f};
    f.write(reinterpret_cast<char *>(v0), 12);
    f.write(reinterpret_cast<char *>(v1), 12);
    f.write(reinterpret_cast<char *>(v2), 12);

    uint16_t attr = 0;
    f.write(reinterpret_cast<char *>(&attr), 2);
  }

  auto result = qe::loader::STLLoader::parse(stl_path);

  SECTION("parse success");
  CHECK(result.success);

  SECTION("triangle count");
  CHECK(result.triangle_count == 1);

  SECTION("3 unique vertices");
  CHECK(result.vertices.size() == 3);
  CHECK(result.indices.size() == 3);

  SECTION("bounds");
  CHECK_APPROX(result.bounds_min.x, 0.0f, 1e-6f);
  CHECK_APPROX(result.bounds_max.x, 1.0f, 1e-6f);
  CHECK_APPROX(result.bounds_max.y, 1.0f, 1e-6f);

  std::filesystem::remove(stl_path);
}

void test_stl_binary_detection() {
  std::cout << "[Test] STLLoader binary detection (SolidWorks header)\n";

  const std::string stl_path = "test_solidworks.stl";
  {
    std::ofstream f(stl_path, std::ios::binary);

    char header[80] = {};
    std::memcpy(header, "solid SolidWorks", 16);
    f.write(header, 80);

    uint32_t tri_count = 1;
    f.write(reinterpret_cast<char *>(&tri_count), 4);

    float normal[3] = {0, 1, 0};
    f.write(reinterpret_cast<char *>(normal), 12);

    float verts[9] = {0, 0, 0, 1, 0, 0, 0, 0, 1};
    f.write(reinterpret_cast<char *>(verts), 36);

    uint16_t attr = 0;
    f.write(reinterpret_cast<char *>(&attr), 2);
  }

  auto result = qe::loader::STLLoader::parse(stl_path);

  SECTION("detected as binary despite 'solid' header");
  CHECK(result.success);
  CHECK(result.triangle_count == 1);
  CHECK(result.vertices.size() == 3);

  std::filesystem::remove(stl_path);
}

void test_stl_binary_dedup() {
  std::cout << "[Test] STLLoader binary deduplication\n";

  const std::string stl_path = "test_dedup.stl";
  {
    std::ofstream f(stl_path, std::ios::binary);

    char header[80] = {};
    f.write(header, 80);

    uint32_t tri_count = 2;
    f.write(reinterpret_cast<char *>(&tri_count), 4);

    float n1[3] = {0, 0, 1};
    float v1[9] = {0, 0, 0, 1, 0, 0, 1, 1, 0};
    uint16_t attr = 0;
    f.write(reinterpret_cast<char *>(n1), 12);
    f.write(reinterpret_cast<char *>(v1), 36);
    f.write(reinterpret_cast<char *>(&attr), 2);

    float n2[3] = {0, 0, 1};
    float v2[9] = {0, 0, 0, 1, 1, 0, 0, 1, 0};
    f.write(reinterpret_cast<char *>(n2), 12);
    f.write(reinterpret_cast<char *>(v2), 36);
    f.write(reinterpret_cast<char *>(&attr), 2);
  }

  auto result = qe::loader::STLLoader::parse(stl_path);

  SECTION("dedup reduces vertex count");
  CHECK(result.success);
  CHECK(result.triangle_count == 2);
  CHECK(result.indices.size() == 6);
  CHECK(result.vertices.size() == 4);

  std::filesystem::remove(stl_path);
}

void test_stl_nonexistent_file() {
  std::cout << "[Test] STLLoader nonexistent file\n";

  auto result = qe::loader::STLLoader::parse("does_not_exist.stl");
  CHECK(!result.success);
  CHECK(!result.error.empty());
}

// ═════════════════════════════════════════════════════════════════════════════
// Vertex Struct Tests
// ═════════════════════════════════════════════════════════════════════════════

void test_vertex_struct() {
  std::cout << "[Test] Vertex defaults\n";

  qe::renderer::Vertex v{};

  SECTION("default position is origin");
  CHECK(v.position[0] == 0.0f && v.position[1] == 0.0f &&
        v.position[2] == 0.0f);

  SECTION("default normal is up");
  CHECK(v.normal[0] == 0.0f && v.normal[1] == 1.0f && v.normal[2] == 0.0f);

  SECTION("default color is white");
  CHECK(v.color[0] == 1.0f && v.color[1] == 1.0f && v.color[2] == 1.0f);

  SECTION("default UV is (0,0)");
  CHECK(v.uv[0] == 0.0f && v.uv[1] == 0.0f);

  SECTION("sizeof(Vertex) = 44 bytes (11 floats)");
  CHECK(sizeof(qe::renderer::Vertex) == 44);
}

// ═════════════════════════════════════════════════════════════════════════════
// VertexHash / VertexEqual Tests
// ═════════════════════════════════════════════════════════════════════════════

void test_vertex_hash() {
  std::cout << "[Test] VertexHash / VertexEqual\n";

  qe::loader::VertexHash hasher;
  qe::loader::VertexEqual eq;

  qe::renderer::Vertex a{};
  a.position[0] = 1.0f;
  a.position[1] = 2.0f;
  a.position[2] = 3.0f;

  qe::renderer::Vertex b{};
  b.position[0] = 1.0f;
  b.position[1] = 2.0f;
  b.position[2] = 3.0f;

  qe::renderer::Vertex c{};
  c.position[0] = 4.0f;
  c.position[1] = 5.0f;
  c.position[2] = 6.0f;

  SECTION("equal vertices have same hash");
  CHECK(hasher(a) == hasher(b));

  SECTION("equal vertices compare equal");
  CHECK(eq(a, b));

  SECTION("different vertices compare not equal");
  CHECK(!eq(a, c));
}

// ═════════════════════════════════════════════════════════════════════════════
// Integration: URDF Hierarchy Tests
// ═════════════════════════════════════════════════════════════════════════════

void test_urdf_hierarchy() {
  std::cout << "[Test] URDF Hierarchy\n";

  const std::string urdf_path = "test_hierarchy.urdf";
  {
    std::ofstream f(urdf_path);
    f << R"(
        <robot name="chain">
            <link name="A"/>
            <link name="B"/>
            <link name="C"/>
            <link name="D"/>
            <joint name="j1" type="revolute">
                <parent link="A"/>
                <child link="B"/>
                <origin xyz="0 1 0"/>
            </joint>
            <joint name="j2" type="revolute">
                <parent link="B"/>
                <child link="C"/>
                <origin xyz="0 1 0"/>
            </joint>
            <joint name="j3" type="fixed">
                <parent link="B"/>
                <child link="D"/>
                <origin xyz="1 0 0"/>
            </joint>
        </robot>
        )";
  }

  auto result = qe::loader::URDFLoader::load(urdf_path);

  SECTION("parse success");
  CHECK(result.success);

  SECTION("root is A");
  CHECK(result.model.root_link_name() == "A");

  SECTION("B has two children (C and D)");
  {
    auto children = result.model.children_of("B");
    CHECK(children.size() == 2);
  }

  SECTION("A has one child (B)");
  {
    auto children = result.model.children_of("A");
    CHECK(children.size() == 1);
    CHECK(children[0]->child_link == "B");
  }

  SECTION("leaf nodes have no children");
  {
    CHECK(result.model.children_of("C").empty());
    CHECK(result.model.children_of("D").empty());
  }

  std::filesystem::remove(urdf_path);
}

// ═════════════════════════════════════════════════════════════════════════════
// Main
// ═════════════════════════════════════════════════════════════════════════════

int main() {
  std::cout << "=== QuatEngine Test Suite ===\n\n";

  // Math
  test_vec3();
  test_quaternion();
  test_mat4();

  // Vertex / Hash
  test_vertex_struct();
  test_vertex_hash();

  // Loaders
  test_urdf_parser();
  test_urdf_hierarchy();
  test_stl_ascii_parse();
  test_stl_binary_parse();
  test_stl_binary_detection();
  test_stl_binary_dedup();
  test_stl_nonexistent_file();

  // Summary
  std::cout << "\n=== Results: " << g_passed << " PASSED, " << g_failed
            << " FAILED (of " << g_total << " total) ===\n";

  return (g_failed == 0) ? 0 : 1;
}
