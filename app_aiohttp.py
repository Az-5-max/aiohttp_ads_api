from aiohttp import web
import sqlite3
from datetime import datetime


def get_db():
    conn = sqlite3.connect('ads.db')
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS ads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at TEXT NOT NULL,
            owner TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


async def create_ad(request):
    data = await request.json()

    if not data.get('title') or not data.get('description') or not data.get('owner'):
        return web.json_response({'error': 'Нужны title, description, owner'}, status=400)

    conn = get_db()
    cursor = conn.execute(
        'INSERT INTO ads (title, description, created_at, owner) VALUES (?, ?, ?, ?)',
        (data['title'], data['description'], datetime.utcnow().isoformat(), data['owner'])
    )
    ad_id = cursor.lastrowid
    conn.commit()

    cursor = conn.execute('SELECT * FROM ads WHERE id = ?', (ad_id,))
    ad = cursor.fetchone()
    conn.close()

    return web.json_response(dict(ad), status=201)


async def get_ad(request):
    ad_id = int(request.match_info['ad_id'])
    conn = get_db()
    cursor = conn.execute('SELECT * FROM ads WHERE id = ?', (ad_id,))
    ad = cursor.fetchone()
    conn.close()

    if not ad:
        return web.json_response({'error': 'Объявление не найдено'}, status=404)

    return web.json_response(dict(ad), status=200)


async def update_ad(request):
    ad_id = int(request.match_info['ad_id'])
    data = await request.json()

    conn = get_db()
    cursor = conn.execute('SELECT * FROM ads WHERE id = ?', (ad_id,))
    ad = cursor.fetchone()

    if not ad:
        conn.close()
        return web.json_response({'error': 'Объявление не найдено'}, status=404)

    conn.execute(
        'UPDATE ads SET title = ?, description = ?, owner = ? WHERE id = ?',
        (
            data.get('title', ad['title']),
            data.get('description', ad['description']),
            data.get('owner', ad['owner']),
            ad_id
        )
    )
    conn.commit()

    cursor = conn.execute('SELECT * FROM ads WHERE id = ?', (ad_id,))
    ad = cursor.fetchone()
    conn.close()

    return web.json_response(dict(ad), status=200)


async def delete_ad(request):
    ad_id = int(request.match_info['ad_id'])
    conn = get_db()
    cursor = conn.execute('SELECT * FROM ads WHERE id = ?', (ad_id,))
    ad = cursor.fetchone()

    if not ad:
        conn.close()
        return web.json_response({'error': 'Объявление не найдено'}, status=404)

    conn.execute('DELETE FROM ads WHERE id = ?', (ad_id,))
    conn.commit()
    conn.close()

    return web.json_response({'message': 'Удалено'}, status=200)


app = web.Application()
app.router.add_post('/ads', create_ad)
app.router.add_get('/ads/{ad_id}', get_ad)
app.router.add_put('/ads/{ad_id}', update_ad)
app.router.add_delete('/ads/{ad_id}', delete_ad)


if __name__ == '__main__':
    init_db()
    web.run_app(app, host='127.0.0.1', port=5000)