#ir_cues/loader.py

import os
import yaml

RECIPES_DIR = os.path.join(os.path.dirname(__file__), "recipes")

def load_index():
    """Return a list of all available recipes with metadata."""
    index = []
    for root, _, files in os.walk(RECIPES_DIR):
        for f in files:
            if f.endswith(".yaml") or f.endswith(".yml"):
                path = os.path.join(root, f)
                with open(path, "r", encoding="utf-8") as fh:
                    try:
                        doc = yaml.safe_load(fh)
                        if doc:
                            index.append({"id": doc.get("id", f), **doc})
                    except Exception as e:
                        index.append({"id": f, "error": str(e)})
    return index

def load_recipe(recipe_id: str):
    """Load a single recipe by id or filename."""
    for root, _, files in os.walk(RECIPES_DIR):
        for f in files:
            if f.endswith((".yaml", ".yml")):
                path = os.path.join(root, f)
                with open(path, "r", encoding="utf-8") as fh:
                    doc = yaml.safe_load(fh)
                    if doc and doc.get("id") == recipe_id:
                        return doc
    raise FileNotFoundError(f"Recipe '{recipe_id}' not found in {RECIPES_DIR}")