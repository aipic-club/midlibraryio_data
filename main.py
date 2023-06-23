import os
import json
import asyncio
import aiohttp
import aiofiles
from prisma import Prisma
from bs4 import BeautifulSoup


cwd = os.getcwd()

async def fetch(url: str) -> BeautifulSoup:
    async with aiohttp.ClientSession() as session:
        print(f'fetch url contents: {url}')
        async with session.get(url=url) as resp:
            #print(resp.status)
            text = await resp.text()
            return BeautifulSoup(text, "html.parser")

async def download_image(url, save_path):
    async with aiohttp.ClientSession() as session:
        print(f'download image: {url}')
        async with session.get(url) as response:
            if response.status == 200:
                async with aiofiles.open(save_path, mode='wb') as file:
                    while True:
                        chunk = await response.content.read(1024)
                        if not chunk:
                            break
                        await file.write(chunk)
                print(f"Image downloaded and saved to: {save_path}")
            else:
                print(f"Failed to download image: {response.status}")
async def save_image(src: str, folder: str , name: str) -> str:
    folder_path = os.path.join('data', 'images', folder)
    file_path = os.path.join(folder_path , f'{name.strip()}.jpg')
    os.makedirs(os.path.join(cwd, folder_path), exist_ok=True)
    file_path = os.path.join(cwd, file_path)
    if not os.path.exists(file_path):
        await download_image(src, file_path )
    return file_path


async def parse_categories():
    soup = await fetch(url='https://www.midlibrary.io/categories')
    div_listitems = soup.find_all("div", attrs={"class": "cat-item"})
    data = []
    for item in div_listitems:
        child_element = item.find("a")
        link = child_element.attrs.get("href")

        children = list(child_element.children)
        src = children[0].attrs.get('src')
        name = children[1].find("div").find("div").text
        data.append({
            'name': name,
            'cover': await save_image(src=src, folder= 'categories', name= name),
            'link': link
        })

        return data


async def parse_a_category(link: str, suffix: str = ''):
    url = f'https://www.midlibrary.io/{link}{suffix}'
    soup = await fetch(url= url)
    page = soup.find("a", attrs={"class": "w-pagination-next"})
    all_styles = soup.find("div", attrs={"class": "shelf-3"})

    items = all_styles.find_all("div", attrs={"role": "listitem", "class": "cat-item-2 w-dyn-item"})
    data  = []
    for item in items:
        a = item.find("a", attrs={"class":"cat-link w-inline-block"})
        href = a.attrs.get("href")
        img = a.find("img")
        src = img.attrs.get("src")
        name = item.find("div",attrs={"fs-cmssort-field": "name"}).text
        sub = item.find("div", attrs={"fs-cmsfilter-field": "sections"})
        sub_title = sub.text if sub else None
        
        data.append({
            'name': name,
            'cover': await save_image(src=src, folder= link, name= name),
            'link': href,
        })

    if page:
        data += await parse_a_category(link=link, suffix=page.attrs.get("href"))
    return data


async def main():
    # prisma = Prisma()
    # await prisma.connect()    
    #await parse_categories()
    # json_data = json.dumps(data)

    # async with aiofiles.open(os.path.join(os.getcwd(), 'data/json', 'categories.json' ), mode='w') as f:
    #     await f.write(json_data)    

    link = 'categories/genres-art-movements'
    data = await parse_a_category(link = 'categories/genres-art-movements')
    json_data = json.dumps(data)
    async with aiofiles.open(os.path.join(os.getcwd(), 'data/json', f'{link }.json' ), mode='w') as f:
        await f.write(json_data)    




if __name__ == "__main__":
    asyncio.run(main())

