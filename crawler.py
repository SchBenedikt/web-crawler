import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
import pymongo
from pymongo import MongoClient
import time
import re

visited_urls = set()
base_url = 'https://github.com/schBenedikt'
url_queue = []

def get_meta_data_from_url(url, max_depth=1000000):
    url, _ = urldefrag(url)
    parsed_url = urlparse(url)
    
    if url in visited_urls:
        return
    
    url_queue.append((url, 1))
    
    while url_queue:
        current_url, depth = url_queue.pop(0)
        
        if depth > max_depth:
            continue
        
        print(f'Crawling URL: {current_url} (Depth: {depth})')
        
        try:
            response = requests.get(current_url)
            
            if response.status_code == 200:
                visited_urls.add(current_url)
                response.encoding = 'utf-8'
                soup = BeautifulSoup(response.content, 'html.parser')
                title = str(soup.title.string) if soup.title else ""
                meta_description = get_meta_description(soup) or ""
                meta_image = get_meta_image(soup) or ""
                meta_locale = get_meta_locale(soup) or ""
                meta_type = get_meta_type(soup) or ""
                
                print(f'Titel der Seite {current_url}: {title}')
                print(f'Meta-Beschreibung der Seite {current_url}: {meta_description}')
                print(f'Bild-URL der Seite {current_url}: {meta_image}')
                print(f'Sprache der Seite {current_url}: {meta_locale}')
                print(f'Typ der Seite {current_url}: {meta_type}')
                
                save_meta_data_to_db(current_url, title, meta_description, meta_image, meta_locale, meta_type)
                
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    next_url = urljoin(current_url, href)
                    if is_valid_url(next_url) and not has_query_params(next_url):
                        url_queue.append((next_url, depth + 1))
            else:
                print(f'Fehler: {response.status_code} bei URL: {current_url}')
                delete_entry_from_db(current_url)
        except requests.exceptions.RequestException as e:
            print(f'RequestException: {str(e)} bei URL: {current_url}')
            time.sleep(5)
            url_queue.append((current_url, depth))
        except Exception as e:
            print(f'Exception: {str(e)} bei URL: {current_url}')

def get_meta_description(soup):
    meta_tag = soup.find('meta', attrs={'property': 'og:description'}) or soup.find('meta', attrs={'name': 'description'})
    return meta_tag['content'].encode('utf-8').strip().decode('utf-8') if meta_tag else None

def get_meta_image(soup):
    meta_tag = soup.find('meta', attrs={'property': 'og:image'})
    return meta_tag['content'].encode('utf-8').strip().decode('utf-8') if meta_tag else None

def get_meta_locale(soup):
    meta_tag = soup.find('meta', attrs={'property': 'og:locale'})
    return meta_tag['content'].encode('utf-8').strip().decode('utf-8') if meta_tag else None

def get_meta_type(soup):
    meta_tag = soup.find('meta', attrs={'property': 'og:type'})
    return meta_tag['content'].encode('utf-8').strip().decode('utf-8') if meta_tag else None

def is_valid_url(url):
    parsed_url = urlparse(url)
    return parsed_url.scheme in {'http', 'https'}

def has_query_params(url):
    parsed_url = urlparse(url)
    return bool(parsed_url.query)

def get_db_connection():
    try:
        client = MongoClient('localhost', 27017)
        db = client['search_engine']
        return db
    except Exception as e:
        print(f'Error: {e}')
        return None

def save_meta_data_to_db(url, title, description, image, locale, type):
    try:
        db = get_db_connection()
        if db:
            collection = db['meta_data']
            existing_entry = collection.find_one({"url": url})

            if existing_entry:
                if (existing_entry['title'] != title or existing_entry['description'] != description or 
                    existing_entry['image'] != image or existing_entry['locale'] != locale or 
                    existing_entry['type'] != type):
                    collection.update_one(
                        {"url": url},
                        {"$set": {
                            "title": title,
                            "description": description,
                            "image": image,
                            "locale": locale,
                            "type": type
                        }}
                    )
                    print(f'Die Meta-Daten für {url} wurden aktualisiert.')
                else:
                    print(f'Die Meta-Daten für {url} sind bereits aktuell.')
            else:
                collection.insert_one({
                    "url": url,
                    "title": title,
                    "description": description,
                    "image": image,
                    "locale": locale,
                    "type": type
                })
                print(f'Die Meta-Daten für {url} wurden gespeichert.')
    except Exception as e:
        print(f'Error: {e}')

def delete_entry_from_db(url):
    try:
        db = get_db_connection()
        if db:
            collection = db['meta_data']
            collection.delete_one({"url": url})
            print(f'Der Eintrag für {url} wurde aus der Datenbank gelöscht, da die Seite nicht mehr erreichbar ist.')
    except Exception as e:
        print(f'Error: {e}')

def is_allowed_by_robots_txt(url):
    parsed_url = urlparse(url)
    robots_url = urljoin(f"{parsed_url.scheme}://{parsed_url.netloc}", "/robots.txt")
    
    try:
        response = requests.get(robots_url)
        if response.status_code == 200:
            robots_txt = response.text
            user_agent = "*"
            disallowed_paths = []
            for line in robots_txt.splitlines():
                line = line.strip()
                if line.startswith("User-agent:"):
                    user_agent = line.split(":")[1].strip()
                elif line.startswith("Disallow:") and user_agent == "*":
                    disallowed_path = line.split(":")[1].strip()
                    disallowed_paths.append(disallowed_path)
            for path in disallowed_paths:
                if re.match(path, parsed_url.path):
                    return False
        return True
    except requests.exceptions.RequestException:
        return True

# Start-URL
start_url = base_url.rstrip('/')

# Meta-Daten für jede URL abrufen und ausgeben
get_meta_data_from_url(start_url)
