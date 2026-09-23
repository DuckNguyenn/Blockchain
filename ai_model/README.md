# AI model

Module AI của HRC Safety Log.

- `detect.py`: pipeline suy luận YOLO, nhận webcam/video và tạo incident log.
- `logging_service.py`: chuẩn hoá JSON, SHA-256 và lưu bằng chứng.
- `verify.py`: xác minh hash của incident log.
- `weights/`: trọng số mô hình của nhóm; file lớn nên quản lý bằng Git LFS.

Chạy từ thư mục gốc:

```powershell
python -m ai_model.detect --source 0 --show
```

Pipeline dùng các adapter vùng an toàn và blockchain trong `iot_code`.
