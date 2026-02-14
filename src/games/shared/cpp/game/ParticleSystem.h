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

    void draw(renderer::Shader& shader) {
        if (!particle_mesh) return;

        // Setup common state
        shader.set_int("uUseTexture", 0);

        for (const auto& p : particles) {
            math::Mat4 model = math::Mat4::identity();
            model = math::Mat4::translate(p.position) * math::Mat4::scale(p.scale);
            
            // Billboard rotation (face camera)?
            // For now just world aligned.
            
            shader.set_mat4("uModel", model);
            shader.set_vec3("uColor", p.color); // Needs fragment shader support or use ambient/diffuse uniform trick
            
            particle_mesh->draw();
        }
    }
};

} // namespace game
} // namespace qe
