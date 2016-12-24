import os
import unittest
import tempfile
from pymessage import pymessage
from flask import json


class PyMessageTestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, pymessage.app.config['DATABASE'] = tempfile.mkstemp()
        pymessage.app.config['TESTING'] = True
        self.client = pymessage.app.test_client()
        with pymessage.app.app_context():
            pymessage.init_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(pymessage.app.config['DATABASE'])

    def test_empty_db(self):
        ret = self.client.get('/testuser')
        self.assertEqual(ret.status_code, 404)

    def test_add_user(self):
        ret = self.client.post('/adduser/test')
        assert b'OK' in ret.data

    def test_send_message(self):
        self.client.post('/adduser/test')
        ret = self.client.post('/test',
                               data=json.dumps(dict(message='A Test Message')),
                               content_type='application/json')
        assert b'OK' in ret.data

    def test_send_nonexisting(self):
        ret = self.client.post('/test',
                               data=json.dumps(dict(message='A Test Message')),
                               content_type='application/json')
        self.assertEqual(ret.status_code, 404)

    def test_send_and_fetch(self):
        self.client.post('/adduser/test')
        self.client.post('/test',
                               data=json.dumps(dict(message='A Test Message')),
                               content_type='application/json')
        ret = self.client.get('/test')
        assert b'application/json' in ret.content_type
        data = json.loads(ret.data)
        self.assertEqual(data['1'], 'A Test Message')

    def test_send_and_fetch_unread(self):
        ''' Create user '''
        self.client.post('/adduser/test')
        ''' Send message to user '''
        self.client.post('/test',
                               data=json.dumps(dict(message='A Test Message')),
                               content_type='application/json')
        ''' Fetch unread messages for user '''
        self.client.get('/test')
        ''' Fetch unread again '''
        ret = self.client.get('/test')
        assert b'application/json' in ret.content_type
        data = json.loads(ret.data)
        ''' Assert there are no unread messages '''
        self.assertEqual(len(data), 0, 'Returned list is not empty')

    def test_send_fetch_multiple(self):
        self.client.post('/adduser/test')
        for x in range(0, 10):
            self.client.post('/test',
                             data=json.dumps(dict(message='Test Message %d' % x)),
                             content_type='application/json')
        ret = self.client.get('/test')
        data = json.loads(ret.data)
        self.assertEqual(len(data), 10, 'Returned list does not contain 10 items')

    def test_fetch_range(self):
        self.client.post('/adduser/test')
        for x in range(1, 11):
            self.client.post('/test',
                             data=json.dumps(dict(message='Test Message %d' % x)),
                             content_type='application/json')
        self.client.get('/test')
        ret = self.client.get('/test')
        data = json.loads(ret.data)
        self.assertEqual(len(data), 0, 'Returned list is not empty')
        ret = self.client.get('/test?from=4&to=8')
        data = json.loads(ret.data)
        self.assertEqual(len(data), 5, 'Returned list does not contain 5 items')
        self.assertEqual(data['6'], 'Test Message 6')

    def test_delete_message(self):
        self.client.post('/adduser/test')
        for x in range(1, 11):
            self.client.post('/test',
                             data=json.dumps(dict(message='Test Message %d' % x)),
                             content_type='application/json')
        ret = self.client.delete('/test/5')
        self.assertEqual(ret.status_code, 200)
        ret = self.client.get('/test')
        data = json.loads(ret.data)
        self.assertEqual(len(data), 9, 'Returned list does not contain 9 items')

    def test_delete_not_owner(self):
        self.client.post('/adduser/test1')
        self.client.post('/adduser/test2')
        self.client.post('/test1',
                         data=json.dumps(dict(message='Test Message')),
                         content_type='application/json')
        ret = self.client.delete('/test2/1')
        self.assertEqual(ret.status_code, 404)
        ret = self.client.delete('/test1/1')
        self.assertEqual(ret.status_code, 200)

if __name__ == '__main__':
    unittest.main()
