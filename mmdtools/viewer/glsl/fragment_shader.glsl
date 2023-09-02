#version 410

// texture samplers
uniform  sampler2D  uTexture;
uniform  sampler2D  uSphereTexture;
uniform  sampler2D  uToonTexture;

// flags
uniform  float      uSphereTextureMode;
uniform  float      uIsToonTexture;

// matrices
uniform  mat4       uITModelViewM;
uniform  mat4       uModelViewM;

// light color and position
uniform  vec3       uLightAmbient;
uniform  vec3       uLightDiffuse;
uniform  vec3       uLightSpecular;
uniform  vec3       uLightPosition;

//
uniform  vec3       uCameraPosition;

// material color
uniform  vec3       uAmbientColor;
uniform  vec3       uSpecularColor;
uniform  vec3       uDiffuseColor;
uniform  float      uAlpha;
uniform  float      uShininess;

// output pixel color
out      vec4        FragColor;

// variables from vertex shader
in       vec2        ShareUV;
in       vec3        SharePos;
in       vec3        ShareNormal;


void main() {

    vec3 vNormal = vec3( uITModelViewM * vec4( ShareNormal, 1.0 ) );
    vNormal      = normalize( vNormal );

    vec3  vColor = vec3( 1.0, 1.0, 1.0 );
    float vAlpha = uAlpha;

    vec4 vTextureColor = texture2D( uTexture, ShareUV );
    vColor *= vTextureColor.rgb;
    vAlpha *= vTextureColor.a;

    vec2 vSphereCoord = ShareUV;
    if ( uSphereTextureMode == 1.0 ) {
        vColor *= texture2D( uSphereTexture, vSphereCoord ).rgb;
    } else if ( uSphereTextureMode == 3.0 ) {
        vColor += texture2D( uSphereTexture, vSphereCoord ).rgb;
    }

    vec3  vPosition = vec3( uModelViewM * vec4( SharePos, 1.0 ) );
    vec3  vLightDir = normalize( uLightPosition - vPosition );
    float vDiffuse = max(dot( vNormal, vLightDir ), 0.0);

    vec3  vViewDir    = normalize( uCameraPosition - vPosition );
    vec3  vHalfwayDir = normalize( vLightDir + vViewDir );
    float vSpecular   = pow( max( dot( vPosition, vHalfwayDir ), 0.0 ), uShininess );

    vec3 ambient  = uAmbientColor * uLightAmbient;
    vec3 specular = uSpecularColor * uLightSpecular * vSpecular;
    vec3 diffuse  = uDiffuseColor * uLightDiffuse * vDiffuse;

    vec3 lighting = ambient + diffuse + specular;
    vColor *= lighting;

    vColor = clamp( vColor, 0.0, 1.0 );
    if ( uIsToonTexture == 2.0 ) {
        vec2 toonCoord = vec2( 0.0, 0.5 * ( 1.0 - dot( vLightDir, vNormal ) ) );
        vColor = vColor * texture2D( uToonTexture, toonCoord ).rgb;
    }

    FragColor = vec4(vColor, vAlpha);
}
