
from parser import FileParser

class LogLine(object):
    """
    Basic object that represents a log line; pass in the timestamp
    and stream name and it will extract the right bits of data and
    make them accessible via attributes.
    """
    
    def __init__(self, redis_conn, stream_name, timestamp):
        self.redis_conn = redis_conn
        self.stream_name = stream_name
        self.timestamp = timestamp
        self.id = "%s:%i" % (self.stream_name, self.timestamp)
        self._load()

    @classmethod
    def by_log_line_id(cls, redis_conn, log_line_id):
        stream, timestamp = log_line_id.split(":", 1)
        timestamp = int(timestamp)
        return cls(redis_conn, stream, timestamp)

    def _load(self):
        # Load the file parser
        fp = FileParser(self.stream_name)
        # Find the offset and load just one item from there
        offset = self.redis_conn.get("log_line:%s:offset" % self.id)
        item = iter(fp.get_chunks(int(offset))).next()
        # Load onto our attributes
        self.lines = item['lines']
        self.page = self.redis_conn.get("log_line:%s:page" % self.id)

    def __repr__(self):
        return "<LogLine %s:%i (%s lines)>" % (self.stream_name, self.timestamp, len(self.lines))
    

class Query(object):
    """
    
    """
    def __init__(self, redis_conn, keys=None):
        self.redis_conn = redis_conn
        if keys is None:
            self.keys = redis_conn.keys( "log_line:*:offset" )
            self.keys = [ ":".join( key.split( ":" )[1:3] ) 
                for key in self.keys
            ]
        else:
            self.keys = keys
    
    def stream(self, stream_name):
        "Returns a new Query filtered by stream"
        return Query( self.redis_conn, [ key for key in self.keys
            if key.split( ':' )[0] == stream_name
        ] )
    
    def range(self, start_time, end_time):
        "Returns a new Query whose results are between two times"
        keys = []
        for key in self.keys:
            timestamp = int(key.split( ':' )[1])
            if start_time <= timestamp < end_time \
            or start_time == timestamp:
                keys.append( key )
        return Query( self.redis_conn, keys )
    
    def speakers(self, speakers):
        "Returns a new Query whose results are any of the specified speakers"
        speaker_keys = set()
        for speaker in speakers:
            speaker_keys.update(
                self.redis_conn.smembers( "speaker:%s" % speaker )
            )
        return Query(
            self.redis_conn,
            [ key for key in self.keys if key in speaker_keys ]
        )
    
    def labels(self, labels):
        "Returns a new Query whose results are any of the specified labels"
        label_keys = set()
        for label in labels:
            label_keys.update(
                self.redis_conn.smembers( "label:%s" % label )
            )
        return Query(
            self.redis_conn,
            [ key for key in self.keys if key in label_keys ]
        )
    
    
    def items(self):
        for key in self.keys:
            stream_name, timestamp = key.split(":", 3)
            yield LogLine(self.redis_conn, stream_name, int(timestamp))
    
    def __iter__(self):
        return iter( self.items() )
    
    def sort_by_time(self):
        "Sorts the query results by timestamp"
        return Query(
            self.redis_conn,
            sorted(self.keys, key=lambda x: int(x.split(":", 3)[1]) ),
        )
    













