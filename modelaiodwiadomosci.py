import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
import datetime # Nowy import do pobierania bieżącego czasu

# Używamy st.cache_data, aby Streamlit zapamiętał wyniki dla danego URL
@st.cache_data
def simple_article_scraper(url):
    """
    Pobiera treść strony, wyodrębnia tytuł (z ulepszoną heurystyką), 
    filtruje i analizuje akapity oraz ustala datę wyszukiwania.
    """
    try:
        # --- 1. Pobranie Bieżącej Daty i Godziny ---
        current_time = datetime.datetime.now()
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
        
        # --- 2. ULEPSZONA Ekstrakcja Tytułu ---
        # A. Spróbuj pobrać tag Open Graph (najbardziej wiarygodny dla newsów)
        og_title_tag = soup.find('meta', property='og:title')
        if og_title_tag and og_title_tag.get('content'):
            title = og_title_tag['content'].strip()
        
        # B. Jeśli og:title nie działa, sprawdź <h1>
        elif soup.find('h1'):
            title = soup.find('h1').text.strip()
        
        # C. Ostatecznie, użyj tagu <title>
        elif soup.find('title'):
            title = soup.find('title').text.strip()

        # --- 3. ULEPSZONA Ekstrakcja i Analiza Głównej Treści ---
        
        # Znalezienie wszystkich tagów akapitów <p>
        paragraphs = soup.find_all('p')
        
        # Filtracja: bierzemy tylko te akapity, które są wystarczająco długie
        # (redukuje ryzyko wzięcia podpisów pod zdjęciami, menu, czy reklam)
        filtered_paragraphs = [
            p.text.strip() for p in paragraphs 
            if p.text.strip() and len(p.text.strip()) > MIN_PARAGRAPH_LENGTH
        ]
        
        # Połączenie przefiltrowanych akapitów
        article_text = '\n\n'.join(filtered_paragraphs)
        
        # DANE DLA OPISU AKAPITÓW/TREŚCI:
        total_paragraphs = len(filtered_paragraphs)
        total_words = len(article_text.split())

        # --- 4. Ekstrakcja Innych Artykułów (Bez zmian) ---
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
        
        # Zwracamy tytuł, treść, czas, linki ORAZ dane do opisu akapitów
        return title, article_text, search_timestamp, related_links, total_paragraphs, total_words

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

