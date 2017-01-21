# -*- coding: utf-8 -*-

import keight as k8
from keight import on



##
## Inheritance of Action class for session handling
##

class Controller(k8.Action):

    def run_action(self, action_func, action_args):
        try:
            # self.db = create_db()
            # self.db.begin()
            content = super(Controller, self).run_action(action_func, action_args)
            # self.db.commit()
            return content
        except Exception as ex:
            # self.db.rollback()
            import traceback
            traceback.print_exc()
            raise


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
