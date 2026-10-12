import * as THREE from 'three';

// Shared metre-scale set. Repeated architectural geometry is instanced by material.
export function createRooftop(data) {
  const group = new THREE.Group();
  group.name = 'ASTRA / Kowloon Rooftop';
  const palette = {};
  for (const [key, value] of Object.entries(data.palette)) {
    const material = new THREE.MeshStandardMaterial({
      color: value.color, roughness: value.roughness,
      metalness: value.metalness || 0,
      emissive: value.emissive || '#000000', emissiveIntensity: value.emission || 0,
    });
    if (key === 'water') {
      material.transparent = true;
      material.opacity = 0.55;
      material.depthWrite = false;
    }
    if (value.surface) {
      // World-space tonal variation stays at the same scale on different sized meshes.
      material.onBeforeCompile = shader => {
        shader.vertexShader = 'varying vec3 vAstraWorld;\n' + shader.vertexShader;
        shader.vertexShader = shader.vertexShader.replace('#include <worldpos_vertex>', `
          #include <worldpos_vertex>
          vec4 astraP = vec4(transformed, 1.0);
          #ifdef USE_INSTANCING
            astraP = instanceMatrix * astraP;
          #endif
          vAstraWorld = (modelMatrix * astraP).xyz;
        `);
        shader.fragmentShader = `varying vec3 vAstraWorld;
          float astraHash(vec3 p){return fract(sin(dot(p,vec3(127.1,311.7,74.7)))*43758.5453);}
          float astraNoise(vec3 p){vec3 i=floor(p);vec3 f=fract(p);f=f*f*(3.0-2.0*f);
            return mix(mix(mix(astraHash(i),astraHash(i+vec3(1,0,0)),f.x),mix(astraHash(i+vec3(0,1,0)),astraHash(i+vec3(1,1,0)),f.x),f.y),mix(mix(astraHash(i+vec3(0,0,1)),astraHash(i+vec3(1,0,1)),f.x),mix(astraHash(i+vec3(0,1,1)),astraHash(i+vec3(1,1,1)),f.x),f.y),f.z);}
          ` + shader.fragmentShader;
        shader.fragmentShader = shader.fragmentShader.replace('#include <color_fragment>', `
          #include <color_fragment>
          float broad = astraNoise(vAstraWorld * 3.0) * 2.0 - 1.0;
          float fine = astraNoise(vAstraWorld * ${value.surface === 'wood' ? 'vec3(1.2, 34.0, 24.0)' : 'vec3(32.0)'}) * 2.0 - 1.0;
          diffuseColor.rgb *= 0.91 + broad * 0.065 + fine * 0.035;
        `);
      };
      material.customProgramCacheKey = () => `astra-world-${value.surface}`;
    }
    material.userData.baseRoughness = value.roughness;
    material.userData.baseColor = material.color.clone();
    material.userData.baseEmission = value.emission || 0;
    palette[key] = material;
  }
  const geometries = {
    box: new THREE.BoxGeometry(1, 1, 1),
    cylinder: new THREE.CylinderGeometry(.5, .5, 1, 16),
    cone: new THREE.ConeGeometry(.5, 1, 16),
    sphere: new THREE.SphereGeometry(.5, 12, 8),
    rod: new THREE.CylinderGeometry(.5, .5, 1, 8),
  };
  const batches = new Map();
  for (const item of data.objects) {
    const key = item.geometry + ':' + item.material;
    if (!batches.has(key)) batches.set(key, []);
    batches.get(key).push(item);
  }
  const dummy = new THREE.Object3D();
  for (const [key, items] of batches) {
    const [geometry, mat] = key.split(':');
    const mesh = new THREE.InstancedMesh(geometries[geometry], palette[mat], items.length);
    mesh.name = `ASTRA / ${key}`;
    mesh.castShadow = mat !== 'water';
    mesh.receiveShadow = true;
    items.forEach((item, index) => {
      dummy.rotation.set(0, 0, 0);
      if (geometry === 'rod') {
        const start = new THREE.Vector3(...item.start);
        const end = new THREE.Vector3(...item.end);
        const delta = end.clone().sub(start);
        dummy.position.copy(start).add(end).multiplyScalar(.5);
        dummy.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), delta.clone().normalize());
        dummy.scale.set(item.radius * 2, delta.length(), item.radius * 2);
      } else {
        dummy.position.set(...item.position);
        dummy.scale.set(...item.size);
        if (item.rotation) dummy.rotation.set(...item.rotation);
      }
      dummy.updateMatrix();
      mesh.setMatrixAt(index, dummy.matrix);
    });
    mesh.instanceMatrix.needsUpdate = true;
    mesh.computeBoundingSphere();
    group.add(mesh);
  }
  for (const label of data.labels) {
    const canvas = document.createElement('canvas');
    canvas.width = 1024; canvas.height = 256;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = label.background; ctx.fillRect(0, 0, 1024, 256);
    ctx.fillStyle = label.color; ctx.font = '600 128px sans-serif';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(label.text, 512, 137, 940);
    const map = new THREE.CanvasTexture(canvas); map.colorSpace = THREE.SRGBColorSpace;
    const plane = new THREE.Mesh(new THREE.PlaneGeometry(label.width, label.height), new THREE.MeshBasicMaterial({ map, toneMapped: false }));
    plane.position.set(...label.position); group.add(plane);
  }
  const task = new THREE.SpotLight(0xffdb9b, 14, 8, .9, .7, 2);
  task.castShadow = true;
  task.shadow.mapSize.set(512, 512);
  task.shadow.camera.near = .05;
  task.shadow.camera.far = 8;
  task.shadow.bias = -.0002;
  task.shadow.normalBias = .006;
  task.position.set(-.53, 2.11, -.49); task.target.position.set(0, .95, 0);
  const sign = new THREE.PointLight(0xb9ee8b, 32, 15, 2);
  sign.position.set(2.8, 3.9, -9.8);
  group.add(task, task.target, sign);
  return {
    group, data,
    update({ wetness, lighting }) {
      const night = lighting === 'neon' || lighting === 'noir';
      for (const key of ['tile', 'tile2', 'concrete', 'wood', 'wood2']) {
        const mat = palette[key];
        mat.roughness = THREE.MathUtils.lerp(mat.userData.baseRoughness, .24, wetness);
        mat.color.copy(mat.userData.baseColor).multiplyScalar(1 - wetness * .2);
      }
      palette.water.opacity = wetness * .7;
      for (const material of Object.values(palette)) {
        material.emissiveIntensity = material.userData.baseEmission * (night ? 1.7 : .45);
      }
      task.intensity = night ? 19 : 4;
      sign.intensity = night ? 50 : 4;
    },
  };
}

export function createSky() {
  const uniforms = {
    top: { value: new THREE.Color('#4b6474') },
    horizon: { value: new THREE.Color('#d1b78e') },
    sunColor: { value: new THREE.Color('#ffe5ac') },
    sunDirection: { value: new THREE.Vector3(-.5, .3, -.7).normalize() },
    sunPower: { value: 1 },
  };
  const material = new THREE.ShaderMaterial({
    uniforms, side: THREE.BackSide, depthWrite: false,
    vertexShader: 'varying vec3 vDirection; void main(){ vDirection=position; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.); }',
    fragmentShader: `varying vec3 vDirection;
      uniform vec3 top; uniform vec3 horizon; uniform vec3 sunColor;
      uniform vec3 sunDirection; uniform float sunPower;
      void main(){vec3 dir=normalize(vDirection);
      float height=pow(max(dir.y,0.0),0.45);
      vec3 color=mix(horizon,top,height);
      float d=max(dot(dir,sunDirection),0.0);
      color+=sunColor*(pow(d,600.0)*2.0+pow(d,14.0)*0.09)*sunPower;
      gl_FragColor=vec4(color,1.);}`,
  });
  const mesh = new THREE.Mesh(new THREE.SphereGeometry(180, 32, 16), material);
  mesh.name = 'Procedural sky — not an HDRI';
  mesh.frustumCulled = false;
  return { mesh, uniforms };
}
