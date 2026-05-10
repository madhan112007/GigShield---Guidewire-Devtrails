import asyncio
import sys
sys.path.insert(0, '.')
from app.services.platform_service import get_city_economics_async

async def test():
    cities = ['Mumbai', 'Mysore', 'Nashik', 'Jodhpur', 'Mysore']
    for city in cities:
        col, sub = await get_city_economics_async(city)
        print(city + ' -> col=' + str(col) + ', subsistence=' + str(sub))

asyncio.run(test())
