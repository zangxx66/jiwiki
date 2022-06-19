from hoshino import Service, aiorequests, logger
from hoshino.util import FreqLimiter
from nonebot.message import CQEvent

sv = Service('小鸡词典')
help_txt = """
小鸡词典使用指北
xxx是什么梗 查询xxx的含义
""".strip()
host = 'https://api.jikipedia.com/go/search_entities'
header = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
    'content-type': 'application/json',
    'referer': 'https://jikipedia.com/',
    'Client': 'web',
    'Client-Version': '2.7.2d',
    'XID': 'OLk5qKoDNfdUKFydz/lB6VFfmrl4IrGnfb/aCR5mzwOLxsqVWLgrPHE4V4zMkCPr2qexM57y5NM210aN67vGiSFMj0HkpGNyXHe6VTdrCzc='
}
freq = FreqLimiter(60)


@sv.on_fullmatch(('小鸡词典', '小鸡字典'))
async def help(bot, event: CQEvent):
    await bot.send(event, help_txt)


@sv.on_suffix(('是什么梗'))
async def query(bot, event: CQEvent):
    keyword = event.message.extract_plain_text().strip()
    if not keyword:
        return
    request_data = {'page': 1, 'phrase': keyword, 'size': 60}
    gid = event.group_id
    if not freq.check(gid):
        await bot.finish(event, f'冷却时间中，请{int(freq.left_time(gid)) + 1}秒后再来')
    try:
        resp = await aiorequests.post(host, headers=header, json=request_data, timeout=10)
        res = await resp.json()
    except Exception as ex:
        logger.exception(ex)
        await bot.finish(event, '查询错误，请重试')

    if 'data' not in res:
        msg = res['message']
        content = msg['content']
        await bot.finish(event, content)

    freq.start_cd(gid)

    data = res['data']
    if len(data) == 0:
        await bot.finish(event, f'没有查询到关于{keyword}的结果')

    result_txt = ''
    definitions = {}
    for el in data:
        if el['category'] != 'definition':
            continue
        if len(el['definitions']) == 0:
            continue
        definitions.update(el['definitions'][0])
        break

    if len(definitions) == 0:
        await bot.finish(event, f'没有查询到关于{keyword}的结果')

    term = definitions['term']
    title = term['title']
    if title != keyword:
        result_txt = f'没有找到{keyword}，我猜你可能在找{title}\n'
    result_txt += definitions['plaintext']
    await bot.finish(event, result_txt)
