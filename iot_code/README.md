# IoT code

Module chính của HRC Safety Log dùng ESP32 và HC-SR04.

- `firmware/hrc_safety_ultrasonic.ino`: đo khoảng cách và xuất Serial JSON với trạng thái `SAFE`, `WARNING` hoặc `SENSOR_FAULT`.
- `gateway.py`: đọc telemetry từ Serial/stdin, bỏ mẫu SAFE, rate-limit và ghi cảnh báo.
- `logging_service.py`: canonical JSON, SHA-256 và lưu log.
- `blockchain.py`: adapter ghi hash cảnh báo lên Smart Contract (tùy chọn).
- `verify.py`: xác minh hash của cảnh báo.

Không có camera, YOLO, mô hình AI, relay, buzzer hoặc E-Stop trong luồng hiện tại.