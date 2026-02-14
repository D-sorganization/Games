#version 330 core

in vec3 vWorldPos;
in vec3 vNormal;
in vec3 vColor;
in vec2 vUV;

out vec4 FragColor;

uniform vec3 uLightDir = vec3(0.5, 1.0, 0.3); // Simple directional light
uniform vec3 uSunColor = vec3(1.0, 1.0, 0.9);
uniform vec3 uAmbient  = vec3(0.3, 0.3, 0.4);

void main() {
    // Lambert
    vec3 N = normalize(vNormal);
    vec3 L = normalize(uLightDir);
    float diff = max(dot(N, L), 0.0);
    
    vec3 lighting = uAmbient + uSunColor * diff;
    vec3 finalColor = vColor * lighting;
    
    FragColor = vec4(finalColor, 1.0);
}
