"""Capture and label part images for training.

Shows a live camera view with a square guide box. One keypress files the frame
under the label you pressed, in the folder layout the training code already
expects, so collected images can be trained on without any conversion:

    <out>/train/ok_front/...     good parts
    <out>/train/def_front/...    defective parts

Keys:
    G  good part            D  defective part
    U  undo last save       SPACE  freeze/unfreeze to line a part up
    Q  quit

Sources:
    --source 0                    built-in or USB camera (default)
    --source 1                    second camera
    --source http://<phone-ip>:8080/video     phone running an IP-camera app

Why it crops square: the classifier resizes to 224x224 without preserving aspect
ratio, so a rectangular frame would be squashed at training time and again at
inference. Cropping to the guide box keeps what the model sees consistent.
"""
import argparse
import sys
from datetime import datetime
from pathlib import Path

import cv2

LABELS = {ord("g"): "ok_front", ord("d"): "def_front"}
PRETTY = {"ok_front": "GOOD", "def_front": "DEFECT"}


def centre_square(frame):
    h, w = frame.shape[:2]
    side = min(h, w)
    y0, x0 = (h - side) // 2, (w - side) // 2
    return frame[y0:y0 + side, x0:x0 + side], (x0, y0, side)


def overlay(frame, box, counts, saved_msg, frozen):
    x0, y0, side = box
    colour = (0, 200, 255) if frozen else (0, 255, 0)
    cv2.rectangle(frame, (x0, y0), (x0 + side, y0 + side), colour, 2)

    lines = [
        f"GOOD {counts['ok_front']}   DEFECT {counts['def_front']}",
        "G=good  D=defect  U=undo  SPACE=freeze  Q=quit",
    ]
    if frozen:
        lines.insert(0, "FROZEN - press SPACE to resume")
    for i, text in enumerate(lines):
        cv2.putText(frame, text, (12, 28 + i * 26),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(frame, text, (12, 28 + i * 26),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 1, cv2.LINE_AA)

    if saved_msg:
        cv2.putText(frame, saved_msg, (12, frame.shape[0] - 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(frame, saved_msg, (12, frame.shape[0] - 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (60, 255, 60), 2, cv2.LINE_AA)
    return frame


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="0",
                    help="camera index, or a URL for an IP/phone camera")
    ap.add_argument("--out", default="data/collected",
                    help="dataset root; images land in <out>/train/<label>/")
    ap.add_argument("--size", type=int, default=512,
                    help="saved image size; 512 leaves headroom above the model's 224")
    ap.add_argument("--prefix", default="",
                    help="tag for this session, e.g. a part or shop name")
    args = ap.parse_args()

    source = int(args.source) if args.source.isdigit() else args.source
    cap = cv2.VideoCapture(source)
    # Ask for a high frame size; the driver clamps to whatever it supports.
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    if not cap.isOpened():
        sys.exit(f"Could not open camera source {args.source!r}. "
                 "Try --source 1, or check that nothing else is using the camera.")

    root = Path(args.out) / "train"
    for label in LABELS.values():
        (root / label).mkdir(parents=True, exist_ok=True)

    counts = {label: len(list((root / label).glob("*.jpg"))) for label in LABELS.values()}
    print(f"saving to {root.resolve()}")
    print(f"existing: GOOD {counts['ok_front']}, DEFECT {counts['def_front']}")
    print("G=good  D=defect  U=undo  SPACE=freeze  Q=quit")

    history, saved_msg, frozen, held = [], "", False, None

    while True:
        if frozen and held is not None:
            frame = held.copy()
        else:
            ok, frame = cap.read()
            if not ok:
                print("camera stopped returning frames")
                break
            held = frame.copy()

        crop, box = centre_square(frame)
        cv2.imshow("Drishti capture", overlay(frame.copy(), box, counts, saved_msg, frozen))

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break

        elif key == ord(" "):
            frozen = not frozen

        elif key in LABELS:
            label = LABELS[key]
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")[:-3]
            name = f"{args.prefix + '-' if args.prefix else ''}{stamp}.jpg"
            path = root / label / name
            square = cv2.resize(crop, (args.size, args.size), interpolation=cv2.INTER_AREA)
            cv2.imwrite(str(path), square, [cv2.IMWRITE_JPEG_QUALITY, 95])

            counts[label] += 1
            history.append(path)
            saved_msg = f"saved {PRETTY[label]}  ->  {name}"
            print(f"  {PRETTY[label]:<7} {path}")
            frozen = False

        elif key == ord("u") and history:
            last = history.pop()
            label = last.parent.name
            last.unlink(missing_ok=True)
            counts[label] = max(0, counts[label] - 1)
            saved_msg = f"undid {last.name}"
            print(f"  undo    {last}")

    cap.release()
    cv2.destroyAllWindows()

    total = sum(counts.values())
    print(f"\ncollected this session and before: "
          f"GOOD {counts['ok_front']}, DEFECT {counts['def_front']}, total {total}")
    if total and min(counts.values()) / max(counts.values()) < 0.4:
        print("NOTE: the two classes are quite unbalanced. A model trained on this "
              "will lean toward whichever class dominates -- try to even them up.")


if __name__ == "__main__":
    main()
