from bot.data import db
from bot.data.penguin import PenguinIntegrations
from bot.misc.penguin import Penguin


async def getPenguinFromInter(inter):
    penguin_id = await db.select([PenguinIntegrations.penguin_id]).where(
        ((PenguinIntegrations.discord_id == str(inter.user.id)) &
         (PenguinIntegrations.current == True))).gino.scalar()
    if penguin_id is None:
        await inter.response.send_message(
            content=f"Мы не нашли вашего пингвина. Пожалуйста воспользуйтесь командой `/login`", ephemeral=True)
        return 
    p = await Penguin().get(penguin_id)
    await p.setup()
    return p


async def getPenguinOrNoneFromInter(inter):
    penguin_id = await db.select([PenguinIntegrations.penguin_id]).where(
        ((PenguinIntegrations.discord_id == str(inter.user.id)) &
         (PenguinIntegrations.current == True))).gino.scalar()
    if penguin_id is None:
        return None
    p = await Penguin().get(penguin_id)
    await p.setup()
    return p
