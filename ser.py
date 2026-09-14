#!/usr/bin/env python3
"""SER Guides — moteur autonome de publication Instagram.

Le dépôt source insta-auto n'est PAS requis. Ce module contient uniquement
la logique SER : catalogue, files d'attente, assets, Cloudinary et Meta API.
"""
from __future__ import annotations
import argparse, json, os, sys, time
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()
ROOT = Path(__file__).resolve().parent
CATALOG = ROOT / "config" / "catalog.json"
HISTORY = ROOT / "state" / "history.json"
META_VERSION = os.getenv("META_API_VERSION", "v26.0")
META = f"https://graph.facebook.com/{META_VERSION}"


def read_json(path: Path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def catalog():
    return read_json(CATALOG, {"niches": []})["niches"]


def niche_dir(niche_id: str) -> Path:
    return ROOT / "niches" / niche_id


def queue(niche_id: str):
    return read_json(niche_dir(niche_id)/"posts"/"queue.json", {"posts": []}).get("posts", [])


def history():
    return read_json(HISTORY, {"posts": []})


def post_key(niche_id: str, post_id: str):
    return f"{niche_id}:{post_id}"


def resolve_slides(niche_id: str, post: dict):
    base = niche_dir(niche_id) / post["slides_dir"]
    files = [base / x for x in post.get("slides", ["slide1.png","slide2.png","slide3.png"])]
    return files


def ready_posts(niche_filter=None):
    used = {p.get("key") for p in history().get("posts", [])}
    items = []
    for n in catalog():
        nid = n["id"]
        if niche_filter and nid != niche_filter:
            continue
        for p in queue(nid):
            key = post_key(nid, p["id"])
            if p.get("status") != "ready" or key in used:
                continue
            slides = resolve_slides(nid, p)
            if all(s.exists() for s in slides):
                items.append((n, p, slides))
    return items


def pick_next(niche_filter=None):
    items = ready_posts(niche_filter)
    if not items:
        return None
    items.sort(key=lambda x: (x[1].get("priority", 100), x[0].get("guide_id", "99"), x[1]["id"]))
    return items[0]


def validate():
    errors=[]
    ids=set()
    for n in catalog():
        nid=n["id"]
        if nid in ids: errors.append(f"Niche dupliquée: {nid}")
        ids.add(nid)
        nd=niche_dir(nid)
        for required in [nd/"config.json", nd/"ebook"/"manifest.json", nd/"posts"/"queue.json", nd/"creative"/"visual.json"]:
            if not required.exists(): errors.append(f"Fichier manquant: {required.relative_to(ROOT)}")
        for p in queue(nid):
            if p.get("status") == "ready":
                for slide in resolve_slides(nid,p):
                    if not slide.exists(): errors.append(f"Slide prête mais absente: {slide.relative_to(ROOT)}")
    if errors:
        print("\n".join("ERREUR: "+x for x in errors)); return 1
    print(f"OK — {len(ids)} niches chargées, structure valide.")
    return 0


def cloudinary_upload(path: Path, niche_id: str, post_id: str):
    import cloudinary, cloudinary.uploader
    cloudinary.config(
        cloud_name=os.environ["CLOUDINARY_CLOUD_NAME"],
        api_key=os.environ["CLOUDINARY_API_KEY"],
        api_secret=os.environ["CLOUDINARY_API_SECRET"],
        secure=True,
    )
    res = cloudinary.uploader.upload(
        str(path), folder=f"ser-guides/{niche_id}",
        public_id=f"{post_id}_{path.stem}_{datetime.now():%Y%m%d%H%M%S%f}",
        resource_type="image",
    )
    url=res["secure_url"]
    for _ in range(10):
        try:
            r=requests.get(url,timeout=15,stream=True)
            if r.ok and r.headers.get("content-type","").startswith("image/"):
                return url
        except requests.RequestException:
            pass
        time.sleep(2)
    raise RuntimeError("Image Cloudinary non accessible: "+url)


def meta_post(url, data, retries=5):
    last=None
    for i in range(retries):
        r=requests.post(url,data=data,timeout=60)
        if r.ok: return r.json()
        last=f"{r.status_code} — {r.text}"
        time.sleep(8*(i+1))
    raise RuntimeError(last)


def wait_container(cid, token):
    for _ in range(35):
        r=requests.get(f"{META}/{cid}",params={"fields":"status_code,status","access_token":token},timeout=30).json()
        status=r.get("status_code")
        if status=="FINISHED": return
        if status in ("ERROR","EXPIRED"): raise RuntimeError(f"Conteneur {cid}: {r}")
        time.sleep(4)
    raise TimeoutError(f"Conteneur {cid} non prêt")


def publish_carousel(ig_id, token, urls, caption):
    children=[]
    for url in urls:
        child=meta_post(f"{META}/{ig_id}/media",{
            "image_url":url,"is_carousel_item":"true","access_token":token
        })
        children.append(child["id"])
    for cid in children: wait_container(cid,token)
    parent=meta_post(f"{META}/{ig_id}/media",{
        "media_type":"CAROUSEL","children":','.join(children),"caption":caption,"access_token":token
    })
    wait_container(parent["id"],token)
    pub=meta_post(f"{META}/{ig_id}/media_publish",{"creation_id":parent["id"],"access_token":token})
    info=requests.get(f"{META}/{pub['id']}",params={"fields":"permalink","access_token":token},timeout=30).json()
    return info.get("permalink",str(pub["id"]))


def show_selected(item):
    n,p,slides=item
    print(f"Niche : {n['name']} ({n['id']})")
    print(f"Post  : {p['id']} — {p['title']}")
    print("Slides:")
    for s in slides: print(" -",s.relative_to(ROOT))
    print("\n--- LÉGENDE ---\n"+p["caption"])


def cmd_list():
    print("SER Guides — 15 niches")
    for n in catalog():
        posts=queue(n["id"])
        ready=sum(1 for p in posts if p.get("status")=="ready")
        print(f"{n['guide_id']:>2}  {n['id']:<26} ebook={n['status']:<5} posts_ready={ready}")


def main():
    ap=argparse.ArgumentParser()
    sp=ap.add_subparsers(dest="cmd",required=True)
    sp.add_parser("list")
    sp.add_parser("validate")
    d=sp.add_parser("dry-run"); d.add_argument("--niche")
    p=sp.add_parser("publish"); p.add_argument("--niche")
    args=ap.parse_args()

    if args.cmd=="list": return cmd_list()
    if args.cmd=="validate": raise SystemExit(validate())
    item=pick_next(getattr(args,"niche",None))
    if not item:
        print("Aucun post READY avec slides complètes à publier.")
        return
    show_selected(item)
    if args.cmd=="dry-run":
        print("\nDRY RUN — rien publié."); return

    ig_id=os.environ.get("IG_USER_ID_MRLIPTN") or os.environ.get("IG_USER_ID")
    token=os.environ.get("IG_TOKEN_MRLIPTN") or os.environ.get("IG_ACCESS_TOKEN")
    if not ig_id or not token:
        raise SystemExit("Secrets manquants: IG_USER_ID_MRLIPTN + IG_TOKEN_MRLIPTN")
    n,post,slides=item
    urls=[cloudinary_upload(s,n["id"],post["id"]) for s in slides]
    permalink=publish_carousel(ig_id,token,urls,post["caption"])
    hist=history(); hist.setdefault("posts",[]).append({
        "key":post_key(n["id"],post["id"]),"niche":n["id"],"post_id":post["id"],
        "date":datetime.now(timezone.utc).isoformat(),"permalink":permalink
    })
    write_json(HISTORY,hist)
    print("\nPublié:",permalink)

if __name__=="__main__": main()
