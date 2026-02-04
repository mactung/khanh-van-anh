import os
import re
import urllib.request
import urllib.parse
import ssl

# Ignore SSL errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Configuration
HTML_FILE = 'index.html'
ASSET_DIRS = {
    'image': 'images',
    'font': 'fonts',
    'script': 'js',
    'css': 'css',
    'audio': 'audio'
}

# Create directories
for dir_name in ASSET_DIRS.values():
    os.makedirs(dir_name, exist_ok=True)

def download_file(url, type_hint='image'):
    if not url.startswith('http'):
        return url # Already local or invalid
    
    try:
        # Create a request with headers to mimic a browser
        req = urllib.request.Request(
            url, 
            data=None, 
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
            }
        )
        
        with urllib.request.urlopen(req, context=ctx) as response:
            content = response.read()
            
            # Extract filename
            parsed_url = urllib.parse.urlparse(url)
            filename = os.path.basename(parsed_url.path)
            if not filename:
                 filename = "downloaded_asset"

            # Handle query parameters in filename (clean it up)
            filename = urllib.parse.unquote(filename)
            
            # Add extension if missing (simple guess)
            if '.' not in filename:
                content_type = response.headers.get('Content-Type', '')
                if 'image' in content_type:
                    filename += '.jpg'
                elif 'javascript' in content_type:
                    filename += '.js'
                elif 'css' in content_type:
                    filename += '.css'
                elif 'audio' in content_type:
                     filename += '.mp3'
            
            # Ensure unique filename if collision (optional but good practice)
            # For now, just overwrite is fine for this task.

            save_path = os.path.join(ASSET_DIRS[type_hint], filename)
            
            with open(save_path, 'wb') as f:
                f.write(content)
                    
            print(f"Downloaded: {url} -> {save_path}")
            return save_path

    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return url

with open(HTML_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Scripts
# <script src="...">
def replace_script(match):
    url = match.group(1)
    local_path = download_file(url, 'script')
    return f'src="{local_path}"'

content = re.sub(r'src="([^"]+?\.js[^"]*)"', replace_script, content)

# 2. Audio src
# <source src="...">
def replace_audio(match):
    url = match.group(1)
    local_path = download_file(url, 'audio')
    return f'src="{local_path}"'
content = re.sub(r'src="(https?://[^"]+\.mp3[^"]*)"', replace_audio, content)
content = re.sub(r'src="(https?://[^"]+/mp3/[^"]+)"', replace_audio, content) # for vocaroo

# 3. CSS url(...)
def replace_url_css(match):
    url = match.group(1)
    if not url.startswith('http'):
        return match.group(0) # Already local
    
    # Simple heuristic
    ext = os.path.splitext(urllib.parse.urlparse(url).path)[1].lower()
    if ext in ['.ttf', '.otf', '.woff', '.woff2']:
        local_path = download_file(url, 'font')
    elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp']:
        local_path = download_file(url, 'image')
    else:
        # Fallback or skip
        local_path = download_file(url, 'image')
        
    return f'url("{local_path}")'

content = re.sub(r'url\("([^"]+?)"\)', replace_url_css, content)

# 4. Standard img src and og:image
# content="..." for og:image
def replace_og_image(match):
    url = match.group(1)
    local_path = download_file(url, 'image')
    return f'content="{local_path}"'
content = re.sub(r'content="(https?://[^"]+\.(?:jpg|png)[^"]*)"', replace_og_image, content)

# SVG image href
def replace_image_href(match):
    url = match.group(1)
    local_path = download_file(url, 'image')
    return f'href="{local_path}"'
content = re.sub(r'href="(https?://[^"]+\.(?:png|jpg|jpeg|svg|gif)[^"]*)"', replace_image_href, content)


with open(HTML_FILE, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done processing index.html")
