import json
from jinja2 import Environment, FileSystemLoader, select_autoescape
from more_itertools import chunked
import os
from livereload import Server, shell


def rebuild():
    env = Environment(
        loader=FileSystemLoader('.'),
        autoescape=select_autoescape(['html'])
    )
    template = env.get_template('template.html')

    filepath = 'pages'
    os.makedirs(filepath, exist_ok=True)

    with open("book_info.json", "r", encoding='utf-8') as file:
        books_info = json.load(file)

    chunks = list(chunked(books_info, 20))
    pages = len(chunks)


    for i, chunk in enumerate(chunks):
        rendered_page = template.render(
            books_info=chunk,
            pages=pages,
            current_page=i
        )

        with open(f'./{filepath}/index_{i}.html', 'w', encoding="utf8") as file:
            file.write(rendered_page)


rebuild()

server = Server()
server.watch('template.html', rebuild)
server.serve(root='.', default_filename='./pages/index_0.html')