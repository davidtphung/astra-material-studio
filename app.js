import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { createRooftop, createSky } from './world.js';
const materials = [
 {id:'metal',name:'Brushed metal',color:'#b7bbb5',roughness:.32,bump:.3,metalness:1,category:'METAL / DIRECTIONAL',description:'Fine directional brushing. Soft reflections. A quietly industrial surface with a precise finish.'},
 {id:'paint',name:'Painted metal',color:'#a74c34',roughness:.42,bump:.25,metalness:0,category:'COATING / WORN',description:'A satin painted shell with exposed metal flecks. Procedural wear, without geometry-aware edge detection.'},
 {id:'concrete',name:'Concrete',color:'#aaa695',roughness:.86,bump:.55,metalness:0,category:'MINERAL / POROUS',description:'Broad mineral variation and fine pores. Grounded, tactile, and best explored under grazing light.'},
 {id:'wood',name:'Wood',color:'#885331',roughness:.48,bump:.35,metalness:0,category:'ORGANIC / GRAIN',description:'Directional grain with a warm, open finish. A procedural interpretation of wood, not a scanned species.'},
 {id:'glass',name:'Glass',color:'#c4dfcb',roughness:.12,bump:.06,metalness:0,category:'DIELECTRIC / TRANSMISSIVE',description:'A softly tinted transmissive surface. Refraction changes with the shape and thickness of the object.'},
 {id:'plastic',name:'Plastic',color:'#ccc079',roughness:.36,bump:.18,metalness:0,category:'POLYMER / MOLDED',description:'Subtle molded texture and a soft sheen. Tune roughness from polished resin to a matte polymer.'}
];
function textureSet(id){const size=512;const canvases=Array.from({length:3},()=>{const c=document.createElement('canvas');c.width=c.height=size;return c;});const contexts=canvases.map(c=>c.getContext('2d'));const images=contexts.map(c=>c.createImageData(size,size));let seed=state.seed;const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};for(let y=0;y<size;y++)for(let x=0;x<size;x++){const noise=random(),broad=(Math.sin(x*.031+Math.sin(y*.04)*2)+Math.cos(y*.025+x*.01))*.5;let h=.5+(noise-.5)*.12,r=.8,v=.9,met=current.metalness;if(id==='metal'){h=.5+.13*Math.sin(y*2.8)+noise*.09;v=.91+noise*.07;r=.65+.3*noise;}if(id==='concrete'){h=.55+broad*.1+(noise-.5)*.2;if(noise>.978)h=.08;v=.83+broad*.09+(noise-.5)*.08;r=.85+noise*.15;}if(id==='wood'){const grain=Math.sin(x*.16+Math.sin(y*.012)*4+Math.sin(x*.021+y*.003)*6);h=.5+grain*.22+noise*.07;v=.73+grain*.19+broad*.05;r=.72+grain*.15;}if(id==='paint'){const mask=Math.sin(x*.087+Math.sin(y*.071)*2)*Math.cos(y*.1+Math.sin(x*.04));const chip=mask>.89;met=chip?1:0;v=chip?.33:.9+noise*.055;h=chip?.1:.6+noise*.015;r=chip?.7:.92;}if(id==='plastic'){h=.5+noise*.08;v=.95+noise*.03;r=.86+noise*.12;}if(id==='glass'){h=.5+noise*.006;v=1;r=.96;}const i=(y*size+x)*4;for(let c=0;c<3;c++)images[0].data[i+c]=Math.round(v*255);images[0].data[i+3]=255;for(let c=0;c<3;c++)images[1].data[i+c]=Math.round(h*255);images[1].data[i+3]=255;images[2].data[i]=255;images[2].data[i+1]=Math.round(r*255);images[2].data[i+2]=Math.round(met*255);images[2].data[i+3]=255;}return canvases.map((c,i)=>{contexts[i].putImageData(images[i],0,0);const t=new THREE.CanvasTexture(c);t.wrapS=t.wrapT=THREE.RepeatWrapping;t.anisotropy=Math.min(8,renderer.capabilities.getMaxAnisotropy());if(i===0)t.colorSpace=THREE.SRGBColorSpace;return t;});}

const $ = id => document.getElementById(id);
let current = materials[0];
let state = {
  material: current.id, color: current.color, roughness: current.roughness,
  scale: 1, bump: current.bump, lighting: 'daylight', shape: 'sculpture', seed: 42,
  environment: 'rooftop', view: 'bench', wetness: .45, haze: .3,
};
let renderer, scene, camera, controls, mesh, material, geometry, lights;
let studioGroup, rooftop, sky, pmrem, studioEnvironment, capturedEnvironment;
let maps = [], autoRotate = false, visible = true, toastTimer, reflectionTimer;
const number = (x, min, max, fallback) => typeof x === 'number' && Number.isFinite(x) ? Math.min(max, Math.max(min, x)) : fallback;

function toast(message) {
  $('toast').textContent = message;
  $('toast').classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => $('toast').classList.remove('show'), 3500);
}
function save(blob, name) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a'); a.href = url; a.download = name; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}
function settings() {
  return { schema: 'astra.look.v1', ...state };
}
try {
  const input = new URLSearchParams(location.search).get('look');
  if (input) {
    const value = JSON.parse(input);
    const m = materials.find(m => m.id === value.material);
    if (!m) throw Error('Unknown material');
    current = m;
    Object.assign(state, {
      material: m.id, color: /^#[0-9a-f]{6}$/i.test(value.color) ? value.color : m.color,
      roughness: number(value.roughness, .04, 1, m.roughness),
      scale: number(value.scale, .3, 4, 1), bump: number(value.bump, 0, 1, m.bump),
      lighting: ['studio','daylight','noir','neon'].includes(value.lighting) ? value.lighting : 'daylight',
      shape: ['sculpture','sphere','block'].includes(value.shape) ? value.shape : 'sculpture',
      environment: ['rooftop','studio'].includes(value.environment) ? value.environment : 'studio',
      view: ['detail','bench','wide'].includes(value.view) ? value.view : 'bench',
      wetness: number(value.wetness, 0, 1, .45), haze: number(value.haze, 0, 1, .3),
    });
  }
} catch { toast('That look link could not be read. The starting scene is loaded.'); }

function syncUI() {
  const index = materials.findIndex(m => m.id === state.material);
  $('material-name').textContent = current.name;
  $('material-desc').textContent = current.description;
  $('material-number').textContent = String(index + 1).padStart(2, '0');
  $('material-code').textContent = `MAT—00${index + 1}`;
  $('material-category').textContent = current.category;
  for (const name of ['color','roughness','scale','bump','wetness','haze']) $(name).value = state[name];
  $('roughness-value').textContent = state.roughness.toFixed(2);
  $('scale-value').textContent = state.scale.toFixed(1) + '×';
  $('bump-value').textContent = state.bump.toFixed(2);
  $('wetness-value').textContent = Math.round(state.wetness * 100) + '%';
  $('haze-value').textContent = Math.round(state.haze * 100) + '%';
  $('location-name').textContent = state.environment === 'rooftop' ? 'KOWLOON / ROOFTOP WORKSHOP' : 'ASTRA / NEUTRAL STUDIO';
  $('context-caption').textContent = state.environment === 'rooftop'
    ? 'A 0.90 m workbench. An inhabited roof. A city beyond.'
    : 'Neutral light and a simple plinth for surface comparison.';
  $('world-controls').hidden = state.environment !== 'rooftop';
  for (const [key, property] of [['material','material'],['shape','shape'],['light','lighting'],['environment','environment'],['view','view']]) {
    document.querySelectorAll(`[data-${key}]`).forEach(button => {
      const active = button.dataset[key] === state[property];
      button.classList.toggle('active', active); button.setAttribute('aria-pressed', active);
    });
  }
}
for (const m of materials) {
  const button = document.createElement('button');
  button.className = 'mat-button'; button.dataset.material = m.id;
  button.innerHTML = `<span class="swatch" style="--swatch:${m.color}"></span><span>${m.name}</span>`;
  button.onclick = () => {
    current = m;
    Object.assign(state, { material: m.id, color: m.color, roughness: m.roughness, bump: m.bump, scale: 1 });
    syncUI(); updateMaterial(true);
  };
  $('materials').append(button);
}
function updateMaterial(rebuild = false) {
  if (!renderer) return;
  if (rebuild) {
    maps.forEach(m => m.dispose()); maps = textureSet(state.material);
    [material.map, material.bumpMap, material.roughnessMap] = maps;
    material.metalnessMap = maps[2]; material.needsUpdate = true;
  }
  material.color.set(state.color);
  material.roughness = state.roughness;
  material.metalness = state.material === 'paint' ? 1 : current.metalness;
  material.bumpScale = state.bump * (state.material === 'concrete' ? .018 : .006);
  material.transmission = state.material === 'glass' ? .98 : 0;
  material.thickness = state.material === 'glass' ? .3 : 0;
  material.ior = 1.46;
  material.clearcoat = state.material === 'plastic' ? .22 : 0;
  maps.forEach(map => map.repeat.set(state.scale * 2, state.scale * 2));
}
function groundHero() {
  const scale = state.environment === 'rooftop' ? rooftop.data.hero.scale : 1;
  mesh.scale.setScalar(scale);
  mesh.position.set(0, 0, 0);
  mesh.updateMatrixWorld(true);
  const bounds = new THREE.Box3().setFromObject(mesh, true);
  mesh.position.y = (state.environment === 'rooftop' ? rooftop.data.hero.support : .12) - bounds.min.y;
}
function updateShape() {
  if (!mesh) return;
  geometry?.dispose();
  geometry = state.shape === 'sphere' ? new THREE.SphereGeometry(1.16, 64, 40)
    : state.shape === 'block' ? new RoundedBoxGeometry(1.95, 1.95, 1.95, 6, .14)
    : new THREE.TorusKnotGeometry(.77, .29, 160, 24, 2, 3);
  mesh.geometry = geometry; mesh.rotation.set(0, -.35, 0); groundHero();
}
function updateCamera() {
  if (!controls) return;
  const cameraState = state.environment === 'rooftop' ? rooftop.data.cameras[state.view]
    : { position: [4, 3.1, 5.6], target: [0, 1.3, 0] };
  camera.position.set(...cameraState.position);
  controls.target.set(...cameraState.target);
  controls.minDistance = state.environment === 'rooftop' ? 1.6 : 3.8;
  controls.maxDistance = state.environment === 'rooftop' ? 27 : 9;
  controls.maxPolarAngle = Math.PI * .485;
  controls.update();
}
const lightPresets = {
  daylight: { top: '#526e80', horizon: '#d6b68a', sun: '#ffcf8e', sunPower: 3.5, ambient: 1.1, exposure: 1.05, env: .9 },
  studio: { top: '#6f8e9c', horizon: '#c4d2d0', sun: '#e2efff', sunPower: 2.4, ambient: 1.4, exposure: 1, env: 1 },
  noir: { top: '#152133', horizon: '#566477', sun: '#a3c5ed', sunPower: .8, ambient: .5, exposure: 1.05, env: .65 },
  neon: { top: '#111b2a', horizon: '#344853', sun: '#7facba', sunPower: .4, ambient: .65, exposure: 1.3, env: .85 },
};
function refreshReflections() {
  if (!renderer) return;
  if (state.environment === 'studio') { scene.environment = studioEnvironment.texture; return; }
  // Capture the actual surrounding geometry for static environment reflections.
  mesh.visible = false;
  scene.environment = studioEnvironment.texture;
  const cubeTarget = new THREE.WebGLCubeRenderTarget(128, { type: THREE.HalfFloatType });
  const cube = new THREE.CubeCamera(.1, 150, cubeTarget);
  cube.position.set(0, 1.5, 0);
  cube.update(renderer, scene);
  const next = pmrem.fromCubemap(cubeTarget.texture);
  scene.environment = next.texture;
  capturedEnvironment?.dispose(); capturedEnvironment = next;
  cubeTarget.dispose(); mesh.visible = true;
}
function queueReflections() {
  clearTimeout(reflectionTimer);
  reflectionTimer = setTimeout(refreshReflections, 180);
}
function updateLighting() {
  if (!lights) return;
  const p = lightPresets[state.lighting];
  const outdoors = state.environment === 'rooftop';
  sky.uniforms.top.value.set(p.top); sky.uniforms.horizon.value.set(p.horizon);
  sky.uniforms.sunColor.value.set(p.sun); sky.uniforms.sunPower.value = state.lighting === 'neon' ? .03 : .45;
  scene.background.set(outdoors ? p.horizon : '#30392f');
  scene.fog = outdoors ? new THREE.FogExp2(p.horizon, .003 + state.haze * .018) : new THREE.Fog('#30392f', 15, 30);
  lights.sun.color.set(p.sun); lights.sun.intensity = p.sunPower;
  lights.ambient.intensity = p.ambient;
  lights.ambient.color.set(p.top).lerp(new THREE.Color('#ffffff'), .45);
  lights.fill.intensity = outdoors ? 0 : 24;
  scene.environmentIntensity = p.env;
  renderer.toneMappingExposure = p.exposure;
  rooftop.update(state); queueReflections();
}
function updateEnvironment() {
  if (!rooftop) return;
  const outdoors = state.environment === 'rooftop';
  rooftop.group.visible = sky.mesh.visible = outdoors;
  studioGroup.visible = !outdoors;
  groundHero(); updateCamera(); updateLighting(); syncUI();
}

async function initialize() {
  try {
    const response = await fetch('./world.json');
    if (!response.ok) throw Error(`World asset HTTP ${response.status}`);
    const data = await response.json();
    renderer = new THREE.WebGLRenderer({ canvas: $('scene'), antialias: true, preserveDrawingBuffer: true });
    renderer.setPixelRatio(Math.min(devicePixelRatio, innerWidth < 760 ? 1.5 : 2));
    renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFShadowMap;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    scene = new THREE.Scene(); scene.background = new THREE.Color('#30392f');
    camera = new THREE.PerspectiveCamera(43, 1, .05, 400);
    controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true; controls.enablePan = false;
    pmrem = new THREE.PMREMGenerator(renderer);
    const room = new RoomEnvironment(); studioEnvironment = pmrem.fromScene(room, .04); room.dispose();
    scene.environment = studioEnvironment.texture;
    rooftop = createRooftop(data); scene.add(rooftop.group);
    sky = createSky(); scene.add(sky.mesh);
    studioGroup = new THREE.Group(); scene.add(studioGroup);
    const ground = new THREE.Mesh(new THREE.PlaneGeometry(100, 100), new THREE.MeshStandardMaterial({ color: '#3a4535', roughness: .9 }));
    ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; studioGroup.add(ground);
    const plinth = new THREE.Mesh(new THREE.CylinderGeometry(1.58,1.62,.12,64), new THREE.MeshStandardMaterial({ color: '#535e49', roughness: .8 }));
    plinth.position.y = .06; plinth.castShadow = plinth.receiveShadow = true; studioGroup.add(plinth);
    material = new THREE.MeshPhysicalMaterial();
    mesh = new THREE.Mesh(new THREE.SphereGeometry(), material); mesh.castShadow = mesh.receiveShadow = true; scene.add(mesh);
    lights = { sun: new THREE.DirectionalLight('#ffce99', 3), ambient: new THREE.HemisphereLight('#b8d1dc', '#575047', 1), fill: new THREE.PointLight('#c7e4ed', 24, 18, 2) };
    lights.sun.position.set(-8, 13, 6); lights.sun.target.position.set(0, .7, 0);
    lights.sun.castShadow = true;
    const shadowSize = innerWidth < 760 ? 1024 : 2048;
    lights.sun.shadow.mapSize.set(shadowSize, shadowSize);
    Object.assign(lights.sun.shadow.camera, { left: -12, right: 12, top: 12, bottom: -12, near: .5, far: 65 });
    lights.sun.shadow.normalBias = .022; lights.sun.shadow.bias = -.0002;
    lights.fill.position.set(3,3,-2); scene.add(lights.sun, lights.sun.target, lights.ambient, lights.fill);
    new ResizeObserver(() => {
      const rect = $('viewport').getBoundingClientRect();
      renderer.setSize(rect.width, rect.height, false);
      camera.aspect = rect.width / rect.height; camera.updateProjectionMatrix();
    }).observe($('viewport'));
    new IntersectionObserver(entries => { visible = entries[0].isIntersecting; }).observe($('viewport'));
    renderer.domElement.addEventListener('webglcontextlost', event => {
      event.preventDefault(); $('render-error').hidden = false; $('capture').disabled = true;
      $('render-error').querySelector('p').textContent = 'Graphics memory was released by your device. Reload this page to restore the scene. Your controls can still be exported.';
    });
    updateShape(); updateMaterial(true); updateEnvironment();
    $('loading-world').hidden = true;
    let last = performance.now();
    renderer.setAnimationLoop(now => {
      const dt = Math.min((now - last) / 1000, .05); last = now;
      if (!visible || document.hidden) return;
      if (autoRotate) { mesh.rotation.y += dt * .2; groundHero(); }
      controls.update(); renderer.render(scene, camera);
    });
    $('world-status').textContent = 'LIVE 3D / METRE-SCALE SET';
  } catch (error) {
    console.error('ASTRA environment:', error);
    renderer = null; $('loading-world').hidden = true; $('render-error').hidden = false;
    $('capture').disabled = $('rotate').disabled = true;
    $('world-status').textContent = '3D PREVIEW UNAVAILABLE';
  }
}
for (const name of ['color','roughness','scale','bump','wetness','haze']) {
  $(name).addEventListener('input', event => {
    state[name] = name === 'color' ? event.target.value : Number(event.target.value);
    syncUI();
    if (name === 'wetness' || name === 'haze') updateLighting(); else updateMaterial();
  });
}
for (const [key, property, update] of [['shape','shape',updateShape],['light','lighting',updateLighting],['environment','environment',updateEnvironment],['view','view',updateCamera]]) {
  document.querySelectorAll(`[data-${key}]`).forEach(button => button.onclick = () => {
    state[property] = button.dataset[key]; syncUI(); update();
  });
}
$('rotate').onclick = () => { autoRotate = !autoRotate; $('rotate').setAttribute('aria-pressed', autoRotate); };
$('reset-camera').onclick = () => { updateCamera(); toast('Camera returned to the selected view.'); };
$('reset').onclick = () => {
  Object.assign(state, { color: current.color, roughness: current.roughness, scale: 1, bump: current.bump });
  syncUI(); updateMaterial(); toast('Surface reset to its starting point.');
};
$('export').onclick = () => {
  save(new Blob([JSON.stringify(settings(), null, 2)], { type: 'application/json' }), `astra-${state.material}.json`);
  toast('Settings exported, including the environment. Import in Blender → ASTRA.');
};
$('share').onclick = async () => {
  const url = new URL(location.href); url.search = ''; url.hash = 'studio';
  url.searchParams.set('look', JSON.stringify(settings()));
  try { await navigator.clipboard.writeText(url.href); toast('Scene link copied, including material, lighting, and environment.'); }
  catch {
    const input = document.createElement('textarea'); input.value = url.href; document.body.append(input); input.select();
    const ok = document.execCommand('copy'); input.remove();
    toast(ok ? 'Scene link copied.' : 'Could not copy. Export settings to save this look.');
  }
};
$('capture').onclick = () => {
  if (!renderer) return;
  renderer.render(scene, camera);
  renderer.domElement.toBlob(blob => {
    if (blob) { save(blob, `astra-${state.environment}-${state.material}.png`); toast('Scene image saved. This is a browser render.'); }
  }, 'image/png');
};
$('scene').addEventListener('keydown', event => {
  if (!mesh || !['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(event.key)) return;
  event.preventDefault();
  if (event.key === 'ArrowLeft') mesh.rotation.y -= .12;
  if (event.key === 'ArrowRight') mesh.rotation.y += .12;
  if (event.key === 'ArrowUp') mesh.rotation.x -= .12;
  if (event.key === 'ArrowDown') mesh.rotation.x += .12;
  groundHero();
});
$('expand-scene').onclick = () => {
  const expanded = $('studio').classList.toggle('is-expanded');
  $('expand-scene').setAttribute('aria-pressed', expanded);
  $('expand-scene').textContent = expanded ? 'Show controls ↙' : 'Expand scene ⛶';
};
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && $('studio').classList.contains('is-expanded')) $('expand-scene').click();
});
syncUI(); initialize();
