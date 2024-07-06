import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
import mysql.connector
from mysql.connector import Error

visited_urls = set()
base_url = 'https://caesar.xn--schchner-2za.de/'

def get_meta_data_from_url(url, depth=1, max_depth=1000000):
    # Defragment the URL (remove the #fragment part)
    url, _ = urldefrag(url)
    
    # Parse the URL
    parsed_url = urlparse(url)
    
    # Check if the URL is within the base domain (including subdomains)
    if not parsed_url.netloc.endswith(urlparse(base_url).netloc) or url in visited_urls or depth > max_depth:
        return
    
    print(f'Crawling URL: {url} (Depth: {depth})')
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            visited_urls.add(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            title = str(soup.title.string) if soup.title else ""
            meta_description = get_meta_description(soup) or ""
            meta_image = get_meta_image(soup) or ""
            meta_locale = get_meta_locale(soup) or ""
            meta_type = get_meta_type(soup) or ""
            
            print(f'Titel der Seite {url}: {title}')
            print(f'Meta-Beschreibung der Seite {url}: {meta_description}')
            print(f'Bild-URL der Seite {url}: {meta_image}')
            print(f'Sprache der Seite {url}: {meta_locale}')
            print(f'Typ der Seite {url}: {meta_type}')
            
            save_meta_data_to_db(url, title, meta_description, meta_image, meta_locale, meta_type)
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                next_url = urljoin(url, href)
                if is_valid_url(next_url) and not has_query_params(next_url):
                    get_meta_data_from_url(next_url, depth + 1, max_depth)
        else:
            print(f'Fehler: {response.status_code} bei URL: {url}')
    except Exception as e:
        print(f'Exception: {str(e)} bei URL: {url}')

def get_meta_description(soup):
    meta_tag = soup.find('meta', attrs={'property': 'og:description'}) or soup.find('meta', attrs={'name': 'description'})
    return meta_tag['content'] if meta_tag else None

def get_meta_image(soup):
    meta_tag = soup.find('meta', attrs={'property': 'og:image'})
    return meta_tag['content'] if meta_tag else None

def get_meta_locale(soup):
    meta_tag = soup.find('meta', attrs={'property': 'og:locale'})
    return meta_tag['content'] if meta_tag else None

def get_meta_type(soup):
    meta_tag = soup.find('meta', attrs={'property': 'og:type'})
    return meta_tag['content'] if meta_tag else None

def is_valid_url(url):
    parsed_url = urlparse(url)
    return parsed_url.scheme in {'http', 'https'}

def has_query_params(url):
    parsed_url = urlparse(url)
    return bool(parsed_url.query)

def url_exists_in_db(url):
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='browser_engine',
            user='root',
            password='25092008'
        )
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM meta_data WHERE url = %s", (url,))
            result = cursor.fetchone()
            cursor.close()
            connection.close()
            
            return result[0] > 0
    except Error as e:
        print(f'Error: {e}')
        return False

def save_meta_data_to_db(url, title, description, image, locale, type):
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='browser_engine',
            user='root',
            password='25092008'
        )
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS meta_data (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    url TEXT NOT NULL,
                    title TEXT,
                    description TEXT,
                    image TEXT,
                    locale TEXT,
                    type TEXT,
                    likes INT
                )
            """)
            
            # Check if the new columns exist and add them if not
            cursor.execute("SHOW COLUMNS FROM meta_data LIKE 'locale'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE meta_data ADD COLUMN locale TEXT")
                print("Die Spalte 'locale' wurde der Tabelle 'meta_data' hinzugefügt.")
            
            cursor.execute("SHOW COLUMNS FROM meta_data LIKE 'type'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE meta_data ADD COLUMN type TEXT")
                print("Die Spalte 'type' wurde der Tabelle 'meta_data' hinzugefügt.")
            
            cursor.execute("SELECT * FROM meta_data WHERE url = %s", (url,))
            existing_entry = cursor.fetchone()
            
            if existing_entry:
                # Eintrag existiert bereits, überprüfe auf Änderungen
                if (existing_entry[2] != title or existing_entry[3] != description or 
                    existing_entry[4] != image or existing_entry[5] != locale or 
                    existing_entry[6] != type):
                    # Titel, Beschreibung, Bild-URL, Locale oder Typ haben sich geändert, führe UPDATE aus
                    cursor.execute("""
                        UPDATE meta_data 
                        SET title = %s, description = %s, image = %s, locale = %s, type = %s
                        WHERE url = %s
                    """, (title, description, image, locale, type, url))
                    print(f'Die Meta-Daten für {url} wurden aktualisiert.')
                else:
                    print(f'Die Meta-Daten für {url} sind bereits aktuell.')
            else:
                # Eintrag existiert nicht, füge neuen Eintrag hinzu
                cursor.execute("""
                    INSERT INTO meta_data (url, title, description, image, locale, type)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (url, title, description, image, locale, type))
                print(f'Die Meta-Daten für {url} wurden gespeichert.')
            
            connection.commit()
            cursor.close()
            connection.close()
    except Error as e:
        print(f'Error: {e}')

def delete_entry_from_db(url):
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='browser_engine',
            user='root',
            password='25092008'
        )
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("DELETE FROM meta_data WHERE url = %s", (url,))
            connection.commit()
            cursor.close()
            connection.close()
            print(f'Der Eintrag für {url} wurde aus der Datenbank gelöscht, da die Seite nicht mehr erreichbar ist.')
    except Error as e:
        print(f'Error: {e}')


# Start-URL
start_url = base_url.rstrip('/')

# Meta-Daten für jede URL abrufen und ausgeben
get_meta_data_from_url(start_url)
