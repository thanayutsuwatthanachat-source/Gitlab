# Playwright MCP — บันทึกการตรวจ B1–B8

24 พ.ย. 2026 · Chrome 158 บน Windows · Flask `127.0.0.1:5055` · ngspice 38

ตรวจด้วยหน้าเว็บจริง: เปิดหน้า → อ่าน accessibility snapshot → เลือกโหมดและกรอกค่า
→ กดปุ่มส่งฟอร์ม → อ่าน snapshot และค่าที่แสดง → เทียบค่าอ้างอิง → บันทึกภาพ
กรณี B7 ใช้ Flask ที่ `:5056` เพิ่มอีกหนึ่งตัว โดยตั้ง `NGSPICE_BIN`
ให้ชี้ไปยังไฟล์ที่ไม่มี แล้วส่งฟอร์มจริงเช่นกัน

## B1 · Regression — PASS

ใช้ VCC = 12 V, RC = 2.2 kΩ, β = 100, VBE = 0.70 V; RB = 1 MΩ สำหรับ
Fixed/Emitter, RE = 1 kΩ สำหรับ Emitter/Divider และ R1/R2 = 100/22 kΩ สำหรับ Divider
ค่าจากตาราง **DC Bias Results** ตรงกับ [ค่าอ้างอิง A1–A3](../validation.md):

| โหมด | VB | VE | VC | VCE | IB | IC | IE |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Fixed | 700 mV | 0 V | 9.51 V | 9.51 V | 11.3 µA | 1.13 mA | 1.14 mA |
| Emitter | 1.74 V | 1.04 V | 9.74 V | 8.71 V | 10.3 µA | 1.03 mA | 1.04 mA |
| Divider | 2.16 V | 1.46 V | 8.78 V | 7.32 V | 14.6 µA | 1.46 mA | 1.48 mA |

Divider แสดงผล exact cross-check แยก: IC 1.23 mA, VCE 8.05 V

## B2–B3 · DC operating point และเปลี่ยน RE — PASS

ทั้งสองรอบตอบ HTTP 200 และแสดง `Succeeded`, `ngspice batch · LAB_NPN · 27 °C`
ตรวจ netlist จากหน้าเว็บแล้วพบความต่างเพียงบรรทัดเดียว:
`RE e 0 1000` → `RE e 0 2000` (Ω)

| RE | VB | VE | VC | VCE | IC | ภาพ |
| --- | --- | --- | --- | --- | --- | --- |
| 1 kΩ | 1.9491 V | 1.2895 V | 9.1894 V | 7.9 V | 1.2775 mA | [ก่อน](lab04-dc.png) |
| 2 kΩ | 2.0482 V | 1.4045 V | 10.469 V | 9.0646 V | 0.69586 mA | [หลัง](lab04-re-2k.png) |

ข้อความที่อ่านจาก **Run log & provenance** ของทั้งสองรอบ (ตัดเฉพาะช่วงต้น):

```text
Note: No compatibility mode selected!

Circuit: lab 04 common-emitter voltage-divider reference

ASCII raw file "run.raw"
Doing analysis at TEMP = 27.000000 and TNOM = 27.000000

No. of Data Columns : 4

No. of Data Rows : 1
```

แยกรัน [netlist ตั้งต้น](baseline-dc.cir) ด้วย ngspice CLI แล้วอ่าน ASCII raw
โดยไม่ใช้ตัวแปลงผลของเว็บ: IC = 1.277540826 และ 0.695856747 mA ตามลำดับ;
VCE = 7.899956488 และ 9.064565490 V ตรงกับค่าหน้าเว็บหลังปัดเศษ

## B4 · AC — PASS

[ภาพ Bode](lab04-ac-desktop.png) แสดง Gain (dB) กับ Phase (°) บนแกน
Frequency (Hz · log) ทั้งคู่ ค่าที่ 1 kHz: **1.75 V/V, 4.860 dB, −179.87°**
ตรวจพบ SVG polyline สองเส้น เส้นละ 361 จุด

```text
Generated netlist:
.ac dec 40 0.1 1e+08
.save v(vin) v(out)

ngspice log:
ASCII raw file "run.raw"
Doing analysis at TEMP = 27.000000 and TNOM = 27.000000

No. of Data Columns : 3

No. of Data Rows : 361
```

รัน netlist เดียวกันอีกครั้งด้วย CLI: ที่ 1 kHz พบ Vin = `1 + j0` V,
Vout = `−1.749797773346835 − j0.003963000377725378` V
เมื่อนำมาหารได้ 4.859779 dB และ −179.870235° ตรงกับหน้าเว็บ

## B5–B6 · Transient และเปลี่ยน Source — PASS

หน้าเว็บแสดงกราฟ Voltage (mV) ตาม Time (ms) และระบุ Vin/Vout คนละเส้น
สองรอบตอบ HTTP 200, log รายงาน 481 แถวต่อรอบ และแต่ละเส้นมี 481 จุด
เมื่อเปลี่ยน Source ตรวจว่าพิกัดของทั้งสองเส้นเปลี่ยน

| รอบ | ค่าที่กรอก | Vin / Vout จากหน้าเว็บ | ช่วงเวลาจริงจาก raw | ภาพ |
| --- | --- | --- | --- | --- |
| B5 | 10 mV peak, 1 kHz | 20 / 34.99 mVpp | 8.00233–12.00000 ms | [ก่อน](lab04-transient.png) |
| B6 | 25 mV peak, 2 kHz | 49.99 / 87.48 mVpp | 4.00117–6.00000 ms | [หลัง](lab04-transient-changed.png) |

ทั้งสองรอบบันทึก `.save v(vin) v(out)`; บรรทัดที่ระบุสัญญาณและช่วงเวลาที่เว็บส่งจริง:

```spice
* B5
Vin vin 0 DC 0 AC 1 SIN(0 0.01 1000)
.tran 8.33333333333e-06 0.012 0.008 8.33333333333e-06
* B6
Vin vin 0 DC 0 AC 1 SIN(0 0.025 2000)
.tran 4.16666666667e-06 0.006 0.004 4.16666666667e-06
```

แยกรันด้วย CLI และตรวจ raw: ที่ยอดบวกของ Vin พบ Vout ติดลบทั้ง B5
(+9.998925 / −17.481317 mV) และ B6 (+24.997313 / −43.720363 mV)
สอดคล้องกับการกลับเฟสของ CE ใน passband

## B7 · Invalid / Fail — PASS

- [RE = 0](lab04-invalid.png) หลังรัน Transient สำเร็จ: HTTP 400, `Invalid input`,
  ฟอร์มแจ้ง `ต้องอยู่ระหว่าง 0.01 ถึง 10000 kΩ` ไม่มีกราฟหรือค่าผลรอบก่อน
- [ไม่พบ ngspice](lab04-engine-unavailable.png): HTTP 503, `Run failed`,
  `ไม่พบ ngspice — เพิ่มลง PATH หรือตั้งค่า NGSPICE_BIN` ไม่มีกราฟหรือค่าผล

## B8 · UI — PASS

| Viewport | ความกว้างเนื้อที่ / scroll (px) | ขอบซ้าย–ขวาของกราฟ (px) | หลักฐาน |
| --- | --- | --- | --- |
| 1280 × 900 | 1265 / 1265 | 400–914 (ทั้งสองกราฟ) | [Desktop AC](lab04-ac-desktop.png) |
| 390 × 844 | 375 / 375 | 27–348 | [Mobile Transient](lab04-mobile.png) |

แถบเลื่อนแนวตั้งใช้พื้นที่ 15 px ต่อขนาดที่ตรวจ; ไม่พบการล้นแนวนอน
แผงและปุ่ม Run อยู่ภายในพื้นที่หน้าเว็บ สลับ AC → Transient บนจอมือถือ
แล้วกด Enter ในช่อง Amplitude ได้สถานะ `Succeeded`
