#version 410

// VAO
layout (location = 0) in vec3 aVertex;
layout (location = 1) in vec3 aNormal;
layout (location = 2) in float aEdgeScale;
layout (location = 3) in vec4 aBoneIndex;
layout (location = 4) in vec4 aBoneWeights;

// matrices
uniform mat4 uProjectionM;
uniform mat4 uModelViewM;
uniform mat4 uBoneTransform[{num_bones}];

// edge size
uniform float uEdgeSize;

void main() {
    mat4 Transform;

    float sum = aBoneWeights.x + aBoneWeights.y + aBoneWeights.z + aBoneWeights.w;
    if (sum == 0.0) {
        Transform = mat4(1.0);
    } else {
        Transform  = aBoneWeights[0] * uBoneTransform[int( aBoneIndex[0] )];
        Transform += aBoneWeights[1] * uBoneTransform[int( aBoneIndex[1] )];
        Transform += aBoneWeights[2] * uBoneTransform[int( aBoneIndex[2] )];
        Transform += aBoneWeights[3] * uBoneTransform[int( aBoneIndex[3] )];
    }

    vec4 pos = uProjectionM * uModelViewM * Transform * vec4( aVertex, 1.0 );
    vec4 pos2 = uProjectionM * uModelViewM * Transform * vec4( aVertex + aNormal, 1.0 );
    vec4 norm_d = normalize(pos2 - pos);
    gl_Position = pos + norm_d * uEdgeSize * aEdgeScale * 0.05;
}
