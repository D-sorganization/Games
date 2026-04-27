cmake_minimum_required(VERSION 3.20)

project(SharedCppTests LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Compiler warnings
if(MSVC)
    add_compile_options(/W4 /WX-)
else()
    add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Shared modules include root
set(SHARED_CPP ${CMAKE_SOURCE_DIR}/src/games/shared/cpp)

# QuatGolf game headers
set(QUATGOLF_SRC ${CMAKE_SOURCE_DIR}/src/games/QuatGolf/src)

# ── Math Tests ───────────────────────────────────────────────────────────────
add_executable(test_cpp_math tests/shared/cpp/test_math.cpp)
target_include_directories(test_cpp_math PRIVATE ${SHARED_CPP})

# ── Game Tests ───────────────────────────────────────────────────────────────
add_executable(test_cpp_game tests/shared/cpp/test_game.cpp)
target_include_directories(test_cpp_game PRIVATE ${SHARED_CPP})

# ── QuatGolf Tests ───────────────────────────────────────────────────────────
# QE_NO_SDL suppresses the SDL include in GLLoader.h (not needed for unit tests)
add_executable(test_quatgolf tests/QuatGolf/cpp/test_quatgolf.cpp)
target_include_directories(test_quatgolf PRIVATE
    ${QUATGOLF_SRC}
    ${SHARED_CPP}
)
target_compile_definitions(test_quatgolf PRIVATE QE_NO_SDL)

# ── CTest ────────────────────────────────────────────────────────────────────
enable_testing()
add_test(NAME CppMathTests COMMAND test_cpp_math)
add_test(NAME CppGameTests COMMAND test_cpp_game)
add_test(NAME QuatGolfTests COMMAND test_quatgolf)
