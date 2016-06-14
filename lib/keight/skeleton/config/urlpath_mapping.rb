# -*- coding: utf-8 -*-

$urlpath_mapping = [
  ['/'                             , "./app/page/welcome:WelcomePage"],
  ['/api', [
    ['/hello'                      , "./app/api/hello:HelloAPI"],
   #['/books'                      , "./app/api/books:BooksAPI"],
   #['/books/{book_id}/comments'   , "./app/api/books:BookCommentsAPI"],
   #['/orders'                     , "./app/api/orders:OrdersAPI"],
  ]],
  ['/admin', [
   #['/books'                      , "./app/admin/books:AdminBooksPage"],
   #['/orders'                     , "./app/admin/orders:AdminOrdersPage"],
  ]],
  ['/sqlreport'                    , "./app/sql_report:SQLReport::EntryAction"],
  ['/static'                       , "./app/action:My::StaticPage"],
]
