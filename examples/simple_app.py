# -*- coding: utf-8 -*-

import keight as k8
from keight import on


class WelcomeAction(k8.Action):

    @on('GET', r'')
    def do_welcome(self):
        return "<h1>hello world</h1>"


class BooksAction(k8.Action):

    @on('GET', r'/')
    def do_index(self):
        return "index"


class AuthorsAction(k8.Action):

    @on('GET', r'/')
    def do_index(self):
        return "index"


mapping_list = [
    (r'/',            WelcomeAction),
    (r'/api', [
        ('/books',    BooksAction),
        ('/authors',  AuthorsAction),
    ]),
]



def main():
    import waitress
    app = k8.wsgi.Application(mapping_list)
    waitress.serve(app)


if __name__ == '__main__':
    main()
