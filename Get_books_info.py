import requests
from urllib.parse import urlsplit
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathlib import Path
import json
from sanitize_filename import sanitize
import argparse


def download_images(img_url, folder):
    os.makedirs(folder, exist_ok=True)
    books_img = requests.get(img_url)
    books_img.raise_for_status()
    imgs_name = urlsplit(img_url).path.split('/')[-1]
    filepath = os.path.join(folder, imgs_name)
    with open(filepath, 'wb') as file:
        file.write(books_img.content)
            

def download_text(full_download_url, book_name, folder='books/'):
    os.makedirs(folder, exist_ok=True)
    books_text = requests.get(full_download_url)
    books_text.raise_for_status()
    filepath = os.path.join(folder, sanitize(book_name))
    with open(f'{filepath}.txt', 'w', encoding='utf8') as file:
        file.write(books_text.text)


def get_book_text_url(soup, url):
    download_links = soup.find_all('div', class_='download-link')
    for link in download_links:
        download_link = link.find('a')['href']
        path_obj = Path(download_link)
        extension = path_obj.suffix
        if extension == '.txt':
            full_download_url = urljoin(url, download_link)
            return full_download_url
    

def get_book(args): 
    books_urls = []
    for page in range(args.first, args.last):
        url = f'https://knigofil.org/page/{page}'
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        all_books = soup.find('div', class_='b-thumbnails')
        books = all_books.find_all('div', class_='b-thumbnail')
        for book in books:
            try:
                book_url = book.find('a')['href']
                books_urls.append(book_url)
            except requests.exceptions.HTTPError as http_err:
                print(f"HTTP error occurred: {http_err}")
            except ConnectionError as conn_err:
                print(f"Connection error occurred: {conn_err}")

    return books_urls


def get_book_info(book_url): 
    response = requests.get(book_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')
    book_info = soup.find_all('div', class_='big-book-stat')
    all_info_book = []
    for info in book_info:
        if info.find('a') is None:
            continue
        book_info = info.find('a').text
        all_info_book.append(book_info)
    book_name = soup.find('h1').text
    author = all_info_book[0]
    genre = all_info_book[1]
    year = all_info_book[2]
    book_info = {
        'name': book_name,
        'author': author,
        'genre': genre,
        'year': year,
    }

    return book_info, book_name


def main():
    parser = argparse.ArgumentParser(description="Программа получает информацию о книгах и скачивает текст и обложки книг")
    parser.add_argument("-f", "--first", help="Введите номер страницы с которой начнутся скачиваться книги", default=1, type=int)
    parser.add_argument("-l", "--last", help="Введите номер страницы на которой закончится скачивание книг", default=11, type=int)
    parser.add_argument("-si", "--skip_imgs", help="Пропустить скачивание картинок", action="store_true")
    parser.add_argument("-st", "--skip_txt", help="Пропустить скачивание текстов", action="store_true")
    args = parser.parse_args()
    url = 'https://knigofil.org/'
    books_urls = get_book(args)
    all_book_info = []
    
    for book_url in books_urls: 
        book_info, book_name = get_book_info(book_url)
        response = requests.get(book_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        txt_link = get_book_text_url(soup, url)
        if txt_link is None:
            print(f"Текстовый файл (.txt) на книгу '{book_name}' не найден")
            continue

        book_img = soup.find('div', class_='big-book-left-block').find('img')['src']
        img_url = urljoin(url, book_img)

        if not args.skip_imgs:
            folder='images/'
            download_images(img_url, folder='images/')
            imgs_name = urlsplit(img_url).path.split('/')[-1]
            book_info.update({'img_src': f'{folder}{imgs_name}'})

        if not args.skip_txt:
            folder='books/'
            download_text(txt_link, book_name, folder='books/')
            book_info.update({'book_path': f'{folder}{book_name}.txt'})

        all_book_info.append(book_info)


    with open('book_info.json', 'w', encoding='utf8') as file:
        json.dump(all_book_info, file, ensure_ascii=False)


if __name__=="__main__":
    main()