# Writes edit/media.json: which slice of which take fills each plate, timed to the VO, plus value blurs.
import json, os, sys
ROOT = os.environ.get("FILM_ROOT") or os.getcwd()  # the film project folder
caps = json.load(open(os.path.join(ROOT, "edit", "captions.json")))
W = {c["id"]: {w["word"].strip(".,").lower(): w["start"] for w in c["words"]} for c in caps}
S = {s["id"]: (s["start"], s["end"]) for s in json.load(open(os.path.join(ROOT, "edit", "timeline.json")))["scenes"]}
t = lambda l, w: W[l][w]

q0 = S["nexus"][0] + 0.05
s1, s2, s3 = t("l05", "your") + 0.2, t("l06", "it") - 0.25, t("l06", "cites") + 0.05
s4, s5 = t("l07", "turns") + 0.05, t("l07", "into") + 0.05
s6, s7 = t("l09", "and"), t("l09", "again") + 0.25
split = t("l04", "with") + 0.05
c1 = t("l10", "what") - 0.05
d = lambda a, b: round(b + 0.15 - a, 3)

# Values the film must not show (CSS px of the capture): costs, tokens, latencies, ratings, counts.
VAL = {
    "nb_home_land": [[296, 220, 210, 48], [636, 220, 210, 48], [954, 220, 210, 48], [1264, 220, 210, 48], [1574, 220, 210, 48]],
    "nb_home_port": [[298, 222, 230, 50], [540, 222, 230, 50], [780, 222, 230, 50], [298, 310, 230, 50], [540, 310, 230, 50]],
    "nb_cost_land": [[288, 108, 300, 60], [612, 108, 300, 60], [936, 108, 300, 60], [1262, 108, 300, 60], [1588, 108, 300, 60],
                     [282, 245, 84, 330], [282, 585, 84, 270], [1370, 815, 540, 34], [280, 1030, 1640, 50]],
    "nb_cost_port": [[284, 112, 780, 66], [282, 252, 76, 236], [282, 596, 76, 190], [726, 1066, 340, 240]],
    "nb_agents_land": [[288, 104, 270, 56], [828, 104, 270, 56], [1368, 104, 270, 56], [540, 698, 1380, 76], [292, 258, 708, 310]],
    "nb_agents_port": [[284, 108, 780, 64], [500, 696, 580, 76], [286, 262, 384, 300]],
    "np_members_land": [[1604, 10, 110, 30]],
    "np_members_port": [[766, 10, 110, 30]],
    "np_overview_land": [[296, 262, 1290, 96]],
}

spec = {}
for fmt in sys.argv[1:] or ["land", "port"]:  # any lib.FORMATS keys
    r, dk, sc, ng, nb = (f"research_{fmt}", f"deck2_{fmt}", f"sched_{fmt}", f"naper_group_{fmt}", f"nimbus_{fmt}")
    nav_blur = VAL["nb_home_" + fmt]
    clips = [
        {"name": "hook_type", "scene": "hook", "take": r, "in": "picked+0.4", "out": "typed+0.4", "dur": 3.95},
        {"name": "nx_pick", "scene": "nexus", "take": r, "in": "picker-open-0.3", "out": "picked+0.5", "dur": d(q0, s1)},
        {"name": "nx_type", "scene": "nexus", "take": r, "in": "picked+0.5", "out": "sent+0.3", "dur": d(s1, s2)},
        {"name": "nx_search", "scene": "nexus", "take": r, "in": "sent+0.3", "out": "done+0.6", "dur": d(s2, s3), "after_send": True},
        {"name": "nx_deck", "scene": "nexus", "take": dk, "in": "sent+0.2", "out": "done+1.0", "dur": d(s4, s5), "after_send": True},
        {"name": "nx_sched", "scene": "nexus", "take": sc, "in": "typed-2.5", "out": "confirm-card+1.0", "dur": d(s6, s7)},
        {"name": "np_group", "scene": "naper", "take": ng, "in": "named-0.6", "out": "connectors-picked+0.4", "dur": round(split + 0.15 - S["naper"][0], 3)},
    ]
    names = ["nx_home", "nx_research_cite", "nx_deck_preview", "nx_sched", "np_overview", "np_group_b", "np_members", "np_limits", "np_neworg",
             "nb_home", "nb_cost", "nb_agents"]
    stills = [{"name": f"{n}_{fmt}", "src": f"{n}_{fmt}", "blur": VAL.get(f"{n}_{fmt}", [])} for n in names]
    if fmt == "port":  # the landscape answer holds its source card whole; the portrait one opens it off the column
        stills.append({"name": "nx_research_cite_land", "src": "nx_research_cite_land", "blur": []})
    stills += [{"name": f"ws_neuron{k}", "src": f"ws_neuron{k}_land", "blur": [], "patch": [[1864, 782, 40, 40]]} for k in range(6)]  # the site's pause button
    D = os.path.join(ROOT, "capture/stills2x_root/dense")
    WEB = {"wsc_nim_home": "NimbusLayerScene_00", "wsc_nim_cost": "NimbusLayerScene_05", "wsc_nim_agents": "NimbusLayerScene_09",
           "wsc_nim_trace": "NimbusLayerScene_16", "wsc_nap_overview": "NaperLayerScene_00", "wsc_nap_members": "NaperLayerScene_03",
           "wsc_nap_moved": "NaperLayerScene_07", "wsc_nap_features": "NaperLayerScene_09", "wsc_nap_limits": "NaperLayerScene_12",
           "wsc_nex_home": "NexusLayerScene_01"}
    stills += [{"name": n, "src": f, "path": D + "/" + f + ".png", "w": 796, "blur": [], "patch": [[748, 393, 38, 38]]} for n, f in WEB.items()]  # netigen.ai product scenes, demo data
    spec[fmt] = {"clips": clips, "stills": stills}
json.dump(spec, open(os.path.join(ROOT, "edit", "media.json"), "w"), indent=1)
print(json.dumps({k: [(c["name"], c["dur"]) for c in v["clips"]] for k, v in spec.items()}))
