import importlib.util,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('world_data',root/'astra/world_data.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
world=module.build_world()
(root/'web/world.json').write_text(json.dumps(world,separators=(',',':')))
print(f'Generated shared world: {len(world["objects"])} objects, metres, seed {world["seed"]}')
