# IoT code

Module IoT/gateway của HRC Safety Log.

- `zone.py`: polygon vùng cảnh báo/nguy hiểm và logic phân loại.
- `blockchain.py`: adapter ghi hash incident và E-Stop lên Smart Contract.
- `firmware/`: mã nạp ESP32/thiết bị IoT.
- `simulator/`: mã mô phỏng cảm biến hoặc thiết bị chấp hành.

Thông số vùng an toàn dùng chung tại `config/zones.json`.
