from logging import makeLogRecord
import unittest
import uuid

from colorama.ansi import (
    Cursor,
    clear_line,
)
from mock import MagicMock

from ...logger.handler import LogLoopStreamHandler


class TestLogStreamLoopHandler(unittest.TestCase):

    def setUp(self):
        self.stream = MagicMock()
        self.handler = LogLoopStreamHandler(self.stream)

    def test_emit_normal_record(self):
        record = makeLogRecord({'msg': 'test'})
        self.handler.emit(record)
        self.assertEqual(self.stream.write.call_count, 1)
        self.assertEqual(self.stream.write.call_args[0][0], 'test\n')

    def test_emit_loop_record(self):
        loop = 0
        loop_id = uuid.uuid4()
        while loop < 2:
            for i in range(3):
                record = makeLogRecord({
                    'msg': 'test {}'.format(i),
                    'index': i,
                    'loop': loop_id,
                })
                self.handler.emit(record)
            loop += 1

        self.assertEqual(len(self.stream.write.call_args_list), 7,
                         'Should have accounted for moving cursor up')

        for index, arg in enumerate(self.stream.write.call_args_list):
            line = arg[0][0]
            if index == 3:
                self.assertTrue(line.startswith(Cursor.UP(4)))
            else:
                self.assertTrue(line.startswith(clear_line()))
