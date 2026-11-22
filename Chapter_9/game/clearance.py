# SPDX-License-Identifier: MIT
"""Where popups go, and keeping them off what matters -- cd-342.46, gathered
here in cd-342.47.6.

Playtest (Chris, 2026-11-21): a caption kept landing on the critter or the
thing you were meant to look at. Two fixes, both decided here as plain
geometry, so they run under desktop Python (tests/test_clearance.py):

- a caption goes in whichever band (bottom, top, middle), and a thought
  bubble in whichever spot, covers the least of what's drawn in the scene
  right now (layout(); things_in() walks the scene's group);
- a critter standing out in the open doesn't count, because it moves instead:
  it dances, hopping side to side in the nearest clear spot, never under a
  popup (plan_dance(), dance_spot()). layout() counts how far it would have
  to go.

comic.Stage shows the popups where layout() says and SceneView moves the
dancers where plan_dance() says; nav_view._Director passes one's answer to the
other.

Rects are (x0, y0, x1, y1) in screen pixels, x1/y1 exclusive.
"""

PANEL = 240
_MIDDLE = PANEL // 2
# A sprite's corners are see-through, so a rect counts as on the panel when
# its corners pulled in by _CORNER_INSET are inside this radius.
_ON_PANEL_RADIUS = 118
_CORNER_INSET = 12
# A dancing critter (SceneView) sways DANCE_SWING px either way, and keeps
# DANCE_MARGIN px between itself and a popup.
DANCE_SWING = 10
DANCE_MARGIN = 3
# Covering the thought bubble is worse than covering a thing.
_THOUGHT_WEIGHT = 4
NOWHERE = 1 << 20  # what layout() charges for leaving a critter nowhere to dance
_DANCE_STEP_COST = 8  # ...and for each px a critter dances


def layout(captions, clouds, things, dancers=()):
    """The best place for a beat's caption and thought bubble.

    captions: the caption's rect in each band, best first, or [None] for no caption
    clouds: the bubble's rects at each spot, best first, or [None] for no bubble
    things: what's drawn in the scene (rects), to keep off
    dancers: (x, y, size) of each critter out in the open, who dances clear

    Returns (spot, band, covers): indices into clouds and captions (None for
    one that isn't there) and the rects the chosen two cover. Most beats
    settle on the first layout tried: dancing only ever adds cost, so the
    dance plans (the slow part, on the board) stop once none left can win.
    """
    tried = []  # (cost before dancing, order, spot, band, covers)
    for spot, cloud in enumerate(clouds):
        for band, caption in enumerate(captions):
            cost, covers = _layout_cost(caption, cloud or (), things)
            tried.append((cost, len(tried), spot, band, covers))
    tried.sort()
    best, best_cost = None, None
    for cost, _order, spot, band, covers in tried:
        if best_cost is not None and cost >= best_cost:
            break
        cost += _dance_cost(covers, dancers) if dancers else 0
        if best_cost is None or cost < best_cost:
            best, best_cost = (spot, band, covers), cost
    spot, band, covers = best
    return (None if clouds[spot] is None else spot,
            None if captions[band] is None else band, covers)


def _layout_cost(caption, cloud, things):
    """How bad a caption at `caption` and a thought bubble over `cloud` (rects;
    either may be missing) are: what they cover, the bubble most of all.
    Returns (cost, the rects they cover)."""
    covers = list(cloud)
    cost = covered(caption, things) if caption else 0
    for rect in cloud:
        cost += covered(rect, things)
    if caption:
        cost += _THOUGHT_WEIGHT * covered(caption, cloud)
        covers.append(caption)
    return cost, covers


def _dance_cost(covers, dancers):
    """How far the critters must dance to get out from under `covers`;
    NOWHERE if one has nowhere to go."""
    spots, stuck = plan_dance(dancers, covers)
    if stuck:
        return NOWHERE
    cost = 0
    for (x, y, _size), spot in zip(dancers, spots):
        if spot is not None:
            cost += _DANCE_STEP_COST * (abs(spot[0] - x) + abs(spot[1] - y))
    return cost


def plan_dance(dancers, covers):
    """Where each critter out in the open dances while popups cover `covers`.

    dancers: (x, y, size): each one's usual top-left, and its size
    Returns (spots, stuck). spots has one entry per dancer: the top-left it
    dances round, keeping DANCE_MARGIN px clear of every popup and of the
    dancers before it (its usual one, if that's clear: it dances on the
    spot), or None if it stays put -- nothing is over it, or it has nowhere
    clear to go. stuck: one had nowhere.
    """
    near = [grow(r, DANCE_MARGIN) for r in covers]
    blocked = list(near)
    spots = []
    stuck = False
    for x, y, size in dancers:
        spot = None
        if covered((x, y, x + size, y + size), near):
            spot = dance_spot((x, y), size, blocked)
            if spot is None:
                stuck = True
            else:
                blocked.append((spot[0] - DANCE_SWING, spot[1],
                                spot[0] + size + DANCE_SWING, spot[1] + size))
        spots.append(spot)
    return spots, stuck


def overlap(a, b):
    """Area two rects share."""
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    return w * h if w > 0 and h > 0 else 0


def covered(rect, things):
    """Total area of `things` (rects, or (rect, weight) pairs) under `rect`."""
    total = 0
    for thing in things:
        if len(thing) == 2:
            thing, weight = thing
            total += weight * overlap(rect, thing)
        else:
            total += overlap(rect, thing)
    return total


def grow(rect, by):
    return (rect[0] - by, rect[1] - by, rect[2] + by, rect[3] + by)


def on_panel(rect):
    """Is a sprite at `rect` on the round panel (see-through corners allowed)?"""
    limit = _ON_PANEL_RADIUS * _ON_PANEL_RADIUS
    for x in (rect[0] + _CORNER_INSET, rect[2] - _CORNER_INSET):
        for y in (rect[1] + _CORNER_INSET, rect[3] - _CORNER_INSET):
            if (x - _MIDDLE) ** 2 + (y - _MIDDLE) ** 2 > limit:
                return False
    return True


def dance_spot(home, size, blocked, swing=None, reach=110):
    """Where a `size`-square sprite whose usual top-left is `home` should dance
    so it's clear of every rect in `blocked`: the nearest top-left (x, y),
    tucked against a popup's edge, from which it can sway `swing` px either way
    and stay clear and on the panel -- `home` itself if that's clear. None if
    nowhere within `reach` px is (any farther isn't dancing round a popup).

    Only spots against an edge are tried (home's row or column, or another
    edge's), not every pixel: a few dozen checks, cheap enough on the board.
    """
    if swing is None:
        swing = DANCE_SWING
    hx, hy = home
    xs, ys = [hx], [hy]
    for x0, y0, x1, y1 in blocked:
        xs.append(x0 - size - swing)
        xs.append(x1 + swing)
        ys.append(y0 - size)
        ys.append(y1)
    limit = reach * reach
    spots = []
    for x in xs:
        for y in ys:
            d = (x - hx) ** 2 + (y - hy) ** 2
            if d <= limit:
                spots.append((d, x, y))
    spots.sort()
    panel = _ON_PANEL_RADIUS * _ON_PANEL_RADIUS
    for _d, x, y in spots:
        left, right, bottom = x - swing, x + size + swing, y + size
        if left < 0 or right > PANEL or y < 0 or bottom > PANEL:
            continue
        hit = False
        for x0, y0, x1, y1 in blocked:  # any overlap at all rules it out
            if x0 < right and left < x1 and y0 < bottom and y < y1:
                hit = True
                break
        if hit:
            continue
        # On the panel at both ends of its sway: the swept box's corners, pulled in.
        dx = max(_MIDDLE - (left + _CORNER_INSET), right - _CORNER_INSET - _MIDDLE)
        dy = max(_MIDDLE - (y + _CORNER_INSET), bottom - _CORNER_INSET - _MIDDLE)
        if dx * dx + dy * dy <= panel:
            return (x, y)
    return None


def things_in(group, skip=(), _ox=0, _oy=0, _scale=1):
    """Screen rects of every visible TileGrid under `group` (a displayio tree),
    not counting any node in `skip` or anything under it. Text labels are
    skipped too: they're words, not things to see."""
    rects = []
    if group.hidden:
        return rects
    for node in group:
        if getattr(node, "hidden", False) or any(node is s for s in skip):
            continue
        if hasattr(node, "anchored_position"):  # a text label
            continue
        x0 = _ox + node.x * _scale
        y0 = _oy + node.y * _scale
        if hasattr(node, "tile_width"):  # a TileGrid
            w = node.width * node.tile_width * _scale
            h = node.height * node.tile_height * _scale
            rects.append((x0, y0, x0 + w, y0 + h))
        elif hasattr(node, "scale"):  # a Group
            rects.extend(things_in(node, skip, x0, y0, _scale * node.scale))
    return rects
