import os

from dotenv import load_dotenv

from database import rebuild_session_factory_for_testing, build_session


def load_testing_environment():
    load_dotenv()
    os.environ['DATABASE_URL'] = 'postgresql://test:test@localhost:999/postgres'
    rebuild_session_factory_for_testing()
    with build_session() as sess:
        sess_url = str(sess.bind.url)

    assert 'localhost' in sess_url
    assert '999' in sess_url
    assert 'test' in sess_url
