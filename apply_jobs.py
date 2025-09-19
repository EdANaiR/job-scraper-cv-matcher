# apply_jobs.py

import os
import json
import time
import gspread
import requests
from google.oauth2.service_account import Credentials
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from selenium import webdriver
from selenium.webdriver.common.by import By


def get_high_score_jobs(sheet, score_col, desc_col, link_col):
    rows = sheet.get_all_values()
    headers = rows[1]
    data = rows[2:]

    high_score_jobs = []

    for i, row in enumerate(data, start=3):
        try:
            score = int(row[score_col]) if row[score_col] else 0
            if score >= 90:
                job_desc = row[desc_col]
                job_link = row[link_col]
                high_score_jobs.append((i, job_desc, job_link))
        except:
            continue

    return high_score_jobs


def generate_updated_cv_html(job_description, cv_text):
    prompt = f"""
İlan açıklamasını dikkate alarak aşağıdaki CV'yi bu ilana uygun şekilde editle. 
Aynı yapıyı koru, sadece görev açıklamaları, projeler gibi içerikleri daha uygun hale getir.

CV:
{cv_text}

İlan Açıklaması:
{job_description}

Yeni CV'yi HTML biçiminde döndür, {{experience}} ve {{projects}} bloklarını HTML olarak yaz.
"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"model": "mistral", "prompt": prompt}),
        stream=True
    )

    result = ""
    for line in response.iter_lines():
        if line:
            data = json.loads(line.decode("utf-8"))
            result += data.get("response", "")

    return result.strip()


def create_custom_cv(experience_html, projects_html, filename):
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('cv_template.html')
    rendered_html = template.render(experience=experience_html, projects=projects_html)

    output_dir = os.path.join(os.path.expanduser("~"), "Desktop", "newcv")
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"{filename}.pdf")

    HTML(string=rendered_html).write_pdf(file_path)
    return file_path


def apply_to_job(url, cv_path):
    driver = webdriver.Chrome()
    driver.get(url)
    time.sleep(4)

    try:
        upload_button = driver.find_element(By.XPATH, '//input[@type="file"]')
        upload_button.send_keys(cv_path)
        submit = driver.find_element(By.XPATH, '//button[contains(text(), "Apply")]')
        submit.click()
    except Exception as e:
        print(f"Başvuru hatası: {e}")

    time.sleep(5)
    driver.quit()


def main():
    cv_text = open("cv_raw.txt", "r", encoding="utf-8").read()

    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file('credentials.json', scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open("LinkedIn Jobs").sheet1

    # Sütun indexleri: Açıklama (C=2), Skor (G=6), Link (F=5)
    jobs = get_high_score_jobs(sheet, score_col=6, desc_col=2, link_col=5)

    for i, description, link in jobs:
        print(f"🔍 {i}. ilan için CV oluşturuluyor ve başvuru yapılıyor...")

        ai_response = generate_updated_cv_html(description, cv_text)

        # İki bölüm çıkar (çok basit ayrım)
        try:
            exp_start = ai_response.index("<div class=\"experience\">")
            proj_start = ai_response.index("<div class=\"project\">")
            experience = ai_response[exp_start:proj_start]
            projects = ai_response[proj_start:]
        except:
            experience = "<p>Boş</p>"
            projects = "<p>Boş</p>"

        filename = f"eda_cv_{i}"
        pdf_path = create_custom_cv(experience, projects, filename)
        apply_to_job(link, pdf_path)

        print(f"✅ Başvuru yapıldı ve {pdf_path} kaydedildi")


if __name__ == "__main__":
    main()
