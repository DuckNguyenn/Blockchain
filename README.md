# HRC Safety Log

Prototype hộp đen an toàn cho robot cộng tác: YOLO phát hiện người, kiểm tra điểm chân với polygon vùng nguy hiểm, ghi incident log có SHA-256 và tùy chọn ghi hash lên Smart Contract.

## Cấu trúc repository

```text
README.md                  Hướng dẫn cài đặt, cấu hình và chạy demo
Report_NhomXX.pdf          Báo cáo kỹ thuật chính thức của nhóm (đặt ở root)
contracts/                 Smart Contract Solidity/Hardhat
ai_model/                  Mã AI, suy luận/huấn luyện và weights/
iot_code/                  Firmware, mô phỏng IoT và blockchain gateway
config/                    Cấu hình dùng chung (zones.json)
data/incidents/            Incident JSON và evidence tạo khi chạy demo
docs/                      Tài liệu kỹ thuật; reference/ chứa tài liệu đề bài
```

`final_project_requirements.pdf` là tài liệu hướng dẫn đồ án, không phải báo cáo nhóm; bản tham khảo được lưu tại `docs/reference/`.

## Phạm vi và giới hạn

- YOLO pretrained chỉ phát hiện lớp `person`, không nhận diện danh tính.
- E-Stop trong prototype là mô phỏng cục bộ; Blockchain không nằm trong vòng điều khiển an toàn.
- Log đầy đủ lưu off-chain tại `data/incidents/`; blockchain chỉ lưu hash và metadata.
- Đây là prototype nghiên cứu, không phải bộ điều khiển an toàn được chứng nhận cho robot công nghiệp.

## Cài đặt

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Blockchain là tùy chọn. Sao chép `.env.example` thành `.env` và điền `HRC_RPC_URL`, `HRC_GATEWAY_PRIVATE_KEY`, `HRC_CONTRACT_ADDRESS` sau khi deploy; không commit `.env`.

## Chạy demo AI/IoT

Chạy từ thư mục gốc repository:

```powershell
python -m ai_model.detect --source 0 --show
python -m ai_model.detect --source "data/sample.mp4" --show
python -m ai_model.detect --source 0 --no-show
python -m ai_model.detect --source 0 --calibrate
```

Mặc định model là `yolo11n.pt`. Có thể chỉ định trọng số khác bằng `--model`; đặt trọng số nhóm trong `ai_model/weights/`.

## Cấu hình vùng nguy hiểm

Sửa `config/zones.json` theo độ phân giải camera. Tọa độ polygon là pixel `(x, y)`:

```json
{
  "camera_id": "CAM-001",
  "robot_id": "ROBOT-001",
  "danger_zone": [[200, 150], [950, 150], [1100, 650], [100, 650]],
  "warning_zone": [[120, 100], [1030, 100], [1180, 700], [50, 700]],
  "confidence_threshold": 0.45,
  "danger_frames": 5,
  "cooldown_seconds": 5
}
```

Trong cửa sổ calibrate, nhấn `d` chọn vùng nguy hiểm, `w` chọn vùng cảnh báo, click ít nhất 3 điểm mỗi polygon, `s` lưu, `r` làm lại, `q` thoát.

## Incident log và xác minh hash

Mỗi sự cố tạo JSON trong `data/incidents/`, có thể kèm ảnh bằng chứng khi thêm `--save-evidence`:

```powershell
python -m ai_model.detect --source 0 --save-evidence
python -m ai_model.verify "data/incidents/INC-....json"
```

## Smart Contract

Hợp đồng MVP ở `contracts/contracts/SafetyLog.sol`; test ở `contracts/test/` và deploy script ở `contracts/scripts/`:

```powershell
cd contracts
npm install
npx hardhat test
npx hardhat node
# terminal khác
npx hardhat run scripts/deploy.js --network localhost
```

Sau khi deploy, đặt địa chỉ vào `HRC_CONTRACT_ADDRESS`. Khi thiếu một trong ba biến blockchain, pipeline vẫn chạy và chỉ lưu log off-chain.

## Tài liệu

- [REPOSITORY_STRUCTURE.md](REPOSITORY_STRUCTURE.md): quy ước phân loại module.
- [ai_model/README.md](ai_model/README.md): module AI và weights.
- [iot_code/README.md](iot_code/README.md): firmware, simulator và gateway.
- [contracts/README.md](contracts/README.md): Smart Contract.