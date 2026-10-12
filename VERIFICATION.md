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
