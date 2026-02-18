#pragma once
/**
 * @file Mesh.h
 * @brief GPU mesh data — VAO/VBO/EBO wrapper for vertex data upload and
 * drawing.
 *
 * Vertex layout: position (3f) + normal (3f) + color (3f) + uv (2f) = 11
 * floats.
 *
 * Resource ownership follows Rule of Five: Mesh owns GPU handles and
 * is move-only (copy is deleted to prevent double-free of GL objects).
 */

#include "GLLoader.h"

#include <cassert>
#include <cmath>
#include <cstddef>
#include <map>
#include <utility>
#include <vector>

namespace qe {
namespace renderer {

// DbC macro — compiles to no-op in release builds
#ifndef NDEBUG
#define QE_REQUIRE(cond, msg) assert((cond) && (msg))
#else
#define QE_REQUIRE(cond, msg) ((void)0)
#endif

static constexpr float kPi = 3.14159265358979323846f;

/** Per-vertex data sent to the GPU. */
struct Vertex {
  float position[3] = {0, 0, 0};
  float normal[3] = {0, 1, 0};
  float color[3] = {1, 1, 1};
  float uv[2] = {0, 0};
};

class Mesh {
public:
  GLuint vao = 0;
  GLuint vbo = 0;
  GLuint ebo = 0;
  GLsizei index_count = 0;

  Mesh() = default;

  // ── Rule of Five: move-only (GPU resource ownership) ──────────────

  Mesh(const Mesh &) = delete;
  Mesh &operator=(const Mesh &) = delete;

  Mesh(Mesh &&other) noexcept
      : vao(other.vao), vbo(other.vbo), ebo(other.ebo),
        index_count(other.index_count) {
    other.vao = 0;
    other.vbo = 0;
    other.ebo = 0;
    other.index_count = 0;
  }

  Mesh &operator=(Mesh &&other) noexcept {
    if (this != &other) {
      destroy();
      vao = other.vao;
      vbo = other.vbo;
      ebo = other.ebo;
      index_count = other.index_count;
      other.vao = 0;
      other.vbo = 0;
      other.ebo = 0;
      other.index_count = 0;
    }
    return *this;
  }

  ~Mesh() { destroy(); }

  // ── Upload / Draw / Destroy ─────────────────────────────────────

  /**
   * Upload vertex + index data to the GPU.
   * @pre vertices is non-empty
   * @pre indices is non-empty
   */
  void upload(const std::vector<Vertex> &vertices,
              const std::vector<unsigned int> &indices) {
    QE_REQUIRE(!vertices.empty(), "Mesh::upload: vertices must not be empty");
    QE_REQUIRE(!indices.empty(), "Mesh::upload: indices must not be empty");

    // Prevent GPU buffer leak on re-upload
    if (vao)
      destroy();

    index_count = static_cast<GLsizei>(indices.size());

    gl::glGenVertexArrays(1, &vao);
    gl::glGenBuffers(1, &vbo);
    gl::glGenBuffers(1, &ebo);

    gl::glBindVertexArray(vao);

    gl::glBindBuffer(GL_ARRAY_BUFFER, vbo);
    gl::glBufferData(GL_ARRAY_BUFFER,
                     static_cast<GLsizeiptr>(vertices.size() * sizeof(Vertex)),
                     vertices.data(), GL_STATIC_DRAW);

    gl::glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo);
    gl::glBufferData(
        GL_ELEMENT_ARRAY_BUFFER,
        static_cast<GLsizeiptr>(indices.size() * sizeof(unsigned int)),
        indices.data(), GL_STATIC_DRAW);

    setup_vertex_attributes();
    gl::glBindVertexArray(0);
  }

  /** @pre mesh has been uploaded (vao != 0) */
  void draw() const {
    QE_REQUIRE(vao != 0, "Mesh::draw: mesh not uploaded");
    gl::glBindVertexArray(vao);
    gl::glDrawElements(GL_TRIANGLES, index_count, GL_UNSIGNED_INT, nullptr);
    gl::glBindVertexArray(0);
  }

  /** Draw with GL_LINES mode (for grids and wireframes). */
  void draw_lines() const {
    QE_REQUIRE(vao != 0, "Mesh::draw_lines: mesh not uploaded");
    gl::glBindVertexArray(vao);
    gl::glDrawElements(GL_LINES, index_count, GL_UNSIGNED_INT, nullptr);
    gl::glBindVertexArray(0);
  }

  /** @pre mesh has been uploaded (vao != 0) */
  void draw_instanced(GLsizei instance_count) const {
    QE_REQUIRE(vao != 0, "Mesh::draw_instanced: mesh not uploaded");
    gl::glBindVertexArray(vao);
    gl::glDrawElementsInstanced(GL_TRIANGLES, index_count, GL_UNSIGNED_INT,
                                nullptr, instance_count);
    gl::glBindVertexArray(0);
  }

  void destroy() {
    if (ebo) {
      gl::glDeleteBuffers(1, &ebo);
      ebo = 0;
    }
    if (vbo) {
      gl::glDeleteBuffers(1, &vbo);
      vbo = 0;
    }
    if (vao) {
      gl::glDeleteVertexArrays(1, &vao);
      vao = 0;
    }
    index_count = 0;
  }

  // ── Primitive Generators ────────────────────────────────────────────

  /** Unit cube with per-face normals, colors, and UV coordinates. */
  static Mesh create_cube() {
    Mesh mesh;
    std::vector<Vertex> vertices = {
        // Front (Z+) — Blue
        {{-0.5f, -0.5f, 0.5f}, {0, 0, 1}, {0.2f, 0.4f, 0.9f}, {0, 0}},
        {{0.5f, -0.5f, 0.5f}, {0, 0, 1}, {0.2f, 0.4f, 0.9f}, {1, 0}},
        {{0.5f, 0.5f, 0.5f}, {0, 0, 1}, {0.3f, 0.5f, 1.0f}, {1, 1}},
        {{-0.5f, 0.5f, 0.5f}, {0, 0, 1}, {0.3f, 0.5f, 1.0f}, {0, 1}},
        // Back (Z-) — Teal
        {{0.5f, -0.5f, -0.5f}, {0, 0, -1}, {0.0f, 0.7f, 0.7f}, {0, 0}},
        {{-0.5f, -0.5f, -0.5f}, {0, 0, -1}, {0.0f, 0.7f, 0.7f}, {1, 0}},
        {{-0.5f, 0.5f, -0.5f}, {0, 0, -1}, {0.1f, 0.8f, 0.8f}, {1, 1}},
        {{0.5f, 0.5f, -0.5f}, {0, 0, -1}, {0.1f, 0.8f, 0.8f}, {0, 1}},
        // Top (Y+) — Green
        {{-0.5f, 0.5f, 0.5f}, {0, 1, 0}, {0.2f, 0.9f, 0.3f}, {0, 0}},
        {{0.5f, 0.5f, 0.5f}, {0, 1, 0}, {0.2f, 0.9f, 0.3f}, {1, 0}},
        {{0.5f, 0.5f, -0.5f}, {0, 1, 0}, {0.3f, 1.0f, 0.4f}, {1, 1}},
        {{-0.5f, 0.5f, -0.5f}, {0, 1, 0}, {0.3f, 1.0f, 0.4f}, {0, 1}},
        // Bottom (Y-) — Orange
        {{-0.5f, -0.5f, -0.5f}, {0, -1, 0}, {0.9f, 0.5f, 0.1f}, {0, 0}},
        {{0.5f, -0.5f, -0.5f}, {0, -1, 0}, {0.9f, 0.5f, 0.1f}, {1, 0}},
        {{0.5f, -0.5f, 0.5f}, {0, -1, 0}, {1.0f, 0.6f, 0.2f}, {1, 1}},
        {{-0.5f, -0.5f, 0.5f}, {0, -1, 0}, {1.0f, 0.6f, 0.2f}, {0, 1}},
        // Right (X+) — Red
        {{0.5f, -0.5f, 0.5f}, {1, 0, 0}, {0.9f, 0.2f, 0.2f}, {0, 0}},
        {{0.5f, -0.5f, -0.5f}, {1, 0, 0}, {0.9f, 0.2f, 0.2f}, {1, 0}},
        {{0.5f, 0.5f, -0.5f}, {1, 0, 0}, {1.0f, 0.3f, 0.3f}, {1, 1}},
        {{0.5f, 0.5f, 0.5f}, {1, 0, 0}, {1.0f, 0.3f, 0.3f}, {0, 1}},
        // Left (X-) — Purple
        {{-0.5f, -0.5f, -0.5f}, {-1, 0, 0}, {0.6f, 0.2f, 0.9f}, {0, 0}},
        {{-0.5f, -0.5f, 0.5f}, {-1, 0, 0}, {0.6f, 0.2f, 0.9f}, {1, 0}},
        {{-0.5f, 0.5f, 0.5f}, {-1, 0, 0}, {0.7f, 0.3f, 1.0f}, {1, 1}},
        {{-0.5f, 0.5f, -0.5f}, {-1, 0, 0}, {0.7f, 0.3f, 1.0f}, {0, 1}},
    };

    std::vector<unsigned int> indices;
    for (unsigned int f = 0; f < 6; ++f) {
      unsigned int b = f * 4;
      indices.push_back(b + 0);
      indices.push_back(b + 1);
      indices.push_back(b + 2);
      indices.push_back(b + 0);
      indices.push_back(b + 2);
      indices.push_back(b + 3);
    }

    mesh.upload(vertices, indices);
    return mesh;
  }

  /** Large textured floor plane on XZ. UVs tile the texture. */
  static Mesh create_floor_plane(float half_size = 20.0f,
                                 float uv_scale = 4.0f) {
    Mesh mesh;
    float s = half_size;
    float u = uv_scale;

    std::vector<Vertex> vertices = {
        {{-s, 0, -s}, {0, 1, 0}, {1, 1, 1}, {0, 0}},
        {{s, 0, -s}, {0, 1, 0}, {1, 1, 1}, {u, 0}},
        {{s, 0, s}, {0, 1, 0}, {1, 1, 1}, {u, u}},
        {{-s, 0, s}, {0, 1, 0}, {1, 1, 1}, {0, u}},
    };

    std::vector<unsigned int> indices = {0, 1, 2, 0, 2, 3};
    mesh.upload(vertices, indices);
    return mesh;
  }

  /**
   * Low-poly sphere (icosphere with subdivisions).
   * Uses midpoint caching to avoid duplicate vertices at shared edges.
   * @pre subdivisions >= 0
   * @pre r > 0
   */
  static Mesh create_sphere(int subdivisions = 2, float r = 0.5f,
                            float cr = 0.8f, float cg = 0.6f, float cb = 0.3f) {
    QE_REQUIRE(subdivisions >= 0,
               "Mesh::create_sphere: subdivisions must be >= 0");
    QE_REQUIRE(r > 0.0f, "Mesh::create_sphere: radius must be positive");

    Mesh mesh;
    std::vector<Vertex> vertices;
    std::vector<unsigned int> indices;

    // Start with icosahedron
    const float t = (1.0f + std::sqrt(5.0f)) / 2.0f;
    std::vector<float> pos = {
        -1, t,  0,  1, t, 0,  -1, -t, 0,  1, -t, 0, 0,  -1, t,  0,  1, t,
        0,  -1, -t, 0, 1, -t, t,  0,  -1, t, 0,  1, -t, 0,  -1, -t, 0, 1,
    };
    // Normalize all to unit sphere
    for (size_t i = 0; i < pos.size(); i += 3) {
      float len = std::sqrt(pos[i] * pos[i] + pos[i + 1] * pos[i + 1] +
                            pos[i + 2] * pos[i + 2]);
      pos[i] /= len;
      pos[i + 1] /= len;
      pos[i + 2] /= len;
    }

    std::vector<unsigned int> idx = {
        0, 11, 5,  0, 5,  1, 0, 1, 7, 0, 7,  10, 0, 10, 11, 1, 5, 9, 5, 11,
        4, 11, 10, 2, 10, 7, 6, 7, 1, 8, 3,  9,  4, 3,  4,  2, 3, 2, 6, 3,
        6, 8,  3,  8, 9,  4, 9, 5, 2, 4, 11, 6,  2, 10, 8,  6, 7, 9, 8, 1,
    };

    // Subdivide with midpoint cache to avoid duplicate vertices
    for (int s = 0; s < subdivisions; ++s) {
      std::vector<unsigned int> new_idx;
      std::map<std::pair<unsigned int, unsigned int>, unsigned int>
          midpoint_cache;

      auto get_midpoint = [&](unsigned int i0,
                              unsigned int i1) -> unsigned int {
        // Canonical edge ordering so (a,b) and (b,a) map to same midpoint
        auto edge = (i0 < i1) ? std::make_pair(i0, i1) : std::make_pair(i1, i0);
        auto it = midpoint_cache.find(edge);
        if (it != midpoint_cache.end())
          return it->second;

        float mx = (pos[i0 * 3] + pos[i1 * 3]) * 0.5f;
        float my = (pos[i0 * 3 + 1] + pos[i1 * 3 + 1]) * 0.5f;
        float mz = (pos[i0 * 3 + 2] + pos[i1 * 3 + 2]) * 0.5f;
        float len = std::sqrt(mx * mx + my * my + mz * mz);
        mx /= len;
        my /= len;
        mz /= len;
        unsigned int ni = static_cast<unsigned int>(pos.size() / 3);
        pos.push_back(mx);
        pos.push_back(my);
        pos.push_back(mz);
        midpoint_cache[edge] = ni;
        return ni;
      };

      for (size_t i = 0; i < idx.size(); i += 3) {
        unsigned int a = idx[i], b = idx[i + 1], c = idx[i + 2];
        unsigned int ab = get_midpoint(a, b);
        unsigned int bc = get_midpoint(b, c);
        unsigned int ca = get_midpoint(c, a);
        new_idx.push_back(a);
        new_idx.push_back(ab);
        new_idx.push_back(ca);
        new_idx.push_back(b);
        new_idx.push_back(bc);
        new_idx.push_back(ab);
        new_idx.push_back(c);
        new_idx.push_back(ca);
        new_idx.push_back(bc);
        new_idx.push_back(ab);
        new_idx.push_back(bc);
        new_idx.push_back(ca);
      }
      idx = new_idx;
    }

    // Build vertex data
    for (size_t i = 0; i < pos.size(); i += 3) {
      Vertex v{};
      v.position[0] = pos[i] * r;
      v.position[1] = pos[i + 1] * r;
      v.position[2] = pos[i + 2] * r;
      v.normal[0] = pos[i];
      v.normal[1] = pos[i + 1];
      v.normal[2] = pos[i + 2];
      v.color[0] = cr;
      v.color[1] = cg;
      v.color[2] = cb;
      v.uv[0] = 0.5f + std::atan2(pos[i + 2], pos[i]) / (2.0f * kPi);
      v.uv[1] = 0.5f - std::asin(pos[i + 1]) / kPi;
      vertices.push_back(v);
    }

    mesh.upload(vertices, idx);
    return mesh;
  }

  /**
   * Grid lines on XZ plane (for spatial reference).
   * Draw with draw_lines() since indices are line pairs.
   */
  static Mesh create_grid(int half_size = 10, float spacing = 1.0f) {
    Mesh mesh;
    std::vector<Vertex> vertices;
    std::vector<unsigned int> indices;
    unsigned int idx = 0;
    float extent = half_size * spacing;

    for (int i = -half_size; i <= half_size; ++i) {
      float pos = i * spacing;
      float brightness = (i == 0) ? 0.6f : 0.25f;

      vertices.push_back({{pos, 0.0f, -extent},
                          {0, 1, 0},
                          {brightness, brightness, brightness},
                          {0, 0}});
      vertices.push_back({{pos, 0.0f, extent},
                          {0, 1, 0},
                          {brightness, brightness, brightness},
                          {1, 0}});
      indices.push_back(idx++);
      indices.push_back(idx++);

      vertices.push_back({{-extent, 0.0f, pos},
                          {0, 1, 0},
                          {brightness, brightness, brightness},
                          {0, 0}});
      vertices.push_back({{extent, 0.0f, pos},
                          {0, 1, 0},
                          {brightness, brightness, brightness},
                          {1, 0}});
      indices.push_back(idx++);
      indices.push_back(idx++);
    }

    // DRY: use upload() instead of duplicating vertex attribute setup
    mesh.upload(vertices, indices);
    return mesh;
  }

private:
  /**
   * Configure vertex attribute pointers for the standard vertex layout.
   * DRY: shared by upload() — all mesh creation goes through upload().
   */
  static void setup_vertex_attributes() {
    // Position (location = 0)
    gl::glVertexAttribPointer(
        0, 3, GL_FLOAT, GL_FALSE, sizeof(Vertex),
        reinterpret_cast<void *>(offsetof(Vertex, position)));
    gl::glEnableVertexAttribArray(0);

    // Normal (location = 1)
    gl::glVertexAttribPointer(
        1, 3, GL_FLOAT, GL_FALSE, sizeof(Vertex),
        reinterpret_cast<void *>(offsetof(Vertex, normal)));
    gl::glEnableVertexAttribArray(1);

    // Color (location = 2)
    gl::glVertexAttribPointer(
        2, 3, GL_FLOAT, GL_FALSE, sizeof(Vertex),
        reinterpret_cast<void *>(offsetof(Vertex, color)));
    gl::glEnableVertexAttribArray(2);

    // UV (location = 3)
    gl::glVertexAttribPointer(3, 2, GL_FLOAT, GL_FALSE, sizeof(Vertex),
                              reinterpret_cast<void *>(offsetof(Vertex, uv)));
    gl::glEnableVertexAttribArray(3);
  }
};

} // namespace renderer
} // namespace qe
