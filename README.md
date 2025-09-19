# LinkedIn Job Matcher (Python + Selenium)

**Overview**  
This project automates LinkedIn job search, scrapes job listings based on chosen filters, and matches them with the user's CV to calculate a compatibility score.  

🔧 **Tech Stack:**  
- **Python**  
- **Selenium** for automated job search and scraping  
- **Pandas & OpenPyXL** for Excel export  
- **String Matching** to compare job descriptions with CV content  

📋 **Features:**  
- Automates login and job search on LinkedIn  
- Extracts job title, company, location, and description  
- Exports results to Excel with matching percentage  
- Helps users find jobs that best fit their profile  

▶️ **How to Run:**  
1. Install requirements: `pip install selenium pandas openpyxl`  
2. Configure LinkedIn credentials and CV text path  
3. Run the script: `python main.py`  
4. View results in generated Excel sheets file  

📊 **Sample Output:**  
| Job Title           | Company | Match % |
|--------------------|---------|--------|
| Python Developer   | XYZ Ltd | 85%   |
| React Engineer     | ABC Inc | 60%   |
