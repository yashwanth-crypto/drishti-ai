# Drishti-AI — what's outstanding

State as of 2026-08-19. Written as a handoff so a new session can pick up
without re-deriving anything.

---

## Where things stand

The system runs. `.\start-app.ps1` brings up Postgres, the FastAPI inference
service, the Spring Boot backend and the dashboard, and prints a public tunnel
URL. Auth works, the defect threshold is applied, operator corrections are
captured, and the model refuses to judge parts it doesn't recognise.

Live now:

- **Site** — https://yashwanth-crypto.github.io/drishti-ai/
- **Demo** — https://yashwanth-crypto.github.io/drishti-ai/demo/ (recorded data, no backend)
- **Repo** — https://github.com/yashwanth-crypto/drishti-ai (main, 23 commits, clean history)
- **LinkedIn** — https://www.linkedin.com/company/drishti-ai-msme

Everything below is what has *not* been done.

---

## 1. The pilot — the only thing that really matters

Everything else on this list is optional. This isn't.

**Collect real images from a shop.** Access is available; the tooling is built
and tested. See [CAPTURE_SETUP.md](CAPTURE_SETUP.md) for the full protocol.

```powershell
cd C:\dev\drishti-ai\module1_cv_defect
..\.venv\Scripts\python.exe src\capture.py --source http://PHONE-IP:8080/video --prefix shopname
```

- Target **200–300 images per class**, one part type only
- Shoot the reject bin first — defects are the bottleneck
- **Back the folder up to a USB drive before anything else.** `data/collected/`
  is gitignored, so git cannot recover it. Re-shooting means another visit.

**Then:** send the class counts and a fine-tuning script gets built — starting
from the existing checkpoint rather than ImageNet, with `strong=True`
augmentation on.

**Then:** re-fit the OOD profile against the new checkpoint, or every part from
that shop reads as unrecognised:

```powershell
..\.venv\Scripts\python.exe src\ood.py fit --checkpoint models\<new>.pt --data-root data\collected
```

---

## 2. Known gaps in the product

| Gap | Detail |
|---|---|
| **Module 3 has no dataset locally** | `module3_predictive_maintenance/data/` doesn't exist. `POST /api/maintenance/predict` only works if the caller supplies all 125 features. Source is a Nature paper, not Kaggle, so it's more effort. The tool-wear charts render fine from seeded data, so this is not urgent. |
| **Feedback is captured, never used** | Corrections accumulate with their images; nothing retrains on them. Deliberate — retraining needs pilot volume. |
| **No Docker** | Needs WSL2, which was declined. `docker compose up` remains the nicest deployment story for a shop-floor mini-PC if it's ever wanted. |
| **Tunnel URL changes every restart** | A stable public URL needs a Cloudflare account plus a domain. |

---

## 3. One factual claim to check before repeating it

The **first LinkedIn post** says *"running fully offline on an ordinary CPU"*
alongside *"14ms average inference."*

That 14ms comes from `avg_inference_ms` in `events.json`, and the inference
service reports `device: cuda`. No CPU benchmark was found anywhere in the repo.
So those two claims probably don't belong in the same sentence.

Not worth editing a three-week-old post, but **worth not repeating**. If
offline-on-CPU is central to the pitch — and it should be, it's the
differentiator — run the benchmark on CPU and get a number that can be defended:

```powershell
cd module1_cv_defect
..\.venv\Scripts\python.exe src\benchmark_latency.py
```

---

## 4. Housekeeping

**`app/secrets.local.json` is not backed up anywhere.** It's correctly
gitignored, which also means losing this laptop loses the database password, the
JWT secret and both account passwords. Copy it to a password manager.

**Uncommitted work in the tree** (all pre-existing, none of it mine):

```
 M make_paper_figures.py
 M paper_figures/fig14_dataset_overview.png
?? Drishti-AI_Overleaf_v2.zip
?? paper_figures/app_architecture.png
?? patent_figures/
```

The Overleaf zip and `patent_figures/` were deliberately kept out of the public
repo. Decide whether they should be gitignored properly rather than left
untracked, where a `git add -A` could sweep them in.

**GitHub contributors list** — history was rewritten to remove the co-author
trailer and `main` is clean (0 trailers, only you as author). GitHub may still
show a second contributor because `refs/pull/1/head` permanently holds the
pre-rewrite commits and cannot be deleted. Expected to age out; if it hasn't
after a few days the only fix is deleting and recreating the repo, which costs
the star, the PR history and the Pages setup.

---

## 5. Content and outreach

**Next post: the site is live.** Draft is in `linkedin-post.md` (gitignored).
Was deliberately held back — the impeller post went out the same day and a
second post competes with it. Post ~3–5 days after that one.

**The post after that is the shop visit.** Real parts, a real camera, photos of
data being collected. Nobody else's feed has that. Worth saving attention for.

**Buy a domain before cold-emailing shops.** `drishti-ai.in` is ~₹600/year. The
reason is email, not the website — `yash@drishti-ai.in` reads as a company,
a personal Gmail reads as a student project. No rush until the outreach starts.

---

## 6. Deferred by choice

Listed in `APP_BUILD_PLAN.md` §12 and not worth doing yet:

- Role-specific dashboards
- Scheduled forecast refresh
- PDF/Excel owner reports
- Multi-class defect typing
- Vision model in-JVM ONNX
- Drift monitoring / MLflow — needs real data first
- Redis, Kafka, Kubernetes, multi-tenant SaaS — over-engineering at this scale

The `events.json` import still costs the bundle ~120 KB of unused base64
thumbnails. Cosmetic.

---

## Reading order for a new session

1. [ARCHITECTURE.md](ARCHITECTURE.md) — what every file does
2. [app/README.md](app/README.md) — how to run it, the API, the verified numbers
3. [CAPTURE_SETUP.md](CAPTURE_SETUP.md) — collecting real images
4. [APP_BUILD_PLAN.md](APP_BUILD_PLAN.md) — the original plan and what's ticked off
