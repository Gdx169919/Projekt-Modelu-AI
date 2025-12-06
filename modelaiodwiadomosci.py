import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
import datetime # Nowy import do pobierania bieżącego czasu

# Używamy st.cache_data, aby Streamlit zapamiętał wyniki dla danego URL
@st.cache_data
def simple_article_scraper(url):
    """
    Pobiera treść strony, wyodrębnia tytuł, treść, oraz ustala datę wyszukiwania.
    """
    try:
        # --- 1. Pobranie Bieżącej Daty i Godziny ---
        current_time = datetime.datetime.now()
        # Formatowanie do czytelnego ciągu tekstowego: RRRR-MM-DD GG:MM:SS
        search_timestamp = current_time.strftime("%Y-%m-%d %H:%M:%S")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        time.sleep(1) 
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status() 
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title = "Tytuł nie znaleziony"
        article_text = ""
        related_links = []

        # --- 2. Ekstrakcja Tytułu ---
        title_tag = soup.find('h1')
        if not title_tag:
            title_tag = soup.find('title')
        title = title_tag.text.strip() if title_tag else title
        
        # --- 3. Ekstrakcja Głównej Treści ---
        paragraphs = soup.find_all('p')
        article_text = '\n\n'.join([p.text.strip() for p in paragraphs if p.text.strip()])

        # --- 4. Ekstrakcja Innych Artykułów (Jak w poprzedniej wersji) ---
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            href = link['href']
            text = link.text.strip()
            
            if (text and len(text) > 15 and 
                not href.startswith(('#', 'mailto:', 'tel:')) and 
                'facebook' not in href and 'twitter' not in href and
                '/' in href):
                
                full_url = requests.compat.urljoin(url, href)
                
                if (text, full_url) not in related_links:
                    related_links.append((text, full_url))
        
        related_links = related_links[:10]
        
        # Zmieniona wartość zwracana: zamiast daty ze strony, zwracamy bieżący czas
        return title, article_text, search_timestamp, related_links

    except requests.exceptions.RequestException as e:
        return f"Błąd połączenia/HTTP: {e}", None, None, None
    except Exception as e:
        return f"Wystąpił nieoczekiwany błąd podczas przetwarzania: {e}", None, None, None

## =================================
## STREAMLIT UI
## =================================

st.set_page_config(
    page_title="Podstawowy Web Scraper by Arek",
    page_icon="✨",
    layout="wide"
)

st.title("✨ Podstawowy Web Scraper by Arek")
st.markdown("Wprowadź adres URL, aby pobrać tytuł, treść, **bieżącą datę wyszukiwania** i powiązane linki.")

if st.button("Wyczyść Pamięć Podręczną Scrapera"):
    st.cache_data.clear()
    st.success("Pamięć podręczna Streamlit została wyczyszczona. Wyszukiwanie dla tego samego URL będzie wykonane od nowa.")

input_url = st.text_input(
    "Adres URL Artykułu",
    placeholder="https://www.przykladowa-strona.pl/artykul-wiadomosciowy"
)

if st.button("Pobierz i Przetwórz Treść", type="primary"):
    if not input_url:
        st.warning("Proszę wprowadzić prawidłowy adres URL.")
    else:
        with st.spinner('Pobieranie, przetwarzanie i analiza strony...'):
            # Zmienna 'timestamp' zawiera teraz bieżącą datę/godzinę wykonania
            title, content, timestamp, links = simple_article_scraper(input_url)

        st.divider()
        st.header("Wyniki Scrapingu")
        
        if content is None:
            st.error(f"❌ Wystąpił błąd krytyczny: {title}")
        else:
            st.success("✅ Pobrano i przetworzono treść.")
            
            col_date, col_title = st.columns([1, 3])
            
            with col_date:
                st.subheader("📅 Data i Godzina Wyszukiwania:")
                # Wyświetlamy bieżący czas
                st.info(timestamp) 
            
            with col_title:
                st.subheader("📜 Tytuł:")
                st.code(title, language="text")

            st.subheader("📝 Treść Artykułu (Akapity):")
            st.text_area(
                "Pełny Tekst", 
                content, 
                height=300
            )

            st.subheader("🔗 Potencjalnie Powiązane Artykuły:")
            
            if links:
                for text, full_url in links:
                    st.markdown(f"* [{text}]({full_url})")
            else:

                st.info("Nie znaleziono wyraźnie powiązanych linków.") 
