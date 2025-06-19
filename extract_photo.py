import os
import stealth_requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor
import time
from fake_useragent import UserAgent
import lxml

ua = UserAgent()
headers = {'User-Agent': ua.random}

def is_valid_image_url(url):
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg')
    return url.lower().endswith(image_extensions)


def download_image(img_url, output_dir, base_url):
    try:
        img_url = urljoin(base_url, img_url)
        parsed = urlparse(img_url)
        filename = os.path.basename(parsed.path)

        if not filename:
            filename = f"image_{int(time.time())}.jpg"

        filepath = os.path.join(output_dir, filename)
        response = stealth_requests.get(img_url, stream=True, headers=headers)
        response.raise_for_status()

        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)

        print(f"Downloaded: {filename}")
        return True
    except Exception as e:
        print(f"Error downloading {img_url}: {str(e)}")
        return False


def download_all_images_from_url(url, output_dir='output', max_workers=5):
    os.makedirs(output_dir, exist_ok=True)

    try:
        print(f"Parsing webpage: {url}")
        response = stealth_requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'lxml')
        img_tags = soup.find_all('img')

        if not img_tags:
            print("No images found on the page")
            return

        print(f"Found {len(img_tags)} potential images")
        image_urls = set()

        for img in img_tags:
            src = img.get('src') or img.get('data-src')
            if src and is_valid_image_url(src):
                image_urls.add(src)

        print(f"Filtered to {len(image_urls)} valid images")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = [executor.submit(download_image, img_url, output_dir, url)
                       for img_url in image_urls]

            for future in results:
                future.result()

        print(f"\nDone! Images saved to '{output_dir}' folder")

    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    print("Enter the URL from where you want to upload the images ")
    target_url = input("URL: ").strip()
    download_all_images_from_url(target_url)
