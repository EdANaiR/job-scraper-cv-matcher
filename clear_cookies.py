import os

cookie_file = "linkedin_cookies.pkl"
if os.path.exists(cookie_file):
    os.remove(cookie_file)
    print("Eski LinkedIn çerez dosyası silindi.")
else:
    print("Çerez dosyası zaten yok.")
