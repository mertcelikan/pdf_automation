import os
import re
import pdfplumber
import pandas as pd
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox, messagebox, simpledialog
import shutil  
import json
from datetime import datetime 

# Müşteri bilgileri dosyası
CUSTOMER_FILE = r"C:\Users\User\Desktop\pdf_evraklar\debug.json"
#CUSTOMER_FILE = "customers.json"

#default_folder_path = "/Users/mertcelikan/Desktop/pdf_otomasyon/yeni_evraklar"
default_folder_path = r"C:\Users\User\Desktop\pdf_evraklar"
#C:/Users/User/Desktop/pdf_evraklar

CUSTOMER_FIELDS = [
    "Tüzel Kişi Vergi No",
    "Tüzel Kişi Ad",
    "İl",
    "İlçe",
    "Mahalle",
    "Cadde",
    "Dış Kapı",
    "İç Kapı",
    "Pay",
    "Payda",
    "TC Kimlik",
    "Yeni Kimlik Kartı",
    "Evrak Sayısı",
    "Alındığı Yer",
    "Evrak Tarihi",
    "Vekalet Bitiş Tarihi",
    "Ticari / Hususi",
    "Doğum Tarihi",
]

def open_edit_customer_window(index):
    customer = customers[index]

    edit_window = tk.Toplevel(root)
    edit_window.title("Müşteri Düzenle")
    edit_window.geometry("400x700")

    vars_and_entries = []

    for field in CUSTOMER_FIELDS:
        var = tk.StringVar(value=customer.get(field, ""))

        frame = tk.Frame(edit_window)
        frame.pack(pady=2, fill="x")

        tk.Label(frame, text=field, width=20, anchor="w").pack(side="left", padx=5)
        tk.Entry(frame, textvariable=var, width=30).pack(side="right", padx=5)

        vars_and_entries.append((field, var))

    # Listeleme İsmi
    tk.Label(edit_window, text="Listeleme İsmi", font=("Arial", 10)).pack(pady=5)
    listing_name_var = tk.StringVar(value=customer.get("Listeleme İsmi", ""))
    tk.Entry(edit_window, textvariable=listing_name_var, width=40).pack(pady=5)

    def save_changes():
        try:
            for field, var in vars_and_entries:
                customer[field] = var.get()

            customer["Listeleme İsmi"] = listing_name_var.get()

            save_customers(customers)
            refresh_customer_list()
            edit_window.destroy()

            messagebox.showinfo("Başarılı", "Müşteri bilgileri güncellendi.")

        except Exception as e:
            messagebox.showerror("Hata", f"Güncelleme başarısız:\n\n{e}")


    tk.Button(
        edit_window,
        text="GÜNCELLE",
        command=save_changes,
        bg="orange",
        fg="black",
        font=("Arial", 11, "bold")
    ).pack(pady=15)

# Global variables for form fields
tax_no_var = None
company_name_var = None
city_var = None
district_var = None
neighborhood_var = None
street_var = None
outdoor_no_var = None
indoor_no_var = None
share_var = None
share_total_var = None
id_no_var = None
new_id_card_var = None
doc_count_var = None
taken_place_var = None
doc_date_var = None
proxy_end_date_var = None
commercial_var = None
dob_var = None

def initialize_variables(root):
    global tax_no_var, company_name_var, city_var, district_var, neighborhood_var, street_var
    global outdoor_no_var, indoor_no_var, share_var, share_total_var, id_no_var, new_id_card_var
    global doc_count_var, taken_place_var, doc_date_var, proxy_end_date_var, commercial_var, dob_var
    
    # Initialize all StringVar objects
    tax_no_var = tk.StringVar(root)
    company_name_var = tk.StringVar(root)
    city_var = tk.StringVar(root)
    district_var = tk.StringVar(root)
    neighborhood_var = tk.StringVar(root)
    street_var = tk.StringVar(root)
    outdoor_no_var = tk.StringVar(root)
    indoor_no_var = tk.StringVar(root)
    share_var = tk.StringVar(root)
    share_total_var = tk.StringVar(root)
    id_no_var = tk.StringVar(root)
    new_id_card_var = tk.StringVar(root)
    doc_count_var = tk.StringVar(root)
    taken_place_var = tk.StringVar(root)
    doc_date_var = tk.StringVar(root)
    proxy_end_date_var = tk.StringVar(root)
    commercial_var = tk.StringVar(root)
    dob_var = tk.StringVar(root)


def prepare_excel(results, static_data):
    data = []
    for result in results:
        row = {
            "SASİ_NO": result["sasi_no"],
            "MOTOR_NO": result["motor_no"],
            "ön_referans": "",
            "ötv_belge_no": result["alindi_no"],
            **static_data,
            "fatura_no": result["fatura_no"],
            "fatura_tarihi": result["fatura_tarihi"],
            "Kasko Kodu": "",
            "Kasko Değeri": "",
            "KDV siz Fatura Bedeli": ""
        }
        data.append(row)

    df = pd.DataFrame(data)

    # Sütun sırasını düzenle
    column_order = [
        "SASİ_NO", "MOTOR_NO", "ön_referans", "ötv_belge_no",
        "tüzel_kişi_vergi_no", "tüzel_kişi_ad", "il", "ilçe", "mahalle",
        "cadde", "dış_kapı", "iç_kapı", "pay", "payda", "tc_kimlik",
        "yeni_kimlik_kartı", "evrak_sayısı", "alındığı yer", "evrak_tarihi",
        "vekalet bitiş tarihi", "fatura_no", "fatura_tarihi", "Ticari / Hususi", "Doğum Tarihi", "Kasko Kodu", "Kasko Değeri", "KDV siz Fatura Bedeli"
    ]
    df = df[column_order]

    return df


def extract_text_from_pdf(pdf_path: str) -> str:
    with pdfplumber.open(pdf_path) as pdf:
        text = ''
        for page in pdf.pages:
            text += page.extract_text() + '\n'

    return text


def extract_fatura_values(text: str) -> dict:
    values = {}
    patterns = {
        'motor_no': r'Motor No: ([A-Za-z0-9]+)',
        'sasi_no': r'Şasi No: ([A-Z0-9]+)',
        'fatura_no': r'MERSISNO:.*?Fatura No: ([A-Za-z0-9]+)',  # Yeni Fatura No deseni
        #'fatura_tarihi': r'Fatura\s*Tarihi:\s*(\d{2}\.\d{2}\.\d{4})'  # Fatura Tarihi deseni
        'fatura_tarihi': r'Fatura\s*(?:Tarihi|)(?:\s*[:\-]?\s*)(\d{2}\.\d{2}\.\d{4})'  # Esnek Fatura Tarihi deseni
    }


    # İlk olarak normal desenlerle arama yapıyoruz
    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        values[key] = match.group(1) if match else 'Bulunamadı'

    # Eğer fatura_tarihi bulunamadıysa, alternatif desenlerle arama yap
    if values['fatura_tarihi'] == 'Bulunamadı':
        # Alternatif 1: FTaatruihria deseni
        alternative_pattern_1 = r'FTaatruihria:\s*(\d{2}\.\d{2}\.\d{4})'
        match = re.search(alternative_pattern_1, text)
        if match:
            values['fatura_tarihi'] = match.group(1)
        else:
            # Alternatif 2: Fatura No'dan sonraki satırda tarih arama
            fatura_no_match = re.search(patterns['fatura_no'], text)
            if fatura_no_match:
                fatura_no_end = fatura_no_match.end()
                remaining_text = text[fatura_no_end:]
                date_pattern = r'(\d{2}\.\d{2}\.\d{4})'
                date_match = re.search(date_pattern, remaining_text)
                if date_match:
                    values['fatura_tarihi'] = date_match.group(1)
                else:
                    # Alternatif 3: "Fatura" kelimesinden sonraki tarih arama
                    alternative_pattern_3 = r'Fatura\s+(\d{2}\.\d{2}\.\d{4})'
                    match = re.search(alternative_pattern_3, text)
                    if match:
                        values['fatura_tarihi'] = match.group(1)
                    else:
                        # Alternatif 4: ALIAS satırında tarih arama
                        alias_pattern = r'ALIAS:.*?(\d{2}\.\d{2}\.\d{4})'
                        match = re.search(alias_pattern, text)
                        if match:
                            values['fatura_tarihi'] = match.group(1)
                        else:
                            # Alternatif 5: Fatura kelimesinden sonra tarih arama (esnek formata)
                            flexible_date_pattern = r'Fatura\s*(\d{2}\.\d{2}\.\d{4})'
                            match = re.search(flexible_date_pattern, text)
                            if match:
                                values['fatura_tarihi'] = match.group(1)

    # Eğer fatura_no bulunamadıysa, alternatif desenlerle arama yap
    if values['fatura_no'] == 'Bulunamadı':
        # Alternatif 1: Direkt bir satırda "Fatura No:" ile arama
        alternative_pattern_2 = r'Fatura No:\s*([A-Za-z0-9]+)'
        match = re.search(alternative_pattern_2, text)
        if match:
            values['fatura_no'] = match.group(1)
        else:
            # Alternatif 2: "BO" ile başlayan ve sayı içeren bir kelime arama
            alternative_pattern_3 = r'\b(BO[A-Za-z0-9]+)\b'
            match = re.search(alternative_pattern_3, text)
            if match:
                values['fatura_no'] = match.group(1)

    # Tip bilgisini almak için özel desen
    tip_pattern = r'Kod Açıklama Miktar Birim Fiyat İskonto Oranı Tutar\s*\n([^\n]+)'
    tip_match = re.search(tip_pattern, text)
    values['tip'] = tip_match.group(1).strip() if tip_match else 'Bulunamadı'
    return values


def extract_otv_values(text: str) -> dict:
    values = {}
    patterns = {
        'marka': r'Markası (\w+)',
        'sasi_no': r'Araç Şasi Numarası ([A-Z0-9]+)',
        'alindi_no': r'tarihli ve ([A-Za-z0-9]+)',
        'model_yili': r'Model Yılı[:\s]*([0-9]{4})',
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        values[key] = match.group(1) if match else 'Bulunamadı'

    # Müşteri adını bulma
    musteri_adi = "Bulunamadı"

    # 1. "Ünvanı" kelimesi yanında bir şeyler yazıyorsa bunu al
    unvani_pattern = r"Ünvanı\s+([^\n]+)"  
    match = re.search(unvani_pattern, text)

    if match and "SIRA NO" not in match.group(1):  # "SIRA NO" içermediğinden emin ol
        musteri_adi = match.group(1).strip()
    else:
        # 2. Eğer Ünvanı tek başına ise ve alttaki satırda "SIRA NO" varsa geçersiz say
        unvani_isolated_pattern = r"Ünvanı\s*\n([^\n]+)"
        match = re.search(unvani_isolated_pattern, text)
        if match and "SIRA NO" not in match.group(1):
            musteri_adi = match.group(1).strip()
        else:
            # 3. Eğer "Ünvanı" bulunamazsa, "Vergi Kimlik Numarası / T.C Kimlik Numarası" altındaki satırı al
            vkn_pattern = r"Vergi Kimlik Numarası / T\.C Kimlik Numarası\s*\d+\s*\n([^\n]+)"
            match = re.search(vkn_pattern, text)
            if match:
                musteri_adi = " ".join(match.group(1).strip().split(" ")[1:])  # İlk kelimeyi at
            else:
                musteri_adi = "Bulunamadı"

    values["musteri_adi"] = musteri_adi

    return values


def get_pdf_files_from_folder(folder_path: str) -> tuple:
    fatura_pdfs = []
    otv_pdfs = []

    for filename in os.listdir(folder_path):
        if filename.lower().endswith('.pdf'):
            pdf_path = os.path.join(folder_path, filename)
            pdf_text = extract_text_from_pdf(pdf_path)

            # PDF metninde "ÖTV ÖDEME BELGESİ" ifadesini kontrol et
            if "ÖTV ÖDEME BELGESİ" in pdf_text:
                otv_pdfs.append(pdf_path)
            else:
                fatura_pdfs.append(pdf_path)

    return fatura_pdfs, otv_pdfs


def process_pdfs(fatura_pdfs, otv_pdfs, folder_path):
    results = []
    unmatched_files = fatura_pdfs + otv_pdfs  # Tüm dosyalar başlangıçta eşleşmemiş sayılır

    # Fatura PDF'lerini işleyerek motor no, şasi no, fatura no ve fatura tarihi bilgilerini çıkar
    fatura_data = []
    for fatura_pdf in fatura_pdfs:
        fatura_text = extract_text_from_pdf(fatura_pdf)
        fatura_values = extract_fatura_values(fatura_text)

        # Fatura no veya fatura tarihi bulunamıyorsa, PDF içeriğini yazdır
        if fatura_values['fatura_no'] == 'Bulunamadı' or fatura_values['fatura_tarihi'] == 'Bulunamadı':
            print(f"Fatura no veya tarihi bulunamadı: {fatura_pdf}")

        fatura_data.append({"path": fatura_pdf, **fatura_values})

    # ÖTV PDF'lerini işleyerek marka, şasi no ve diğer bilgileri çıkar
    otv_data = []
    for otv_pdf in otv_pdfs:
        otv_text = extract_text_from_pdf(otv_pdf)
        otv_values = extract_otv_values(otv_text)
        otv_data.append({"path": otv_pdf, **otv_values})

    # Fatura ve ÖTV verilerini eşleştir
    for fatura in fatura_data:
        for otv in otv_data:
            if fatura['sasi_no'] == otv['sasi_no']:
                result = {
                    'motor_no': fatura['motor_no'],
                    'sasi_no': fatura['sasi_no'],
                    'fatura_no': fatura['fatura_no'],
                    'fatura_tarihi': fatura['fatura_tarihi'],
                    'marka': otv['marka'],
                    'alindi_no': otv['alindi_no'],
                    'model_yili':otv['model_yili'],
                    'tip': fatura['tip'],
                    'musteri_adi': otv['musteri_adi']
                }
                results.append(result)
                # Eşleşen dosyaları eşleşmemiş listeden çıkar
                unmatched_files.remove(fatura['path'])
                unmatched_files.remove(otv['path'])
                break

    # Eşleşmeyen dosyaları taşı
    move_unmatched_files(unmatched_files, folder_path)

    return results


def select_folder():
    folder = filedialog.askdirectory(initialdir=default_folder_path, title="Klasör Seç")
    if folder:
        folder_path_var.set(folder)


def move_unmatched_files(unmatched_files, folder_path):
    """Eşleşmeyen dosyaları 'eşleşmeyenler' klasörüne taşır."""
    unmatched_folder = os.path.join(folder_path, "eşleşmeyenler")
    os.makedirs(unmatched_folder, exist_ok=True)

    for file_path in unmatched_files:
        file_name = os.path.basename(file_path)
        destination = os.path.join(unmatched_folder, file_name)
        shutil.move(file_path, destination)


def prepare_second_excel(results):
    data = []
    for result in results:
        row = {
            "Müşteri Adı":result["musteri_adi"],
            "Marka": result["marka"],
            "Model": result["model_yili"],
            "Tip": result["tip"],
            "Şase No": result["sasi_no"],
            "Motor No": result["motor_no"],
            "Araç Cinsi": "Otomobil",
            "İşlem Türü" : "Tescil",
            "Teslimat Lokasyon": "",
            "Firma": ""
        }
        data.append(row)
    df = pd.DataFrame(data)
    return df 


def start_process():
    folder_path = folder_path_var.get()
    if not os.path.exists(folder_path):
        messagebox.showerror("Hata", "Geçerli bir klasör yolu seçiniz.")
        return

    # "Başlat" butonunu devre dışı bırak
    start_button.config(state="disabled")
    try:
        def safe_int(value, default=0):
            """Değeri int'e dönüştürmeye çalışır, başarısız olursa varsayılan değeri döner."""
            try:
                return int(value)
            except (ValueError, TypeError):
                return default
        static_data = {
            "tüzel_kişi_vergi_no": tax_no_var.get() or "",
            "tüzel_kişi_ad": company_name_var.get() or "",
            "il": city_var.get() or "",
            "ilçe": district_var.get() or "",
            "mahalle": neighborhood_var.get() or "",
            "cadde": street_var.get() or "",
            "dış_kapı": outdoor_no_var.get() or "",
            "iç_kapı": indoor_no_var.get() or "",
            "pay": safe_int(share_var.get()),
            "payda": safe_int(share_total_var.get()),
            "tc_kimlik": id_no_var.get() or "",
            "yeni_kimlik_kartı": new_id_card_var.get() or "",
            "evrak_sayısı": safe_int(doc_count_var.get()),
            "alındığı yer": taken_place_var.get() or "",
            "evrak_tarihi": doc_date_var.get() or "",
            "vekalet bitiş tarihi": proxy_end_date_var.get() or "",
            "Ticari / Hususi": commercial_var.get() or "",
            "Doğum Tarihi": dob_var.get() or "" 
        }

        fatura_pdfs, otv_pdfs = get_pdf_files_from_folder(folder_path)
        if not fatura_pdfs and not otv_pdfs:
            messagebox.showwarning("Uyarı", "Seçilen klasörde uygun PDF dosyası bulunamadı.")
            return
        results = process_pdfs(fatura_pdfs, otv_pdfs, folder_path)
        if not results:
            messagebox.showinfo("Bilgi", "Hiçbir sonuç eşleştirilemedi.")
            return

        df = prepare_excel(results, static_data)
        output_file = os.path.join(folder_path, "hazirlanan_asbis.xlsx")
        df.to_excel(output_file, index=False)
        df_second = prepare_second_excel(results)
        output_file = os.path.join(folder_path, "islem_listesi.xlsx")
        df_second.to_excel(output_file, index=False)


        messagebox.showinfo("Başarılı", f"Excel dosyası başarıyla oluşturuldu:\n{output_file}")
    except Exception as e:
        messagebox.showerror("Hata", f"Bir hata oluştu:\n{e}")
        print(f"Bir hata oluştu:\n{e}")
    finally:
        start_button.config(state="normal")


def load_customers():
    if os.path.exists(CUSTOMER_FILE):
        with open(CUSTOMER_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    return []



def save_customers(customers):
    try:
        with open(CUSTOMER_FILE, "w", encoding="utf-8") as file:
            json.dump(customers, file, indent=4, ensure_ascii=False)
    except Exception as e:
        messagebox.showerror("Kayıt Hatası", f"customers.json kaydedilemedi:\n\n{e}")
        raise



def add_customer(new_customer_window, vars_and_entries, listing_name_var):
    try:
        new_customer = {}
        for label, var in vars_and_entries:
            new_customer[label] = var.get()

        new_customer["Listeleme İsmi"] = listing_name_var.get()

        customers.append(new_customer)
        save_customers(customers)

        refresh_customer_list()
        new_customer_window.destroy()

        messagebox.showinfo("Başarılı", "Müşteri başarıyla eklendi.")

    except Exception as e:
        messagebox.showerror("Hata", f"Müşteri eklenemedi:\n\n{e}")



def delete_customer(index):
    if messagebox.askyesno("Onay", "Bu müşteriyi silmek istediğinize emin misiniz?"):
        del customers[index]
        save_customers(customers)
        refresh_customer_list()


def refresh_customer_list():
    # Önceki listeyi temizle
    for widget in customer_list_frame.winfo_children():
        widget.destroy()

    def select_customer(index):
        # Tüm butonları eski hale getir
        for child in customer_list_frame.winfo_children():
            for widget in child.winfo_children():
                if isinstance(widget, tk.Button) and widget["text"] == "Seçili":
                    widget.config(text="Seç", bg="white", fg="black")

        # Seçili müşteriyi yeşil yap
        selected_button = customer_list_frame.winfo_children()[index].winfo_children()[1]
        selected_button.config(text="Seçili", bg="green", fg="white")

        # Seçili müşterinin ismini kalın ve büyük yap
        for frame in customer_list_frame.winfo_children():
            name_label = frame.winfo_children()[0]  # Listeleme ismi label'ı
            if name_label.cget("text") == customers[index]["Listeleme İsmi"]:
                name_label.config(font=("Arial", 12, "bold"))  # Kalın ve büyük yazı
            else:
                name_label.config(font=("Arial", 10))  # Normal yazı

        selected_customer = customers[index]
        
        # Müşteri bilgilerini formdaki alanlara yerleştir
        tax_no_var.set(selected_customer.get("Tüzel Kişi Vergi No", ""))  # Example for populating fields
        company_name_var.set(selected_customer.get("Tüzel Kişi Ad", ""))
        city_var.set(selected_customer.get("İl", ""))
        district_var.set(selected_customer.get("İlçe", ""))
        neighborhood_var.set(selected_customer.get("Mahalle", ""))
        street_var.set(selected_customer.get("Cadde", ""))
        outdoor_no_var.set(selected_customer.get("Dış Kapı", ""))
        indoor_no_var.set(selected_customer.get("İç Kapı", ""))
        share_var.set(selected_customer.get("Pay", ""))
        share_total_var.set(selected_customer.get("Payda", ""))
        id_no_var.set(selected_customer.get("TC Kimlik", ""))
        new_id_card_var.set(selected_customer.get("Yeni Kimlik Kartı", ""))
        doc_count_var.set(selected_customer.get("Evrak Sayısı", ""))
        taken_place_var.set(selected_customer.get("Alındığı Yer", ""))
        doc_date_var.set(selected_customer.get("Evrak Tarihi", ""))
        proxy_end_date_var.set(selected_customer.get("Vekalet Bitiş Tarihi", ""))
        commercial_var.set(selected_customer.get("Ticari / Hususi", ""))
        dob_var.set(selected_customer.get("Doğum Tarihi", ""))

    # Her müşteriyi listele
    for index, customer in enumerate(customers):
        frame = tk.Frame(customer_list_frame)
        frame.pack(fill="x", pady=2)

        name_label = tk.Label(frame, text=customer["Listeleme İsmi"], anchor="w", width=30)
        name_label.pack(side="left", padx=5)

        # Seçim butonunu ekle
        select_button = tk.Button(frame, text="Seç", command=lambda i=index: select_customer(i))
        select_button.pack(side="left", padx=5)

        # Silme butonunu ekle
        delete_button = tk.Button(frame, text="❌", command=lambda i=index: delete_customer(i), fg="red")
        delete_button.pack(side="left", padx=5)
        
        # Düzenleme butonunu ekle
        edit_button = tk.Button(
            frame,
            text="✏️",
            command=lambda i=index: open_edit_customer_window(i)
        )
        edit_button.pack(side="left", padx=5)


def open_add_customer_window():
    new_customer_window = tk.Toplevel(root)
    new_customer_window.title("Yeni Müşteri Ekle")
    new_customer_window.geometry("400x700")

    vars_and_entries = []
    for label, default in [
        ("Tüzel Kişi Vergi No", ""),
        ("Tüzel Kişi Ad", ""),
        ("İl", ""),
        ("İlçe", ""),
        ("Mahalle", ""),
        ("Cadde", ""),
        ("Dış Kapı", ""),
        ("İç Kapı", ""),
        ("Pay", ""),
        ("Payda", ""),
        ("TC Kimlik", ""),
        ("Yeni Kimlik Kartı", ""),
        ("Evrak Sayısı", ""),
        ("Alındığı Yer", ""),
        ("Evrak Tarihi", ""),
        ("Vekalet Bitiş Tarihi", ""),
        ("Ticari / Hususi", ""),
        ("Doğum Tarihi", "")
    ]:
        var = tk.StringVar(value=default)
        frame = tk.Frame(new_customer_window)
        frame.pack(pady=2, fill="x")
        tk.Label(frame, text=label, width=20, anchor="w").pack(side="left", padx=5)
        entry = tk.Entry(frame, textvariable=var, width=30)
        entry.pack(side="right", padx=5)
        vars_and_entries.append((label, var))

    tk.Label(new_customer_window, text="Listeleme İsmi", font=("Arial", 10)).pack(pady=5)
    listing_name_var = tk.StringVar()
    tk.Entry(new_customer_window, textvariable=listing_name_var, width=40).pack(pady=5)

    tk.Button(
        new_customer_window, text="Müşteri Ekle", 
        command=lambda: add_customer(new_customer_window, vars_and_entries, listing_name_var),
        bg="green", fg="white"
    ).pack(pady=10)


if __name__ == "__main__":
    # Tkinter UI
    root = tk.Tk()
    root.title("NUR TRAFİK - PDF Otomasyon")
    root.geometry("550x800")

    initialize_variables(root)

    

    # Path alanı
    folder_path_var = tk.StringVar(value=default_folder_path)
    tk.Label(root, text="PDF Evrakların Klasör Yolu:", font=("Arial", 10)).pack(pady=5)
    tk.Entry(root, textvariable=folder_path_var, width=60).pack(pady=5)
    tk.Button(root, text="Klasör Seç", command=select_folder, width=15).pack(pady=5)

    customers = load_customers()

    tk.Label(root, text="Müşteri Listesi", font=("Arial", 12, "bold")).pack(pady=15)

    customer_list_container = tk.Frame(root)
    customer_list_container.pack(fill="both", expand=True, padx=10, pady=10)

    canvas = tk.Canvas(customer_list_container)
    scrollbar = ttk.Scrollbar(customer_list_container, orient="vertical", command=canvas.yview)
    customer_list_frame = tk.Frame(canvas)

    customer_list_frame.bind(
        "<Configure>", 
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=customer_list_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    refresh_customer_list()

    tk.Button(root, text="Yeni Müşteri Ekle", command=open_add_customer_window, bg="blue", fg="white").pack(pady=10)

    start_button = tk.Button(
        root,
        text="BAŞLAT",
        command=start_process,
        bg="white",
        fg="black",
        font=("Arial", 15, "bold"),
        width=12,
        height=1,
    )
    start_button.pack(pady=20)
    root.mainloop()