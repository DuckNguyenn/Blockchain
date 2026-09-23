# HRC Safety Log

HRC Safety Log là prototype ghi cảnh báo khoảng cách dùng **ESP32 và cảm biến siêu âm HC-SR04**. ESP32 đo khoảng cách và xuất telemetry JSON qua Serial. Gateway tùy chọn đọc telemetry, ghi cảnh báo có SHA-256 và có thể lưu hash lên Smart Contract.

> Phạm vi hiện tại chỉ là đo khoảng cách và ghi cảnh báo. Dự án **không dùng camera, YOLO, mô hình AI, relay, buzzer hoặc E-Stop**.

## Luồng hoạt động

```text
HC-SR04 -> ESP32 đo khoảng cách -> SAFE/WARNING/SENSOR_FAULT
        -> Serial JSON -> gateway tùy chọn
        -> JSON cảnh báo + SHA-256 -> Smart Contract tùy chọn
```

Ngưỡng mặc định trong `config/sensor.json`:

- `distance >= 50 cm`: `SAFE`, không tạo cảnh báo.
- `distance < 50 cm`: `WARNING`, gateway ghi một cảnh báo (có cooldown).
- Không nhận được echo: `SENSOR_FAULT`, gateway ghi lỗi cảm biến.

## Cấu trúc repository

```text
README.md                         Hướng dẫn cài đặt và demo
Report_NhomXX.pdf                 Báo cáo kỹ thuật chính thức (bổ sung khi có)
contracts/                        Smart Contract Solidity/Hardhat
iot_code/firmware/                Firmware ESP32 + HC-SR04
iot_code/gateway.py               Gateway đọc Serial/stdin và ghi cảnh báo
iot_code/logging_service.py       Canonical JSON + SHA-256
iot_code/blockchain.py            Adapter audit tùy chọn
ai_model/                         Placeholder; không dùng trong phiên bản này
config/sensor.json                Ngưỡng và sơ đồ chân
data/incidents/                   Cảnh báo JSON sinh ra khi chạy gateway
docs/de_tai_2_esp32_sieu_am.md    Tài liệu kỹ thuật phần cứng
docs/reference/                   Tài liệu hướng dẫn môn học tham khảo
```

## Phần cứng

- ESP32 DevKit V1 (WROOM-32).
- HC-SR04.
- Cầu phân áp 1 kΩ/2 kΩ cho chân `ECHO` 5 V trước khi vào GPIO26.
- Dây nối, breadboard và nguồn phù hợp.

Pin mặc định: `TRIG=25`, `ECHO=26`. Không đưa tín hiệu ECHO 5 V trực tiếp vào ESP32.

## Nạp firmware

1. Mở `iot_code/firmware/hrc_safety_ultrasonic.ino` bằng Arduino IDE hoặc PlatformIO.
2. Chọn board ESP32 Dev Module và đúng cổng COM.
3. Kiểm tra cầu phân áp ECHO.
4. Upload, mở Serial Monitor ở `115200 baud`.
5. Đưa vật cản qua mốc 50 cm và quan sát các dòng JSON.

Firmware chỉ đo và gửi dữ liệu; quyết định ghi cảnh báo nằm ở gateway.

## Chạy gateway Python

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

# Đọc trực tiếp cổng ESP32 (Windows)
python -m iot_code.gateway --port COM3

# Demo không cần phần cứng
Get-Content .\docs\sample_telemetry.json | python -m iot_code.gateway --stdin --cooldown-seconds 0

# Xác minh một cảnh báo đã ghi
python -m iot_code.verify data\incidents\WARN-....json
```

Gateway bỏ qua dòng khởi động không phải JSON, không ghi mẫu `SAFE`, và rate-limit các cảnh báo lặp theo `--cooldown-seconds`.

## Smart Contract tùy chọn

Contract ở `contracts/contracts/SafetyLog.sol`, test ở `contracts/test/` và deploy script ở `contracts/scripts/`:

```powershell
cd contracts
npm install
npx hardhat test
npx hardhat node
# terminal khác
npx hardhat run scripts/deploy.js --network localhost
```

Sao chép `.env.example` thành `.env` khi muốn bật audit blockchain. Gateway vẫn ghi log cục bộ nếu RPC/contract chưa cấu hình. Không commit private key.

## Kiểm thử

```powershell
python -m unittest discover -s tests -v
python -m compileall -q iot_code
```

## Giới hạn

Đây là prototype nghiên cứu, không phải hệ thống an toàn được chứng nhận. Kiểm tra phần cứng và giới hạn đo của HC-SR04 trước khi dùng trong bất kỳ môi trường thực tế nào.