#version 330 core

in vec3 vWorldPos;
in vec3 vNormal;
in vec3 vColor;
in vec2 vUV;

uniform vec3 uLightDir;
uniform vec3 uLightColor;
uniform vec3 uAmbient;
uniform vec3 uCameraPos;
uniform sampler2D uTexture0;
uniform int uUseTexture;

out vec4 FragColor;

void main() {
    vec3 normal = normalize(vNormal);
    vec3 lightDir = normalize(uLightDir);

    // Diffuse (Lambert) — wrap lighting for softer look on terrain
    float diff = max(dot(normal, lightDir), 0.0);
    float wrapDiff = diff * 0.7 + 0.3;  // Never fully dark
    vec3 diffuse = wrapDiff * uLightColor;

    // Specular (Blinn-Phong) — subtle for terrain
    vec3 viewDir = normalize(uCameraPos - vWorldPos);
    vec3 halfDir = normalize(lightDir + viewDir);
    float spec = pow(max(dot(normal, halfDir), 0.0), 64.0);
    vec3 specular = spec * uLightColor * 0.15;

    // Base color
    vec3 baseColor = vColor;
    if (uUseTexture > 0) {
        vec3 texColor = texture(uTexture0, vUV).rgb;
        baseColor = texColor * vColor;
    }

    // Lighting
    vec3 lighting = uAmbient + diffuse + specular;
    vec3 result = baseColor * lighting;

    // Distance fog — sky blue, extended for outdoor course
    float fogDist = length(uCameraPos - vWorldPos);
    float fogStart = 80.0;
    float fogEnd   = 250.0;
    float fogFactor = clamp(1.0 - (fogDist - fogStart) / (fogEnd - fogStart), 0.0, 1.0);
    vec3 fogColor = vec3(0.45, 0.65, 0.85);  // Match sky clear color
    result = mix(fogColor, result, fogFactor);

    // Subtle gamma correction for outdoor lighting
    result = pow(result, vec3(0.95));

    FragColor = vec4(result, 1.0);
}
