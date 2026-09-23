# Cấu trúc repository

```
HRC-Safety-Log/
├── README.md                 # Cài đặt, cấu hình và chạy demo
├── Report_NhomXX.pdf         # Báo cáo kỹ thuật chính thức (thêm khi hoàn thiện)
├── contracts/                # Smart contracts Solidity/Hardhat
├── ai_model/                 # Mã huấn luyện/suy luận AI và trọng số
├── iot_code/                 # Firmware, mô phỏng IoT và gateway
├── config/                   # Cấu hình dùng chung, ví dụ zones.json
├── data/                     # Incident log, evidence, dữ liệu demo (không commit dữ liệu nhạy cảm)
└── docs/                     # Tài liệu tham khảo và tài liệu kỹ thuật bổ sung
```

## Phân loại mã hiện hữu

| Mã hiện hữu | Vị trí chuẩn |
| --- | --- |
| `src/detect.py`, `src/logging_service.py`, `src/verify.py` | `ai_model/` |
| `src/zone.py`, `src/blockchain.py` | `iot_code/` |
| `contracts/contracts/SafetyLog.sol` | `contracts/contracts/` |

Các module cũ trước đây nằm trong `src/` đã được chuyển vào các vị trí chuẩn ở trên; repository không giữ bản implementation trùng lặp trong `src/`.

`final_project_requirements.pdf` là hướng dẫn đồ án, không phải báo cáo chính
thức; giữ nó dưới `docs/reference/` nếu cần lưu trong repository. Không đổi tên
nó thành `Report_NhomXX.pdf`.
