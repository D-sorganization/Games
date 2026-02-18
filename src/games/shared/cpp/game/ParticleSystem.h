#pragma once
/**
 * @file ParticleSystem.h
 * @brief GPU-instanced particle system for debris and visual effects.
 *
 * Uses instanced rendering to draw thousands of particles efficiently.
 * Each particle is a small cube mesh drawn via glDrawElementsInstanced.
 */

#include "../math/Mat4.h"
#include "../math/Vec3.h"
#include "../renderer/Mesh.h"
#include "../renderer/Shader.h"

#include <memory>
#include <random>
#include <vector>

namespace qe {
namespace game {

struct Particle {
  math::Vec3 position;
  math::Vec3 velocity;
  math::Vec3 color;
  float life = 0.0f;
  float max_life = 1.0f;
  float scale = 0.1f;
};

class ParticleSystem {
public:
  std::vector<Particle> particles;
  std::shared_ptr<renderer::Mesh> particle_mesh;

  ParticleSystem() = default;

  /** Initialize particle mesh and instanced shader. */
  void init() {
    particle_mesh =
        std::make_shared<renderer::Mesh>(renderer::Mesh::create_cube());
    instanced_shader.load_from_files("shaders/particle_instanced.vert",
                                     "shaders/particle_instanced.frag");
  }

  void spawn(const math::Vec3 &pos, int count, const math::Vec3 &color) {
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_real_distribution<float> dis(-1.0f, 1.0f);

    for (int i = 0; i < count; ++i) {
      Particle p;
      p.position = pos;
      float vx = dis(gen), vy = dis(gen) + 2.0f, vz = dis(gen);
      float len = std::sqrt(vx * vx + vy * vy + vz * vz);
      if (len > 1e-6f) {
        vx /= len;
        vy /= len;
        vz /= len;
      }
      float speed = dis(gen) + 2.0f;
      p.velocity = math::Vec3(vx * speed, vy * speed, vz * speed);
      p.color = color;
      p.life = 1.0f + dis(gen) * 0.5f;
      p.max_life = p.life;
      p.scale = 0.05f + dis(gen) * 0.02f;
      particles.push_back(p);
    }
  }

  void update(float dt) {
    for (auto it = particles.begin(); it != particles.end();) {
      it->life -= dt;
      if (it->life <= 0) {
        it = particles.erase(it);
      } else {
        it->velocity.y -= 9.8f * dt;
        it->position = it->position + it->velocity * dt;

        if (it->position.y < 0) {
          it->position.y = 0;
          it->velocity.y *= -0.5f;
          it->velocity.x *= 0.8f;
          it->velocity.z *= 0.8f;
        }
        ++it;
      }
    }
  }

  void draw(const math::Mat4 &view_proj) {
    if (!particle_mesh || particles.empty())
      return;
    if (!instancing_initialized_)
      setup_instancing();

    draw_models_.clear();
    draw_colors_.clear();
    draw_models_.reserve(particles.size());
    draw_colors_.reserve(particles.size());

    for (const auto &p : particles) {
      draw_models_.push_back(math::Mat4::translate(p.position) *
                             math::Mat4::scale(p.scale));
      draw_colors_.push_back(p.color);
    }

    using namespace renderer::gl;

    glBindBuffer(GL_ARRAY_BUFFER, instance_vbo_model_);
    glBufferData(
        GL_ARRAY_BUFFER,
        static_cast<GLsizeiptr>(draw_models_.size() * sizeof(math::Mat4)),
        draw_models_.data(), GL_STREAM_DRAW);

    glBindBuffer(GL_ARRAY_BUFFER, instance_vbo_color_);
    glBufferData(
        GL_ARRAY_BUFFER,
        static_cast<GLsizeiptr>(draw_colors_.size() * sizeof(math::Vec3)),
        draw_colors_.data(), GL_STREAM_DRAW);

    instanced_shader.use();
    instanced_shader.set_mat4("uViewProjection", view_proj);
    instanced_shader.set_vec3("uLightDir", {0.5f, 1.0f, 0.3f});
    instanced_shader.set_vec3("uSunColor", {1.0f, 1.0f, 0.9f});
    instanced_shader.set_vec3("uAmbient", {0.3f, 0.3f, 0.4f});

    particle_mesh->draw_instanced(static_cast<GLsizei>(particles.size()));
  }

  renderer::Shader instanced_shader;

private:
  // Mat4 column stride for instanced vertex attributes (4 floats per column)
  static constexpr size_t kMat4ColStride = sizeof(float) * 4;

  GLuint instance_vbo_model_ = 0;
  GLuint instance_vbo_color_ = 0;
  bool instancing_initialized_ = false;

  // Reusable draw buffers (avoid allocation per frame)
  std::vector<math::Mat4> draw_models_;
  std::vector<math::Vec3> draw_colors_;

  void setup_instancing() {
    if (instancing_initialized_ || !particle_mesh)
      return;

    using namespace renderer::gl;
    glBindVertexArray(particle_mesh->vao);

    // Instance Model matrix (locations 4-7, one vec4 per column)
    glGenBuffers(1, &instance_vbo_model_);
    glBindBuffer(GL_ARRAY_BUFFER, instance_vbo_model_);
    glBufferData(GL_ARRAY_BUFFER,
                 static_cast<GLsizeiptr>(2048 * sizeof(math::Mat4)), nullptr,
                 GL_STREAM_DRAW);

    for (int i = 0; i < 4; ++i) {
      glEnableVertexAttribArray(4 + i);
      glVertexAttribPointer(4 + i, 4, GL_FLOAT, GL_FALSE, sizeof(math::Mat4),
                            reinterpret_cast<void *>(i * kMat4ColStride));
      glVertexAttribDivisor(4 + i, 1);
    }

    // Instance Color (location 8)
    glGenBuffers(1, &instance_vbo_color_);
    glBindBuffer(GL_ARRAY_BUFFER, instance_vbo_color_);
    glBufferData(GL_ARRAY_BUFFER,
                 static_cast<GLsizeiptr>(2048 * sizeof(math::Vec3)), nullptr,
                 GL_STREAM_DRAW);

    glEnableVertexAttribArray(8);
    glVertexAttribPointer(8, 3, GL_FLOAT, GL_FALSE, sizeof(math::Vec3),
                          nullptr);
    glVertexAttribDivisor(8, 1);

    glBindVertexArray(0);
    instancing_initialized_ = true;
  }
};

} // namespace game
} // namespace qe
