import streamlit as st
from PIL import Image
import requests
import pandas as pd
from datetime import datetime
import plotly.express as px

favicon = Image.open("logo_seffaf.png") # Resmin adını ne koyduysan buraya yaz

st.set_page_config(
    page_title="Kişisel Finans",
    page_icon=favicon, # Emojiyi sildik, yerine resmi koyduk
    layout="wide"
)

API_URL = "https://personalfinanceapp-f3d9.onrender.com"
#API_URL = "http://127.0.0.1:8000"

# --- OTURUM (SESSION) YÖNETİMİ ---
if "user" not in st.session_state:
    st.session_state["user"] = None

# EĞER KULLANICI GİRİŞ YAPMAMIŞSA (LOGIN EKRANI)
if st.session_state["user"] is None:
    st.title("💸 Finans Asistanına Hoş Geldiniz")
    t_giris, t_kayit = st.tabs(["🔑 Giriş Yap", "📝 Kayıt Ol"])

    with t_giris:
        with st.form("giris_form"):
            k_adi = st.text_input("Kullanıcı Adı")
            sifre = st.text_input("Şifre", type="password")
            if st.form_submit_button("Giriş"):
                try:
                    res = requests.post(f"{API_URL}/giris/", json={"username": k_adi, "password": sifre})
                    if res.status_code == 200:
                        data = res.json()
                        if "user_id" in data:
                            st.session_state["user"] = data
                            st.success("Giriş başarılı! Yönlendiriliyorsunuz...")
                            st.rerun()
                        else:
                            st.error(data.get("hata", "Giriş yapılamadı."))
                    else:
                        st.error(
                            f"⚠️ Arka Plan Çöktü (Hata {res.status_code}): Lütfen PyCharm terminalindeki kırmızı hatayı kontrol et.")
                except Exception as e:
                    st.error(f"Sunucuya bağlanılamadı: {e}")

    with t_kayit:
        with st.form("kayit_form"):
            isim = st.text_input("Ad Soyad")
            yeni_k_adi = st.text_input("Kullanıcı Adı")
            yeni_sifre = st.text_input("Şifre", type="password")
            if st.form_submit_button("Kayıt Ol"):
                try:
                    res = requests.post(f"{API_URL}/kayit/",
                                        json={"username": yeni_k_adi, "password": yeni_sifre, "full_name": isim})
                    if res.status_code == 200:
                        data = res.json()
                        if "user_id" in data:
                            st.success("Kayıt başarılı! Şimdi yandaki sekmeden giriş yapabilirsiniz.")
                        else:
                            st.error(data.get("hata", "Kayıt işlemi başarısız."))
                    else:
                        st.error(
                            f"⚠️ Arka Plan Çöktü (Hata {res.status_code}): Lütfen PyCharm terminalindeki kırmızı hatayı kontrol et.")
                except Exception as e:
                    st.error(f"Sunucuya bağlanılamadı: {e}")

# EĞER GİRİŞ YAPILMIŞSA (ANA UYGULAMA)
else:
    USER_ID = st.session_state["user"]["user_id"]

    st.sidebar.title("🧭 Menü")
    st.sidebar.markdown(f"👤 **Hoş geldin, {st.session_state['user']['full_name']}**")
    if st.sidebar.button("🚪 Çıkış Yap"):
        st.session_state["user"] = None
        st.rerun()

    sayfa = st.sidebar.radio("Bölüm Seçin:",
                             ["📊 Genel Bakış", "📈 Gelir Yönetimi", "📉 Gider Yönetimi", "💳 Kart & Taksit",
                              "🧾 Fatura Takibi", "⚙️ Kategori Yönetimi"])


    # --- VERİ ÇEKME FONKSİYONU ---
    def veri_getir():
        try:
            k = requests.get(f"{API_URL}/kategoriler/{USER_ID}").json()
            i = requests.get(f"{API_URL}/islemler/{USER_ID}").json()
            c = requests.get(f"{API_URL}/kredi-kartlari/{USER_ID}").json()
            t = requests.get(f"{API_URL}/taksit-planlari/{USER_ID}").json()
            f = requests.get(f"{API_URL}/faturalar/{USER_ID}").json()
            return (k if isinstance(k, list) else []), (i if isinstance(i, list) else []), (
                c if isinstance(c, list) else []), (t if isinstance(t, list) else []), (
                f if isinstance(f, list) else [])
        except:
            return [], [], [], [], []


    kategoriler, islemler, kartlar, taksitler, faturalar = veri_getir()

    df_bilesik = pd.DataFrame()
    if islemler and kategoriler:
        df_bilesik = pd.merge(pd.DataFrame(islemler), pd.DataFrame(kategoriler), on="category_id")
        if not df_bilesik.empty:
            df_bilesik["transaction_date"] = pd.to_datetime(df_bilesik["transaction_date"])
            df_bilesik["Tarih"] = df_bilesik["transaction_date"].dt.strftime('%Y-%m-%d')

    # ==========================================
    # 1. SAYFA: GENEL BAKIŞ
    # ==========================================
    if sayfa == "📊 Genel Bakış":
        st.title("📊 Aylık Finansal Analiz")

        # UX DOKUNUŞU: Kullanıcıyı hesap kesim mantığı hakkında bilgilendiriyoruz
        st.info(
            "💡 **Bilgi:** Bu sayfadaki veriler standart takvim aylarına göre değil, kredi kartlarınızın **hesap kesim tarihlerine (ekstre dönemlerine)** göre hesaplanmaktadır.")

        c1, c2 = st.columns(2)
        secilen_yil = c1.selectbox("Yıl", [2025, 2026, 2027], index=1)

        # AYLARI İSİMLENDİRME: Sadece rakam yerine ay isimlerini kullanmak UX açısından daha profesyoneldir
        aylar = {1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan", 5: "Mayıs", 6: "Haziran",
                 7: "Temmuz", 8: "Ağustos", 9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"}
        secilen_ay_isim = c2.selectbox("Dönem (Ay)", list(aylar.values()), index=datetime.now().month - 1)
        secilen_ay = list(aylar.keys())[list(aylar.values()).index(secilen_ay_isim)]

        rapor_res = requests.get(f"{API_URL}/aylik-rapor/{USER_ID}/{secilen_yil}/{secilen_ay}")
        if rapor_res.status_code == 200 and isinstance(rapor_res.json(), list):
            df_rapor = pd.DataFrame(rapor_res.json())
            if not df_rapor.empty:
                aylik_gelir = df_rapor[df_rapor["islem_turu"] == "Gelir"]["tutar"].sum()
                aylik_gider = df_rapor[df_rapor["islem_turu"] == "Gider"]["tutar"].sum()
                aylik_net = aylik_gelir - aylik_gider

                m1, m2, m3 = st.columns(3)
                m1.metric("🟢 Dönem Geliri", f"{aylik_gelir:,.2f} ₺")
                m2.metric("🔴 Dönem Gideri", f"{aylik_gider:,.2f} ₺")
                m3.metric("🔵 Dönem Net Durumu", f"{aylik_net:,.2f} ₺", delta=f"{aylik_net:,.2f} ₺")
                st.markdown("---")

                r1c1, r1c2 = st.columns(2)
                r2c1, r2c2 = st.columns(2)

                with r1c1:
                    st.subheader("Harcama Dağılımı")
                    gider_df = df_rapor[df_rapor["islem_turu"] == "Gider"]
                    if not gider_df.empty:
                        pasta_verisi = gider_df.groupby("kategori_adi", as_index=False)["tutar"].sum()
                        fig1 = px.pie(pasta_verisi, values="tutar", names="kategori_adi", hole=0.6)
                        fig1.update_layout(showlegend=True, legend=dict(orientation="h", y=-0.1), annotations=[
                            dict(text=f"<b>Total</b><br>₺{aylik_gider:,.0f}", x=0.5, y=0.5, font_size=16,
                                 showarrow=False)])
                        st.plotly_chart(fig1, use_container_width=True)

                with r1c2:
                    st.subheader("Fatura Detayı")
                    fatura_df = df_rapor[df_rapor["kaynak"] == "Fatura"]
                    if not fatura_df.empty:
                        f_v = fatura_df.groupby("aciklama", as_index=False)["tutar"].sum()
                        fig2 = px.pie(f_v, values="tutar", names="aciklama", hole=0.6)
                        fig2.update_layout(showlegend=True, legend=dict(orientation="h", y=-0.1), annotations=[
                            dict(text=f"<b>Faturalar</b><br>₺{f_v['tutar'].sum():,.0f}", x=0.5, y=0.5, font_size=16,
                                 showarrow=False)])
                        st.plotly_chart(fig2, use_container_width=True)
                    else:
                        st.info("Bu döneme ait fatura yok.")

                with r2c1:
                    st.subheader("Taksit Detayı")
                    taksit_df = df_rapor[df_rapor["kaynak"] == "Taksit"]
                    if not taksit_df.empty:
                        t_v = taksit_df.groupby("aciklama", as_index=False)["tutar"].sum()
                        fig3 = px.pie(t_v, values="tutar", names="aciklama", hole=0.6)
                        fig3.update_layout(showlegend=True, legend=dict(orientation="h", y=-0.1), annotations=[
                            dict(text=f"<b>Taksitler</b><br>₺{t_v['tutar'].sum():,.0f}", x=0.5, y=0.5, font_size=16,
                                 showarrow=False)])
                        st.plotly_chart(fig3, use_container_width=True)
                    else:
                        st.info("Bu döneme ait taksit yok.")

                with r2c2:
                    st.subheader("Kart Bazlı Dağılım")
                    if not gider_df.empty:
                        k_v = gider_df.groupby("kart_adi", as_index=False)["tutar"].sum()
                        fig4 = px.pie(k_v, values="tutar", names="kart_adi", hole=0.6)
                        fig4.update_layout(showlegend=True, legend=dict(orientation="h", y=-0.1), annotations=[
                            dict(text=f"<b>Kartlar</b><br>₺{aylik_gider:,.0f}", x=0.5, y=0.5, font_size=16,
                                 showarrow=False)])
                        st.plotly_chart(fig4, use_container_width=True)
            else:
                st.info("Bu dönem için herhangi bir işlem bulunmuyor.")

    # ==========================================
    # 2. SAYFA: GELİR YÖNETİMİ
    # ==========================================
    elif sayfa == "📈 Gelir Yönetimi":
        st.title("📈 Gelir Kayıtları")
        c_f1, c_f2 = st.columns(2)
        f_yil = c_f1.selectbox("Yıl", [2025, 2026, 2027], index=1, key="g_yil")

        # AY İSİMLENDİRMESİ
        aylar = {1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan", 5: "Mayıs", 6: "Haziran",
                 7: "Temmuz", 8: "Ağustos", 9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"}
        secilen_ay_isim = c_f2.selectbox("Dönem (Ay)", list(aylar.values()), index=datetime.now().month - 1,
                                         key="g_ay_isim")
        f_ay = list(aylar.keys())[list(aylar.values()).index(secilen_ay_isim)]

        col1, col2 = st.columns([1, 2])
        with col1:
            st.subheader("Gelir Ekle")
            gelir_kat = [k for k in kategoriler if k['type'] == 'Gelir']
            if gelir_kat:
                with st.form("gelir_form"):
                    kat = st.selectbox("Kategori", [k['name'] for k in gelir_kat])
                    tutar = st.number_input("Tutar", min_value=0.0)
                    tarih = st.date_input("Tarih")
                    desc = st.text_input("Açıklama")
                    if st.form_submit_button("Kaydet") and tutar > 0:
                        k_id = next(k['category_id'] for k in gelir_kat if k['name'] == kat)
                        requests.post(f"{API_URL}/islemler/",
                                      json={"user_id": USER_ID, "category_id": k_id, "amount": tutar,
                                            "transaction_date": str(tarih), "description": desc})
                        st.rerun()
        with col2:
            st.subheader(f"Gelir Listesi ({secilen_ay_isim} Dönemi)")
            if not df_bilesik.empty and "type" in df_bilesik.columns:
                filtrelenmis = df_bilesik[
                    (df_bilesik["type"] == "Gelir") &
                    (df_bilesik["transaction_date"].dt.year == f_yil) &
                    (df_bilesik["transaction_date"].dt.month == f_ay)
                    ].sort_values(by="transaction_date")

                # YENİ ÖZELLİK: DÖNEM TOPLAMI GÖSTERGESİ
                donem_toplami = filtrelenmis['amount'].sum() if not filtrelenmis.empty else 0.0
                st.metric(label="📌 Bu Dönemin Toplam Geliri", value=f"{donem_toplami:,.2f} ₺")
                st.markdown("---")

                if not filtrelenmis.empty:
                    for index, satir in filtrelenmis.iterrows():
                        islem_id = satir['transaction_id']
                        with st.container(border=True):
                            if st.session_state.get('edit_id') == islem_id:
                                mevcut = next((i for i in islemler if i['transaction_id'] == islem_id), None)
                                k_idx = [k['category_id'] for k in gelir_kat].index(mevcut['category_id']) if mevcut[
                                                                                                                  'category_id'] in [
                                                                                                                  k[
                                                                                                                      'category_id']
                                                                                                                  for k
                                                                                                                  in
                                                                                                                  gelir_kat] else 0
                                d_kat = st.selectbox("Kategori", [k['name'] for k in gelir_kat], index=k_idx,
                                                     key=f"g_k_{islem_id}")
                                d_tut = st.number_input("Tutar", min_value=0.0, value=float(mevcut['amount']),
                                                        key=f"g_t_{islem_id}")
                                d_tar = st.date_input("Tarih",
                                                      value=datetime.strptime(mevcut['transaction_date'].split("T")[0],
                                                                              '%Y-%m-%d'), key=f"g_d_{islem_id}")
                                d_desc = st.text_input("Açıklama", value=mevcut.get('description', ''),
                                                       key=f"g_c_{islem_id}")

                                cb1, cb2 = st.columns(2)
                                if cb1.button("💾 Güncelle", key=f"g_s_{islem_id}", use_container_width=True):
                                    k_id = next(k['category_id'] for k in gelir_kat if k['name'] == d_kat)
                                    requests.put(f"{API_URL}/islemler/{islem_id}",
                                                 json={"user_id": USER_ID, "category_id": k_id, "amount": d_tut,
                                                       "transaction_date": str(d_tar), "description": d_desc})
                                    st.session_state['edit_id'] = None
                                    st.rerun()
                                if cb2.button("❌ İptal", key=f"g_i_{islem_id}", use_container_width=True):
                                    st.session_state['edit_id'] = None
                                    st.rerun()
                            else:
                                c_i1, c_i2, c_i3, c_i4 = st.columns([3, 2, 3, 1])
                                c_i1.markdown(f"**{satir['name']}**<br><small>{satir['Tarih']}</small>",
                                              unsafe_allow_html=True)
                                c_i2.markdown(f"<h4 style='color: #2e7d32; margin:0;'>+{satir['amount']:,.2f} ₺</h4>",
                                              unsafe_allow_html=True)
                                c_i3.write(satir['description'] if satir['description'] else "-")
                                with c_i4:
                                    with st.popover("⋮"):
                                        if st.button("✏️ Düzenle", key=f"g_e_{islem_id}", use_container_width=True):
                                            st.session_state['edit_id'] = islem_id
                                            st.rerun()
                                        if st.button("🗑️ Sil", key=f"g_del_{islem_id}", use_container_width=True):
                                            requests.delete(f"{API_URL}/islemler/{islem_id}")
                                            st.rerun()
                else:
                    st.info("Bu döneme ait gelir yok.")

    # ==========================================
    # 3. SAYFA: GİDER YÖNETİMİ
    # ==========================================
    elif sayfa == "📉 Gider Yönetimi":
        st.title("📉 Gider Kayıtları")
        st.info(
            "💡 **Bilgi:** Giderleriniz takvim aylarına göre değil, kredi kartlarınızın **hesap kesim tarihlerine (ekstre dönemlerine)** göre listelenmektedir.")

        c_f1, c_f2 = st.columns(2)
        f_yil = c_f1.selectbox("Yıl", [2025, 2026, 2027], index=1, key="gid_yil")

        # AY İSİMLENDİRMESİ (UX Geliştirmesi)
        aylar = {1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan", 5: "Mayıs", 6: "Haziran",
                 7: "Temmuz", 8: "Ağustos", 9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"}
        secilen_ay_isim = c_f2.selectbox("Dönem (Ay)", list(aylar.values()), index=datetime.now().month - 1,
                                         key="gid_ay_isim")
        f_ay = list(aylar.keys())[list(aylar.values()).index(secilen_ay_isim)]

        col1, col2 = st.columns([1, 2])
        with col1:
            st.subheader("Gider Ekle")
            gider_kat = [k for k in kategoriler if k['type'] == 'Gider']
            if gider_kat:
                with st.form("gider_form"):
                    kat = st.selectbox("Kategori", [k['name'] for k in gider_kat])
                    tut = st.number_input("Tutar", min_value=0.0)
                    tar = st.date_input("Tarih")
                    o_sec = ["Nakit / Banka Kartı"] + [k['card_name'] for k in kartlar]
                    secilen_odeme = st.selectbox("Ödeme Yöntemi", o_sec)
                    desc = st.text_input("Açıklama")
                    if st.form_submit_button("Kaydet") and tut > 0:
                        k_id = next(k['category_id'] for k in gider_kat if k['name'] == kat)
                        c_id = next(c['card_id'] for c in kartlar if
                                    c['card_name'] == secilen_odeme) if secilen_odeme != "Nakit / Banka Kartı" else None
                        requests.post(f"{API_URL}/islemler/",
                                      json={"user_id": USER_ID, "category_id": k_id, "card_id": c_id, "amount": tut,
                                            "transaction_date": str(tar), "description": desc})
                        st.rerun()
        with col2:
            st.subheader(f"Gider Listesi ({secilen_ay_isim} Dönemi)")

            if not df_bilesik.empty and "type" in df_bilesik.columns:

                # --- AKILLI DÖNEM HESAPLAMA MÜDAHALESİ BAŞLANGICI ---
                kart_kesim = {k['card_id']: k['closing_day'] for k in kartlar}


                def donem_hesapla(row):
                    t_tar = row['transaction_date']
                    cid = row.get('card_id')
                    y, m = t_tar.year, t_tar.month
                    if pd.notna(cid) and cid in kart_kesim:
                        if t_tar.day > kart_kesim[cid]:
                            m += 1
                            if m > 12:
                                m = 1
                                y += 1
                    return pd.Series([y, m])


                # df_bilesik tablosuna 'donem_yil' ve 'donem_ay' adında iki yeni kolon öğretiyoruz
                df_bilesik[['donem_yil', 'donem_ay']] = df_bilesik.apply(donem_hesapla, axis=1)

                # Filtrelemeyi artık standart 'transaction_date' ile değil, yeni öğrettiğimiz dönem kolonları ile yapıyoruz
                filtrelenmis = df_bilesik[
                    (df_bilesik["type"] == "Gider") &
                    (df_bilesik["donem_yil"] == f_yil) &
                    (df_bilesik["donem_ay"] == f_ay)
                    ].sort_values(by="transaction_date")
                # --- MÜDAHALE BİTİŞİ ---

                # YENİ ÖZELLİK: DÖNEM TOPLAMI GÖSTERGESİ
                donem_toplami = filtrelenmis['amount'].sum() if not filtrelenmis.empty else 0.0
                st.metric(label="📌 Bu Dönemin Toplam Gideri", value=f"{donem_toplami:,.2f} ₺")
                st.markdown("---")

                if not filtrelenmis.empty:
                    for index, satir in filtrelenmis.iterrows():
                        islem_id = satir['transaction_id']
                        with st.container(border=True):
                            # ... BUNDAN SONRASI SENİN MEVCUT DÜZENLEME VE SİLME KODLARINLA BİREBİR AYNI ...
                            if st.session_state.get('edit_id') == islem_id:
                                mevcut = next((i for i in islemler if i['transaction_id'] == islem_id), None)
                                k_idx = [k['category_id'] for k in gider_kat].index(mevcut['category_id']) if mevcut[
                                                                                                                  'category_id'] in [
                                                                                                                  k[
                                                                                                                      'category_id']
                                                                                                                  for k
                                                                                                                  in
                                                                                                                  gider_kat] else 0
                                d_kat = st.selectbox("Kategori", [k['name'] for k in gider_kat], index=k_idx,
                                                     key=f"gid_k_{islem_id}")
                                d_tut = st.number_input("Tutar", min_value=0.0, value=float(mevcut['amount']),
                                                        key=f"gid_t_{islem_id}")
                                d_tar = st.date_input("Tarih",
                                                      value=datetime.strptime(mevcut['transaction_date'].split("T")[0],
                                                                              '%Y-%m-%d'), key=f"gid_d_{islem_id}")

                                m_kart = "Nakit / Banka Kartı"
                                if mevcut.get('card_id'):
                                    m_kart = next(
                                        (k['card_name'] for k in kartlar if k['card_id'] == mevcut['card_id']),
                                        "Nakit / Banka Kartı")
                                o_sec = ["Nakit / Banka Kartı"] + [k['card_name'] for k in kartlar]
                                d_odeme = st.selectbox("Ödeme Yöntemi", o_sec,
                                                       index=o_sec.index(m_kart) if m_kart in o_sec else 0,
                                                       key=f"gid_o_{islem_id}")

                                d_desc = st.text_input("Açıklama", value=mevcut.get('description', ''),
                                                       key=f"gid_c_{islem_id}")

                                cb1, cb2 = st.columns(2)
                                if cb1.button("💾 Güncelle", key=f"gid_s_{islem_id}", use_container_width=True):
                                    k_id = next(k['category_id'] for k in gider_kat if k['name'] == d_kat)
                                    c_id = next(c['card_id'] for c in kartlar if
                                                c['card_name'] == d_odeme) if d_odeme != "Nakit / Banka Kartı" else None
                                    requests.put(f"{API_URL}/islemler/{islem_id}",
                                                 json={"user_id": USER_ID, "category_id": k_id, "card_id": c_id,
                                                       "amount": d_tut, "transaction_date": str(d_tar),
                                                       "description": d_desc})
                                    st.session_state['edit_id'] = None
                                    st.rerun()
                                if cb2.button("❌ İptal", key=f"gid_i_{islem_id}", use_container_width=True):
                                    st.session_state['edit_id'] = None
                                    st.rerun()
                            else:
                                c_i1, c_i2, c_i3, c_i4 = st.columns([3, 2, 3, 1])
                                c_i1.markdown(f"**{satir['name']}**<br><small>{satir['Tarih']}</small>",
                                              unsafe_allow_html=True)
                                c_i2.markdown(f"<h4 style='color: #d32f2f; margin:0;'>-{satir['amount']:,.2f} ₺</h4>",
                                              unsafe_allow_html=True)

                                k_isim = "Nakit"
                                if satir.get('card_id') and not pd.isna(satir['card_id']):
                                    k_isim = next((k['card_name'] for k in kartlar if k['card_id'] == satir['card_id']),
                                                  "Nakit")
                                c_i3.markdown(
                                    f"<small>💳 {k_isim}</small><br>{satir['description'] if satir['description'] else '-'}",
                                    unsafe_allow_html=True)

                                with c_i4:
                                    with st.popover("⋮"):
                                        if st.button("✏️ Düzenle", key=f"gid_e_{islem_id}", use_container_width=True):
                                            st.session_state['edit_id'] = islem_id
                                            st.rerun()
                                        if st.button("🗑️ Sil", key=f"gid_del_{islem_id}", use_container_width=True):
                                            requests.delete(f"{API_URL}/islemler/{islem_id}")
                                            st.rerun()
                else:
                    st.info("Bu döneme ait gider yok.")
    # ==========================================
    # 4. KART & TAKSİT
    # ==========================================
    elif sayfa == "💳 Kart & Taksit":
        st.title("💳 Kart ve Taksit Takibi")
        t1, t2 = st.tabs(["Taksitlerim", "Kartlarım"])
        with t1:
            col1, col2 = st.columns([1, 2])
            with col1:
                st.subheader("Yeni Taksit Ekle")
                gider_kat = [k for k in kategoriler if k['type'] == 'Gider']
                if kartlar and gider_kat:
                    with st.form("taksit_ekle"):
                        aciklama = st.text_input("Açıklama")
                        t_tutar = st.number_input("Toplam Tutar", min_value=0.0)
                        t_sayisi = st.number_input("Taksit Sayısı", min_value=2, step=1)
                        t_tarih = st.date_input("Alışveriş Tarihi")
                        kat_isim = st.selectbox("Kategori", [k['name'] for k in gider_kat])
                        kart_isim = st.selectbox("Kart", [k['card_name'] for k in kartlar])
                        if st.form_submit_button("Başlat") and t_tutar > 0:
                            k_id = next(k['category_id'] for k in gider_kat if k['name'] == kat_isim)
                            c_id = next(c['card_id'] for c in kartlar if c['card_name'] == kart_isim)
                            requests.post(f"{API_URL}/taksit-planlari/",
                                          json={"user_id": USER_ID, "category_id": k_id, "card_id": c_id,
                                                "description": aciklama, "total_amount": t_tutar,
                                                "installment_count": int(t_sayisi), "start_date": str(t_tarih)})
                            st.rerun()
            with col2:
                st.subheader("İlerleme Durumu")
                if taksitler:
                    bugun = datetime.today()
                    for t in taksitler:
                        try:
                            bas_tar = datetime.strptime(t['start_date'], '%Y-%m-%d')
                            gecen_ay = (bugun.year - bas_tar.year) * 12 + bugun.month - bas_tar.month
                            odenen = min(max(gecen_ay + 1, 0), t['installment_count'])
                            oran = odenen / t['installment_count']
                        except:
                            oran, odenen = 0.0, 0

                        with st.expander(f"📦 {t['description']} - Toplam: {t['total_amount']:,.2f} ₺"):
                            st.write(f"Başlangıç: {t['start_date']}")
                            st.progress(oran, text=f"{odenen} / {t['installment_count']} Taksit Ödendi")
                            if st.button("🗑️ Planı Sil", key=f"s_{t['plan_id']}"):
                                requests.delete(f"{API_URL}/taksit-planlari/{t['plan_id']}")
                                st.rerun()

        with t2:
            c1, c2 = st.columns([1, 2])
            with c1:
                st.subheader("Yeni Kart Ekle")
                with st.form("kart_ekle"):
                    isim = st.text_input("Kart Adı")
                    limit = st.number_input("Limit (₺)", min_value=0.0)
                    kesim = st.number_input("Hesap Kesim Günü", min_value=1, max_value=31, step=1)
                    if st.form_submit_button("Ekle") and isim:
                        requests.post(f"{API_URL}/kredi-kartlari/",
                                      json={"user_id": USER_ID, "card_name": isim, "limit_amount": limit,
                                            "closing_day": int(kesim), "due_day": 1})
                        st.rerun()
            with c2:
                st.subheader("Tanımlı Kartlar")
                if kartlar:
                    for k in kartlar:
                        k_id = k['card_id']
                        with st.container(border=True):
                            # DÜZENLEME MODU
                            if st.session_state.get('edit_card_id') == k_id:
                                d_isim = st.text_input("Kart Adı", value=k['card_name'], key=f"c_n_{k_id}")
                                d_limit = st.number_input("Limit (₺)", min_value=0.0, value=float(k['limit_amount']),
                                                          key=f"c_l_{k_id}")
                                d_kesim = st.number_input("Kesim Günü", min_value=1, max_value=31,
                                                          value=int(k['closing_day']), key=f"c_c_{k_id}")

                                cb1, cb2 = st.columns(2)
                                if cb1.button("💾 Kaydet", key=f"c_s_{k_id}", use_container_width=True):
                                    requests.put(f"{API_URL}/kredi-kartlari/{k_id}",
                                                 json={"user_id": USER_ID, "card_name": d_isim, "limit_amount": d_limit,
                                                       "closing_day": d_kesim, "due_day": 1})
                                    st.session_state['edit_card_id'] = None
                                    st.rerun()

                                if cb2.button("❌ İptal", key=f"c_i_{k_id}", use_container_width=True):
                                    st.session_state['edit_card_id'] = None
                                    st.rerun()

                            # NORMAL GÖRÜNÜM MODU
                            else:
                                col_a, col_b = st.columns([3, 1])
                                col_a.markdown(
                                    f"💳 **{k['card_name']}**<br><small>Limit: {k['limit_amount']:,.2f} ₺ | Kesim: Her ayın {k['closing_day']}. günü</small>",
                                    unsafe_allow_html=True)

                                with col_b:
                                    with st.popover("⋮"):
                                        if st.button("✏️ Düzenle", key=f"c_e_{k_id}", use_container_width=True):
                                            st.session_state['edit_card_id'] = k_id
                                            st.rerun()

                                        if st.button("🗑️ Sil", key=f"c_d_{k_id}", use_container_width=True):
                                            requests.delete(f"{API_URL}/kredi-kartlari/{k_id}")
                                            st.rerun()
                else:
                    st.info("Henüz eklenmiş bir kartınız bulunmuyor.")

    # ==========================================
    # 5. SAYFA: FATURA TAKİBİ
    # ==========================================
    elif sayfa == "🧾 Fatura Takibi":
        st.title("🧾 Fatura Yönetimi")
        st.info(
            "💡 **Bilgi:** Faturalar ait oldukları 'Fatura Dönemine' göre listelenir. Ancak ödendiklerinde, 'Ödeme Yapılan Tarih' ve kartın 'Hesap Kesim Tarihine' göre harcama grafiklerine yansırlar.")

        c_f1, c_f2 = st.columns(2)
        f_yil = c_f1.selectbox("Yıl", [2025, 2026, 2027], index=1, key="fat_yil")

        aylar = {1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan", 5: "Mayıs", 6: "Haziran",
                 7: "Temmuz", 8: "Ağustos", 9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"}
        secilen_ay_isim = c_f2.selectbox("Listelenecek Dönem (Ay)", list(aylar.values()),
                                         index=datetime.now().month - 1, key="fat_ay_isim")
        f_ay = list(aylar.keys())[list(aylar.values()).index(secilen_ay_isim)]

        col1, col2 = st.columns([1, 2])
        with col1:
            st.subheader("Yeni Fatura Ekle")
            f_kat = [k for k in kategoriler if k['type'] == 'Fatura']
            if f_kat:
                with st.form("fatura_ekle"):
                    tur = st.selectbox("Fatura Türü", [k['name'] for k in f_kat])

                    st.markdown("**Ait Olduğu Dönem (Listeleme)**")
                    fd_1, fd_2 = st.columns(2)
                    ekle_donem_yil = fd_1.selectbox("Dönem Yılı", [2025, 2026, 2027], index=1)
                    ekle_donem_ay_isim = fd_2.selectbox("Dönem Ayı", list(aylar.values()),
                                                        index=datetime.now().month - 1)
                    ekle_donem_ay = list(aylar.keys())[list(aylar.values()).index(ekle_donem_ay_isim)]

                    tutar = st.number_input("Tutar (₺)", min_value=0.0)
                    tarih_son = st.date_input("Son Ödeme Tarihi")

                    o_sec = ["Nakit / Banka Kartı"] + [k['card_name'] for k in kartlar]
                    secilen_odeme = st.selectbox("Ödeme Yöntemi", o_sec)

                    if st.form_submit_button("Kaydet") and tutar > 0:
                        c_id = next(c['card_id'] for c in kartlar if
                                    c['card_name'] == secilen_odeme) if secilen_odeme != "Nakit / Banka Kartı" else None
                        # Payment date formdan kaldırıldı, API'ye de gönderilmiyor.
                        requests.post(f"{API_URL}/faturalar/",
                                      json={"user_id": USER_ID, "type": tur, "amount": tutar,
                                            "due_date": str(tarih_son), "card_id": c_id,
                                            "period_year": ekle_donem_yil, "period_month": ekle_donem_ay})
                        st.rerun()
        with col2:
            st.subheader(f"Faturalar ({secilen_ay_isim} Dönemi)")
            if faturalar:
                df_fat = pd.DataFrame(faturalar)

                if 'period_year' in df_fat.columns and 'period_month' in df_fat.columns:
                    filtrelenmis = df_fat[
                        (df_fat['period_year'] == f_yil) & (df_fat['period_month'] == f_ay)
                        ].sort_values(by="due_date")
                else:
                    df_fat['due_date'] = pd.to_datetime(df_fat['due_date'])
                    filtrelenmis = df_fat[(df_fat['due_date'].dt.year == f_yil) & (df_fat['due_date'].dt.month == f_ay)]

                donem_toplami = filtrelenmis['amount'].sum() if not filtrelenmis.empty else 0.0
                st.metric(label="📌 Bu Dönemin Toplam Faturası", value=f"{donem_toplami:,.2f} ₺")
                st.markdown("---")

                if not filtrelenmis.empty:
                    for index, f in filtrelenmis.iterrows():
                        f_id = f['invoice_id']
                        with st.container(border=True):
                            if st.session_state.get('edit_id') == f_id:
                                # --- DÜZENLEME EKRANI ---
                                mevcut = next((inv for inv in faturalar if inv['invoice_id'] == f_id), None)
                                k_idx = [k['name'] for k in f_kat].index(mevcut['type']) if mevcut['type'] in [k['name']
                                                                                                               for k in
                                                                                                               f_kat] else 0

                                d_tur = st.selectbox("Fatura Türü", [k['name'] for k in f_kat], index=k_idx,
                                                     key=f"f_k_{f_id}")

                                fd_d1, fd_d2 = st.columns(2)
                                d_d_yil = fd_d1.selectbox("Dönem Yılı", [2025, 2026, 2027],
                                                          index=[2025, 2026, 2027].index(
                                                              mevcut.get('period_year', f_yil)), key=f"f_dy_{f_id}")
                                m_ay_isim = aylar[mevcut.get('period_month', f_ay)]
                                d_d_ay_isim = fd_d2.selectbox("Dönem Ayı", list(aylar.values()),
                                                              index=list(aylar.values()).index(m_ay_isim),
                                                              key=f"f_da_{f_id}")
                                d_d_ay = list(aylar.keys())[list(aylar.values()).index(d_d_ay_isim)]

                                d_tut = st.number_input("Tutar", min_value=0.0, value=float(mevcut['amount']),
                                                        key=f"f_t_{f_id}")

                                # Tarihler
                                date_str = mevcut['due_date'].split("T")[0] if isinstance(mevcut['due_date'], str) else \
                                mevcut['due_date'].strftime('%Y-%m-%d')
                                d_tar_son = st.date_input("Son Ödeme Tarihi",
                                                          value=datetime.strptime(date_str, '%Y-%m-%d'),
                                                          key=f"f_ds_{f_id}")

                                # YENİ MANTIK: Sadece fatura ödenmişse Ödeme Tarihini düzenlemeye aç
                                d_tar_odeme = None
                                if mevcut.get('is_paid'):
                                    p_date_raw = mevcut.get('payment_date')
                                    if pd.isna(p_date_raw) or p_date_raw is None:
                                        p_date_raw = mevcut['due_date']

                                    p_date_str = p_date_raw.split("T")[0] if isinstance(p_date_raw,
                                                                                        str) else p_date_raw.strftime(
                                        '%Y-%m-%d')
                                    d_tar_odeme = st.date_input("Ödeme Yapılan Tarih",
                                                                value=datetime.strptime(p_date_str, '%Y-%m-%d'),
                                                                key=f"f_po_{f_id}")

                                m_kart = "Nakit / Banka Kartı"
                                if mevcut.get('card_id'):
                                    m_kart = next(
                                        (k['card_name'] for k in kartlar if k['card_id'] == mevcut['card_id']),
                                        "Nakit / Banka Kartı")
                                o_sec = ["Nakit / Banka Kartı"] + [k['card_name'] for k in kartlar]
                                d_odeme = st.selectbox("Ödeme Yöntemi", o_sec,
                                                       index=o_sec.index(m_kart) if m_kart in o_sec else 0,
                                                       key=f"f_o_{f_id}")

                                cb1, cb2 = st.columns(2)
                                if cb1.button("💾 Güncelle", key=f"f_s_{f_id}", use_container_width=True):
                                    c_id = next(c['card_id'] for c in kartlar if
                                                c['card_name'] == d_odeme) if d_odeme != "Nakit / Banka Kartı" else None

                                    update_payload = {"user_id": USER_ID, "type": d_tur, "amount": d_tut,
                                                      "due_date": str(d_tar_son), "card_id": c_id,
                                                      "period_year": d_d_yil, "period_month": d_d_ay}
                                    if d_tar_odeme:
                                        update_payload["payment_date"] = str(d_tar_odeme)

                                    requests.put(f"{API_URL}/faturalar/{f_id}", json=update_payload)
                                    st.session_state['edit_id'] = None
                                    st.rerun()
                                if cb2.button("❌ İptal", key=f"f_i_{f_id}", use_container_width=True):
                                    st.session_state['edit_id'] = None
                                    st.rerun()
                            else:
                                # --- NORMAL GÖRÜNÜM MODU ---
                                c_i1, c_i2, c_i3, c_i4 = st.columns([3, 2, 3, 1])
                                tarih_str = f['due_date'].split("T")[0] if isinstance(f['due_date'], str) else f[
                                    'due_date'].strftime('%Y-%m-%d')
                                k_isim = "Nakit"
                                if f.get('card_id') and not pd.isna(f['card_id']):
                                    k_isim = next((k['card_name'] for k in kartlar if k['card_id'] == f['card_id']),
                                                  "Nakit")

                                p_ay = aylar.get(f.get('period_month', f_ay), "")
                                p_yil = f.get('period_year', f_yil)

                                if f['is_paid']:
                                    odeme_raw = f.get('payment_date')
                                    if pd.notna(odeme_raw) and odeme_raw is not None:
                                        odeme_str = odeme_raw.split("T")[0] if isinstance(odeme_raw,
                                                                                          str) else odeme_raw.strftime(
                                            '%Y-%m-%d')
                                    else:
                                        odeme_str = tarih_str

                                    c_i1.markdown(
                                        f"✅ **{f['type']}** ({p_ay} {p_yil})<br><small>Son: {tarih_str} | Ödendi: {odeme_str}</small>",
                                        unsafe_allow_html=True)
                                    c_i2.markdown(f"<h4 style='color: #2e7d32; margin:0;'>{f['amount']:,.2f} ₺</h4>",
                                                  unsafe_allow_html=True)
                                else:
                                    c_i1.markdown(
                                        f"⏳ **{f['type']}** ({p_ay} {p_yil})<br><small>Son Ödeme: {tarih_str}</small>",
                                        unsafe_allow_html=True)
                                    c_i2.markdown(f"<h4 style='color: #ef6c00; margin:0;'>{f['amount']:,.2f} ₺</h4>",
                                                  unsafe_allow_html=True)

                                c_i3.markdown(f"<small>💳 {k_isim}</small>", unsafe_allow_html=True)

                                with c_i4:
                                    with st.popover("⋮"):
                                        if not f['is_paid']:
                                            if st.button("💵 Öde", key=f"f_ode_{f_id}", use_container_width=True):
                                                requests.put(f"{API_URL}/faturalar/ode/{f_id}")
                                                st.rerun()
                                        if st.button("✏️ Düzenle", key=f"f_e_{f_id}", use_container_width=True):
                                            st.session_state['edit_id'] = f_id
                                            st.rerun()
                                        if st.button("🗑️ Sil", key=f"f_del_{f_id}", use_container_width=True):
                                            requests.delete(f"{API_URL}/faturalar/{f_id}")
                                            st.rerun()
                else:
                    st.info("Bu döneme ait fatura yok.")
    #======================
    # 5. SAYFA : KATEGORİ YÖNETİMİ
    #======================

    elif sayfa == "⚙️ Kategori Yönetimi":
        st.title("⚙️ Kategori Ayarları")
        col1, col2 = st.columns([1, 2])
        with col1:
            with st.form("kat_ekle"):
                isim = st.text_input("Kategori Adı")
                tur = st.selectbox("Tür", ["Gider", "Gelir", "Yatırım", "Fatura"])
                if st.form_submit_button("Ekle") and isim:
                    requests.post(f"{API_URL}/kategoriler/", json={"user_id": USER_ID, "name": isim, "type": tur})
                    st.rerun()
        with col2:
            if kategoriler:
                for k in kategoriler:
                    c1, c2 = st.columns([3, 1])
                    c1.write(f"🏷️ **{k['name']}** ({k['type']})")
                    if c2.button("🗑️ Sil", key=f"ks_{k['category_id']}"):
                        requests.delete(f"{API_URL}/kategoriler/{k['category_id']}")
                        st.rerun()