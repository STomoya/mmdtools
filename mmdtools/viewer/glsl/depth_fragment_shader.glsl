#version 410

out vec4 FragColor;

uniform float uNear;
uniform float uFar;

float LinearizeDepth(float depth)
{
    float z = depth * 2.0 - 1.0; // back to NDC
    return (2.0 * uNear * uFar) / (uFar + uNear - z * (uFar - uNear));
}

void main()
{
    float vDepth = LinearizeDepth(gl_FragCoord.z) / uFar;
    FragColor = vec4( vec3(vDepth), 1.0);
}
