# ASTRA Material Studio

Interactive browser material explorer and a Blender 5.2.2 toolkit. Built for desktop and mobile, with procedural material previews, lighting exploration, and a browser → JSON → Blender workflow.

## Website

Production: https://sere.davidtphung.com/astra-material-studio/

Source: https://github.com/davidtphung/astra-material-studio

```sh
npm ci
npm run check
npm run build
npm run dev
```

Open `http://127.0.0.1:4173`. The site is static and publishes from `dist/`. Production uses GitHub Pages on the `gh-pages` branch; a Vercel configuration is also included for future use. The Vercel team was at its 200-project limit during initial publication. No accounts, API keys, asset uploads, or database are required. Three.js 0.186.1 is pinned and served locally. Google Fonts is optional; system fonts are the fallback.

Features: six materials, three preview shapes, four lighting environments, surface tint, roughness, detail scale, bump, orbit/pinch zoom, keyboard arrow rotation, optional automatic rotation, PNG capture, shareable look URLs, and JSON settings export. Automatic rotation starts off. Rendering pauses while the page or viewport is hidden. Pixel density is capped at 2 for mobile performance. WebGL failure leaves settings export available.

Share links put the selected settings into the URL. Recipients and hosting access logs can therefore see those settings; do not treat shared looks as private data. No user texture files leave the device.

## Install the Blender add-on

1. Download `web/downloads/astra.zip` from the live site or this repository.
2. Blender 5.2.2: **Edit → Preferences → Add-ons → menu → Install from Disk**.
3. Select the ZIP and enable **ASTRA Material Studio**.
4. In the 3D View, press **N**, then select the **ASTRA** tab.

This is a legacy add-on ZIP, not a Blender Extensions package. Only Blender 5.2.2 was executed and verified. Earlier versions are not claimed compatible.

### Complete material → object → light → camera → render workflow

1. Select an editable mesh in Object mode.
2. Choose a material and click **Load material defaults**, or **Import browser settings** with the exported JSON file.
3. Tune the surface controls and click **Create and apply material**.
4. With the mesh selected, choose a lighting preset and click **Apply editable lighting rig**.
5. Choose framing and click **Create framed camera**.
6. Choose Draft, Look development, or Final and click **Apply render preset (CPU)**.
7. Click **Validate scene**, then press **F12** to render.

The import only loads controls; applying the material and rig remain explicit actions. Browser and Blender use different procedural representations and lighting, so export transfers artist parameters, not pixel-matched appearance. Browser shape does not modify existing Blender geometry; explicit rooftop generation uses the selected sample shape.

### Demonstration

Open `web/downloads/astra-demo.blend`, or click **Generate demonstration scene** in the sidebar. The operation confirms replacement of ASTRA-owned demonstration objects, creates its own scene, and retains unrelated scenes. Repeating it keeps object and mesh counts stable. It includes six material objects, six flat samples, material labels, bevelled forms, a glass shell with 20 mm wall thickness, studio lights, overview camera, and close-up camera.

`web/downloads/blender-preview.png` is an actual Cycles CPU smoke render, 800 × 600 at 24 samples with denoising. It was visually inspected for framing, material separation and obvious artifacts. It is a small validation render, not proof of scan-level realism or production readiness.

## Material assumptions

One Blender unit represents one metre. Object coordinates are the default. Non-unit object scale can stretch procedural texture detail; ASTRA warns rather than silently applying transforms. UV mode requires a valid UV map. Browser previews use mesh UVs and may show projection seams, particularly on rounded blocks.

| Material | Intended use | Important notes |
|---|---|---|
| Brushed metal | Industrial/product surfaces | Directional coordinate stretch, anisotropic BSDF, radial Z tangent approximation; edit mapping rotation/tangent for your asset. |
| Painted metal | Coated industrial surfaces | Metal appears only through the thresholded chip mask. Noise-based chipping is not geometry-aware edge wear. |
| Concrete | Matte cast surfaces | Broad tonal noise and modest structure bump; no geometric aggregate or true cracks. |
| Wood | Warm directional surfaces | Stretched noise grain; not an exact species, end-grain model, or scanned wood. |
| Glass | Closed glass volumes | Principled transmission, IOR 1.46, absorption tint. Requires actual thickness and suitable light paths. |
| Plastic | Molded products | Fine bump, subtle color/roughness variation and restrained coat. |

Shared node group **ASTRA / Surface field v1** exposes scale and seed and outputs macro, structure, and micro fields. Material graphs label coordinates, direction, tonal variation, roughness, and bump. Roughness/bump remain editable in the shader graph. Height is bump-only; no true displacement or automatic subdivision is added.

Materials are keyed by parameters and reused when settings match. New parameter combinations create separate resources and preserve already assigned materials. **Create separate material** explicitly makes a duplicate for manual editing. Assignment changes only selected editable mesh objects and copies shared mesh data first to protect unselected instances. Existing non-ASTRA lights are retained. Applying a lighting preset replaces only ASTRA-owned lights in that scene. Camera creation changes the active camera but does not overwrite or animate an existing non-ASTRA camera.

## PBR texture workflow

1. Expand **Texture Import / Review maps** and click **Scan texture folder**.
2. Review every detected path. Missing or ambiguous names are reported. Multiple resolution variants intentionally remain unresolved; choose the desired file in the path field.
3. Correct paths manually. Choose RGB, R, G, B, or A for each map. Packed map names are not guessed: set the same source path on each intended map and choose its channel explicitly.
4. Select DirectX normals if needed; only green is inverted. Normal maps default to OpenGL.
5. Optionally enable AO multiplication as an artistic override.
6. Select your mesh and click **Apply reviewed texture maps**.

Recognized maps: base color/albedo/diffuse, roughness, metallic, normal, height/displacement, AO, alpha/opacity, emission. Names must be delimited by underscore, hyphen, period, or space. Color/emission maps use sRGB; data maps use Non-Color. Image datablocks are separate to avoid changing existing users' color interpretation. Source files are never resized or overwritten. Normal+height maps combine via a normal-map node feeding the bump node. Height uses safe bump with 1 mm distance. Alpha feeds Principled Alpha; renderer-specific transparency modes are left editable. Import does not infer or configure true displacement.

## Render presets

| Preset | Samples | Engine/device | Denoising | Tradeoff |
|---|---:|---|---|---|
| Draft | 16 | Cycles CPU | On | Fast feedback; fine relief may be lost. |
| Look development | 64 | Cycles CPU | On | Moderate noise/quality compromise. |
| Final | 256 | Cycles CPU | On | More samples; still needs review for glass and fine detail. |

Presets leave resolution, geometry, volume limits, color management and compositing unchanged. No fixed timing or speedup is claimed. Device discovery found Apple M3 Pro CPU and Metal GPU in this environment, but the toolkit deliberately uses the safe CPU path. GPU selection is manual. **Restore previous render settings** restores the engine, sample count, device and denoising values captured before the first ASTRA preset.

## Verification

```sh
blender --background --factory-startup --python-exit-code 1 --python tests/blender_smoke.py
python3 scripts/package.py
npm run check
npm run build
```

The smoke script tests registration/unregistration, all six shader graphs and controls, resource reuse, assignment, map detection, color spaces, DirectX conversion, packed-channel wiring, missing files, browser settings import, preset/restore, scene preservation, idempotent demo generation, lights, cameras, glass thickness, validation, save/reopen, and a real render. See `VERIFICATION.md` and `web/downloads/validation.json` for executed results. `artifacts/` holds local test fixtures and is not published. The downloadable scene is saved before reducing resolution/samples for the smoke test.

## Scope and known limits

This initial release completes the core workflow. The larger brief's additional rubber/leather/fabric/ceramic/stone/asphalt library, geometry-aware wear, oxidation, general material wetness masks (roof dampness is implemented), dedicated crack/scratch/dirt groups, true triplanar mapping, true displacement, HDRI loading, general-purpose volumetric rigs (the rooftop has bounded haze), compositor finishing, and automatic GPU selection are not implemented. There are no placeholder buttons claiming these features.

No mobile physical-device testing or exhaustive browser compatibility matrix was performed. Responsive browser testing covers desktop and a 390 px phone viewport; hardware performance varies. Legacy add-on installation was verified through Blender's add-on installation API, with runtime tests in background mode.

## ASTRA 0.2 — Rooftop field studio

The model now sits in a complete, fictional Kowloon-inspired rooftop workshop. This is a procedural set, not a real-address survey, photogrammetry asset, or historical reconstruction.

- A supporting building and street beneath a 16 × 14 metre tiled roof, 0.90 m workbench, 0.99 m sample support, stools, a measurement rule, paint tin, gloves, crates, cones, and plants.
- Surrounding apartment buildings with front and side windows, balconies, floor bands, AC units, drain stacks, and antennae.
- A service room, roof tank, utility pipes, laundry lines, railings, signs, drains, and damp patches.
- **Detail / Workbench / Neighbourhood** camera views, **Expand scene** mode, camera reset, four lighting moods, surface dampness and atmospheric haze controls.
- Browser environment reflections are captured from the generated scene at the sample position and refreshed when lighting or weather changes. They are static local approximations, not screen-space or per-pixel ray-traced reflections.
- Browser geometry uses instanced batches. The Blender equivalent uses shared mesh datablocks while keeping individual objects editable.

`astra/world_data.py` defines the complete set using a deterministic seed and Y-up metre coordinates. `python3 scripts/generate-world.py` writes the exact matching browser asset, `web/world.json`. The Blender builder converts the same transforms into Z-up coordinates. Do not hand-edit the generated JSON independently.

### Open or generate the rooftop

Download `web/downloads/astra-rooftop.blend` and open it in Blender 5.2.2. It includes editable geometry, three cameras, procedural materials, a directional sky light, a visible workbench lamp, sign lighting, and bounded volumetric haze.

Alternatively, install the updated ZIP, import an exported browser settings file, then select **ASTRA → Rooftop / Real-world context → Generate rooftop environment**. The explicit generation action creates its own scene and replaces only ASTRA-owned objects in that scene on repeat runs. Unowned objects, including objects placed inside the generated collection, are preserved. Generation never wraps an arbitrary selected user model automatically: it creates the configured sample shape. You can replace the sample manually in the editable scene.

The browser export now includes `environment`, `view`, `shape`, `wetness`, and `haze`. Old v1 material exports remain accepted. Browser and Blender share geometry and artist controls, but use different shading, sky, and atmospheric implementations; their images will differ. Browser haze is depth-based fog; Blender uses bounded volume scattering. Dampness changes roughness and color and reveals thin water patches; it is not a fluid simulation. Buildings have exterior detail, not full interiors. Laundry and plants remain static. No stock image, external model, or HDRI is used.

### Validate and publish updates

```sh
python3 scripts/generate-world.py
blender --background --factory-startup --python-exit-code 1 --python tests/blender_smoke.py
blender --background --factory-startup --python-exit-code 1 --python tests/rooftop_smoke.py
python3 scripts/package.py
npm run check
npm run build
# Review and commit changes, push main, then:
python3 scripts/publish-pages.py
```

The publication script verifies a clean checkout and the exact existing GitHub destination, rebuilds the site, then updates `gh-pages` through a temporary clone without force-pushing. A `main` push alone does not rebuild the deployed website. Check GitHub Pages deployment completion after publishing.
