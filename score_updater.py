import os
import gspread
from google.oauth2.service_account import Credentials
import time
import random

import requests
import json
import re

def human_delay(min_sec=1, max_sec=2):
    time.sleep(random.uniform(min_sec, max_sec))

def get_match_score(job_description):
    cv_text = """Eda Nur Nair Full Stack Developer

Education
Bartın University, Bachelor's Degree, Management Information Systems Sep 2020– Jun 2024

Technical Skills
Frontend Development: React, Next.js, TypeScript, JavaScript (ES6+), SCSS, TailwindCSS, Radix UI, Shadcn UI, Material UI, Responsive Design
Backend & Databases: ASP.NET, Entity Framework, RESTful APIs, MS SQL, Supabase, PostgreSQL, Docker

Professional Experience
Freelance JavaScript Developer – AI Training, G2i INC – Remote (Apr 2025 – Jun 2025)
• Evaluated AI-generated frontend code using JavaScript and React
• Debugged and optimized React-based outputs
• Contributed to AI model training on React components and JavaScript patterns

IT Intern – Social Office – Remote (Apr 2025 – Jun 2025)
• Learned core IT tools including Excel, AutoCAD, Photoshop, Python
• Contributed to design and production using acquired skills

Technical Writer – Huawei Student Developer Group – Remote (Mar 2025 – Present)
• Published articles on React, Next.js, .NET Core
• Guided developers within Huawei's ecosystem

Frontend Developer Intern – Software.xyz – Remote (Aug 2024 – Oct 2024)
• Built product filtering, payment flows using React, TypeScript, Next.js
• Worked in a 9-person Agile team

Projects
HookCraft – AI Viral Content Platform (May 2025)
• Created AI-integrated web app for content suggestions
• Used React, Supabase, DeepSeek AI, Paddle, TailwindCSS

Ankara Magnets Website – Client Project (Apr 2025)
• Developed corporate site with admin panel
• Used Next.js, Supabase, Shadcn UI

Current Headlines News Portal (Oct 2024)
• Built SEO-optimized news platform with admin interface
• Used ASP.NET API, MS SQL, Next.js, TailwindCSS
"""

    prompt = f"""You are an experienced recruiter. Your task is to evaluate how well the following CV matches the given job description.

CV:
{cv_text}

Job Description:
{job_description}

You are a recruiter and give a match score (0-100) on how well your CV fits the job. Just spin the number."""

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            headers={"Content-Type": "application/json"},
            data=json.dumps({
                "model": "mistral",
                "prompt": prompt,
            }),
            stream=True
        )
        result_text = ""
        for line in response.iter_lines():
            if line:
                data = json.loads(line.decode("utf-8"))
                result_text += data.get("response", "")
        result_text = result_text.strip()
        print("Model cevabı:", result_text)

        # Sayı çekme
        match = re.search(r"(Final Score|Score)[:\s]*([0-9]{1,3})", result_text, re.IGNORECASE)
        if match:
            score = int(match.group(2))
        else:
            matches = re.findall(r"\b\d{1,3}\b", result_text)
            score = int(matches[-1]) if matches else 0
        return min(max(score, 0), 100)

    except Exception as e:
        print(f"❌ Lokal AI hatası: {e!r}")
        return 0  

def main():
    # Google Sheets API yetkilendirmesi 
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file('credentials.json', scopes=scope)
    client = gspread.authorize(creds)

    # Google Sheets dosyasını aç
    sheet = client.open("LinkedIn Jobs").sheet1

    # Tüm satırları çek
    rows = sheet.get_all_values()
    print(f"Toplam {len(rows)-1} ilan var. Skor hesaplanıyor...")

    headers = rows[1]  # 2. satır başlık
    data_rows = rows[2:]  # 3. satırdan itibaren veri

    try:
        description_index = headers.index("Açıklama")
        score_index = headers.index("Skor")
    except ValueError as e:
        print("❌ Başlık bulunamadı:", e)
        print("Mevcut başlıklar:", headers)
        return

    success_count = 0
    error_count = 0 
    skorlar = []

    for i, row in enumerate(data_rows, start=3):  # Google Sheets 1-based index
        try:
            description = row[description_index] if description_index < len(row) else ""
            current_score = row[score_index] if score_index < len(row) else ""

            if current_score and str(current_score).strip() and str(current_score).strip() != '0':
                print(f"⏭️  {i}. satır zaten skorlanmış: {current_score}")
                skorlar.append([current_score])
                continue

            if not description.strip():
                print(f"⚠️  {i}. satır boş açıklama, atlanıyor")
                skorlar.append([""])
                continue

            print(f"🔄 {i}. satır skorlanıyor...")
            score = get_match_score(description)
            print(f"✅ {i}. satır için skor güncellendi: {score}")
            skorlar.append([score])
            success_count += 1

            human_delay(2, 4)

        except Exception as e:
            print(f"❌ {i}. satır hatası: {e}")
            skorlar.append([""])
            error_count += 1
            continue

    range_notasyonu = f"G3:G{len(data_rows)+2}"

    max_retries = 3
    for attempt in range(max_retries):
        try:
            sheet.update(values=skorlar, range_name=range_notasyonu)
            print("✅ Skorlar Google Sheets'e başarıyla güncellendi.")
            break
        except Exception as e:
            print(f"❌ Google Sheets güncelleme başarısız (deneme {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
            else:
                print("⚠️ Maksimum deneme sayısına ulaşıldı, güncelleme başarısız oldu.")

    print(f"\n🎉 İşlem tamamlandı!")
    print(f"✅ Başarılı: {success_count}")
    print(f"❌ Hatalı: {error_count}")

if __name__ == "__main__":
    main()
