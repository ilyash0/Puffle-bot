from loguru import logger
from bot.data import penguin
from bot.data.item import PenguinItemCollection
from bot.data.mail import PenguinPostcard
from bot.data.penguin import PenguinIntegrations
from bot.data.plugin import PenguinAttributeCollection
from bot.data.stamp import PenguinStampCollection


class Penguin(penguin.Penguin):
    __slots__ = (
        'muted',

        'login_key',

        'is_member',
        'membership_days_total',
        'membership_days_remain',
    )

    def __init__(self, *args):
        super().__init__(*args)

        self.muted = False

        self.login_key = None

        self.is_member = False
        self.membership_days_total = 0
        self.membership_days_remain = -1

        self.can_dig_gold = False
        # self.server = server
        self.logger = logger

    async def setup(self):
        self.inventory = await PenguinItemCollection.get_collection(self.id)
        self.stamps = await PenguinStampCollection.get_collection(self.id)
        self.attributes = await PenguinAttributeCollection.get_collection(self.id)

    def safe_name(self):
        return self.safe_nickname()

    def member(self):
        return int(self.is_member)

    def count_epf_awards(self):
        result: int = 0
        AWARD_STAMP_IDS = list(range(801, 807)) + list(range(808, 812)) + list(range(813, 821)) + [822, 823, 8007, 8008]

        for stamp in AWARD_STAMP_IDS:
            if stamp in self.inventory:
                result += 1
        return result

    async def add_inventory(self, item, cost=None):
        if item.id in self.inventory:
            return False

        cost = cost if cost is not None else item.cost

        await self.inventory.insert(item_id=item.id)
        await self.update(coins=self.coins - cost).apply()

        self.logger.info(f'{self.username} added \'{item.name}\' to their clothing inventory')

        return True

    async def add_epf_inventory(self, item, cost=None):
        if not item.epf:
            return False

        if item.id in self.inventory:
            return False

        cost = cost if cost is not None else item.cost

        await self.inventory.insert(item_id=item.id)
        await self.update(agent_medals=self.agent_medals - cost).apply()

        return True

    async def add_igloo(self, igloo, cost=None):
        if igloo.id in self.igloos:
            return False

        cost = cost if cost is not None else igloo.cost

        await self.igloos.insert(igloo_id=igloo.id)
        await self.update(coins=self.coins - cost).apply()

        self.logger.info(f'{self.username} added \'{igloo.name}\' to their igloos inventory')

        return True

    async def add_puffle_item(self, care_item, quantity=1, cost=None):
        if care_item.type not in ['food', 'head', 'play']:
            return False

        care_item_id = care_item.parent_id
        quantity = quantity * care_item.quantity

        if care_item.type == 'play' and care_item_id in self.puffle_items:
            return False

        if care_item_id in self.puffle_items:
            penguin_care_item = self.puffle_items[care_item_id]
            if penguin_care_item.quantity >= 100:
                return False

            await penguin_care_item.update(
                quantity=penguin_care_item.quantity + quantity).apply()
        else:
            penguin_care_item = await self.puffle_items.insert(item_id=care_item_id,
                                                               quantity=quantity)

        cost = cost if cost is not None else care_item.cost
        await self.update(coins=self.coins - cost).apply()

        self.logger.info(f'{self.username} added \'{care_item.name}\' to their puffle care inventory')

        return True

    async def add_furniture(self, furniture, quantity=1, cost=None):
        if furniture.id in self.furniture:
            penguin_furniture = self.furniture[furniture.id]
            if penguin_furniture.quantity >= furniture.max_quantity:
                return False

            await penguin_furniture.update(
                quantity=penguin_furniture.quantity + quantity).apply()
        else:
            await self.furniture.insert(furniture_id=furniture.id)

        cost = cost if cost is not None else furniture.cost
        await self.update(coins=self.coins - cost).apply()

        self.logger.info(f'{self.username} added \'{furniture.name}\' to their furniture inventory')

        return True

    async def add_card(self, card, quantity=0, member_quantity=0):
        quantity = max(1, quantity + member_quantity)
        if card.id in self.cards:
            penguin_card = self.cards[card.id]

            await penguin_card.update(
                quantity=penguin_card.quantity + quantity,
                member_quantity=penguin_card.member_quantity + member_quantity).apply()
        else:
            await self.cards.insert(card_id=card.id, quantity=quantity, member_quantity=member_quantity)

        self.logger.info(f'{self.username} added \'{card.name}\' to their ninja deck')

        return True

    async def add_flooring(self, flooring, cost=None):
        if flooring.id in self.flooring:
            return False

        cost = cost if cost is not None else flooring.cost

        await self.flooring.insert(flooring_id=flooring.id)
        await self.update(coins=self.coins - cost).apply()

        self.logger.info(f'{self.username} added \'{flooring.name}\' to their flooring inventory')

        return True

    async def add_location(self, location, cost=None):
        if location.id in self.locations:
            return False

        cost = cost if cost is not None else location.cost

        await self.locations.insert(location_id=location.id)
        await self.update(coins=self.coins - cost).apply()

        self.logger.info(f'{self.username} added \'{location.name}\' to their location inventory')

        return True

    async def add_stamp(self, stamp):
        if stamp.id in self.stamps:
            return False

        await self.stamps.insert(stamp_id=stamp.id)

        self.logger.info(f'{self.username} earned stamp \'{stamp.name}\'')

        return True

    async def add_inbox(self, postcard_id, sender_id=None, details=""):
        await PenguinPostcard.create(penguin_id=self.id, sender_id=sender_id, postcard_id=postcard_id, details=details)

    def get_custom_attribute(self, name, default=None):
        penguin_attribute = self.attributes.get(name, default)
        if penguin_attribute == default:
            return default
        return penguin_attribute.value

    async def set_custom_attribute(self, name, value):
        if name not in self.attributes:
            await self.attributes.insert(name=name, value=value)
        else:
            attribute = self.attributes[name]
            await attribute.update(value=value).apply()

        self.logger.info(f'{self.username} set custom attribute \'{name}\' to \'{value}\'')

        return True

    async def delete_custom_attribute(self, name):
        if name in self.attributes:
            await self.attributes.delete(name)

        self.logger.info(f'{self.username} deleted attribute \'{name}\'')

        return True

    async def add_coins(self, coins):
        await self.update(coins=self.coins + coins).apply()
        return self.coins

    async def set_integration(self, userID, currentStatus=False):
        await PenguinIntegrations.create(penguin_id=self.id, discord_id=str(userID), current=currentStatus)

    async def set_integration_current_status(self, userID, currentStatus):
        await (await PenguinIntegrations.get([self.id, str(userID)])).update(current=currentStatus).apply()

    async def delete_integration(self, userID):
        await (await PenguinIntegrations.get([self.id, str(userID)])).delete()

    def __repr__(self):
        if self.id is not None:
            return f'<Penguin ID=\'{self.id}\' Username=\'{self.username}\'>'
        return super().__repr__()
