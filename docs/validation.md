# Lab 03 — ตารางตรวจผล A1–A5

VCC = 12 V, RC = 2.2 kΩ, beta = 100, VBE = 0.70 V
เกณฑ์ของกลุ่ม: |ΔIC| ≤ 0.01 mA และ |ΔVCE| ≤ 0.02 V เทียบค่าอ้างอิงที่ยังไม่ปัดเศษ
หน้าเว็บแสดง 3 significant figures (เช่น 1.03 mA) จึงต้องเผื่อความละเอียดนี้ไว้

| กรณี | โหมดและอินพุต | คาดหมาย (คำนวณมือ) | เห็นจริง | วิธีตรวจ | สถานะ |
| --- | --- | --- | --- | --- | --- |
| A1 | Divider · R1 = 100 kΩ, R2 = 22 kΩ, RE = 1 kΩ | 1.2299 mA · 8.0522 V (exact) — หน้าเว็บโชว์ approx 1.46 mA / 7.32 V เท่าเดิม | | | |
| A2 | Fixed · RB = 1 MΩ | 1.1300 mA · 9.5140 V | | | |
| A3 | Emitter · RB = 1 MΩ, RE = 1 kΩ | 1.0263 mA · 8.7054 V | | | |
| A4 | Emitter · RB = 1 MΩ, RE = 2 kΩ | 0.9401 mA · 8.0328 V (IC ลดจาก A3) | | | |
| A5 | Fixed · RB = 0 | ฟอร์มแจ้ง `ต้องมากกว่า 0`, เว็บไม่ล่ม, ไม่แสดงผลรอบก่อน | | | |

## ค่าอ้างอิงที่ยังไม่ปัดเศษ

- A1: VBB = 2.163934 V, RB(Thévenin) = 18.0328 kΩ, IB = 12.2986 µA
  → IC = 1.229858 mA, IE = 1.242157 mA, VE = 1.242157 V, VB = 1.942157 V,
  VC = 9.294312 V, VCE = 8.052155 V
- A2: IB = 11.3 µA → IC = 1.13 mA, IE = 1.1413 mA, VE = 0 V, VB = 0.70 V,
  VC = 9.514 V, VCE = 9.514 V
- A3: IB = 11.3 / 1.101 MΩ = 10.2634 µA → IC = 1.026340 mA, IE = 1.036603 mA,
  VE = 1.036603 V, VB = 1.736603 V, VC = 9.742053 V, VCE = 8.705450 V
- A4: IB = 11.3 / 1.202 MΩ = 9.4010 µA → IC = 0.940099 mA, IE = 0.949501 mA,
  VE = 1.899002 V, VB = 2.599002 V, VC = 9.931782 V, VCE = 8.032780 V

## A3 → A4

RE ใหญ่ขึ้น → ตัวส่วน `RB + (1 + beta)RE` ใหญ่ขึ้น → IB และ IC ลดลง
→ VE = IE·RE เพิ่มขึ้น แต่ VC แทบไม่เปลี่ยน → VCE ลดลง
ทำนายก่อนรัน: IC ลด, VCE ลด

## Lab 04 — Browser acceptance

ตรวจวันที่ 24 พ.ย. 2026: Windows, Python 3.12.7, ngspice 38, Chrome ผ่าน
**Playwright MCP** ที่ Flask localhost (`:5055`). ใช้โมเดลสอน `LAB_NPN`
ที่ 27 °C; ไม่พบ Instructor Starter Kit หรือ model card ในวัสดุที่ได้รับ
จึงไม่อ้างว่าเป็นโมเดลที่ผู้สอนรับรอง

ดู [บันทึกการตรวจ Playwright MCP ฉบับละเอียด](evidence/playwright-b1-b8.md)
สำหรับค่าที่อ่านจากเว็บ, ข้อความ ngspice log, การเทียบกับการรัน ngspice CLI
และภาพก่อน–หลังที่แยกตามกรณี

| Case | วิธี / อินพุต | คาดหมาย / อ้างอิง | ผลที่อ่านจริง | หลักฐาน | สถานะ |
| --- | --- | --- | --- | --- | --- |
| B1 | โหลดและส่งฟอร์ม Lab 03 ทั้งสามโหมดด้วยค่า A1–A3 | IC/VCE ตรงตารางอ้างอิงหลังปัดเศษ | Fixed: 1.13 mA / 9.51 V; Emitter: 1.03 mA / 8.71 V; Divider: 1.46 mA / 7.32 V | ตาราง DC Bias Results ของทั้งสามโหมด | PASS |
| B2 | Run DC ค่าเริ่มต้น | มี `.op` หนึ่งแถว; ค่าและหน่วยตรง raw | VB 1.9491 V, VE 1.2895 V, VC 9.1894 V, VCE 7.9000 V, IC 1.2775 mA; `Succeeded`, `LAB_NPN` | [หน้าจอ DC](evidence/lab04-dc.png), [netlist](evidence/baseline-dc.cir), [ASCII raw](evidence/baseline-dc.raw) | PASS |
| B3 | เปลี่ยนเฉพาะ RE จาก 1 เป็น 2 kΩ แล้ว Run DC | IC ลดลงเมื่อ emitter degeneration เพิ่ม | IC 1.2775 → 0.69586 mA; VCE 7.9 → 9.0646 V; Run log รายงาน 1 แถวทั้งสองรอบ และ netlist ระบุ `RE e 0 2000` ในรอบหลัง | [ก่อน: 1 kΩ](evidence/lab04-dc.png), [หลัง: 2 kΩ](evidence/lab04-re-2k.png) | PASS |
| B4 | Run AC ค่าเริ่มต้น | กราฟ gain (dB) และ phase (°) ตามแกนความถี่ log; CE กลับเฟสใน passband | ที่ 1 kHz: 1.75 V/V, 4.860 dB, −179.87°; −3 dB ที่ 1.825 Hz และ 73.19 MHz เทียบจุด 1 kHz; log และแต่ละเส้น 361 จุด | [Bode](evidence/lab04-ac-desktop.png), ตัวอย่าง raw ด้านล่าง | PASS |
| B5 | Run Transient ที่ 10 mV peak, 1 kHz | สี่คาบสุดท้ายราว 8–12 ms, Vin ≈ 20 mVpp, Vout กลับเฟส | Vin 20 mVpp, Vout 34.99 mVpp; log และแต่ละเส้น 481 จุด; ที่ 11.25233 ms: Vin +9.999 mV และ Vout −17.481 mV จาก raw | [Baseline transient](evidence/lab04-transient.png) | PASS |
| B6 | เปลี่ยน Source เป็น 25 mV peak, 2 kHz | Vin ≈ 50 mVpp; เวลาสี่คาบสุดท้ายลดครึ่ง; เส้น Vout เปลี่ยน | Vin 49.99 mVpp, Vout 87.48 mVpp; เวลาประมาณ 4–6 ms; พิกัด SVG ของ Vin และ Vout เปลี่ยนทั้งคู่; netlist เปลี่ยนเป็น `SIN(0 0.025 2000)` | [Before](evidence/lab04-transient.png) / [After](evidence/lab04-transient-changed.png) | PASS |
| B7 | ส่ง RE = 0 หลังมีกราฟ; ทดสอบอีกเซิร์ฟเวอร์ `:5056` ที่ตั้ง `NGSPICE_BIN` ให้ชี้ไฟล์ที่ไม่มี | แจ้งสาเหตุและไม่แสดงกราฟหรือสถานะสำเร็จ | อินพุต: HTTP 400, `Invalid input`; ไม่พบ engine: HTTP 503, `Run failed`; ทั้งสองกรณีไม่แสดงกราฟหรือผลเดิม | [RE = 0](evidence/lab04-invalid.png), [ไม่พบ ngspice](evidence/lab04-engine-unavailable.png) | PASS |
| B8 | Desktop 1280 × 900 และ mobile viewport 390 × 844; สลับ AC → Transient แล้ว Run ด้วย Enter ในฟอร์ม | ปุ่มและกราฟอยู่ในจอ ไม่มี horizontal overflow | client width เท่ากับ scroll width (1265 px และ 375 px ตามลำดับเมื่อหักแถบเลื่อน); กราฟไม่ล้น สลับโหมดและกด Enter แล้ว `Succeeded` | [Desktop](evidence/lab04-ac-desktop.png), [Mobile](evidence/lab04-mobile.png) | PASS |

### ที่มาของตัวเลขและการรันซ้ำ

- `baseline-dc.raw` เป็นผลจาก ngspice แบบ batch ของ `baseline-dc.cir` (ตัด
  ช่องว่างท้ายบรรทัดในตัวอย่างที่เก็บใน Git เท่านั้น) รันซ้ำจาก root:
  `ngspice -n -b -o dc.log -r dc.raw docs/evidence/baseline-dc.cir`
  (Windows ใช้ `ngspice_con.exe` หากต่างชื่อ) ค่า VCE คำนวณจาก `v(c) - v(e)`;
  IC คือกระแสใน Vsense ขนาด 0 V โดยนับทิศเข้าคอลเลกเตอร์เป็นบวก
- AC raw ที่ 1 kHz ให้ Vin = `1 + j0` V และ
  Vout = `−1.749797773 − j0.003963000` V; หารเพื่อหา gain และแปลงขนาดเป็น dB
  ได้เฟสประมาณ −179.87° ซึ่งเทียบเท่า 180.13° เมื่อวัดในช่วง 0–360°
- Python approximation ให้ IC 1.46 mA และ VCE 7.32 V (ต่างจาก `.op`
  ประมาณ 0.18 mA และ 0.58 V) เพราะใช้ β และ VBE คงที่กับการประมาณ divider;
  VBE ของ `.op` รอบนี้ประมาณ 0.660 V และโมเดลมี Early effect
- ช่วง −3 dB อ้างอิงที่ 1 kHz ไม่ใช่ตัวเลขตายตัว หากไม่มีจุดตัดจะแสดง
  `Not determined in sweep range` ส่วน Transient เป็น 4 คาบท้ายที่เลือก
  ไม่รับประกันว่าเข้าสู่ steady state สำหรับทุกค่าที่ป้อน

### UI polish และขอบเขตการตรวจ

- **ก่อน:** [หน้า Lab 03 เดิม](evidence/lab03-before.png) — มีเฉพาะเครื่องคำนวณ
  bias; ใช้เป็นภาพอ้างอิงก่อนเพิ่มพื้นที่แสดงกราฟและที่มาของผล
- **หลัง:** [หน้า Lab 04 บน desktop](evidence/lab04-ac-desktop.png) และ
  [mobile](evidence/lab04-mobile.png) — ใช้โครงสามส่วนจากตัวอย่าง: วงจรและ
  อินพุต, โหมดและกราฟ, ผลพร้อมสถานะ; จอแคบเรียงเป็นคอลัมน์เดียว
- ใช้ Impeccable 4.10.0 (`polish`/`audit` playbooks และ detector บนหน้า AC
  ก่อนรัน) พบกล่องซ้อนและการตัดบรรทัดคำท้ายบนมือถือ จึงเปลี่ยนข้อความสถานะ
  เป็นเส้นคั่นและย่อข้อความ หลังแก้ detector คืน `[]` ที่ทั้งสองขนาด viewport
  ที่ตรวจ ไม่ได้อ้างว่าเป็นการรับรอง WCAG; ตรวจกราฟจริงแยกด้วย Playwright MCP
  และปรับเลขกำกับแกนให้ไม่ชนชื่อแกนในจอแคบ
- รัน `python -m unittest discover -v` โดยเปิดใช้ ngspice จริง: 42 tests
  ผ่าน (รวม 35 tests เดิม) การตรวจ timeout ใช้การจำลองใน unit test

### AI และสิ่งที่ผู้เรียนควรตรวจเอง

- AI ช่วยเพิ่ม adapter, หน้า simulator, กราฟ SVG และเอกสาร โดยคงตัวคำนวณ Lab 03 ไว้
- AI ตรวจผลด้วย ngspice, Playwright MCP และชุดทดสอบตามหลักฐานด้านบน
- ผู้เรียนควรลองเปลี่ยน RE และ Source เอง แล้วเทียบตัวเลข/หน่วยกับ raw และตรวจ
  model card ที่ผู้สอนกำหนดก่อนสาธิต
