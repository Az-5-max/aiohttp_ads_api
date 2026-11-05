from aiohttp import web
import aiosqlite
from datetime import datetime

DB_PATH = 'ads.db'


async def init_db(app):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS ads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                created_at TEXT NOT NULL,
                owner TEXT NOT NULL
            )
        ''')
        await db.commit()
    app['db'] = DB_PATH


async def cleanup_db(app):
    pass


async def create_ad(request):
    data = await request.json()

    if not data.get('title') or not data.get('description') or not data.get('owner'):
        return web.json_response({'error': 'Нужны title, description, owner'}, status=400)

    async with aiosqlite.connect(request.app['db']) as db:
        cursor = await db.execute(
            'INSERT INTO ads (title, description, created_at, owner) VALUES (?, ?, ?, ?)',
            (data['title'], data['description'], datetime.utcnow().isoformat(), data['owner'])
        )
        ad_id = cursor.lastrowid
        await db.commit()

        cursor = await db.execute('SELECT * FROM ads WHERE id = ?', (ad_id,))
        row = await cursor.fetchone()

    return web.json_response({
        'id': row[0],
        'title': row[1],
        'description': row[2],
        'created_at': row[3],
        'owner': row[4]
    }, status=201)


async def get_all_ads(request):
    async with aiosqlite.connect(request.app['db']) as db:
        cursor = await db.execute('SELECT * FROM ads')
        rows = await cursor.fetchall()

    result = [
        {
            'id': row[0],
            'title': row[1],
            'description': row[2],
            'created_at': row[3],
            'owner': row[4]
        }
        for row in rows
    ]
    return web.json_response(result, status=200)


async def get_ad(request):
    ad_id = int(request.match_info['ad_id'])

    async with aiosqlite.connect(request.app['db']) as db:
        cursor = await db.execute('SELECT * FROM ads WHERE id = ?', (ad_id,))
        row = await cursor.fetchone()

    if not row:
        return web.json_response({'error': 'Объявление не найдено'}, status=404)

    return web.json_response({
        'id': row[0],
        'title': row[1],
        'description': row[2],
        'created_at': row[3],
        'owner': row[4]
    }, status=200)


async def update_ad(request):
    ad_id = int(request.match_info['ad_id'])
    data = await request.json()

    async with aiosqlite.connect(request.app['db']) as db:
        cursor = await db.execute('SELECT * FROM ads WHERE id = ?', (ad_id,))
        row = await cursor.fetchone()

        if not row:
            return web.json_response({'error': 'Объявление не найдено'}, status=404)

        await db.execute(
            'UPDATE ads SET title = ?, description = ?, owner = ? WHERE id = ?',
            (
                data.get('title', row[1]),
                data.get('description', row[2]),
                data.get('owner', row[4]),
                ad_id
            )
        )
        await db.commit()

        cursor = await db.execute('SELECT * FROM ads WHERE id = ?', (ad_id,))
        row = await cursor.fetchone()

    return web.json_response({
        'id': row[0],
        'title': row[1],
        'description': row[2],
        'created_at': row[3],
        'owner': row[4]
    }, status=200)


async def delete_ad(request):
    ad_id = int(request.match_info['ad_id'])

    async with aiosqlite.connect(request.app['db']) as db:
        cursor = await db.execute('SELECT * FROM ads WHERE id = ?', (ad_id,))
        row = await cursor.fetchone()

        if not row:
            return web.json_response({'error': 'Объявление не найдено'}, status=404)

        await db.execute('DELETE FROM ads WHERE id = ?', (ad_id,))
        await db.commit()

    return web.json_response({'message': 'Удалено'}, status=200)


app = web.Application()
app.on_startup.append(init_db)
app.on_cleanup.append(cleanup_db)

app.router.add_post('/ads', create_ad)
app.router.add_get('/ads', get_all_ads)
app.router.add_get('/ads/{ad_id}', get_ad)
app.router.add_put('/ads/{ad_id}', update_ad)
app.router.add_delete('/ads/{ad_id}', delete_ad)


if __name__ == '__main__':
    web.run_app(app, host='127.0.0.1', port=5000)