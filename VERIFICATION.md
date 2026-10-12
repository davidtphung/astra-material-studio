# Verification — ASTRA 0.1

Executed on 2026-10-11 (America/Los_Angeles).

- Blender 5.2.2 LTS, build d13f752e3b9c: all **43** smoke checks passed.
- Demo .blend generated, saved, and reopened successfully.
- Actual Cycles CPU render: 800 × 600, 24 samples, denoised. Visually inspected; all six objects framed, readable surface distinctions, contact shadows, and glass thickness. Fine detail remains subtle at this resolution and is not a claim of production fidelity.
- Discovered devices: Apple M3 Pro CPU and Apple M3 Pro Metal GPU. Tests used CPU only.
- Website JavaScript syntax checks and static build passed.
- Browser testing at 1440 × 1000 and 390 × 844: material/shape/light switching, roughness keyboard adjustment, shared settings restoration, JSON export. Phone document width equals viewport width (390 px); no horizontal overflow.
- Packaged ZIP installed and enabled in an isolated Blender scripts directory; imported the actual browser-downloaded file successfully, then disabled the add-on.
- Browser export downloaded and parsed as `astra.look.v1`, including the changed roughness value.
- Three.js removed-shadow-mode warning repaired by switching to supported PCFShadowMap.
- No physical phone hardware test; touch gestures use Three.js OrbitControls and remain device-dependent.
- No backend: data flow is browser controls → local Three.js renderer → file download or shared URL → explicit Blender import.

The initial website is an interactive approximation, not a remote Blender session. Rendering in Blender remains a local operation.

## Rooftop environment update — 2026-10-12

- Original 43 Blender material-toolkit checks rerun and passed.
- 20 additional rooftop checks passed: deterministic shared scene data, browser/Blender parity, environment settings import, UI generation operator, original-scene preservation, metre units, material assignment, exact sample/support contact, three cameras, three motivated lights, bounded haze, unowned-object preservation, stable datablock counts, shared geometry, save/reopen, active camera persistence, real render, and unregister.
- 4,340 shared set elements, with fewer than 65 unique mesh datablocks in Blender.
- Real rooftop Cycles CPU render generated at 1200 × 900 / 40 samples, then visually reviewed for framing, contact, scene detail, shadows and material response.
- Website syntax checks and static build passed. Browser shows no shader errors.
- Phone viewport 390 × 844: no horizontal overflow, functioning scene, environment slider updates, JSON export, and expanded scene mode. Desktop testing covers camera and nighttime lighting changes.
- Updated ZIP installed and enabled in an isolated Blender scripts directory. The actual browser-downloaded environment file generated the rooftop successfully with wetness 0.5 and haze 0; zero haze omitted the atmosphere geometry.
- The updated scene export records dampness and haze explicitly. The downloaded browser fixture had wetness 0.5 and haze 0.
- Remaining limitations: no physical-device performance benchmark, no fluid simulation or moving cloth, static local environment reflections, and a fictional architectural set rather than a scan.
