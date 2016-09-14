"""

mbtileserver.py
===============

A minimal Flask application for serving map tiles from an MBTiles file.

Quick Usage:

    MBTILES_PATH=/path/to/my.mbtiles python mbtileserver.py

Copyright 2013 Evan Friis

License: MIT

"""

from flask import Flask, g, abort, Blueprint, current_app
from flask.ext.cache import Cache
import os
import sqlite3

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO  # NOQA


frontend = Blueprint('frontend', __name__)
cache = Cache()


@frontend.before_request
def before_request():
    """Ensure database is connected for each request """
    g.db = sqlite3.connect(current_app.config['MBTILES_PATH'])


@frontend.teardown_request
def teardown_request(exception):
    """Cleanup database afterwards """
    if hasattr(g, 'db'):
        g.db.close()


@frontend.route("/<int:zoom>/<int:column>/<int:row>.<ext>")
@cache.cached(timeout=300)
def query_tile(zoom, column, row, ext):
    """Get a tile from the MBTiles database """
    query = 'SELECT tile_data FROM tiles '\
            'WHERE zoom_level = ? AND tile_column = ? AND tile_row = ?;'
    cur = g.db.execute(query, (zoom, column, row))
    results = cur.fetchall()
    if not results:
        abort(404)
    the_image = results[0][0]

    mimeType = "image/png"
    if ext == "jpg":
        mimeType = 'image/jpeg'
    elif ext == "pbf":
        mimeType = "application/x-protobuf"

    return current_app.response_class(
        StringIO(the_image).read(),
        mimetype=mimeType
    )


def create_app(mbtiles=None, cache_config=None):
    """Initialize the application with a given configuration.

    mbtiles must be a path to the MBTiles sqlite file.

    """
    app = Flask(__name__)
    app.config.update({
        'MBTILES_PATH': mbtiles
    })
    app.register_blueprint(frontend)
    cache.init_app(app, config=cache_config)
    return app


if __name__ == "__main__":
    app = create_app(
        mbtiles=os.environ['MBTILES_PATH'],
        cache_config={
            'CACHE_TYPE': 'simple',
        }
    )
    app.run(debug=True, port=os.environ.get('MBTILES_PORT', 41815))
