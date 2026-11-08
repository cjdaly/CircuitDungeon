#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Trial: 32x32 critters and objects from an image model, prompted from today's art -- cd-342.35.

    source downloads/imagegen/env.sh
    downloads/imagegen/venv/bin/python Chapter_9/tools/gen_sprites_ai.py \\
        [--only chirpy,yarn] [--seeds 1,2,3,4] [--strength 0.85]

Today's critters are 16x16 (DawnLike, CC-BY) pixel-doubled, and the scene
objects are 16x16 shown at 4x: chunkier than the 2x room art. This tries the
local SDXL (downloads/imagegen/README.md) at drawing them at 32x32, for 2x:
each subject's current sprite, smoothed and blown up to 960px on flat green,
is the reference for shape and colours (on flat magenta, keyed out after), and a descriptive prompt says what it
is (art_sets/README.md "IP rule": plain descriptions, no names of anyone
else's characters). Results are shrunk to 32x32, the magenta keyed out, snapped
to DB16, inked round. A critter's second animation frame is derived from the
first (a 1px breathing bob), so the pair always match -- the model draws each
frame differently.

Writes <out>/<subject>/seed<N>.png (RGBA, 32x32; critters also _f1) and
<out>/sheet.png: each subject's current sprite, then the candidates, at 4x.
"""
import argparse
import glob
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.join(HERE, "..", "game")
sys.path.insert(0, GAME)
import critter_candidates  # noqa: E402
import scene_art  # noqa: E402

sys.path.insert(0, HERE)
import scene_art_src  # noqa: E402  (the 16x16 originals)

GEN = 960  # 30 x 32
KEY_RGB = (255, 0, 255)  # magenta: no art here uses it, unlike green (carrot tops, holly)
DB16 = np.array([((c >> 16) & 255, (c >> 8) & 255, c & 255) for c in scene_art.COLORS[1:17]],
                dtype=np.int32)
INK = 0  # index of ink in DB16 above
STYLE = ("pixel art game sprite, bold black outline, flat colours, cute, side view, "
         "on a plain flat magenta background")
NEGATIVE = ("text, letters, watermark, photo, photorealistic, 3d render, blurry, scenery, "
            "background objects, shadow, frame, border, multiple, two")

# subject -> (kind, source id, prompt). Critters: candidate ids in critters.py;
# descriptions from doc/CRITTERS.md, plus one festive touch.
SUBJECTS = {
    # critters (critters.CAST), each with one festive touch
    "patch": ("critter", "dog_0_0", "a white dog with orange patches and perky ears, a red collar with a gold bell"),
    "sparky": ("critter", "dog_3_0", "a red-orange dog with floppy ears wearing a green and white striped scarf"),
    "woofer": ("critter", "dog_4_0", "a big bulky white and tan dog wearing a red knitted scarf"),
    "chirpy": ("critter", "cat_0_1", "an orange tabby cat with a little red Christmas bow"),
    "nutmeg": ("critter", "rodent_0_0", "a red-orange squirrel with a big bushy tail and a sprig of holly"),
    "acorn": ("critter", "rodent_1_0", "a grey and blue-grey squirrel with a big bushy tail holding an acorn"),
    "vixen": ("critter", "quadraped_0_8",
              "an orange reindeer with red markings, antlers, a harness with a gold jingle bell, dark nose"),
    "blitzen": ("critter", "quadraped_1_8",
                "a brown and grey reindeer with big antlers, a harness with gold jingle bells, dark nose"),
    "rivet": ("critter", "elemental_1_1", "a chunky grey-blue tin robot with rivets and a strand of red tinsel"),
    "echo": ("critter", "elemental_3_1", "a dark grey four-legged robot dog with a red light on top"),
    "jingle": ("critter", "elemental_4_0", "a shiny gold four-legged robot with a little round bell"),
    # lures and props (scene_art_src.ART)
    "yarn": ("object", "ball of yarn", "a ball of red knitting yarn with a loose strand curling off it"),
    "squeaky ball": ("object", "squeaky ball", "a round blue and red rubber dog toy ball"),
    "walnuts": ("object", "walnuts", "three brown walnuts in their shells in a little blue bowl"),
    "carrot": ("object", "carrot", "one orange carrot with a green leafy top"),
    "oil can": ("object", "oil can", "an old metal oil can with a long thin spout"),
    "batteries": ("object", "batteries", "a small pack of batteries"),
    "snowman": ("object", "snowman", "a small snowman with coal eyes, a carrot nose and a red scarf"),
    # hiding spots: a critter peeks over the top of these
    "potted plant": ("object", "potted plant", "a leafy green houseplant in a terracotta pot"),
    "snowy bush": ("object", "snowy bush", "a round green bush with snow on top"),
    "cardboard box": ("object", "cardboard box", "an open brown cardboard box"),
    "leaf pile": ("object", "leaf pile", "a heap of orange, red and brown fallen leaves"),
    "chimney": ("object", "chimney", "a red brick chimney top with snow on it"),
}


def art_image(rows):
    img = Image.new("RGB", (16, 16), KEY_RGB)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                c = scene_art.COLORS[scene_art.KEY[ch]]
                img.putpixel((x, y), ((c >> 16) & 255, (c >> 8) & 255, c & 255))
    return img


def critter_frame(cid, frame=0):
    """Today's 16x16 frame for a critter candidate, on flat green."""
    i = [c[0] for c in critter_candidates.CANDIDATES].index(cid)
    sheet = Image.open(os.path.join(GAME, "art", "critters_nn.bmp"))  # today's DawnLike sprites
    f = 2 * i + frame
    t = critter_candidates.TILE
    x, y = (f % critter_candidates.TILES_WIDE) * t, (f // critter_candidates.TILES_WIDE) * t
    tile = sheet.crop((x, y, x + t, y + t))
    rgb = np.asarray(tile.convert("RGB")).copy()
    rgb[np.asarray(tile) == 0] = KEY_RGB
    return Image.fromarray(rgb).resize((16, 16), Image.NEAREST)


def source(kind, ref):
    return critter_frame(ref) if kind == "critter" else art_image(scene_art_src.ART[ref])


def to_sprite(img):
    """Model output -> 32x32 RGBA in DB16: green keyed out, fringe dropped, inked round."""
    small = np.asarray(img.convert("RGB").resize((32, 32), Image.BOX), dtype=np.int32)
    r, g, b = small[:, :, 0], small[:, :, 1], small[:, :, 2]
    bg = (r > g + 90) & (b > g + 90) & (r > 140) & (b > 140)
    idx = ((small[:, :, None, :] - DB16[None, None]) ** 2).sum(-1).argmin(-1)
    fringe = (r > g + 40) & (b > g + 40)  # half-magenta pixels at the edge
    for _ in range(2):
        edge = np.zeros_like(bg)
        edge[1:] |= bg[:-1]
        edge[:-1] |= bg[1:]
        edge[:, 1:] |= bg[:, :-1]
        edge[:, :-1] |= bg[:, 1:]
        bg = bg | (edge & fringe)
    opaque = ~bg
    near = np.zeros_like(opaque)  # ink where a see-through pixel touches the sprite
    near[1:] |= opaque[:-1]
    near[:-1] |= opaque[1:]
    near[:, 1:] |= opaque[:, :-1]
    near[:, :-1] |= opaque[:, 1:]
    ink = bg & near
    idx = np.where(ink, INK, idx)
    alpha = np.where(opaque | ink, 255, 0).astype(np.uint8)
    rgb = DB16[idx].astype(np.uint8)
    return Image.fromarray(np.dstack([rgb, alpha]), "RGBA")


def bob(sprite):
    """Frame 2: everything above the feet sits 1px lower (a breath)."""
    a = np.asarray(sprite).copy()
    rows = np.where(a[:, :, 3].any(1))[0]
    if len(rows) < 6:
        return sprite
    top, feet = rows[0], rows[-1] - 3
    a[top + 1:feet + 1] = np.asarray(sprite)[top:feet]
    a[top] = 0
    return Image.fromarray(a, "RGBA")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--only", help="comma-separated subjects (default: all)")
    ap.add_argument("--seeds", default="1,2,3,4,5")
    ap.add_argument("--strength", type=float, default=0.85)
    ap.add_argument("--steps", type=int, default=30)
    ap.add_argument("--out", default=os.path.join(HERE, "..", "..", "downloads", "imagegen",
                                                  "out-sprites-trial"))
    args = ap.parse_args()
    if not os.environ.get("HF_HOME"):
        sys.exit("source downloads/imagegen/env.sh first")
    names = args.only.split(",") if args.only else list(SUBJECTS)
    seeds = [int(s) for s in args.seeds.split(",")]

    import torch
    from diffusers import StableDiffusionXLImg2ImgPipeline

    snap = glob.glob(os.path.join(os.environ["HF_HOME"], "hub",
                                  "models--stabilityai--stable-diffusion-xl-base-1.0", "snapshots", "*"))
    if not snap:
        sys.exit("SDXL isn't downloaded; see downloads/imagegen/README.md")
    pipe = StableDiffusionXLImg2ImgPipeline.from_pretrained(
        snap[0], torch_dtype=torch.float16, variant="fp16", use_safetensors=True).to("mps")

    rows = []
    for name in names:
        kind, ref, what = SUBJECTS[name]
        out_dir = os.path.join(args.out, name.replace(" ", "_"))
        os.makedirs(out_dir, exist_ok=True)
        src = source(kind, ref)
        init = src.resize((GEN, GEN), Image.LANCZOS)  # smoothed: redraw, don't copy the 16px grid
        prompt = what + ", " + STYLE
        row = [("now", src.resize((32, 32), Image.NEAREST).convert("RGBA"))]
        for seed in seeds:
            g = torch.Generator("cpu").manual_seed(seed)
            raw = pipe(prompt, negative_prompt=NEGATIVE, image=init, strength=args.strength,
                       num_inference_steps=args.steps, guidance_scale=7.0, generator=g).images[0]
            raw.save(os.path.join(out_dir, "seed{}_raw.png".format(seed)))
            sprite = to_sprite(raw)
            sprite.save(os.path.join(out_dir, "seed{}.png".format(seed)))
            if kind == "critter":
                bob(sprite).save(os.path.join(out_dir, "seed{}_f1.png".format(seed)))
            row.append(("seed {}".format(seed), sprite))
            print("{}: seed {}".format(name, seed), flush=True)
        rows.append((name, row))
    cell = 32 * 4 + 12
    sheet = Image.new("RGB", (cell * (len(seeds) + 1), len(rows) * (cell + 4)), (48, 52, 80))
    draw = ImageDraw.Draw(sheet)
    for r, (name, row) in enumerate(rows):
        for c, (label, im) in enumerate(row):
            big = im.resize((128, 128), Image.NEAREST)
            sheet.paste(big, (c * cell + 6, r * (cell + 4) + 4), big)
            draw.text((c * cell + 6, r * (cell + 4) + 133), "{} {}".format(name, label),
                      fill=(235, 235, 235))
    sheet.save(os.path.join(args.out, "sheet.png"))
    print("sheet", os.path.join(args.out, "sheet.png"))


if __name__ == "__main__":
    main()
