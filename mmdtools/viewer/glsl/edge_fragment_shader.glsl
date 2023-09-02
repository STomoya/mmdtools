#version 410

uniform vec4 uEdgeColor;
uniform float uAlpha;

out vec4 FragColor;

void main() {
    FragColor = vec4( uEdgeColor.rgb, uAlpha );
}
