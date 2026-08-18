import os
import json
import glob

# Recherche des fichiers de préférences LM Studio dans ~/.cache et ~/.config
lm_config_paths = glob.glob(os.path.expanduser("~/.config/LM-Studio*/**/settings.json"), recursive=True) + \
                  glob.glob(os.path.expanduser("~/.lmstudio/**/config.json"), recursive=True)

tweaked = 0
for path in lm_config_paths:
    try:
        with open(path, 'r') as f:
            cfg = json.load(f)
        cfg["gpuOffload"] = "max"
        cfg["keepModelInMemory"] = True
        cfg["flashAttention"] = True
        cfg["contextLength"] = 8192
        with open(path, 'w') as f:
            json.dump(cfg, f, indent=2)
        tweaked += 1
    except Exception:
        pass

print(f"Configurations LM Studio système : {tweaked} fichiers ajustés pour puissance maximale !")
