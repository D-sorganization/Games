/**
 * @file main.cpp
 * @brief QuatGolf — 3D golf game built on shared C++ engine.
 *
 * Thin orchestration layer. All logic lives in:
 *   - terrain/Terrain.h      (heightmap mesh + surface queries)
 *   - course/CourseBuilder.h  (hole layout → terrain stamping)
 *   - physics/BallPhysics.h  (flight, bounce, roll)
 *   - game/Club.h            (club selection, launch parameters)
 *   - shared/input/           (keyboard + gamepad)
 *   - shared/renderer/        (GL, camera, shaders)
 */

#include "game/Club.h"
#include "physics/BallPhysics.h"
#include "course/CourseBuilder.h"
#include "course/Hole.h"
#include "terrain/Terrain.h"
#include "terrain/Surface.h"

#include "input/InputManager.h"
#include "math/Mat4.h"
#include "math/Quaternion.h"
#include "math/Vec3.h"
#include "renderer/Camera.h"
#include "renderer/GLLoader.h"
#include "renderer/Mesh.h"
#include "renderer/Shader.h"
#include "game/EnemyManager.h"
#include "game/ParticleSystem.h"
#include "audio/AudioSystem.h"
#include "renderer/Texture.h"

#include <SDL.h>

#include <iostream>
#include <sstream>
#include <string>
#include <vector>

// ── Application State ───────────────────────────────────────────────────────

struct App {
    SDL_Window*   window     = nullptr;
    SDL_GLContext  gl_context = nullptr;
    bool running = true;

    // Subsystems
    qe::input::InputManager input;
    qe::renderer::Camera    camera;
    qe::renderer::Shader    world_shader;
    qe::renderer::Shader    hud_shader;

    // Course
    qg::terrain::Terrain terrain;
    std::vector<qg::course::Hole> holes;
    int current_hole = 0;

    // Meshes (reused)
    qe::renderer::Mesh ball_mesh;
    qe::renderer::Mesh flag_pole;
    qe::renderer::Mesh flag_mesh;
    qe::renderer::Mesh power_bar_bg;
    qe::renderer::Mesh power_bar_fill;
    qe::renderer::Mesh aim_line;

    // Entities
    // Entities
    qe::game::EnemyManager enemy_manager;
    qe::game::ParticleSystem particle_system;
    qe::audio::AudioSystem audio_system;

    // Ball state
    qg::physics::BallPhysics physics;
    qg::physics::BallState   ball;

    // Shot control
    int selected_club = 0;  // Index into CLUBS[]
    float aim_yaw = 0.0f;
    float power   = 0.0f;
    bool  charging = false;
    bool  ball_in_play = false;
    int   stroke_count = 0;
    int   total_score = 0; // Game score (points)
    std::vector<int> scores;  // Per-hole stroke count

    // Visual
    float time = 0.0f;
    bool  free_cam = false;

    // Timing
    Uint64 last_time = 0;
    int    frame_count = 0;
    float  fps_timer = 0.0f;
    float  current_fps = 0.0f;
};

// ── Forward Declarations ────────────────────────────────────────────────────
bool init_window(App& app);
bool init_gl(App& app);
void init_assets(App& app);
void init_course(App& app);
void setup_hole(App& app, int hole_idx);
void handle_events(App& app);
void update(App& app, float dt);
void render_world(App& app);
void render_hud(App& app);
void update_title(App& app);
void cleanup(App& app);

// Helper meshes
void build_aim_line(App& app);
void build_power_bar(App& app);

// ── Entry Point ─────────────────────────────────────────────────────────────
int main(int /*argc*/, char* /*argv*/[]) {
    App app;

    if (!init_window(app)) return 1;
    if (!init_gl(app))     return 1;
    init_assets(app);
    init_course(app);

    // Camera
    qe::renderer::Camera::Config cc;
    cc.aspect = 1280.0f / 720.0f;
    cc.smoothing = 0.90f;
    cc.move_speed = 15.0f;
    cc.sprint_mult = 3.0f;
    cc.near_z = 0.05f;
    cc.far_z = 500.0f;
    app.camera = qe::renderer::Camera(cc);
    app.camera.set_fov(50.0f * 3.14159f / 180.0f);  // 50° FOV for golf

    // Input
    app.input.init();
    app.input.set_gamepad_look_speed(3.0f);

    // Start on hole 1
    setup_hole(app, 0);

    SDL_SetRelativeMouseMode(SDL_TRUE);
    app.last_time = SDL_GetPerformanceCounter();

    std::cout << "\nQuatGolf v0.1 — 3-Hole Course\n"
              << "  1-9          Select club\n"
              << "  Mouse / R.Stick  Aim\n"
              << "  Space / A    Power (hold + release)\n"
              << "  Tab / Y      Free camera toggle\n"
              << "  N / B        Next hole\n"
              << "  R / Back     Reset ball\n"
              << "  F            Wireframe\n"
              << "  Esc          Quit\n";

    while (app.running) {
        Uint64 now = SDL_GetPerformanceCounter();
        float dt = static_cast<float>(now - app.last_time) /
                   static_cast<float>(SDL_GetPerformanceFrequency());
        app.last_time = now;
        if (dt > 0.1f) dt = 0.1f;

        handle_events(app);
        update(app, dt);
        render_world(app);
        render_hud(app);
        SDL_GL_SwapWindow(app.window);

        app.frame_count++;
        app.fps_timer += dt;
        if (app.fps_timer >= 0.5f) {
            app.current_fps = static_cast<float>(app.frame_count) / app.fps_timer;
            update_title(app);
            app.frame_count = 0;
            app.fps_timer = 0.0f;
        }
    }

    cleanup(app);
    return 0;
}

// ── Init: Window ────────────────────────────────────────────────────────────
bool init_window(App& app) {
    if (SDL_Init(SDL_INIT_VIDEO | SDL_INIT_TIMER | SDL_INIT_GAMECONTROLLER) != 0) {
        std::cerr << "SDL: " << SDL_GetError() << std::endl;
        return false;
    }
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, 3);
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, 3);
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_PROFILE_MASK, SDL_GL_CONTEXT_PROFILE_CORE);
    SDL_GL_SetAttribute(SDL_GL_DOUBLEBUFFER, 1);
    SDL_GL_SetAttribute(SDL_GL_DEPTH_SIZE, 24);

    app.window = SDL_CreateWindow("QuatGolf",
        SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED, 1280, 720,
        SDL_WINDOW_OPENGL | SDL_WINDOW_SHOWN | SDL_WINDOW_RESIZABLE);
    if (!app.window) return false;

    app.gl_context = SDL_GL_CreateContext(app.window);
    if (!app.gl_context) return false;

    SDL_GL_SetSwapInterval(1);
    return true;
}

// ── Init: OpenGL ────────────────────────────────────────────────────────────
bool init_gl(App& app) {
    if (!qe::renderer::gl::load()) return false;

    const char* gpu = reinterpret_cast<const char*>(
        qe::renderer::gl::glGetString(GL_RENDERER));
    std::cout << "GPU: " << (gpu ? gpu : "?") << std::endl;

    using namespace qe::renderer::gl;
    glEnable(GL_DEPTH_TEST);
    glEnable(GL_CULL_FACE);
    glCullFace(GL_BACK);
    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    glClearColor(0.45f, 0.65f, 0.85f, 1.0f);  // Sky blue

    // Compile shaders
    if (!app.world_shader.load_from_files("shaders/basic.vert", "shaders/basic.frag"))
        return false;

    const char* hud_v = R"(#version 330 core
        layout(location=0) in vec3 aPos;
        layout(location=2) in vec3 aColor;
        out vec3 vColor;
        void main() { gl_Position=vec4(aPos,1); vColor=aColor; })";
    const char* hud_f = R"(#version 330 core
        in vec3 vColor; out vec4 FragColor;
        void main() { FragColor=vec4(vColor,0.9); })";
    return app.hud_shader.compile(hud_v, hud_f);
}

// ── Init: Assets ────────────────────────────────────────────────────────────
void init_assets(App& app) {
    // Ball — small white sphere
    app.ball_mesh = qe::renderer::Mesh::create_sphere(3, 0.15f, 1, 1, 1);

    // Flag pole — tall thin cube
    {
        using qe::renderer::Vertex;
        std::vector<Vertex> v;
        std::vector<unsigned> idx;
        // Simple line representation
        Vertex top, bot;
        bot.position[0] = 0; bot.position[1] = 0; bot.position[2] = 0;
        bot.color[0] = 0.3f; bot.color[1] = 0.3f; bot.color[2] = 0.3f;
        top.position[0] = 0; top.position[1] = 2.5f; top.position[2] = 0;
        top.color[0] = 0.3f; top.color[1] = 0.3f; top.color[2] = 0.3f;
        v.push_back(bot); v.push_back(top);
        idx = {0, 1};
        app.flag_pole.upload(v, idx);
        app.flag_pole.index_count = 2;
    }

    // Flag — triangle
    {
        using qe::renderer::Vertex;
        std::vector<Vertex> v;
        Vertex a, b, c;
        a.position[0] = 0;    a.position[1] = 2.5f; a.position[2] = 0;
        b.position[0] = 0;    b.position[1] = 2.0f; b.position[2] = 0;
        c.position[0] = 0.5f; c.position[1] = 2.25f; c.position[2] = 0;
        a.color[0] = 1; a.color[1] = 0; a.color[2] = 0;
        b.color[0] = 1; b.color[1] = 0; b.color[2] = 0;
        c.color[0] = 0.9f; c.color[1] = 0.1f; c.color[2] = 0;
        a.normal[1] = b.normal[1] = c.normal[1] = 0;
        a.normal[2] = b.normal[2] = c.normal[2] = 1;
        v = {a, b, c};
        std::vector<unsigned> idx = {0, 1, 2};
        app.flag_mesh.upload(v, idx);
    }

    build_power_bar(app);
    build_aim_line(app);

    // Humanoid Enemies
    app.enemy_manager.init();
    app.particle_system.init();
    
    // Spawn a few sample enemies
    app.enemy_manager.spawn("grunt", {2.0f, 0.0f, 2.0f});
    app.enemy_manager.spawn("grunt", {-2.0f, 0.0f, 3.0f});
    app.enemy_manager.spawn("grunt", {0.0f, 0.0f, 5.0f});

    // If other types exist (need to generate them first!)
    // app.enemy_manager.spawn("scout", {4.0f, 0.0f, 4.0f});
}

void build_power_bar(App& app) {
    using qe::renderer::Vertex;
    // Background bar (grey)
    {
        std::vector<Vertex> v;
        float x0 = -0.85f, x1 = -0.80f, y0 = -0.5f, y1 = 0.5f;
        Vertex tl, tr, bl, br;
        tl.position[0] = x0; tl.position[1] = y1; tl.color[0] = 0.2f; tl.color[1] = 0.2f; tl.color[2] = 0.2f;
        tr.position[0] = x1; tr.position[1] = y1; tr.color[0] = 0.2f; tr.color[1] = 0.2f; tr.color[2] = 0.2f;
        bl.position[0] = x0; bl.position[1] = y0; bl.color[0] = 0.2f; bl.color[1] = 0.2f; bl.color[2] = 0.2f;
        br.position[0] = x1; br.position[1] = y0; br.color[0] = 0.2f; br.color[1] = 0.2f; br.color[2] = 0.2f;
        v = {tl, tr, bl, br};
        std::vector<unsigned> idx = {0, 2, 1, 1, 2, 3};
        app.power_bar_bg.upload(v, idx);
    }
    // Fill bar (green→red gradient) — rebuilt each frame based on power
    {
        std::vector<Vertex> v;
        float x0 = -0.85f, x1 = -0.80f, y0 = -0.5f, y1 = -0.5f;  // starts empty
        Vertex tl, tr, bl, br;
        tl.position[0] = x0; tl.position[1] = y1; tl.color[0] = 1; tl.color[1] = 0; tl.color[2] = 0;
        tr.position[0] = x1; tr.position[1] = y1; tr.color[0] = 1; tr.color[1] = 0; tr.color[2] = 0;
        bl.position[0] = x0; bl.position[1] = y0; bl.color[0] = 0; bl.color[1] = 1; bl.color[2] = 0;
        br.position[0] = x1; br.position[1] = y0; br.color[0] = 0; br.color[1] = 1; br.color[2] = 0;
        v = {tl, tr, bl, br};
        std::vector<unsigned> idx = {0, 2, 1, 1, 2, 3};
        app.power_bar_fill.upload(v, idx);
    }
}

void build_aim_line(App& app) {
    using qe::renderer::Vertex;
    // Simple line in front of ball
    Vertex a, b;
    a.position[0] = 0; a.position[1] = 0.1f; a.position[2] = 0;
    a.color[0] = 1; a.color[1] = 1; a.color[2] = 0;
    b.position[0] = 0; b.position[1] = 0.1f; b.position[2] = -10;
    b.color[0] = 1; b.color[1] = 0.5f; b.color[2] = 0;
    std::vector<Vertex> v = {a, b};
    std::vector<unsigned> idx = {0, 1};
    app.aim_line.upload(v, idx);
    app.aim_line.index_count = 2;
}

// ── Course ──────────────────────────────────────────────────────────────────
void init_course(App& app) {
    // Generate terrain
    qg::course::CourseBuilder::generate_base(app.terrain, 256, 256, 1.0f);

    // Build hole layouts
    app.holes = qg::course::CourseBuilder::default_course();

    // Stamp all holes onto terrain
    for (auto& hole : app.holes) {
        qg::course::CourseBuilder::stamp_hole(app.terrain, hole);
    }

    // Build the mesh
    app.terrain.build_mesh();
}

void setup_hole(App& app, int hole_idx) {
    if (hole_idx < 0 || hole_idx >= static_cast<int>(app.holes.size())) return;
    app.current_hole = hole_idx;
    auto& hole = app.holes[hole_idx];

    // Place ball on tee
    app.ball.position = hole.tee.position;
    app.ball.position.y = app.terrain.height_at_world(
        hole.tee.position.x, hole.tee.position.z) + 0.15f;
    app.ball.velocity = {0, 0, 0};
    app.ball.spin = {0, 0, 0};
    app.ball.stopped = true;
    app.ball.in_flight = false;
    app.ball.rolling = false;
    app.ball.in_water = false;
    app.ball_in_play = false;
    app.stroke_count = 0;
    app.power = 0;
    app.charging = false;

    // Aim toward green
    auto aim = hole.green.pin - hole.tee.position;
    app.aim_yaw = std::atan2(aim.x, -aim.z);

    // Camera behind ball, looking toward green
    app.camera.set_position(app.ball.position + qe::math::Vec3(0, 3, 5));

    // Auto-select driver for par 4+, putter for short shots
    if (hole.par <= 3 && hole.yards < 200) {
        app.selected_club = 2;  // 5 Iron
    } else {
        app.selected_club = 0;  // Driver
    }

    std::cout << "\n=== Hole " << hole.number << " | Par " << hole.par
              << " | " << static_cast<int>(hole.yards) << " yards ===\n";
}

// ── Events ──────────────────────────────────────────────────────────────────
void handle_events(App& app) {
    app.input.begin_frame();

    SDL_Event ev;
    while (SDL_PollEvent(&ev)) {
        if (ev.type == SDL_QUIT) { app.running = false; return; }
        if (ev.type == SDL_WINDOWEVENT &&
            ev.window.event == SDL_WINDOWEVENT_SIZE_CHANGED) {
            qe::renderer::gl::glViewport(0, 0, ev.window.data1, ev.window.data2);
            app.camera.config.aspect =
                static_cast<float>(ev.window.data1) / ev.window.data2;
        }
        app.input.handle_event(ev);

        // Club selection (keyboard 1-9)
        if (ev.type == SDL_KEYDOWN) {
            int key = ev.key.keysym.sym;
            if (key >= SDLK_1 && key <= SDLK_9) {
                app.selected_club = key - SDLK_1;
                std::cout << "Club: " << qg::game::CLUBS[app.selected_club].name << "\n";
            }
            // Space = start charging / release = shoot
            if (key == SDLK_SPACE && app.ball.stopped && !app.charging) {
                app.charging = true;
                app.power = 0;
            }
            // Next hole
            if (key == SDLK_n) {
                int next = (app.current_hole + 1) % static_cast<int>(app.holes.size());
                setup_hole(app, next);
            }
        }
        if (ev.type == SDL_KEYUP && ev.key.keysym.sym == SDLK_SPACE) {
            if (app.charging) {
                // Fire!
                app.charging = false;
                auto& club = qg::game::CLUBS[app.selected_club];
                qe::math::Vec3 aim(std::sin(app.aim_yaw), 0, -std::cos(app.aim_yaw));
                app.physics.launch(app.ball,
                    club.launch_velocity(aim, app.power),
                    club.default_spin(aim));
                app.ball_in_play = true;
                app.stroke_count++;
                std::cout << "Shot " << app.stroke_count
                          << " | " << club.name
                          << " | Power: " << static_cast<int>(app.power * 100) << "%\n";
            }
        }
    }
    app.input.poll();

    if (app.input.quit()) app.running = false;

    // Free camera toggle
    if (app.input.toggle_camera()) {
        app.free_cam = !app.free_cam;
    }

    // Wireframe toggle
    static bool wireframe = false;
    if (app.input.toggle_wireframe()) {
        wireframe = !wireframe;
        qe::renderer::gl::glPolygonMode(
            GL_FRONT_AND_BACK, wireframe ? GL_LINE : GL_FILL);
    }

    // Reset ball
    if (app.input.reset()) {
        setup_hole(app, app.current_hole);
    }
}

// ── Update ──────────────────────────────────────────────────────────────────
void update(App& app, float dt) {
    app.time += dt;

    // Update enemies
    app.enemy_manager.update(dt, app.ball.position);


    // Power meter
    if (app.charging) {
        app.power += dt * 0.8f;  // Full power in ~1.25 seconds
        if (app.power > 1.0f) app.power = 1.0f;

        // Update power bar fill mesh
        float y0 = -0.5f;
        float y1 = y0 + app.power * 1.0f;
        using qe::renderer::Vertex;
        float x0 = -0.85f, x1 = -0.80f;
        Vertex tl, tr, bl, br;
        tl.position[0] = x0; tl.position[1] = y1;
        tr.position[0] = x1; tr.position[1] = y1;
        bl.position[0] = x0; bl.position[1] = y0;
        br.position[0] = x1; br.position[1] = y0;
        // Color gradient: green at bottom, red at top
        float r = app.power;
        float g = 1.0f - app.power;
        tl.color[0] = r; tl.color[1] = g; tl.color[2] = 0;
        tr.color[0] = r; tr.color[1] = g; tr.color[2] = 0;
        bl.color[0] = 0; bl.color[1] = 1; bl.color[2] = 0;
        br.color[0] = 0; br.color[1] = 1; br.color[2] = 0;
        app.power_bar_fill.destroy();
        std::vector<Vertex> v = {tl, tr, bl, br};
        std::vector<unsigned> idx = {0, 2, 1, 1, 2, 3};
        app.power_bar_fill.upload(v, idx);
    }

    // Aim adjustment (when ball stopped)
    if (app.ball.stopped && !app.free_cam) {
        app.aim_yaw += app.input.look_x() * 0.003f;
        // Gamepad aim
        app.aim_yaw += app.input.move_right() * dt * 2.0f;
    }

    // Ball physics
    app.physics.update(app.ball, app.terrain, dt);

    // Enemy collision
    if (app.ball.in_flight || app.ball.rolling) {
        qe::math::Vec3 normal;
        int points = app.enemy_manager.check_collision(app.ball.position, app.physics.constants.radius, normal);
        if (points > 0) {
            // Reflect velocity
            float v_dot_n = app.ball.velocity.dot(normal);
            // Only reflect if moving towards enemy
            if (v_dot_n < 0) {
                 app.ball.velocity = app.ball.velocity - normal * (2.0f * v_dot_n);
                 // Add some energy loss and maybe randomness
                 app.ball.velocity = app.ball.velocity * 0.7f;
                 app.total_score += points;
                 std::cout << "Bonk! Enemy hit. +" << points << " Points (Total: " << app.total_score << ")\n";
                 
                 // Play sound
                 // app.audio_system.play("hit"); 
                 // Synthetic fallback
                 app.audio_system.play_synthetic(440.0f + (points > 10 ? 220.0f : 0.0f), 0.1f);
                 
                 // Spawn particles
                 app.particle_system.spawn(app.ball.position, 20, {1.0f, 0.8f, 0.2f});
            }
        }
    }

    // Update Particles
    app.particle_system.update(dt);

    // Check if ball in water — penalty
    if (app.ball.in_water) {
        std::cout << "Water hazard! 1 stroke penalty.\n";
        app.stroke_count++;
        // Reset ball to last position (simplified: back to tee area)
        setup_hole(app, app.current_hole);
        app.stroke_count = app.stroke_count;  // Preserve stroke count
    }

    // Check if ball reached green and stopped near pin
    if (app.ball.stopped && app.ball_in_play) {
        auto& hole = app.holes[app.current_hole];
        float dist_to_pin = app.ball.position.distance_to(hole.green.pin);

        if (dist_to_pin < 0.3f) {
            // Holed out!
            int score = app.stroke_count;
            int diff = score - hole.par;
            std::string result;
            if (diff <= -2)      result = "Eagle!";
            else if (diff == -1) result = "Birdie!";
            else if (diff == 0)  result = "Par";
            else if (diff == 1)  result = "Bogey";
            else if (diff == 2)  result = "Double Bogey";
            else                 result = std::to_string(diff) + " over par";

            std::cout << "HOLED! " << result << " (" << score << " strokes)\n";
            app.scores.push_back(score);

            // Move to next hole
            int next = app.current_hole + 1;
            if (next < static_cast<int>(app.holes.size())) {
                setup_hole(app, next);
            } else {
                // Round complete
                int total = 0;
                for (int s : app.scores) total += s;
                int total_par = 0;
                for (const auto& h : app.holes) total_par += h.par;
                std::cout << "\n=== Round Complete! ===\n"
                          << "Total: " << total << " (" << total - total_par
                          << " to par)\n";
                setup_hole(app, 0);
                app.scores.clear();
            }
        }
        app.ball_in_play = !app.ball.stopped || !app.ball_in_play;
    }

    // Camera follows ball
    if (!app.free_cam) {
        if (app.ball.in_flight || app.ball.rolling) {
            // Track shot — behind and above ball
            qe::math::Vec3 behind = app.ball.velocity.normalized() * -1.0f;
            if (behind.length() < 0.5f) behind = {0, 0, 1};
            behind.y = 0;
            behind = behind.normalized();
            qe::math::Vec3 target = app.ball.position + behind * 8 + qe::math::Vec3(0, 4, 0);
            app.camera.set_position(
                app.camera.position().lerp(target, dt * 3));
            // Look at ball
            auto dir = (app.ball.position - app.camera.position()).normalized();
            float pitch = -std::asin(dir.y);
            float yaw_angle = std::atan2(dir.x, -dir.z);
            app.camera.set_angles(yaw_angle, pitch);
        } else {
            // Behind ball, looking toward aim direction
            qe::math::Vec3 aim(std::sin(app.aim_yaw), 0, -std::cos(app.aim_yaw));
            qe::math::Vec3 target = app.ball.position - aim * 6 + qe::math::Vec3(0, 3, 0);
            app.camera.set_position(
                app.camera.position().lerp(target, dt * 5));
            auto dir = (app.ball.position - app.camera.position()).normalized();
            float pitch = -std::asin(dir.y);
            float yaw_angle = std::atan2(dir.x, -dir.z);
            app.camera.set_angles(yaw_angle, pitch);
        }
    } else {
        // Free camera
        app.camera.process_mouse(app.input.look_x(), app.input.look_y());
        app.camera.process_movement(
            app.input.move_forward(), app.input.move_right(),
            app.input.move_up(), app.input.sprint(), dt);
    }
    app.camera.update(dt);
}

// ── Render: World ───────────────────────────────────────────────────────────
void render_world(App& app) {
    using namespace qe::renderer::gl;
    using namespace qe::math;

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
    app.world_shader.use();

    Mat4 vp = app.camera.vp_matrix();
    app.world_shader.set_mat4("uViewProjection", vp);
    app.world_shader.set_vec3("uLightDir", Vec3(0.4f, 0.8f, 0.3f).normalized());
    app.world_shader.set_vec3("uLightColor", Vec3(1.0f, 0.98f, 0.92f));
    app.world_shader.set_vec3("uAmbient", Vec3(0.3f, 0.35f, 0.35f));
    app.world_shader.set_vec3("uCameraPos", app.camera.position());
    app.world_shader.set_int("uUseTexture", 0);

    // Enemies
    app.enemy_manager.draw(app.world_shader);

    // Particles
    app.particle_system.draw(view_proj);

    // Terrain
    app.world_shader.set_mat4("uModel", Mat4::identity());
    glDisable(GL_CULL_FACE);
    app.terrain.draw();
    glEnable(GL_CULL_FACE);

    // Ball
    app.world_shader.set_mat4("uModel",
        Mat4::trs(app.ball.position, Quaternion::identity(), Vec3::one()));
    app.ball_mesh.draw();

    // Flag pins for all holes
    for (const auto& hole : app.holes) {
        auto pin = hole.green.pin;
        pin.y = app.terrain.height_at_world(pin.x, pin.z);

        // Pole
        app.world_shader.set_mat4("uModel",
            Mat4::trs(pin, Quaternion::identity(), Vec3::one()));
        glLineWidth(2.0f);
        glBindVertexArray(app.flag_pole.vao);
        glDrawElements(GL_LINES, 2, GL_UNSIGNED_INT, nullptr);
        glBindVertexArray(0);
        glLineWidth(1.0f);

        // Flag triangle (waving)
        float wave = std::sin(app.time * 3 + pin.x) * 0.1f;
        auto flag_rot = Quaternion::from_axis_angle(Vec3::up(), wave);
        app.world_shader.set_mat4("uModel",
            Mat4::trs(pin, flag_rot, Vec3::one()));
        glDisable(GL_CULL_FACE);
        app.flag_mesh.draw();
        glEnable(GL_CULL_FACE);
    }

    // Aim line (when ball stopped)
    if (app.ball.stopped) {
        auto aim_rot = Quaternion::from_axis_angle(Vec3::up(), app.aim_yaw);
        app.world_shader.set_mat4("uModel",
            Mat4::trs(app.ball.position, aim_rot, Vec3::one()));
        glLineWidth(2.0f);
        glBindVertexArray(app.aim_line.vao);
        glDrawElements(GL_LINES, 2, GL_UNSIGNED_INT, nullptr);
        glBindVertexArray(0);
        glLineWidth(1.0f);
    }
}


// ── Render: HUD ─────────────────────────────────────────────────────────────
void render_hud(App& app) {
    using namespace qe::renderer::gl;

    glDisable(GL_DEPTH_TEST);
    app.hud_shader.use();

    // Power bar (always visible when ball stopped)
    if (app.ball.stopped || app.charging) {
        app.power_bar_bg.draw();
        if (app.charging) {
            app.power_bar_fill.draw();
        }
    }

    glEnable(GL_DEPTH_TEST);
}

// ── Title ───────────────────────────────────────────────────────────────────
void update_title(App& app) {
    if (app.current_hole >= static_cast<int>(app.holes.size())) return;
    auto& hole = app.holes[app.current_hole];
    auto surface_type = app.terrain.surface_at_world(
        app.ball.position.x, app.ball.position.z);
    auto surface = qg::terrain::get_surface(surface_type);

    float dist_to_pin = app.ball.position.distance_to(hole.green.pin);

    std::ostringstream t;
    t << "QuatGolf | " << static_cast<int>(app.current_fps) << " FPS"
      << " | Hole " << hole.number << " Par " << hole.par
      << " | Score: " << app.total_score
      << " | " << qg::game::CLUBS[app.selected_club].name
      << " | Strokes: " << app.stroke_count
      << " | " << static_cast<int>(dist_to_pin) << "m to pin"
      << " | " << surface.name();
    if (app.ball.in_flight) t << " | IN FLIGHT";
    if (app.ball.rolling)   t << " | ROLLING";
    if (app.input.gamepad_connected())
        t << " | Gamepad: " << app.input.gamepad().name();
    SDL_SetWindowTitle(app.window, t.str().c_str());
}

// ── Cleanup ─────────────────────────────────────────────────────────────────
void cleanup(App& app) {
    app.terrain.destroy();
    app.ball_mesh.destroy();
    app.flag_pole.destroy();
    app.flag_mesh.destroy();
    app.power_bar_bg.destroy();
    app.power_bar_fill.destroy();
    app.aim_line.destroy();
    app.world_shader.destroy();
    app.hud_shader.destroy();
    if (app.gl_context) SDL_GL_DeleteContext(app.gl_context);
    if (app.window) SDL_DestroyWindow(app.window);
    SDL_Quit();
}
