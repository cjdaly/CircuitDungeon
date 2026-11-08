#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Trial: room backdrops from an image model, to compare with the drawn ones -- cd-342.35.

    source downloads/imagegen/env.sh
    downloads/imagegen/venv/bin/python Chapter_9/tools/gen_backdrops_ai.py \\
        [--rooms "Sewing Nook,Basement,Roof"] [--out downloads/imagegen/out]

Needs the local SDXL setup in downloads/imagegen (gitignored; see the README
there): a pinned venv, the official stabilityai SDXL base weights as fp16
safetensors, every cache kept in that folder, no remote code.

For each room it makes:
- img2img: the drawn backdrop (tools/build_backdrops.py), blown up to 1024,
  repainted at a few strengths -- low keeps our layout (quiet middle, clear
  caption band), high lets the model compose;
- txt2img: from the prompt alone, for contrast.
Every result is shrunk to 120x120 and snapped to the 16 DB16 colours, so it is
a real backdrop: `art_set.py add SET ROOM <out>/<room>/<name>.bmp --note ...`
puts one in an art set (art_sets/README.md), and <out>/<room>/sheet.png shows
them all beside the drawn one.
"""
import argparse
import os
import sys
import time

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_backdrops  # noqa: E402

backdrop = build_backdrops.backdrop
SIZE = backdrop.SIZE
GEN = 960  # 8 x 120: shrinks back to 120 exactly
PALETTE = np.array([((c >> 16) & 255, (c >> 8) & 255, c & 255) for c in backdrop.COLORS],
                   dtype=np.int32)

# Short on purpose: SDXL's text encoders read only 77 tokens, and the room's own
# words go first. ("open floor in the middle" keeps critters' spot clear.)
STYLE = ("pixel art, bold black outlines, flat colours, comic style, front view, "
         "Christmas Eve night, warm light, open floor in the middle")
NEGATIVE = ("text, letters, words, watermark, signature, photo, photorealistic, 3d render, blurry, "
            "people, person, hands, animals, cat, dog, cluttered centre")

# Themes: the look a set is painted in. Describe a style in plain words only --
# never name an artist, book, character or place (the repo is public and the
# boards are gifts; see art_sets/README.md, "IP rule").
THEMES = {
    "christmas": (STYLE, ""),
    # Topsy-turvy storybook: wobbly shapes, stripes, spirals -- original, no characters.
    "whimsy": ("whimsical storybook pixel art, wobbly curvy shapes, spirals, candy stripes, "
               "pom-pom trees, black outlines, open floor in middle",
               ", creature, monster, character, face, fur"),
}
PROMPTS = {
    "Sewing Nook": "a sewing nook: an old black sewing machine with gold decoration on a wooden "
                   "table, a red stocking half sewn under its needle, a dress form wearing a Santa "
                   "dress, flowery wallpaper, a braided rug",
    "Basement": "a dim stone basement: an old round furnace glowing orange with ducts going up, "
                "wooden stairs going up on the right, a bare light bulb, concrete floor",
    "Roof": "on a snowy rooftop at night: red shingles under thick snow, the neighbours' roofs "
            "with lit windows, a full moon with Santa's sleigh and reindeer silhouetted across "
            "it, a TV antenna, stars",
}
STRENGTHS = (0.45, 0.6, 0.75)
SEEDS = (1, 2)


def describe(room):
    """A prompt from the room's own description in the game (rooms.py)."""
    sys.path.insert(0, os.path.join(HERE, "..", "game"))
    import rooms

    text = rooms.make_world().get(room).description.rstrip(".")
    return text[0].lower() + text[1:]


def drawn(room):
    """The current hand-drawn backdrop, as RGB."""
    return build_backdrops.to_image(build_backdrops.ROOMS[room]()).convert("RGB")


def to_backdrop(img):
    """Any image -> 120x120 P image in backdrop.COLORS order (nearest colour, no dither)."""
    small = np.asarray(img.convert("RGB").resize((SIZE, SIZE), Image.BOX), dtype=np.int32)
    d = ((small[:, :, None, :] - PALETTE[None, None, :, :]) ** 2).sum(-1)
    out = Image.fromarray(d.argmin(-1).astype(np.uint8), "P")
    out.putpalette(PALETTE.astype(np.uint8).flatten().tolist() + [0] * (768 - 3 * len(PALETTE)))
    return out


def round_preview(img, scale=2):
    big = img.convert("RGB").resize((SIZE * scale, SIZE * scale), Image.NEAREST)
    mask = Image.new("L", big.size, 0)
    ImageDraw.Draw(mask).ellipse((0, 0, big.size[0] - 1, big.size[1] - 1), fill=255)
    out = Image.new("RGB", big.size, (24, 24, 28))
    out.paste(big, mask=mask)
    return out


def sheet(items, path):
    cols = 4
    w = SIZE * 2 + 8
    h = w + 14
    rows = (len(items) + cols - 1) // cols
    out = Image.new("RGB", (cols * w, rows * h), (24, 24, 28))
    draw = ImageDraw.Draw(out)
    for i, (label, img) in enumerate(items):
        x, y = (i % cols) * w + 4, (i // cols) * h + 4
        out.paste(round_preview(img), (x, y))
        draw.text((x, y + SIZE * 2 + 1), label, fill=(210, 210, 210))
    out.save(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--rooms", default=",".join(PROMPTS),
                    help='comma-separated, or "all" (rooms without a prompt here use their '
                         'rooms.py description)')
    ap.add_argument("--theme", default="christmas", choices=sorted(THEMES),
                    help="the look to paint in (THEMES)")
    ap.add_argument("--strengths", default=",".join(str(x) for x in STRENGTHS),
                    help="img2img strengths for the sheet of variants")
    ap.add_argument("--only", metavar="STRENGTH:SEED",
                    help="just this one repaint per room, e.g. 0.75:2 (no sheet of variants)")
    ap.add_argument("--add-to", metavar="SET",
                    help="with --only: add each result to this art set (art_set.py add)")
    ap.add_argument("--out", default=os.path.join(HERE, "..", "..", "downloads", "imagegen", "out"))
    ap.add_argument("--steps", type=int, default=30)
    args = ap.parse_args()
    if args.add_to and not args.only:
        sys.exit("--add-to needs --only STRENGTH:SEED (one result per room)")
    if not os.environ.get("HF_HOME"):
        sys.exit("source downloads/imagegen/env.sh first (keeps the model cache in that folder)")

    import torch
    from diffusers import StableDiffusionXLImg2ImgPipeline, StableDiffusionXLPipeline

    import glob

    # Load from the downloaded folder itself: by repo name, diffusers wants
    # every fp16 file in the repo, including a spare VAE we didn't fetch.
    snaps = glob.glob(os.path.join(os.environ["HF_HOME"], "hub",
                                   "models--stabilityai--stable-diffusion-xl-base-1.0",
                                   "snapshots", "*"))
    if not snaps:
        sys.exit("SDXL isn't downloaded; see downloads/imagegen/README.md")
    t2i = StableDiffusionXLPipeline.from_pretrained(
        snaps[0], torch_dtype=torch.float16, variant="fp16", use_safetensors=True).to("mps")
    i2i = StableDiffusionXLImg2ImgPipeline(**t2i.components)

    room_names = [r.strip() for r in args.rooms.split(",")]
    if room_names == ["all"]:
        room_names = sorted(build_backdrops.ROOMS)
    for room in room_names:
        room = room.strip()
        style, avoid = THEMES[args.theme]
        prompt = (PROMPTS.get(room) or describe(room)) + ", " + style
        negative = NEGATIVE + avoid
        out_dir = os.path.join(args.out, backdrop.file_name(room)[:-4])
        os.makedirs(out_dir, exist_ok=True)
        base = drawn(room)
        items = [("drawn (current)", base)]
        init = base.resize((GEN, GEN), Image.NEAREST)
        if args.only:
            strength, seed = args.only.split(":")
            jobs = [("i2i_s{:.2f}_seed{}".format(float(strength), int(seed)),
                     float(strength), int(seed))]
        else:
            strengths = [float(x) for x in args.strengths.split(",")]
            jobs = [("i2i_s{:.2f}_seed{}".format(s, seed), s, seed)
                    for s in strengths for seed in SEEDS]
            jobs += [("t2i_seed{}".format(seed), None, seed) for seed in SEEDS]
        for name, strength, seed in jobs:
            t = time.time()
            g = torch.Generator("cpu").manual_seed(seed)
            if strength is None:
                img = t2i(prompt, negative_prompt=negative, num_inference_steps=args.steps,
                          guidance_scale=7.0, width=GEN, height=GEN, generator=g).images[0]
            else:
                img = i2i(prompt, negative_prompt=negative, image=init, strength=strength,
                          num_inference_steps=args.steps, guidance_scale=7.0, generator=g).images[0]
            img.save(os.path.join(out_dir, name + "_raw.png"))
            bd = to_backdrop(img)
            bd.save(os.path.join(out_dir, name + ".bmp"))
            items.append((name, bd))
            if args.add_to and args.only:
                import art_set

                art_set.add(args.add_to, backdrop.file_name(room),
                            os.path.join(out_dir, name + ".bmp"),
                            "gen_backdrops_ai.py --theme {} img2img strength {} seed {}, {} steps; prompt: {}"
                            .format(args.theme, strength, seed, args.steps, prompt))
            print("{}: {} {:.1f}s".format(room, name, time.time() - t), flush=True)
        sheet(items, os.path.join(out_dir, "sheet.png"))
        print("{}: sheet {}".format(room, os.path.join(out_dir, "sheet.png")), flush=True)


if __name__ == "__main__":
    main()
