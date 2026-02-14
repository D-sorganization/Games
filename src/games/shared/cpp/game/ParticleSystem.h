#pragma once

#include "renderer/Shader.h"
#include "renderer/Mesh.h"
#include "math/Vec3.h"
#include "math/Mat4.h"

#include <vector>
#include <memory>
#include <random>

namespace qe {
namespace game {

struct Particle {
    math::Vec3 position;
    math::Vec3 velocity;
    math::Vec3 color;
    float life = 0.0f; // Remaining life
    float max_life = 1.0f;
    float scale = 0.1f;
};

class ParticleSystem {
public:
    std::vector<Particle> particles;
    std::shared_ptr<renderer::Mesh> particle_mesh; // Cube?

    ParticleSystem() = default;

    void init() {
        // Use standard cube for particles
        particle_mesh = std::make_shared<renderer::Mesh>(renderer::Mesh::create_cube());
    }

    void spawn(const math::Vec3& pos, int count, const math::Vec3& color) {
        std::random_device rd;
        std::mt19937 gen(rd());
        std::uniform_real_distribution<> dis(-1.0, 1.0);

        for (int i = 0; i < count; ++i) {
            Particle p;
            p.position = pos;
            p.velocity = math::Vec3(dis(gen), dis(gen)+2.0f, dis(gen)).normalized() * (dis(gen) + 2.0f); // Upward burst
            p.color = color;
            p.life = 1.0f + static_cast<float>(dis(gen)) * 0.5f;
            p.max_life = p.life;
            p.scale = 0.05f + static_cast<float>(dis(gen)) * 0.02f;
            particles.push_back(p);
        }
    }

    void update(float dt) {
        for (auto it = particles.begin(); it != particles.end();) {
            it->life -= dt;
            if (it->life <= 0) {
                it = particles.erase(it);
            } else {
                // Physics
                it->velocity.y -= 9.8f * dt; // Gravity
                it->position = it->position + it->velocity * dt;
                
                // Ground collision (simple)
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

    renderer::Shader instanced_shader;
    GLuint instance_vbo_model = 0;
    GLuint instance_vbo_color = 0;
    bool instancing_initialized = false;

    void init() {
        particle_mesh = std::make_shared<renderer::Mesh>(renderer::Mesh::create_cube());
        // Load instanced shader
        instanced_shader.load_from_files("shaders/particle_instanced.vert", "shaders/particle_instanced.frag");
    }
    
    void setup_instancing() {
        if (instancing_initialized || !particle_mesh) return;
        
        using namespace renderer::gl;
        glBindVertexArray(particle_mesh->vao);
        
        // Instance Model (4,5,6,7)
        glGenBuffers(1, &instance_vbo_model);
        glBindBuffer(GL_ARRAY_BUFFER, instance_vbo_model);
        // Reserve buffer
        glBufferData(GL_ARRAY_BUFFER, 2048 * sizeof(math::Mat4), nullptr, GL_STREAM_DRAW);
        
        for (int i = 0; i < 4; ++i) {
            glEnableVertexAttribArray(4 + i);
            glVertexAttribPointer(4 + i, 4, GL_FLOAT, GL_FALSE, sizeof(math::Mat4), (void*)(i * sizeof(math::Vec4)));
            glVertexAttribDivisor(4 + i, 1);
        }
        
        // Instance Color (8)
        glGenBuffers(1, &instance_vbo_color);
        glBindBuffer(GL_ARRAY_BUFFER, instance_vbo_color);
        glBufferData(GL_ARRAY_BUFFER, 2048 * sizeof(math::Vec3), nullptr, GL_STREAM_DRAW);
        
        glEnableVertexAttribArray(8);
        glVertexAttribPointer(8, 3, GL_FLOAT, GL_FALSE, sizeof(math::Vec3), (void*)0);
        glVertexAttribDivisor(8, 1);
        
        glBindVertexArray(0);
        instancing_initialized = true;
    }

    void draw(const math::Mat4& view_proj) {
         if (!particle_mesh || particles.empty()) return;
         if (!instancing_initialized) setup_instancing();
         
         static std::vector<math::Mat4> models;
         static std::vector<math::Vec3> colors;
         models.clear(); 
         colors.clear();
         models.reserve(particles.size()); 
         colors.reserve(particles.size());
         
         for (const auto& p : particles) {
            models.push_back(math::Mat4::translate(p.position) * math::Mat4::scale(p.scale));
            colors.push_back(p.color);
         }
         
         using namespace renderer::gl;
         
         // Orphan buffer if too small? For simplicty just re-upload
         glBindBuffer(GL_ARRAY_BUFFER, instance_vbo_model);
         glBufferData(GL_ARRAY_BUFFER, models.size() * sizeof(math::Mat4), models.data(), GL_STREAM_DRAW);
         
         glBindBuffer(GL_ARRAY_BUFFER, instance_vbo_color);
         glBufferData(GL_ARRAY_BUFFER, colors.size() * sizeof(math::Vec3), colors.data(), GL_STREAM_DRAW);
         
         instanced_shader.use();
         instanced_shader.set_mat4("uViewProjection", view_proj);
         // Default light
         instanced_shader.set_vec3("uLightDir", {0.5f, 1.0f, 0.3f});
         instanced_shader.set_vec3("uSunColor", {1.0f, 1.0f, 0.9f});
         instanced_shader.set_vec3("uAmbient", {0.3f, 0.3f, 0.4f});
         
         particle_mesh->draw_instanced(static_cast<GLsizei>(particles.size()));
    }
};

} // namespace game
} // namespace qe
