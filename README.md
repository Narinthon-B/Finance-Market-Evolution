# Finance Market Evolution: Automated Data Pipeline

โปรเจกต์นี้เป็นการสร้าง Automated Data Pipeline สำหรับดึงข้อมูลราคาหุ้นกลุ่มธนาคาร (SCB, KBANK, BBL, KTC) แบบอัตโนมัติรายวัน และจัดเก็บข้อมูลลงในระบบ Cloud Storage (MinIO)

## System Workflow

#### 1. Docker Compose

-   ใช้ **Docker Compose** ในการควบคุม Microservices ทั้ง 3 ส่วน (Airflow, MinIO, Postgres) ให้ทำงานร่วมกันภายใต้ Network เดียวกัน

#### 2. การดึงข้อมูล (Task 1: `extract_data`)

-   ใช้ตัวแปร `ds` จาก Airflow เพื่อระบุวันที่ต้องการดึงข้อมูล ทำให้ระบบสามารถดึงข้อมูลย้อนหลัง
    
-   ใช้ Library `yfinance` ในการดึงข้อมูลราคาปิด (Close Price) ของหุ้น `['SCB.BK', 'KBANK.BK', 'BBL.BK', 'KTC.BK']`
    
-   ระบบมีการเช็ค `df.empty` หากเป็นวันหยุดที่ตลาดปิด ระบบจะส่ง `AirflowSkipException` เพื่อข้ามการทำงานในวันนั้นทันที (สถานะ Skipped) เพื่อป้องกัน Pipeline
    
-   ข้อมูลจะถูกจัดเก็บชั่วคราวเป็นไฟล์ `.csv` ในโฟลเดอร์ `/opt/airflow/data/` เพื่อรอการส่งต่อ
    

#### 3. การนำเข้าข้อมูล (Task 2: `upload_to_storage`)

-   ใช้ `S3Hook` เชื่อมต่อกับ MinIO ผ่านโปรโตคอล S3 โดยระบุพิกัดผ่าน `minio_conn`
    
-   ข้อมูลถูกจัดเก็บด้วยโครงสร้างโฟลเดอร์ `raw/YYYY-MM-DD/prices.csv`
    
#### 4. การจัดการทรัพยากร

-   หลังจากส่งข้อมูลขึ้น MinIO สำเร็จ ระบบจะใช้คำสั่ง `os.remove(local_file)` เพื่อลบไฟล์ชั่วคราวทิ้ง

## วิธีใช้งานและตรวจสอบผลลัพธ์

1.  **Deployment:** รันคำสั่ง `docker-compose up -d` ในเครื่องที่มี Docker
    
2.  **Configuration:** สร้าง Connection `minio_conn` ใน Airflow Admin และสร้าง Bucket `finance-market` ใน MinIO
    
3.  **Monitoring:**
    
    -   ตรวจสอบสถานะการทำงานผ่าน Airflow Grid View (สีเขียว = สำเร็จ, สีชมพู = วันหยุด)
  
      
      ![Airflow](https://github.com/user-attachments/assets/47b8646e-d3af-42bf-a15b-7172ea4f41c4)
   

        
    -    ดูไฟล์ที่ถูกจัดเก็บจริงผ่าน **MinIO Console** (localhost:9001)


      ![miniO](https://github.com/user-attachments/assets/aa2b96be-459b-436f-8742-95abb6643f8f)
