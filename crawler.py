import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
import mysql.connector
from mysql.connector import Error

visited_urls = set()
base_url = 'https://technik.schächner.de/'

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
            
            print(f'Titel der Seite {url}: {title}')
            print(f'Meta-Beschreibung der Seite {url}: {meta_description}')
            
            save_meta_data_to_db(url, title, meta_description)
            
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
            password=''
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

# In der Funktion save_meta_data_to_db() vor dem Einfügen überprüfen
def save_meta_data_to_db(url, title, description):
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='browser_engine',
            user='root',
            password=''
        )
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS meta_data (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    url TEXT NOT NULL,
                    title TEXT,
                    description TEXT,
                    likes INT
                )
            """)
            
            cursor.execute("SELECT * FROM meta_data WHERE url = %s", (url,))
            existing_entry = cursor.fetchone()
            
            if existing_entry:
                # Eintrag existiert bereits, überprüfe auf Änderungen
                if existing_entry[2] != title or existing_entry[3] != description:
                    # Titel oder Beschreibung haben sich geändert, führe UPDATE aus
                    cursor.execute("""
                        UPDATE meta_data 
                        SET title = %s, description = %s 
                        WHERE url = %s
                    """, (title, description, url))
                    print(f'Die Meta-Daten für {url} wurden aktualisiert.')
                else:
                    print(f'Die Meta-Daten für {url} sind bereits aktuell.')
            else:
                # Eintrag existiert nicht, füge neuen Eintrag hinzu
                cursor.execute("""
                    INSERT INTO meta_data (url, title, description)
                    VALUES (%s, %s, %s)
                """, (url, title, description))
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
            password=''
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
