# -*- coding: utf-8 -*-

import keight as k8
from keight import on



##
## Inheritance of Action class for session handling
##

class Controller(k8.Action):

    def before_action(self):
        # self.db = create_db()
        # self.db.begin()
        print("start session")
        super(Controller, self).before_action()

    def after_action(self, ex):
        if not ex:
            print("commit")
            # self.db.commit()
            pass
        else:
            print("rollback")
            # self.db.rollback()
            pass


class WelcomeAction(Controller):

    @on('GET', r'')
    def do_welcome(self):
        return "<h1>hello world</h1>"


class BooksAction(Controller):

    @on('GET', r'/')
    def do_index(self):
        return "index"


class AuthorsAction(Controller):

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
