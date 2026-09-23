from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from ultralytics import YOLO

from iot_code.blockchain import BlockchainRecorder
from .logging_service import sha256_hex, utc_now, write_incident
from iot_code.zone import ZoneConfig, classify_foot_point, draw_zones


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ZONE_PATH = ROOT / "config" / "zones.json"
DEFAULT_INCIDENT_DIR = ROOT / "data" / "incidents"


def load_config(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def to_zone_config(config: dict[str, Any]) -> ZoneConfig:
    return ZoneConfig(
        danger_zone=tuple(tuple(point) for point in config["danger_zone"]),
        warning_zone=tuple(tuple(point) for point in config["warning_zone"]),
    )


def parse_source(value: str) -> int | str:
    return int(value) if value.isdigit() else value


def incident_id(sequence: int) -> str:
    stamp = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    return f"INC-{stamp}-{sequence:06d}"


def run(args: argparse.Namespace) -> None:
    config = load_config(args.zone_config)
    zones = to_zone_config(config)
    model = YOLO(args.model)
    capture = cv2.VideoCapture(parse_source(args.source))
    blockchain = BlockchainRecorder.from_environment()

    if not capture.isOpened():
        raise RuntimeError(f"Cannot open source: {args.source}")

    danger_frames = 0
    sequence = 0
    in_danger = False
    last_incident_at = 0.0
    robot_stopped = False
    last_state = "SAFE"

    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break

            annotated = draw_zones(frame, zones)
            current_state = "SAFE"
            detections: list[dict[str, Any]] = []

            result = model.predict(
                source=frame,
                classes=[0],
                conf=float(config.get("confidence_threshold", 0.45)),
                verbose=False,
            )[0]

            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                confidence = float(box.conf[0])
                foot_point = (int((x1 + x2) / 2), y2)
                zone = classify_foot_point(foot_point, zones)
                detections.append(
                    {
                        "confidence": round(confidence, 4),
                        "foot_point": foot_point,
                        "zone": zone,
                    }
                )
                if zone == "DANGER":
                    current_state = "DANGER"
                elif zone == "WARNING" and current_state == "SAFE":
                    current_state = "WARNING"

                color = {
                    "SAFE": (0, 200, 0),
                    "WARNING": (0, 165, 255),
                    "DANGER": (0, 0, 255),
                }[zone]
                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                cv2.circle(annotated, foot_point, 5, color, -1)
                cv2.putText(
                    annotated,
                    f"person {confidence:.2f} {zone}",
                    (x1, max(y1 - 8, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    color,
                    2,
                )

            if current_state == "DANGER":
                danger_frames += 1
            else:
                danger_frames = 0

            threshold = int(config.get("danger_frames", 5))
            if danger_frames >= threshold:
                robot_stopped = True
                if not in_danger:
                    now = time.monotonic()
                    cooldown = float(config.get("cooldown_seconds", 5))
                    if now - last_incident_at >= cooldown:
                        sequence += 1
                        event = {
                            "incident_id": incident_id(sequence),
                            "event_type": "PERSON_ENTERED_DANGER_ZONE",
                            "camera_id": config.get("camera_id", "CAM-UNKNOWN"),
                            "robot_id": config.get("robot_id", "ROBOT-UNKNOWN"),
                            "track_id": None,
                            "timestamp_utc": utc_now(),
                            "confidence": max(
                                (d["confidence"] for d in detections if d["zone"] == "DANGER"),
                                default=0.0,
                            ),
                            "foot_point": next(
                                (d["foot_point"] for d in detections if d["zone"] == "DANGER"),
                                None,
                            ),
                            "action": "EMERGENCY_STOP_LOCAL_SIMULATION",
                        }
                        event["log_sha256"] = sha256_hex(event)
                        evidence = None
                        if args.save_evidence:
                            ok_encode, encoded = cv2.imencode(".jpg", annotated)
                            if ok_encode:
                                evidence = encoded.tobytes()
                        write_incident(event, args.incident_dir, evidence)
                        if blockchain is not None:
                            try:
                                incident_tx, stop_tx = blockchain.record(event)
                                print(f"[BLOCKCHAIN] incident_tx={incident_tx}")
                                print(f"[BLOCKCHAIN] estop_tx={stop_tx}")
                            except Exception as error:
                                print(f"[BLOCKCHAIN_ERROR] {error}")
                        print(
                            f"[INCIDENT] {event['incident_id']} "
                            f"hash={event['log_sha256']}"
                        )
                        last_incident_at = now
                    in_danger = True
            else:
                in_danger = False

            label = f"STATE: {current_state}"
            if robot_stopped:
                label += " | ROBOT: EMERGENCY_STOPPED"
            cv2.putText(
                annotated,
                label,
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.85,
                (0, 0, 255) if robot_stopped else (0, 200, 0),
                2,
            )
            cv2.putText(
                annotated,
                f"Previous: {last_state} | danger frames: {danger_frames}/{threshold}",
                (20, 68),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2,
            )
            last_state = current_state

            if args.show:
                cv2.imshow("HRC Safety Log", annotated)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q") or key == 27:
                    break

    finally:
        capture.release()
        cv2.destroyAllWindows()


def calibrate(source: str, output_path: Path) -> None:
    capture = cv2.VideoCapture(parse_source(source))
    if not capture.isOpened():
        raise RuntimeError(f"Cannot open source: {source}")

    warning: list[list[int]] = []
    danger: list[list[int]] = []
    mode = "danger"

    def on_click(event: int, x: int, y: int, _flags: int, _param: Any) -> None:
        if event == cv2.EVENT_LBUTTONDOWN:
            points = danger if mode == "danger" else warning
            points.append([x, y])

    try:
        cv2.namedWindow("Zone calibration")
        cv2.setMouseCallback("Zone calibration", on_click)
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            view = frame.copy()
            points = danger if mode == "danger" else warning
            for point in points:
                cv2.circle(view, tuple(point), 5, (0, 0, 255), -1)
            if len(points) >= 2:
                cv2.polylines(view, [np.asarray(points, dtype=np.int32)], False, (0, 0, 255), 2)
            cv2.putText(
                view,
                f"MODE: {mode.upper()} | click points | d danger | w warning | s save | r reset | q quit",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2,
            )
            cv2.imshow("Zone calibration", view)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q") or key == 27:
                break
            if key == ord("d"):
                mode = "danger"
            elif key == ord("w"):
                mode = "warning"
            elif key == ord("r"):
                danger.clear()
                warning.clear()
            elif key == ord("s") and len(danger) >= 3 and len(warning) >= 3:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                existing = load_config(output_path) if output_path.exists() else {}
                existing.update({"danger_zone": danger, "warning_zone": warning})
                output_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
                print(f"Saved zones to {output_path}")
                break
    finally:
        capture.release()
        cv2.destroyAllWindows()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="HRC Safety Log person intrusion detector")
    parser.add_argument("--source", default="0", help="Webcam index or video path")
    parser.add_argument("--model", default="yolo11n.pt", help="Ultralytics pretrained model")
    parser.add_argument("--zone-config", type=Path, default=DEFAULT_ZONE_PATH)
    parser.add_argument("--incident-dir", type=Path, default=DEFAULT_INCIDENT_DIR)
    parser.add_argument("--show", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--save-evidence", action="store_true")
    parser.add_argument("--calibrate", action="store_true")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.calibrate:
        calibrate(args.source, args.zone_config)
    else:
        run(args)


if __name__ == "__main__":
    main()
