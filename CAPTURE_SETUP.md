# Collecting real part images

Everything needed to walk into a shop, photograph parts, and come back with a
dataset you can fine-tune on.

---

## 1. The camera

You do **not** need an industrial camera to start. Three options, in order of how
easily you can begin:

| Option | Cost | Use when |
|---|---|---|
| **Your phone** as an IP camera | free | first visit, proving the workflow |
| **USB webcam**, 1080p, manual focus | ₹1,500–4,000 | a repeat visit or a fixed bench |
| **Industrial USB camera** (Basler, FLIR, e-con) | ₹15,000+ | an actual installed pilot |

### Phone as a camera

Install an IP-camera app (IP Webcam on Android, or similar), connect the phone
and laptop to the **same Wi-Fi**, and the app shows a URL like
`http://192.168.1.42:8080`. Then:

```bash
python src/capture.py --source http://192.168.1.42:8080/video
```

Phone cameras are excellent — often better than a cheap webcam. The catch is
that autofocus and auto-exposure keep changing, so images vary more than a fixed
rig would. Lock focus and exposure in the app if it allows it.

### USB webcam

Plug in and:

```bash
python src/capture.py --source 0
```

If it opens the wrong camera (a laptop's built-in one, say), try `--source 1`.

**Buy one with manual focus if you can.** Autofocus hunting between shots is the
single most common cause of inconsistent images.

---

## 2. The physical setup — this matters more than the camera

Your existing model reaches 99.3% partly because its training images came from a
rig where every photo is near-identical: brightness varies by about **±6 levels
out of 255** across the whole dataset. That consistency is doing real work.

Aim for the same. Five things, in order of importance:

**1. Fixed distance.** Mount the camera or mark the bench. Same distance every
shot. A phone stand or a cheap tripod is enough.

**2. Consistent lighting.** One lamp, always on, positioned the same way. A cheap
LED ring or panel light beats ceiling fluorescents, which flicker and shift
colour. **Avoid daylight** — it changes hour to hour and ruins consistency.

**3. Plain background.** A sheet of matte card. Not the shop floor, not a hand
holding the part. The model will learn the background if you let it.

**4. Same orientation.** Parts face the camera the same way each time.

**5. No shadows across the part.** Light from the front or a ring around the
lens, not from one side.

> Ten minutes spent taping a lamp and a card in place will do more for your
> accuracy than any change to the model.

---

## 3. Collecting

```bash
cd module1_cv_defect
python src/capture.py --prefix shopname
```

A window opens with a green square guide. Put the part inside the square.

| Key | Does |
|---|---|
| `G` | save as a **good** part |
| `D` | save as a **defective** part |
| `SPACE` | freeze the frame to line a part up, then press G or D |
| `U` | undo the last save (misclicked) |
| `Q` | quit |

Images are saved 512×512, cropped square from the centre of the frame, into:

```
data/collected/train/ok_front/     good
data/collected/train/def_front/    defective
```

That is exactly the layout the training code already reads — no conversion step.

### Options

```bash
--source 0        camera index, or an IP-camera URL
--out PATH        dataset root (default data/collected)
--size 512        saved image size
--prefix NAME     tags filenames, e.g. per shop or per part type
```

---

## 4. Labelling

**You label as you shoot** — that is the whole point of the two keys. There is no
separate labelling stage, no CSV, no annotation tool.

This works because the task is one decision per image: good or defective. It only
breaks down if you later want to mark *where* the defect is (bounding boxes), and
you do not need that for pass/fail.

### Who should press the key

Ideally the shop's own inspector, not you. They know what counts as a reject in
their process. If you are labelling yourself, get someone to check a sample —
mislabelled training data is worse than less data.

### How many

| Images per class | What you get |
|---|---|
| ~50 | proves the pipeline works, model still unreliable |
| 200–300 | a genuinely usable fine-tune |
| 500+ | solid |

**Keep the classes roughly balanced.** A shop makes far more good parts than
defective ones, so defects are the constraint — collect every reject you can find
and match the good count to it. The capture tool warns you if the ratio drifts
past about 40%.

**One part type first.** Two hundred images of one component beats fifty each of
four components.

### Also photograph the awkward cases

Borderline parts, unusual lighting, a part slightly off-centre. Those are what the
model gets wrong in production, and having a few in training helps a lot.

---

## 5. What to take to the shop

- Laptop, charged, with this repo working (`.\start-app.ps1` runs)
- Camera or phone, plus a stand
- A lamp, and something to clamp or tape it with
- A sheet of white or grey matte card
- Tape measure or a marked stick for repeatable distance
- Something to carry rejects in, if they will let you borrow parts

Test the whole flow **at home first**. Capture twenty images of anything, confirm
they land in the right folders. Do not debug camera drivers in front of a client.

---

## 6. After collecting

Check what you have:

```bash
python -c "from torchvision import datasets; d=datasets.ImageFolder('data/collected/train'); print(d.classes, len(d))"
```

Then fine-tune from the existing checkpoint rather than from ImageNet — it
already understands castings, so it needs far fewer images. That script is the
next thing to build; ask for it when you have images.

Turn on the wider augmentation for that run:

```python
build_transforms(image_size, train=True, strong=True)
```

Your published model was trained without it, which is why a different lamp breaks
it. Anything trained for a real deployment should have it on.

---

## 7. Re-fit the "unfamiliar part" detector afterwards

The out-of-distribution check is calibrated against whatever the model was
trained on. After fine-tuning, rebuild it:

```bash
python src/ood.py fit --checkpoint models/<your-new-checkpoint>.pt --data-root data/collected
```

Skip this and the system will flag every part from the new shop as unrecognised —
because, as far as the old profile is concerned, they are.
