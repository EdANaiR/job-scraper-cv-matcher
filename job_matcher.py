import os
import requests
import time
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# CV metni (gerekirse ayrı dosyadan da okunabilir)
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

class CVMatcher:
    def __init__(self):
        self.hf_token = os.getenv("HUGGINGFACE_TOKEN")
        self.hf_url = "https://api-inference.huggingface.co/models/google/flan-t5-base"

        if not self.hf_token:
            raise ValueError("❌ HUGGINGFACE_TOKEN environment variable is not set! Lütfen .env dosyasına ekleyin.")

    def _post_to_hf(self, prompt):
        headers = {"Authorization": f"Bearer {self.hf_token}"}
        try:
            response = requests.post(self.hf_url, headers=headers, json={"inputs": prompt}, timeout=30)
            response.raise_for_status()
            output = response.json()

            
            if isinstance(output, list) and "generated_text" in output[0]:
                return output[0]["generated_text"]
            elif isinstance(output, dict) and "generated_text" in output:
                return output["generated_text"]
            elif isinstance(output, dict) and "text" in output:
                return output["text"]
            return ""
        except requests.RequestException as e:
            print(f"❌ API hatası: {e}")
            return ""

    def get_match_score(self, job_description):
        """CV + iş ilanı eşleşme skoru döndürür (0-100)"""
        prompt = f"""
You are an experienced recruiter assessing a candidate's fit for a job role.

Candidate CV:
{cv_text}

Job Description:
{job_description}

Please evaluate how well the candidate's skills and experience align with the job. 
Return only a match score between 0 and 100. No extra text. Just the number.
"""
        result = self._post_to_hf(prompt)
        score_str = ''.join(filter(str.isdigit, result))
        return min(max(int(score_str) if score_str else 0, 0), 100)

    def generate_cover_letter(self, job_description, company_name, job_title):
        """Türkçe kısa bir cover letter oluşturur."""
        prompt = f"""
You are a professional cover letter writer.

CANDIDATE INFO:
{cv_text}

JOB DESCRIPTION:
{job_description}

COMPANY: {company_name}
POSITION: {job_title}

Write a short and effective cover letter (max 150 words) in Turkish for this position and candidate.
"""
        return self._post_to_hf(prompt).strip() or "Cover letter oluşturulamadı."

    def test_apis(self):
        """API test fonksiyonu"""
        test_job = "React, TypeScript, Next.js bilgisi gerekli. 2+ yıl deneyim şartı."
        print("🔍 Hugging Face API testi:")
        score = self.get_match_score(test_job)
        print(f"   Skor: {score}")
        print("\n2️⃣ Cover letter testi:")
        cover_letter = self.generate_cover_letter(test_job, "Test Şirketi", "Frontend Developer")
        print(f"   Cover letter: {cover_letter[:100]}...")
        return score > 0

def main():
    matcher = CVMatcher()

    if not matcher.test_apis():
        print("❌ API çalışmıyor!")
        return

    print("\n✅ API çalışıyor!")

    sample_jobs = [
        {
            "title": "Senior Frontend Developer",
            "company": "Tech Startup",
            "description": """
            Deneyimli Frontend Developer aranıyor.
            Gereksinimler:
            - React, Next.js, TypeScript
            - 3+ yıl deneyim
            - Responsive design
            - RESTful API entegrasyonu
            """
        },
        {
            "title": "Full Stack Developer",
            "company": "E-ticaret Şirketi",
            "description": """
            Full Stack Developer pozisyonu.
            Gereksinimler:
            - React, Node.js
            - MongoDB, PostgreSQL
            - AWS deneyimi
            - Microservices
            """
        }
    ]

    for job in sample_jobs:
        print(f"\n📊 {job['company']} - {job['title']} skorlanıyor...")
        score = matcher.get_match_score(job['description'])
        print(f"   Skor: {score}/100")
        if score >= 80:
            print("   🎯 Yüksek skor! Cover letter oluşturuluyor...")
            cover_letter = matcher.generate_cover_letter(job['description'], job['company'], job['title'])
            print(f"   Cover letter: {cover_letter}")
        time.sleep(1)

if __name__ == "__main__":
    main()
